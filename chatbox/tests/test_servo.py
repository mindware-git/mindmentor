"""
Only RPI servo test
"""

from django.test import TestCase
from unittest import skipIf

try:
    from gpiozero import Servo

    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False


@skipIf(not GPIOZERO_AVAILABLE, reason="gpiozero not available")
class ServoTestCase(TestCase):
    def setUp(self):
        self.servo = Servo(18)  # Using GPIO pin 18

    def tearDown(self):
        self.servo.close()

    def test_servo_movement(self):
        # Test min position
        self.servo.min()
        self.assertEqual(self.servo.value, -1)

        # Test mid position
        self.servo.mid()
        self.assertEqual(self.servo.value, 0)

        # Test max position
        self.servo.max()
        self.assertEqual(self.servo.value, 1)

        # Test specific value
        self.servo.value = 0.5
        self.assertEqual(self.servo.value, 0.5)
