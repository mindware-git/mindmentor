from django.shortcuts import render
import os
import pyaudio


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
