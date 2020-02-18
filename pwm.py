import pigpio
import subprocess
from time import sleep


#$ あるGPIOピンにPWMを出力するクラス
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


#$ 「python pwm.py」の場合はこれを実行
if __name__ == '__main__':

    pwm = PWM(pin=18)

    try:
        duty = 0.9
        pwm.write(duty)
        print("write with duty:" + str(duty))
        while True:
            sleep(10000)
    except KeyboardInterrupt:
        pass
