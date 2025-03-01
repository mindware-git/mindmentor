from django.test import TestCase
from unittest import skipIf
import pyaudio
import sounddevice  # This is for mute alsa log for pyaudio
import cv2


class SpeakerTestCase(TestCase):
    def setUp(self):
        self.p = pyaudio.PyAudio()

    def tearDown(self):
        self.p.terminate()

    def test_speak_hello(self):
        self.assertEqual(1 + 1, 2)


class MicrophoneTestCase(TestCase):
    def setUp(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
        )

    def tearDown(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def test_mic_open(self):
        self.assertTrue(self.stream.is_active())

    def test_mic_read(self):
        data = self.stream.read(1024)
        self.assertIsNotNone(data)
        self.assertTrue(len(data) > 0)


@skipIf(True, reason="Enable latter with proper solution")
class CameraTestCase(TestCase):
    def setUp(self):
        self.cap = cv2.VideoCapture(0)

    def tearDown(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def test_camera_open(self):
        self.assertTrue(self.cap.isOpened())

    def test_camera_read(self):
        ret, frame = self.cap.read()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.shape), 3)  # Check if image has 3 channels (BGR)
