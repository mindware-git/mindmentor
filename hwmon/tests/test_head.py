from django.test import TestCase
import pyaudio
import cv2


class SpeakerTestCase(TestCase):
    def setUp(self):
        self.p = pyaudio.PyAudio()

    def tearDown(self):
        self.p.terminate()

    def test_speak_hello(self):
        self.assertEqual(1 + 1, 2)
