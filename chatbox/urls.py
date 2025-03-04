from django.urls import path
from . import views

urlpatterns = [
    path("auth", views.auth),
    path("users/teacher", views.teachers),
    path("users/learner", views.learners),
    path("users/learner/ask", views.ask_question, name="ask_question"),
    path("users/teacher/start", views.start_lecture, name="start_lecture"),
    path("lectures", views.get_lecture, name="get_lecture"),
    path("robot/status", views.robot_status),
    path("robot/mode", views.mode),
]
