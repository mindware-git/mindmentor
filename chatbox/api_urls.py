from django.urls import path
from . import views

urlpatterns = [
    path("users/learner/ask", views.ask_question),
    # path("lectures/<int:lecture_id>/start", views.start_lecture),
    # path("lectures/<int:lecture_id>/stop", views.stop_lecture),
]
