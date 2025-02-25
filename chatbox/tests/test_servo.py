"""
Only RPI5 servo test
HW pwm needs firmware config /boot/firmware/config.txt
Check https://github.com/Pioreactor/rpi_hardware_pwm
"""

from django.test import TestCase
from unittest import skipIf
import time

try:
    from rpi_hardware_pwm import HardwarePWM

    RPI5_AVAILABLE = True
except ImportError:
    RPI5_AVAILABLE = False


@skipIf(not RPI5_AVAILABLE, reason="RPI5 only")
class ServoTestCase(TestCase):
    def setUp(self):
        self.pwm = HardwarePWM(pwm_channel=2, hz=50, chip=2)
        self.pwm.start(7.5)
        time.sleep(1)

    def tearDown(self):
        time.sleep(1)
        self.pwm.stop()

    def test_servo_1ms(self):
        # Test min position
        self.pwm.change_duty_cycle(3)

    def test_servo_1_5ms(self):
        # Test mid position
        self.pwm.change_duty_cycle(7.5)

    def test_servo_2ms(self):
        # Test max position
        self.pwm.change_duty_cycle(12)
