from django.urls import path
from . import views

urlpatterns = [
    path("auth", views.auth),
    path("users/tt", views.teachers),
    path("users/tl", views.learners),
    path("users/ask", views.ask_question, name="ask_question"),
    path("users/lecture/start", views.start_lecture, name="start_lecture"),
    path("users/lecture", views.get_lecture, name="get_lecture"),
    path("robot/status", views.robot_status),
    path("robot/mode", views.mode),
]
