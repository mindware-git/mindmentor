from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .robot import Robot, play_audio, play_audio_async, get_mode, set_mode
from .models import RobotStatus, Lecture


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
            # robot = Robot()

            # # Initialize the lecture in robot
            # response = robot.start_lecture(lecture)

            # if response.get("status") == "success":
            #     return JsonResponse(
            #         {
            #             "message": "Lecture started successfully",
            #             "lecture_id": lecture_id,
            #         }
            #     )
            # else:
            #     return JsonResponse(
            #         {
            #             "error": "Failed to start lecture",
            #             "details": response.get("message", "Unknown error"),
            #         },
            #         status=500,
            #     )

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
            lecture = Lecture.objects.get(id=lecture_id)
            # robot = Robot()

            # # Initialize the lecture in robot
            # response = robot.start_lecture(lecture)

            # if response.get("status") == "success":
            #     return JsonResponse(
            #         {
            #             "message": "Lecture started successfully",
            #             "lecture_id": lecture_id,
            #         }
            #     )
            # else:
            #     return JsonResponse(
            #         {
            #             "error": "Failed to start lecture",
            #             "details": response.get("message", "Unknown error"),
            #         },
            #         status=500,
            #     )

        except Lecture.DoesNotExist:
            return JsonResponse({"error": "Lecture not found"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"error": "Server error", "details": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)
