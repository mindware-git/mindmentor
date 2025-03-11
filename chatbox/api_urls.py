from django.urls import path
from . import views

urlpatterns = [
    path("users/learner/ask", views.ask_question),
    path("lectures", views.get_lecture_list),
    path("lectures/<int:lecture_id>", views.get_lecture_content),
    path("lectures/<int:lecture_id>/start", views.start_lecture),
    path("lectures/<int:lecture_id>/stop", views.stop_lecture),
    path("lectures/<int:lecture_id>/question", views.get_questions),
]
