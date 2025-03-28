"""
Robot interface.
Robot can handle on server side using api.
api will be ask, start, stop lecture.

Also robot will send message to client using websocket.
Status is maintained in database so that it can be accessed by multiple.
"""

import os
from collections import deque
import time
import wave
import threading
import sys

from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
import numpy as np
import nbformat
from nbclient import NotebookClient
import pyaudio
import sounddevice
import groq
import tomllib
import platform

from django.conf import settings
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer

from .models import RobotStatus

try:
    from rpi_hardware_pwm import HardwarePWM

    RPI5_AVAILABLE = True
except ImportError:
    RPI5_AVAILABLE = False


class Mindbot:

    def __init__(self):
        self.lock = threading.Lock()
        self.memory = [{"state": "idle"}]

        self.lecture_thread = None
        self.stop_event = threading.Event()
        self.vad_thread = None
        self.vad_event = threading.Event()

    def boot(self):
        """
        This bring system fixed configuration.
        All file configuration must be load and not other place.
        Instead of here, please make things on run-time.
        """

        with open("mindbot.toml", "rb") as f:
            data = tomllib.load(f)
        # self.measure_silence()
        self.silence_minmax = data["silence"]
        self.device_tree = {"soc": platform.platform()}

    def speak_from_wav(self, wav_file_path, sector=0) -> int:
        with wave.open(wav_file_path, "rb") as wf:
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
            wf.setpos(sector * chunk_size)
            data = wf.readframes(chunk_size)

            while data:
                stream.write(data)
                sector += 1
                if self.stop_event.is_set():
                    return sector

                data = wf.readframes(chunk_size)

            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()

        return 0

    def measure_silence(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )
        print("Please keep quite for 5 seconds")
        min_v = sys.maxsize
        max_v = 0

        start_time = time.time()
        while time.time() - start_time < 5:
            data = stream.read(1024)
            current_value = np.sum(np.abs(np.frombuffer(data, dtype=np.int16)))
            if current_value < min_v:
                min_v = current_value
            if current_value > max_v:
                max_v = current_value

        minmax = (int(min_v), int(max_v))
        print(minmax)
        return minmax

    def webrtc_vad(self):
        import webrtcvad
        import pyaudio
        import os

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )

        p = pyaudio.PyAudio()
        vad = webrtcvad.Vad(0)

        frames = []
        print("start...")
        while True:
            data = stream.read(int(48000 / 100))
            is_speech = vad.is_speech(data, sample_rate=48000)
            if is_speech:
                frames.append(data)
            else:
                break
        print("end...")
        stream.stop_stream()
        stream.close()
        p.terminate()

    def voice_activity_detection(self, vad_second=2):

        self.vad_event.clear()

        # This should be always on thread.
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )

        print("Detecting voice activity...")

        # 1024 samples / 48000 Hz
        window_size = vad_second * 48000 // 1024

        frames = []
        less_than_speak = self.silence_minmax[1] * 4
        threshold = less_than_speak * window_size

        audio_window = deque(maxlen=window_size)
        audio_window.extend([less_than_speak // 10] * audio_window.maxlen)
        window_value = less_than_speak * window_size // 10

        while True:
            data = stream.read(1024)
            frames.append(data)

            current_value = np.sum(np.abs(np.frombuffer(data, dtype=np.int16)))
            last_value = audio_window.popleft()
            audio_window.append(current_value)
            window_value = window_value + current_value - last_value
            print(current_value, last_value, window_value, threshold)

            if window_value > threshold:
                break
        print("Voice detected")
        self.vad_event.set()

    def ved_listen_to_wav(self, wav_file_path, ved_second=10):
        """
        Voice Endpointing Detection
        """
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )
        print("Now make sound for record")

        # 1024 samples / 48000 Hz
        window_size = ved_second * 48000 // 1024

        frames = []
        # 50938 on mac
        more_than_slience = self.silence_minmax[1]
        threshold = more_than_slience * window_size

        audio_window = deque(maxlen=window_size)  # Sliding window for audio data
        audio_window.extend([more_than_slience * 10] * audio_window.maxlen)
        window_value = more_than_slience * 10 * window_size

        while True:
            data = stream.read(1024)
            frames.append(data)

            current_value = np.sum(np.abs(np.frombuffer(data, dtype=np.int16)))
            last_value = audio_window.popleft()
            audio_window.append(current_value)
            window_value = window_value + current_value - last_value
            # print(current_value, last_value, window_value, threshold)

            if window_value < threshold:
                break

        # Save the recorded data as a WAV file
        wave_file = wave.open(wav_file_path, "wb")
        wave_file.setnchannels(1)
        wave_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(48000)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

    # start, stop lecture
    # agent mode is can not control

    def start_lecture(self, lecture_info) -> bool:
        if self.memory[-1]["state"] != "idle":
            print("Not idle so can not jump to lecturer")
            return False

        self.memory.append({"state": "lecturer"})
        self.memory[-1].update(lecture_info)

        if self.lecture_thread is None or not self.lecture_thread.is_alive():
            self.stop_event.clear()
            self.lecture_thread = threading.Thread(target=self.lecture)
            self.lecture_thread.start()
            return True
        else:
            print("should not be here!")
        return False

    def stop_lecture(self) -> dict:
        if self.memory[-1]["state"] != "lecturer":
            print("Not lecturing")
            return {}

        if self.lecture_thread and self.lecture_thread.is_alive():
            self.stop_event.set()
        else:
            print("stop_lecture : Lecture thread is not running.")

        # Wait for the thread to finish
        if self.lecture_thread:
            self.lecture_thread.join()  # Wait for the thread to finish

        last_memory = self.memory.pop()
        return last_memory

    def lecture(self):
        ipynb = self.memory[-1]["ipynb"]
        code_idx = self.memory[-1]["current_lesson"]
        code_style = self.memory[-1]["current_code_style"]
        code_info = self.memory[-1]["current_code_info"]

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

                code_style = self.memory[-1]["current_code_style"] = "code"

            elif code_style == "code":
                try:
                    with open(ipynb) as f:
                        notebook = nbformat.read(f, as_version=4)
                except FileNotFoundError:
                    print("Lesson file not found.")
                    return

                ipynb_prefix = ipynb.split(os.sep)[:-1]
                static_prefix = ipynb_prefix[2:]
                ipynb_dir = os.path.join(*ipynb_prefix)
                static_dir = os.path.join(*static_prefix)

                for idx, cell in enumerate(notebook.cells):

                    # jump to status.memory["current_lesson"]
                    if idx < code_idx:
                        continue

                    if cell.cell_type == "code":
                        source = cell.source
                        if "Image(" in source:
                            image_path = source.split('"')[1]
                            full_image_path = os.path.join(static_dir, image_path)
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
                            full_audio_path = os.path.join(ipynb_dir, audio_path)

                            # if audio extension is mp3
                            if full_audio_path.endswith(".mp3"):
                                audio = AudioSegment.from_file(
                                    full_audio_path, format="mp3"
                                )
                                audio.export("lesson.wav", format="wav")
                                full_audio_path = "lesson.wav"

                            audio_head = self.speak_from_wav(full_audio_path, code_info)
                            self.memory[-1]["current_code_info"] = audio_head
                            if audio_head != 0:
                                return

                        elif "print(" in source:
                            assert (
                                cell.outputs is not None and len(cell.outputs) > 0
                            ), "ipynb should executed all"
                            print_text = cell.outputs[0].text

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

                    self.memory[-1]["current_lesson"] = idx + 1
                    if self.stop_event.is_set():
                        return

                code_style = self.memory[-1]["current_code_style"] = "eof"

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
        robot_status, created = RobotStatus.objects.update_or_create(
            name="mindmentor",
            defaults={
                "state": "idle",
                "device": {"servo": False},
                "memory": {
                    "prev_state": "idle",
                    "ipynb": "",
                    "current_lesson": 0,
                    "current_code_style": "sof",
                    "current_code_info": 0,
                },
                "description": {
                    "version": "1.0",
                    "capabilities": ["voice_interaction"],
                    "profile": "voice",
                    "local_llm": True,
                },
            },
        )
        if not created:
            print("Robot status already exists.")

    def get_state(self) -> str:
        rv = ""
        status = RobotStatus.objects.get(name="mindmentor")
        rv = status.state
        return rv

    def ta(self) -> bool:
        status = RobotStatus.objects.get(name="mindmentor")
        if status.state != "idle":
            print("Not idle so can not jump to TA")
            return False
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
        if status.state != "idle":
            print("Not idle so can not jump to lecturer")
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
            print("save_lecture_and_exit : Lecture thread is not running.")

        # Wait for the thread to finish
        if self.lecture_thread:
            self.lecture_thread.join()  # Wait for the thread to finish

        status = RobotStatus.objects.get(name="mindmentor")
        status.state = "idle"
        status.save()
        return True

    def ved_listen_to_wav(self, wav_file_path, ved_second=3):
        """
        Voice Endpointing Detection
        when silence current_value 156957 ~ 641132
        TODO: VAD should combinate with this to remove ask button.
        """
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )
        print("Now make sound for record")

        # 1024 samples / 48000 Hz
        window_size = ved_second * 48000 // 1024

        frames = []
        # 50938 on mac
        more_than_slience = 641132
        threshold = more_than_slience * window_size

        audio_window = deque(maxlen=window_size)  # Sliding window for audio data
        audio_window.extend([more_than_slience * 10] * audio_window.maxlen)
        window_value = more_than_slience * 10 * window_size

        while True:
            data = stream.read(1024)
            frames.append(data)

            current_value = np.sum(np.abs(np.frombuffer(data, dtype=np.int16)))
            last_value = audio_window.popleft()
            audio_window.append(current_value)
            window_value = window_value + current_value - last_value
            # print(current_value, last_value, window_value, threshold)

            if window_value < threshold:
                break

        # Save the recorded data as a WAV file
        wave_file = wave.open(wav_file_path, "wb")
        wave_file.setnchannels(1)
        wave_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(48000)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

    def listen_to_wav(self, wav_file_path, record_second=5):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )
        print("Now make sound for record")
        # Record for 5 seconds
        frames = []
        start_time = time.time()
        while time.time() - start_time < record_second:
            data = stream.read(1024)
            frames.append(data)

        # Save the recorded data as a WAV file
        with wave.open(wav_file_path, "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wave_file.setframerate(48000)
            wave_file.writeframes(b"".join(frames))
            wave_file.close()
        p.terminate()

    def speak_from_wav(self, wav_file_path):
        with wave.open(wav_file_path, "rb") as wf:
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

    def assistant(self):

        if RPI5_AVAILABLE:
            pwm = HardwarePWM(pwm_channel=2, hz=50, chip=2)
            pwm.start(7.5)
            pwm.change_duty_cycle(12)

        # speak what's your question
        self.speak_from_wav("chatbox/res/react_sara.wav")

        # self.listen_to_wav("question.wav")
        self.ved_listen_to_wav("question.wav")

        status = RobotStatus.objects.get(name="mindmentor")
        local_llm = status.description["local_llm"]
        prev_state = status.memory["prev_state"]
        if prev_state == "idle":
            status.state = "idle"
        else:
            status.state = "lecturer"
        status.memory["prev_state"] = "idle"
        status.save()

        if local_llm:
            self.speak_from_wav("question.wav")
        else:
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

            # Now llm generate answer
            # TODO: stream API, RAG
            chat_completion = client.chat.completions.create(
                #
                # Required parameters
                #
                messages=[
                    # Set an optional system message. This sets the behavior of the
                    # assistant and can be used to provide specific instructions for
                    # how it should behave throughout the conversation.
                    {"role": "system", "content": "you are a helpful class teacher."},
                    # Set a user message for the assistant to respond to.
                    {
                        "role": "user",
                        "content": completion,
                    },
                ],
                # The language model which will generate the completion.
                model="llama-3.3-70b-versatile",
                #
                # Optional parameters
                #
                # Controls randomness: lowering results in less random completions.
                # As the temperature approaches zero, the model will become deterministic
                # and repetitive.
                temperature=0.5,
                # The maximum number of tokens to generate. Requests can use up to
                # 32,768 tokens shared between prompt and completion.
                max_completion_tokens=64,
                # Controls diversity via nucleus sampling: 0.5 means half of all
                # likelihood-weighted options are considered.
                top_p=1,
                # A stop sequence is a predefined or user-specified text string that
                # signals an AI to stop generating content, ensuring its responses
                # remain focused and concise. Examples include punctuation marks and
                # markers like "[end]".
                stop=None,
                # If set, partial message deltas will be sent.
                stream=False,
            )

            # Print the completion returned by the LLM.
            answer = chat_completion.choices[0].message.content
            print(answer)

            # make answer
            # gtts only makes mp3 file
            speech = gTTS(text=answer, slow=False)
            audio_fp = BytesIO()
            speech.write_to_fp(audio_fp)
            audio_fp.seek(0)
            audio = AudioSegment.from_file(audio_fp, format="mp3")
            audio.export("answer.wav", format="wav")

            self.speak_from_wav("answer.wav")

        print("TA done")

        if RPI5_AVAILABLE:
            pwm.change_duty_cycle(7.5)

        # Check previous state and if lecturer then jump to lecture
        if prev_state == "lecturer":
            self.lecture()

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
                        notebook = nbformat.read(f, as_version=4)
                except FileNotFoundError:
                    print("Lesson file not found.")
                    return

                ipynb_prefix = ipynb.split(os.sep)[:-1]
                static_prefix = ipynb_prefix[2:]
                ipynb_dir = os.path.join(*ipynb_prefix)
                static_dir = os.path.join(*static_prefix)

                for idx, cell in enumerate(notebook.cells):

                    # jump to status.memory["current_lesson"]
                    if idx < code_idx:
                        continue

                    if cell.cell_type == "code":
                        source = cell.source
                        if "Image(" in source:
                            image_path = source.split('"')[1]
                            full_image_path = os.path.join(static_dir, image_path)
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
                            full_audio_path = os.path.join(ipynb_dir, audio_path)

                            # if audio extension is mp3
                            if full_audio_path.endswith(".mp3"):
                                audio = AudioSegment.from_file(
                                    full_audio_path, format="mp3"
                                )
                                audio.export("lesson.wav", format="wav")
                                full_audio_path = "lesson.wav"

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
                            assert (
                                cell.outputs is not None and len(cell.outputs) > 0
                            ), "ipynb should executed all"
                            print_text = cell.outputs[0].text

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
