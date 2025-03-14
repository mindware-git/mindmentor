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

stop_event = asyncio.Event()


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
                    "current_code_style": "",
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

    # def set_ipynb(self):
    #     status = RobotStatus.objects.get(id=1)
    #     status.memory["ipynb"] = (
    #         "chatbox/static/chatbox/mm-course/lang/eng/family/01_family.ipynb"
    #     )
    #     status.save()

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

    def lecture(self):
        # restore memory
        status = RobotStatus.objects.get(name="mindmentor")
        # ipynb = status.memory["ipynb"]
        # code_idx = status.memory["current_lesson"]
        # code_style = status.memory["current_code_style"]
        code_info = status.memory["current_code_info"]

        # go to step

        # basically lecture is just play audio for now
        # TODO: Change it to lecture

        # Open the WAV file
        wf = wave.open(self.wav_file_path, "rb")

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

        while data and not self.stop_event.is_set():
            stream.write(data)
            code_info += 1
            data = wf.readframes(chunk_size)

        status = RobotStatus.objects.get(name="mindmentor")
        status.memory["current_code_info"] = code_info
        status.save()

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()


def play_audio(wav_file_path):

    # Open the WAV file
    wf = wave.open(wav_file_path, "rb")

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
        if stop_event.is_set():
            break
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()


async def play_audio_async(wav_file_path):
    stop_event.clear()
    await asyncio.to_thread(play_audio, wav_file_path)


async def stop_audio():
    stop_event.set()


async def process_notebook(room_group_name):
    notebook_path = "chatbox/static/chatbox/mm-course/lang/eng/family/01_family.ipynb"
    try:
        with open(notebook_path) as f:
            notebook = read(f, as_version=4)
    except FileNotFoundError:
        print("Lesson file not found.")
        return

    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        room_group_name,
        {"type": "classroom_message", "message": {"type": "sof"}},
    )

    for idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            source = cell.source
            if "Image(" in source:
                image_path = source.split('"')[1]
                full_image_path = "chatbox/mm-course/lang/eng/family/" + image_path
                await channel_layer.group_send(
                    room_group_name,
                    {
                        "type": "classroom_message",
                        "message": {"type": "image", "path": full_image_path},
                    },
                )
            elif "Audio(" in source:
                audio_path = source.split('"')[1]
                full_audio_path = (
                    "chatbox/static/chatbox/mm-course/lang/eng/family/" + audio_path
                )
                # Save current lesson state before playing audio
                await sync_to_async(_save_lesson_state)(notebook_path, idx)
                await play_audio_async(full_audio_path)
            elif "print(" in source:
                print_text = source.split('print("')[1].split('")')[0]
                await channel_layer.group_send(
                    room_group_name,
                    {
                        "type": "classroom_message",
                        "message": {"type": "text", "content": print_text},
                    },
                )
            elif "clear_output(wait=True)" in source:
                await channel_layer.group_send(
                    room_group_name,
                    {"type": "classroom_message", "message": {"type": "clear"}},
                )
                await asyncio.sleep(2)

    # Send EOF message after processing all cells
    await channel_layer.group_send(
        room_group_name,
        {"type": "classroom_message", "message": {"type": "eof"}},
    )


def send_lesson_content():
    async_to_sync(process_notebook)("classroom")


def _save_lesson_state(notebook_path, current_cell_index):
    """Save the current lesson state to RobotStatus memory"""
    robot_status = RobotStatus.objects.get(pk=1)
    robot_status.memory["current_lesson"] = {
        "notebook_path": notebook_path,
        "cell_index": current_cell_index,
    }
    robot_status.save()
