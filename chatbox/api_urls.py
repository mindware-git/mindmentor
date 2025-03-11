from django.urls import path
from . import views

urlpatterns = [
    # auth
    path("users/learner/ask", views.ask_question),
    # path("users/teacher/start", views.start_lecture, name="start_lecture"),
    # path("lectures", views.get_lecture, name="get_lecture"),
]
