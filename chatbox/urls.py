from django.urls import path
from . import views

urlpatterns = [
    path("robot/status", views.robot_status),
    path("users/tt", views.teachers),
    path("users/tl", views.learners),
    path("robot/mode", views.mode),
]
