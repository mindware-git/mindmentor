from django.shortcuts import render
import os
import pyaudio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import wave

MM_MODE = "idle"


def index(request):
    p = pyaudio.PyAudio()
    info = []
    for i in range(p.get_device_count()):
        info.append(p.get_device_info_by_index(i))
    context = {
        "os": os.uname(),
        "num_cameras": "? TODO",
        "sound": info,
    }
    return render(request, "hwmon/index.html", context)


@csrf_exempt
def mode(request):
    global MM_MODE

    valid_modes = ["idle", "lecturer", "teaching_assistant"]

    if request.method == "POST":
        print("current mode " + MM_MODE)
        mm_mode = request.POST.get("mode")

        print("mm_mode is " + mm_mode)
        if mm_mode == "teaching_assistant":
            print("listening")
            play_audio("hwmon/res/react_sara.wav")
        elif mm_mode == "lecturer":
            print("let's start talking classs meterials")
            play_audio("hwmon/res/lecture1.wav")
        MM_MODE = mm_mode
        return JsonResponse({"status": "success"})
    elif request.method == "GET":
        print("current mode " + MM_MODE)
        return JsonResponse({"current_mode": MM_MODE})
    return JsonResponse({"status": "failed"}, status=400)


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

    # Play the audio
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()
