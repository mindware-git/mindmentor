from django.shortcuts import render
import os
import pyaudio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import wave
import threading

MM_MODE = "idle"


def robot_status(request):
    p = pyaudio.PyAudio()
    info = []
    for i in range(p.get_device_count()):
        info.append(p.get_device_info_by_index(i))
    context = {
        "os": os.uname(),
        "num_cameras": "? TODO",
        "sound": info,
    }
    return render(request, "chatbox/robot_status.html", context)


def learners(request):
    context = {
        "quiz": "What is 2 + 4 is?",
    }
    return render(request, "chatbox/learner_quiz.html", context)


def teachers(request):
    # teacher = get_object_or_404(Teacher, id=teacher_id)
    # # Assuming you have a way to get the subject, course, and lecture
    # subject = Subject.objects.first()  # Replace with actual logic
    # course = Course.objects.filter(subject=subject).first()  # Replace with actual logic
    # lecture = Lecture.objects.filter(course=course).first()  # Replace with actual logic

    context = {
        "teacher": "Jone doe",
        "subject": "Math",
        "course": "2nd grade",
        "lecture": "Add and subtraction",
    }
    return render(request, "chatbox/teacher_detail.html", context)


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
            play_audio("chatbox/res/react_sara.wav")
        elif mm_mode == "lecturer":
            print("let's start talking classs meterials")
            play_audio_async("chatbox/res/lecture1.wav")
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


def play_audio_async(wav_file_path):
    thread = threading.Thread(target=play_audio, args=(wav_file_path,), daemon=True)
    thread.start()
