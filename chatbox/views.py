from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .robot import play_audio, play_audio_async, get_mode, set_mode
from .models import DeviceStatus


def robot_status(request):
    device_statuses = DeviceStatus.objects.all()

    context = {
        "device_statuses": device_statuses,
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
    if request.method == "POST":
        mm_mode = request.POST.get("mode")
        if mm_mode == "teaching_assistant":
            play_audio("chatbox/res/react_sara.wav")
        elif mm_mode == "lecturer":
            play_audio_async("chatbox/res/lecture1.wav")
        set_mode(mm_mode)
        return JsonResponse({"status": "success"})
    elif request.method == "GET":
        return JsonResponse({"current_mode": get_mode()})
    return JsonResponse({"status": "failed"}, status=400)
