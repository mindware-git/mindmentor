from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/auth", views.auth),
    path("api/v1/users/learner/ask", views.ask_question, name="ask_question"),
    path("api/v1/users/teacher/start", views.start_lecture, name="start_lecture"),
    path("api/v1/lectures", views.get_lecture, name="get_lecture"),
    path("api/v1/robot/mode", views.mode),
    path("users/teacher", views.teachers),
    path("users/learner", views.learners),
    path("robot/status", views.robot_status),
]
