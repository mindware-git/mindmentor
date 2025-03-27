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
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
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
        wave_file.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(48000)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

    def test_detect_VAD(self):
        import numpy as np
        from collections import deque

        # Define the threshold for voice activity detection
        threshold = 30  # Assuming this is a suitable threshold for your audio data

        # Define window size (number of frames to keep in the sliding window)
        window_size = 50  # This will give us roughly 5 seconds of audio (50 * 1024 samples / 48000 Hz)

        # Initialize variables for recording and VAD
        frames = []
        audio_window = deque(maxlen=window_size)  # Sliding window for audio data
        voice_active = False
        voice_start_time = None

        # Start recording
        print("Recording...")
        while True:
            data = self.stream.read(1024)
            frames.append(data)

            # Convert the raw audio data to a numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_window.append(audio_data)

            # Calculate RMS using only the data in the sliding window
            if len(audio_window) == window_size:
                window_data = np.concatenate(list(audio_window))
                rms = np.sqrt(np.mean(window_data**2))
                print(rms)

                # Check if the RMS is above the threshold
                if rms > threshold:
                    if not voice_active:
                        voice_active = True
                        voice_start_time = time.time()
                else:
                    if voice_active:
                        # If the voice has been active for more than 1 second, stop recording
                        if time.time() - voice_start_time > 1:
                            break
                        voice_active = False

        # Save the recorded data as a WAV file
        wave_file = wave.open("mic_vad.wav", "wb")
        wave_file.setnchannels(1)
        wave_file.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(48000)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

        print("Recording saved as mic_vad.wav")


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
