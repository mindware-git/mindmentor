from django.test import TestCase, TransactionTestCase
from chatbox.robot import Robot
import time


class StateTestCase(TestCase):
    def setUp(self):
        self.robot = Robot()
        self.robot.init_db()

    def test_idle(self):
        self.assertEqual(self.robot.get_state(), "idle")

    def test_ved_listen(self):
        self.robot.ved_listen_to_wav("test.wav")


class LecturerTestCase(TransactionTestCase):
    def setUp(self):
        self.robot = Robot()
        self.robot.init_db()

    def test_start_lecture(self):
        self.robot.restore_lecture_and_resume()
        self.assertEqual(self.robot.get_state(), "lecturer")
        time.sleep(6)

    def test_stop_lecture(self):
        self.robot.restore_lecture_and_resume()
        self.assertEqual(self.robot.get_state(), "lecturer")
        time.sleep(2)
        self.robot.save_lecture_and_exit()
        self.assertEqual(self.robot.get_state(), "idle")

        time.sleep(2)
        self.robot.restore_lecture_and_resume()
        self.assertEqual(self.robot.get_state(), "lecturer")
        time.sleep(6)


class TeachingAssistantTestCase(TransactionTestCase):
    def setUp(self):
        self.robot = Robot()
        self.robot.init_db()

    def test_start_ta(self):
        self.robot.ta()
        time.sleep(10)

    def test_stop_ta(self):
        self.robot.ta()
        time.sleep(2)

        self.robot.stop_ta()
        time.sleep(2)
