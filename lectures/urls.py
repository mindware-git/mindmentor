from django.urls import path

from . import views

urlpatterns = [
    path("learners/", views.learners, name="learners"),
    path("teachers/", views.teachers, name="teachers"),
]
