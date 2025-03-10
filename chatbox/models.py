from django.db import models
from django.db.models import JSONField

"""
Example of lecture
title 'Add and subtract'
content will be
index, transcript, voice, teaching material

0 , 'What we want to do in ...', voice data, like this video

https://www.youtube.com/watch?v=dDv4FTqKBmY&t=5s
"""


class Lecture(models.Model):
    title = models.CharField(max_length=200)


class RobotStatus(models.Model):
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    device = JSONField(default=dict)
    memory = JSONField(default=dict)
    description = JSONField(default=dict)

    def __str__(self):
        return self.name
