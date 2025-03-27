from unittest import TestCase
from chatbox.robot import Mindbot


class MindbotTestCase(TestCase):
    def setUp(self):
        self.bot = Mindbot()
        self.bot.boot()

    def test_ved(self):
        print("Now detecting voice endpoint...")
        self.bot.ved_listen_to_wav("ved.wav")

    def test_avd(self):
        print("Now detecting voice activity...")
        self.bot.voice_activity_detection()

    def test_duplex(self):
        """
        While mindbot speaking, voice_activity_detection only detects other's voice.
        """
        pass

    def test_start_lecture(self):
        pass

    def test_start_lecture(self):
        pass
