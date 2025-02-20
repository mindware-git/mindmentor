from django.http import HttpResponse


def learners(request):
    return HttpResponse("Hello, learners.")


def teachers(request):
    return HttpResponse("Hello, teachers.")
