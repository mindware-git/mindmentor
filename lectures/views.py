from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

# from .models import Teacher, Subject, Course, Lecture


def learners(request):
    return HttpResponse("Hello, learners.")


def teachers(request):
    # teacher = get_object_or_404(Teacher, id=teacher_id)
    # # Assuming you have a way to get the subject, course, and lecture
    # subject = Subject.objects.first()  # Replace with actual logic
    # course = Course.objects.filter(subject=subject).first()  # Replace with actual logic
    # lecture = Lecture.objects.filter(course=course).first()  # Replace with actual logic

    template = loader.get_template("lectures/teacher_detail.html")

    context = {
        "teacher": "Jone doe",
        "subject": "Math",
        "course": "2nd grade",
        "lecture": "Add and subtraction",
    }
    return HttpResponse(template.render(context, request))
