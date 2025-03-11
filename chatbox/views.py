from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .robot import Robot, play_audio, play_audio_async, get_mode, set_mode
from .models import RobotStatus


def auth(request):
    """Allow users to select their role (teacher or learner)."""
    if request.method == "POST":
        role = request.POST.get("role")
        if role not in ["teacher", "learner"]:
            return JsonResponse({"error": "Invalid role"}, status=400)
        request.session["role"] = role
        return JsonResponse({"message": f"Logged in as {role}"})
    return JsonResponse({"error": "Invalid request method"}, status=405)


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


def ask_question(request):
    if request.method == "GET":
        robot = Robot()
        response = robot.get_question()
        return JsonResponse(
            {"status": response["status"]}, status=response["status_code"]
        )
    return JsonResponse({"status": "failed"}, status=400)


def home(request):
    robot = Robot()
    robot.init_db()
    return render(request, "chatbox/home.html")  # Render the home.html template
