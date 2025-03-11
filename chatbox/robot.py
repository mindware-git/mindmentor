import wave
import threading
import pyaudio
import asyncio
from .models import RobotStatus
from nbformat import read
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer


# from queue import PriorityQueue

# task_queue = PriorityQueue()


stop_event = asyncio.Event()


class Robot:
    """
    If there is shared resource (e.g. servo, motor) then it should be managed by DeviceStatus
    """

    def __init__(self):
        print("Init robot...")

    def init_db(self):
        """Initialize the robot status in the database if it doesn't exist."""
        robot_status, created = RobotStatus.objects.get_or_create(
            name="mindmentor",
            defaults={
                "state": "idle",
                "device": {},
                "memory": {},
                "description": {
                    "version": "1.0",
                    "capabilities": ["voice_interaction"],
                    "profile": "voice",
                },
            },
        )
        return robot_status

    def get_question(self):
        """
        Check if robot can accept questions based on its current state.
        If in a valid state, changes to teaching_assistant mode.
        Returns:
            dict: Response with status code 200 if robot can accept questions,
                 400 otherwise
        """
        robot_status = RobotStatus.objects.get(pk=1)
        if robot_status.state in ["idle", "lecturer"]:

            previous_state = robot_status.state

            if robot_status.state == "lecturer":
                asyncio.run(stop_audio())
                robot_status.memory["previous_state"] = previous_state

            robot_status.state = "teaching_assistant"
            robot_status.save()
            return {"status": "success", "status_code": 200}
        return {"status": "failed", "status_code": 400}


def get_mode():
    robot_status = RobotStatus.objects.get(pk=1)
    return robot_status.state


def set_mode(mode):
    robot_status = RobotStatus.objects.get(pk=1)
    robot_status.state = mode
    robot_status.save()


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


async def send_lesson_content(room_group_name):
    await process_notebook(room_group_name)


def _save_lesson_state(notebook_path, current_cell_index):
    """Save the current lesson state to RobotStatus memory"""
    robot_status = RobotStatus.objects.get(pk=1)
    robot_status.memory["current_lesson"] = {
        "notebook_path": notebook_path,
        "cell_index": current_cell_index,
    }
    robot_status.save()
