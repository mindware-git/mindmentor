from django.shortcuts import render
import os
import pyaudio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
        elif mm_mode == "lecturer":
            print("let's start talking classs meterials")
        MM_MODE = mm_mode
        return JsonResponse({"status": "success"})
    elif request.method == "GET":
        print("current mode " + MM_MODE)
        return JsonResponse({"current_mode": MM_MODE})
    return JsonResponse({"status": "failed"}, status=400)
