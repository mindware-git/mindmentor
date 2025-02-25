from django.db import models


class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Learner(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


"""
For example math subject, there is 2nd grade course and first lecture.
"""


class Subject(models.Model):
    name = models.CharField(max_length=100)


class Course(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.IntegerField()


"""
Example of lecture
title 'Add and subtract'
content will be
index, transcript, voice, teaching material

0 , 'What we want to do in ...', voice data, like this video

https://www.youtube.com/watch?v=dDv4FTqKBmY&t=5s
"""


class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)


class DeviceStatus(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    note = models.CharField(max_length=100)
