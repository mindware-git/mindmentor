"""
Robot interface.
Robot can handle on server side using api.
api will be ask, start, stop lecture.

Also robot will send message to client using websocket.
Status is maintained in database so that it can be accessed by multiple.
"""

import time
import wave
import pyaudio
import asyncio
import sounddevice
from .models import RobotStatus
from nbformat import read
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
import threading
import groq
from django.conf import settings
from gtts import gTTS


class Robot:
    """
    If there is shared resource (e.g. servo, motor) then it should be managed by DeviceStatus
    """

    def __init__(self):
        print("Init robot...")
        self.memory = 0  # 마지막에 센 숫자를 저장
        self.lecture_thread = None  # lecture 쓰레드 객체
        self.stop_event = threading.Event()  # 쓰레드 종료 신호
        self.wav_file_path = "chatbox/res/lecture1.wav"

    def init_db(self):
        """Initialize the robot status in the database if it doesn't exist."""
        robot_status, created = RobotStatus.objects.get_or_create(
            name="mindmentor",
            defaults={
                "state": "idle",
                "device": {},
                "memory": {
                    "ipynb": "",
                    "current_lesson": 0,
                    "current_code_style": "sof",
                    "current_code_info": 0,
                },
                "description": {
                    "version": "1.0",
                    "capabilities": ["voice_interaction"],
                    "profile": "voice",
                },
            },
        )

    def get_state(self) -> str:
        rv = ""
        status = RobotStatus.objects.get(name="mindmentor")
        rv = status.state
        return rv

    def ta(self) -> bool:
        status = RobotStatus.objects.get(name="mindmentor")
        status.state = "teaching_assistant"
        status.save()

        if self.lecture_thread is None or not self.lecture_thread.is_alive():
            self.stop_event.clear()
            self.lecture_thread = threading.Thread(target=self.assistant)
            self.lecture_thread.start()
            return True
        else:
            print("should not be here!")
        return False

    def restore_lecture_and_resume(self) -> bool:
        status = RobotStatus.objects.get(name="mindmentor")
        if status.state == "lecturer":
            print("Already lecturing")
            return False

        status.state = "lecturer"
        status.save()

        if self.lecture_thread is None or not self.lecture_thread.is_alive():
            self.stop_event.clear()
            self.lecture_thread = threading.Thread(target=self.lecture)
            self.lecture_thread.start()
            return True
        else:
            print("should not be here!")
        return False

    def save_lecture_and_exit(self) -> bool:
        status = RobotStatus.objects.get(name="mindmentor")
        if status.state != "lecturer":
            print("Not lecturing")
            return False

        if self.lecture_thread and self.lecture_thread.is_alive():
            self.stop_event.set()
        else:
            print("Lecture thread is not running.")

        # Wait for the thread to finish
        if self.lecture_thread:
            self.lecture_thread.join()  # Wait for the thread to finish

        status = RobotStatus.objects.get(name="mindmentor")
        status.state = "idle"
        status.save()
        return True

    def assistant(self):

        # speak what's your question

        # Open the WAV file
        wf = wave.open("chatbox/res/react_sara.wav", "rb")

        # Create a PyAudio object
        p = pyaudio.PyAudio()

        # Open a stream to play the audio
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        # Read data in chunks
        chunk_size = 1024

        data = wf.readframes(chunk_size)

        while data:
            stream.write(data)
            if self.stop_event.is_set():
                return

            data = wf.readframes(chunk_size)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()

        # listening
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
        )
        print("Now make sound for record")
        # Record for 5 seconds
        frames = []
        start_time = time.time()
        while time.time() - start_time < 5:
            data = stream.read(1024)
            frames.append(data)

        # Save the recorded data as a WAV file
        wave_file = wave.open("question.wav", "wb")
        wave_file.setnchannels(1)
        wave_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(44100)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

        client = groq.Client(api_key=settings.GROQ_API_KEY)
        filename = "question.wav"  # Replace with the path to your audio file
        with open(filename, "rb") as f:
            try:
                completion = client.audio.transcriptions.create(
                    model="distil-whisper-large-v3-en",
                    file=(filename, f.read()),
                    response_format="text",
                )
                print(completion)
            except Exception as e:
                return f"Error in transcription: {str(e)}"

        # make answer
        speech = gTTS(text=completion, slow=False)
        speech.save("answer.wav")

        wf = wave.open("answer.wav", "rb")

        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        # Read data in chunks
        chunk_size = 1024

        data = wf.readframes(chunk_size)

        while data:
            stream.write(data)
            if self.stop_event.is_set():
                return

            data = wf.readframes(chunk_size)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()

        print("TA done")

    def stop_ta(self):
        if self.lecture_thread and self.lecture_thread.is_alive():
            self.stop_event.set()
        else:
            print("Lecture thread is not running.")

        # Wait for the thread to finish
        if self.lecture_thread:
            self.lecture_thread.join()  # Wait for the thread to finish

        status = RobotStatus.objects.get(name="mindmentor")
        status.state = "idle"
        status.save()
        return True

    def lecture(self):
        # restore memory
        status = RobotStatus.objects.get(name="mindmentor")
        ipynb = status.memory["ipynb"]
        code_idx = status.memory["current_lesson"]
        code_style = status.memory["current_code_style"]
        code_info = status.memory["current_code_info"]

        room_group_name = "classroom"
        channel_layer = get_channel_layer()

        while code_style != "eof":
            if self.stop_event.is_set():
                return

            if code_style == "sof":
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {"type": "classroom_message", "message": {"type": "sof"}},
                )

                code_style = status.memory["current_code_style"] = "code"
                status.save()

            elif code_style == "code":
                try:
                    with open(ipynb) as f:
                        notebook = read(f, as_version=4)
                except FileNotFoundError:
                    print("Lesson file not found.")
                    return

                for idx, cell in enumerate(notebook.cells):

                    # jump to status.memory["current_lesson"]
                    if idx < code_idx:
                        continue

                    if cell.cell_type == "code":
                        source = cell.source
                        if "Image(" in source:
                            image_path = source.split('"')[1]
                            full_image_path = (
                                "chatbox/mm-course/lang/eng/family/" + image_path
                            )
                            async_to_sync(channel_layer.group_send)(
                                room_group_name,
                                {
                                    "type": "classroom_message",
                                    "message": {
                                        "type": "image",
                                        "path": full_image_path,
                                    },
                                },
                            )
                        elif "Audio(" in source:
                            audio_path = source.split('"')[1]
                            full_audio_path = (
                                "chatbox/static/chatbox/mm-course/lang/eng/family/"
                                + audio_path
                            )

                            # Open the WAV file
                            wf = wave.open(full_audio_path, "rb")

                            # Create a PyAudio object
                            p = pyaudio.PyAudio()

                            # Open a stream to play the audio
                            stream = p.open(
                                format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True,
                            )

                            # Read data in chunks
                            chunk_size = 1024
                            # move wf to code_info
                            wf.setpos(code_info * chunk_size)

                            data = wf.readframes(chunk_size)

                            while data:
                                stream.write(data)
                                code_info += 1
                                if self.stop_event.is_set():
                                    status = RobotStatus.objects.get(name="mindmentor")
                                    status.memory["current_code_info"] = code_info
                                    status.save()
                                    return

                                data = wf.readframes(chunk_size)

                            status = RobotStatus.objects.get(name="mindmentor")
                            code_info = status.memory["current_code_info"] = 0
                            status.save()

                            # Stop and close the stream
                            stream.stop_stream()
                            stream.close()
                            p.terminate()
                            wf.close()

                        elif "print(" in source:
                            print(source)

                            print_text = source.split('print("')[1].split('")')[0]
                            async_to_sync(channel_layer.group_send)(
                                room_group_name,
                                {
                                    "type": "classroom_message",
                                    "message": {"type": "text", "content": print_text},
                                },
                            )
                        elif "clear_output(wait=True)" in source:
                            async_to_sync(channel_layer.group_send)(
                                room_group_name,
                                {
                                    "type": "classroom_message",
                                    "message": {"type": "clear"},
                                },
                            )
                            time.sleep(2)
                        else:
                            print("Unkown code block")
                            print(source)

                    status.memory["current_lesson"] = idx + 1
                    status.save()
                    if self.stop_event.is_set():
                        return

                code_style = status.memory["current_code_style"] = "eof"
                status.save()

        if code_style == "eof":
            print("send eof")

            # Send EOF message after processing all cells
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {"type": "classroom_message", "message": {"type": "eof"}},
            )
            print("Keep eof until exiplit reset")

        else:
            print("unknown style")
