import wave
import threading
import pyaudio
import asyncio
from .models import RobotStatus


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
