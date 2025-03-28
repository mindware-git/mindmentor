from unittest import TestCase
from chatbox.robot import Mindbot
import time


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
        self.assertTrue(
            self.bot.start_lecture(
                {
                    "ipynb": "chatbox/static/chatbox/mm-course/lang/eng/family/01_family_run.ipynb",
                    "current_lesson": 0,
                    "current_code_style": "sof",
                    "current_code_info": 0,
                }
            )
        )
        self.bot.lecture_thread.join()

    def test_stop_lecture_negative(self):
        self.assertEqual(self.bot.stop_lecture(), {})

    def test_stop_lecture_positive(self):
        self.bot.start_lecture(
            {
                "ipynb": "chatbox/static/chatbox/mm-course/lang/eng/family/01_family_run.ipynb",
                "current_lesson": 0,
                "current_code_style": "sof",
                "current_code_info": 0,
            }
        )
        time.sleep(1)
        self.assertTrue(self.bot.stop_lecture())
