from HeatGrove import ble_io
from HeatGrove import sensing
from HeatGrove import duty_control
from HeatGrove import pwm

from time import sleep
import json
import threading
import traceback


CONSOLE_PRINT = True


#$ スマートヒートグローブの機能を集めたクラス
class SmartHeatGrove:

    #$ このクラスの機能を持ったインスタンスを作るときは，はじめにこの関数が実行される．
    #$ スマートヒートグローブの機能を初期化するための関数．
    def __init__(self):

        #$ アプリから送られたデータはここに格納する
        self.from_app_data = None

        #$ ここから下は他の.pyファイルにあるクラスを使ってインスタンスを生成しておく箇所

        # setup each sensor
        self.sensor = sensing.SenseHeatGrove(bending_sensor_pin=0, button_status_pin=1)

        # setup ble
        self.ble = ble_io.BleModule()

        # setup pwm
        self.pwm = pwm.PWM(pin=18)

        # read study.json

        # setup duty controller with study.json
        self.controller = duty_control.DutyController()

    def main_loop(self):

        #$ このスレッドでは，
        #$ 1.温度センサーの値を取得
        #$ 2.BLEでセンサー情報を送信
        #$ 3.温度センサーとアプリの設定からduty比を決定する
        #$ 4.duty比を使ってグローブの電熱線にpwmを出力する
        #$ を繰り返し行う

        while True:

            # read sensor data
            bending = self.sensor.bending
            button_status = self.sensor.button_status
            temp = {'temp': self.sensor.temp['28-011438d141aa'], 'inside': self.sensor.temp['28-0213265d51aa']}

            # send temperature with ble
            self.ble.set(json.dumps(temp))

            # duty control
            duty = self.controller.get_duty(temp['temp'], temp['inside'],
                                            button_status, bending, self.from_app_data)

            # set duty to pwm
            self.pwm.write(duty)

            if CONSOLE_PRINT:
                print("sensor bending :" + str(bending))
                print("sensor button :" + str(button_status))
                print("temp :" + str(temp))
                print("ble read :" + str(self.from_app_data))
                print("duty :" + str(duty))

    def run_sensor(self):

        #$ このスレッドではセンシングを繰り返し行う

        while True:
            self.sensor.run_sensing()

    def read_ble(self):

        #$ このスレッドではBLEでアプリから送信されているデータを5秒おきに読みに行く

        while True:

            ble_get = self.ble.get()
            if ble_get is not None:
                from_app_data = json.loads(ble_get)
                self.from_app_data = {k: int(v) for k, v in from_app_data.items()}
            sleep(5)

    def start(self):

        #$ 非同期処理（マルチスレッド）のためのスレッドを用意
        thread_sensing = threading.Thread(target=self.run_sensor)
        thread_reading_ble = threading.Thread(target=self.read_ble)
        thread_mainloop = threading.Thread(target=self.main_loop)

        #$ 各スレッドを開始
        thread_sensing.start()
        thread_reading_ble.start()
        thread_mainloop.start()


#$ 「python main.py」の場合はこれを実行
if __name__ == '__main__':

    try:
        #$ main.pyで最初に実行する部分，SmartHeatGroveクラスの__init__関数を実行して，インスタンスを作る
        shg = SmartHeatGrove()

        #$ SmartHeatGroveの機能を持っているインスタンスの，start関数を実行
        shg.start()

    except:

        #$ 何かのエラーが起きた場合は，error.logファイルにエラー内容を記録する
        with open("error.log", 'a') as f:
            traceback.print_exc(file=f)
