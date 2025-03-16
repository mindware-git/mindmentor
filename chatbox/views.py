import os
import platform
from django.shortcuts import render
from django.http import JsonResponse

from .robot import Robot, RobotStatus
from .models import Lecture

robot = Robot()


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
    # Get platform information
    platform_info = {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor(),
        "npu": "Not Available",  # This can be updated based on specific NPU detection logic
    }

    # Get software information
    software_info = {
        "django_version": "Don't needs to know",
    }

    context = {
        "platform": platform_info,
        "software": software_info,
        "device_statuses": [],  # This can be populated with actual device statuses
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

    # Look for .ipynb files in the course directory and add them to Lecture DB
    course_dir = os.path.join("chatbox", "static", "chatbox", "mm-course")
    if os.path.exists(course_dir):
        for root, dirs, files in os.walk(course_dir):
            for file in files:
                if file.endswith(".ipynb"):
                    # Extract course name from directory path
                    course_path = os.path.relpath(root, course_dir)
                    course_name = (
                        course_path.split(os.sep)[0]
                        if course_path != "."
                        else "default"
                    )

                    # Create lecture with proper title and description
                    lecture_name = os.path.splitext(file)[0]
                    lecture_path = os.path.join(root, file)
                    Lecture.objects.get_or_create(
                        title=lecture_name,
                        defaults={
                            "description": {
                                "file_path": lecture_path,
                                "course": course_name,
                                "content": [],
                            }
                        },
                    )
    return render(request, "chatbox/home.html")


def lectures(request):
    lectures = Lecture.objects.all()
    context = {"lectures": lectures}
    return render(request, "chatbox/lectures.html", context)


def lecture(request, lecture_id):
    lecture = Lecture.objects.get(id=lecture_id)
    context = {"lecture": lecture}
    return render(request, "chatbox/lecture.html", context)


def start_lecture(request, lecture_id):
    """Start a lecture session."""
    if request.method == "GET":
        try:
            lecture = Lecture.objects.get(id=lecture_id)
            status = RobotStatus.objects.get(name="mindmentor")

            status.memory["ipynb"] = lecture.description["file_path"]
            status.save()

            if robot.restore_lecture_and_resume():
                return JsonResponse({"message": "Lecture started successfully"})
            else:
                return JsonResponse({"error": "Robot busy"}, status=500)

        except Lecture.DoesNotExist:
            return JsonResponse({"error": "Lecture not found"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"error": "Server error", "details": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)


def stop_lecture(request, lecture_id):
    """Start a lecture session."""
    if request.method == "GET":
        try:
            # TODO: check start, stop pair
            # lecture = Lecture.objects.get(id=lecture_id)
            if robot.save_lecture_and_exit():
                return JsonResponse({"message": "Lecture started successfully"})
            else:
                return JsonResponse({"message": "Lecture stopped successfully"})

        except Lecture.DoesNotExist:
            return JsonResponse({"error": "Lecture not found"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"error": "Server error", "details": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)


def reset_lecture(request, lecture_id):
    """Reset a lecture session."""
    if request.method == "GET":
        try:
            status = RobotStatus.objects.get(name="mindmentor")
            if status.state != "lecturer":
                return JsonResponse({"error": "Robot busy"}, status=500)
            status.state = "idle"
            status.memory["current_lesson"] = 0
            status.memory["current_code_style"] = "sof"
            status.memory["current_code_info"] = 0

            status.save()
            return JsonResponse({"message": "Lecture reset successfully"})

        except Lecture.DoesNotExist:
            return JsonResponse({"error": "Lecture not found"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"error": "Server error", "details": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)
