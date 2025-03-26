from unittest import TestCase
from chatbox.robot import Mindbot


class MindbotTestCase(TestCase):
    def setUp(self):
        self.bot = Mindbot()
        self.bot.boot()

    def test_duplex(self):
        pass
