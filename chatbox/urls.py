from django.urls import path, include
from . import views

urlpatterns = [
    path("api/v1/", include("chatbox.api_urls")),
    path("home", views.home),
    path("users/teacher", views.teachers),
    path("users/learner", views.learners),
    path("robot/status", views.robot_status),
]
