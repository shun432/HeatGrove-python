# import pigpio
# import time
#
# gpio_pin0 = 18
#
# pi = pigpio.pi()
# pi.set_mode(gpio_pin0, pigpio.OUTPUT)
#
# # GPIO18: 2Hz、duty比0.5
# pi.hardware_PWM(gpio_pin0, 2, 500000)
#
# try:
#     while True:
#         time.sleep(10000)
# except KeyboardInterrupt:
#     pass
#
# pi.set_mode(gpio_pin0, pigpio.INPUT)
# pi.stop()

import pigpio
import subprocess
from time import sleep

class PWM:

    def __init__(self, pin):

        self.pin = pin

        subprocess.call(["sudo", "pigpiod"])
        sleep(3)

        self.pi = pigpio.pi()
        self.pi.set_mode(pin, pigpio.OUTPUT)

    def __del__(self):

        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.stop()

    def write(self, duty, freq=1):

        self.pi.hardware_PWM(self.pin, freq, int(duty * 1000000))


if __name__ == '__main__':

    pwm = PWM(pin=18)

    try:
        pwm.write(0.9)
        while True:
            sleep(10000)
    except KeyboardInterrupt:
        pass
