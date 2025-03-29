from unittest import TestCase
from chatbox.robot import Mindbot
import time
from threading import Thread


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
        speak_thread = Thread(target=self.bot.speak_from_wav, args=("chatbox/res/lecture1.wav",))
        ved_thread = Thread(target=self.bot.ved_listen_to_wav, args=("same_time.wav",))

        speak_thread.start()
        ved_thread.start()

        speak_thread.join()
        ved_thread.join()

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
        self.bot.working_thread.join()

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
        last_memory = self.bot.stop_lecture()
        self.assertEqual(last_memory["state"], "lecturer")
        self.assertEqual(last_memory["current_code_style"], "code")

    def test_restart_lecture(self):
        self.bot.start_lecture(
            {
                "ipynb": "chatbox/static/chatbox/mm-course/lang/eng/family/01_family_run.ipynb",
                "current_lesson": 0,
                "current_code_style": "sof",
                "current_code_info": 0,
            }
        )
        time.sleep(1)
        last_memory = self.bot.stop_lecture()
        self.assertEqual(last_memory["state"], "lecturer")
        self.assertEqual(last_memory["current_code_style"], "code")
        time.sleep(2)

        self.bot.start_lecture(last_memory)
        time.sleep(2)
        self.bot.stop_lecture()

    def test_idle_assistant(self):
        self.bot.start_assistant()

    def test_lecture_assistant(self):
        self.bot.start_lecture(
            {
                "ipynb": "chatbox/static/chatbox/mm-course/lang/eng/family/01_family_run.ipynb",
                "current_lesson": 0,
                "current_code_style": "sof",
                "current_code_info": 0,
            }
        )
        time.sleep(1)
        self.bot.start_assistant()
        time.sleep(10)
        self.bot.stop_lecture()

    def test_cloud_assistantistant(self):
        self.bot.cloud_simple_assistant()
