from django.test import TestCase
from unittest import skipIf
import pyaudio
import sounddevice  # This is for mute alsa log for pyaudio
import cv2

import wave
import time
from gtts import gTTS


class SpeakerTestCase(TestCase):
    def setUp(self):
        self.p = pyaudio.PyAudio()

    def tearDown(self):
        self.p.terminate()

    def test_speak_hello(self):
        speech = gTTS(text="Hello world!", slow=False)
        speech.save("speak_hello.wav")


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

    def test_mic_to_wav(self):
        print("Now make sound for record")
        # Record for 5 seconds
        frames = []
        start_time = time.time()
        while time.time() - start_time < 5:
            data = self.stream.read(1024)
            frames.append(data)

        # Save the recorded data as a WAV file
        wave_file = wave.open("mic_out.wav", "wb")
        wave_file.setnchannels(1)
        wave_file.setsampwidth(self.p.get_sample_size(pyaudio.paFloat32))
        wave_file.setframerate(44100)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()


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
