import wave
import threading
import pyaudio
import asyncio


# from queue import PriorityQueue

# task_queue = PriorityQueue()


stop_event = asyncio.Event()

MM_MODE = "idle"


class Robot:
    """
    If there is shared resource (e.g. servo, motor) then it should be managed by DeviceStatus
    """

    def __init__(self):
        print("Init robot...")


def get_mode():
    return MM_MODE


def set_mode(mode):
    global MM_MODE
    MM_MODE = mode


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
