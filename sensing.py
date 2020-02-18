import RPi.GPIO as GPIO
from time import sleep
import subprocess
import os


#$ pythonで電圧を測れる素子(ADコンバータ)を使うためのクラス
class AdConverter:

    def __init__(self, SPICLK=11, SPIMOSI=10, SPIMISO=9, SPICS=8):

        GPIO.setmode(GPIO.BCM)
        self.SPICLK = SPICLK
        self.SPIMOSI = SPIMOSI
        self.SPIMISO = SPIMISO
        self.SPICS = SPICS

        self.gpio_setup()

    def gpio_setup(self):

        GPIO.setup(self.SPICLK, GPIO.OUT)
        GPIO.setup(self.SPIMOSI, GPIO.OUT)
        GPIO.setup(self.SPIMISO, GPIO.IN)
        GPIO.setup(self.SPICS, GPIO.OUT)

    def read(self, ch, subtraction=False):

        if ch > 7 or ch < 0:
            return -1
        GPIO.output(self.SPICS, GPIO.HIGH)
        GPIO.output(self.SPICLK, GPIO.LOW)
        GPIO.output(self.SPICS, GPIO.LOW)

        commandout = ch
        if not subtraction:
            # logic sum of 11000, channel number put in last 3 bit
            commandout |= 0x18
        else:
            # logic sum of 10000, subtraction between ch[0-1,2-3,4-5,6-7], argument number is plus, another is minus
            commandout |= 0x10
        commandout <<= 3
        for i in range(5):
            if commandout & 0x80:
                GPIO.output(self.SPIMOSI, GPIO.HIGH)
            else:
                GPIO.output(self.SPIMOSI, GPIO.LOW)
            commandout <<= 1
            GPIO.output(self.SPICLK, GPIO.HIGH)
            GPIO.output(self.SPICLK, GPIO.LOW)
        adcout = 0
        for i in range(13):
            GPIO.output(self.SPICLK, GPIO.HIGH)
            GPIO.output(self.SPICLK, GPIO.LOW)
            adcout <<= 1
            if i > 0 and GPIO.input(self.SPIMISO) == GPIO.HIGH:
                adcout |= 0x1
        GPIO.output(self.SPICS, GPIO.HIGH)

        return adcout


#$ pythonで温度センサー（DS18B20）を読むためのクラス
class DS18B20:

    def __init__(self):

        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        self.base_dir = '/sys/bus/w1/devices/'
        self.file = '/w1_slave'

    def read_temp_raw(self, folder_name):
        cat_data = subprocess.Popen(['cat', self.base_dir + folder_name + self.file],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cat_data.communicate()
        out_decode = out.decode('utf-8')
        lines = out_decode.split('\n')
        return lines

    def read(self, folder_name):
        lines = self.read_temp_raw(folder_name)
        while lines[0].strip()[-3:] != 'YES':
            sleep(0.2)
            lines = self.read_temp_raw(folder_name)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f


#$ 上２つのクラスを使って，ヒートグローブに付いている全てのセンサーを読むクラス
class SenseHeatGrove:

    def __init__(self, bending_sensor_pin=0, button_status_pin=1,
                 bending_threshold=700, button_threshold=(2000, 4000)):

        self.bending_sensor_pin = bending_sensor_pin
        self.button_status_pin = button_status_pin
        self.bending_threshold = bending_threshold
        self.button_threshold = button_threshold
        self.loop = 9
        self.button = [0] * self.loop

        self.bending = False
        self.button_status = 'r'
        self.temp = {'28-011438d141aa': 0.0, '28-0213265d51aa': 0.0}

        self.adc = AdConverter(SPICLK=11, SPIMOSI=10, SPIMISO=9, SPICS=8)
        self.therm = DS18B20()

    def run_sensing(self):

        #$ DS18B20を読む
        for i in self.temp.keys():
            self.temp[i], _ = self.therm.read(i)

        #$ ADコンバータを使って曲げセンサーを読む
        bending = self.adc.read(self.bending_sensor_pin)
        if bending < self.bending_threshold:
            self.bending = True
        else:
            self.bending = False

        #$ ADコンバータを使ってグローブに付いているボタンの状態（赤，緑，青）を読む
        for n in range(self.loop):
            self.button[n] = self.adc.read(self.button_status_pin)
            sleep(1)
        button_status = sum(self.button)
        if button_status < self.button_threshold[0]:
            self.button_status = 'g'
        elif button_status < self.button_threshold[1]:
            self.button_status = 'b'
        else:
            self.button_status = 'r'


def io():
    while True:

        input("---( press enter key )---")

        print("bending :" + str(hg.bending))
        print("button  :" + hg.button_status)
        print("temp    :" + str(hg.temp))


def start_sensing(sense):

    while True:
        sense.run_sensing()


#$ 「python sensing.py」の場合はこれを実行
if __name__ == '__main__':

    import threading

    hg = SenseHeatGrove(bending_sensor_pin=0, button_status_pin=1)

    thread_0 = threading.Thread(target=start_sensing, args=(hg, ))
    thread_1 = threading.Thread(target=io)

    thread_0.start()
    thread_1.start()
