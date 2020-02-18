from HeatGrove.Test.test_AI import PredictTemperature, DutyController, update
from matplotlib import pyplot as plt
from time import sleep
from multiprocessing import Process, Value
from websocket_server import WebsocketServer
import json
import os


aa_temp = 10
tt_temp = 26


class Simulate:

    def __init__(self):

        self.path = "HeatGrove/simulation/temp.json"

        self.jobs = None
        self.atm_temp = 10
        self.t_temp = 26

    def ai(self, t_temp, a_temp):
        # pred = PredictTemperature(k_atm=0.5, k_out=0.5)

        pred = PredictTemperature(k_atm=0.53158313567, k_out=0.0784919)
        max_temp = pred.simulate_max_temp(10)
        print(max_temp)

        controller = DutyController()

        atm_temp = 10
        before_inner_temp = atm_temp
        truth_inner_temp = before_inner_temp
        x = range(10)
        inner_temp_list = [0] * 10
        atm_temp_list = [10] * 10
        target_temp_list = [26] * 10

        n = 0

        while True:
            self.atm_temp = a_temp.value
            self.t_temp = t_temp.value

            # atm_t = input("atmosphere temp :")
            # user_temp = input("user temp :")
            #
            # if atm_t is not '':
            #     atm_temp = atm_t
            #
            # if user_temp is '':
            #     user_temp = None

            button_status = 0

            # if n == 30:
            #     self.atm_temp = 15
            #
            # if n == 40:
            #     self.t_temp = 23

            atm_temp = self.atm_temp * 0.3 + atm_temp * 0.7

            new_duty = controller.get_duty(atm_temp, truth_inner_temp, button_status, self.t_temp)

            pred.update(atm_temp, new_duty)

            truth_inner_temp = pred.fit(0.2, 0.03, before_inner_temp)     # for simulation

            pred.learn(truth_inner_temp, 0.01)

            update(target_temp_list, controller.target_temp)
            update(inner_temp_list, truth_inner_temp)
            update(atm_temp_list, atm_temp)

            plt.clf()
            plt.plot(x, target_temp_list, marker="o", color="r", linewidth=3.0, label="target")
            plt.plot(x, inner_temp_list, color="g", linewidth=3.0, label="inner")
            plt.plot(x, atm_temp_list, color="b", linewidth=3.0, label="outside")
            plt.xlim(0, 10)
            plt.ylim(0, 40)
            plt.legend()
            plt.pause(0.001)

            # print("truth temp :" + str(truth_inner_temp) + "| pred temp :" + str(pred.inner_temp) + "| duty :" + str(new_duty))
            # print("k_atm :" + str(pred.k_atm) + "| k_out :" + str(pred.k_out))
            print(self.t_temp)
            print(self.atm_temp)

            before_inner_temp = truth_inner_temp
            n += 1
            sleep(1)

    def new_client(self, client, server):
        print("new_client:", client['address'])

    def message_received(self, client, server, message):
        print("message_received:", message)
        print("message_received_type:", type(message))
        df = message.split('/')
        # df = json.loads(message)
        global aa_temp, tt_temp
        aa_temp = float(df[0])
        tt_temp = float(df[1])
        # server.send_message(client, "hello from server")

    def read_websocket(self):

        server = WebsocketServer(port=5001, host='127.0.0.1')
        server.set_fn_new_client(self.new_client)
        server.set_fn_message_received(self.message_received)
        server.run_forever()

            # if os.path.exists(self.path):
            #     with open(self.path) as f:
            #         df = json.load(f)
            #         self.atm_temp = df["temp"]
            #         self.t_temp = df["inside"]
            # sleep(1)


    def data_set(self, atm_temp, t_temp):

        while True:
            atm_temp.value = tt_temp
            t_temp.value = aa_temp

            sleep(1)

    def multi_thread(self, atm_temp, t_temp):

        import threading

        thread_0 = threading.Thread(target=self.read_websocket)
        thread_1 = threading.Thread(target=self.data_set, args=(atm_temp, t_temp))

        thread_0.start()
        thread_1.start()


    def main(self):

        temp = Value('f', 26)
        inside = Value('f', 10)

        self.jobs = [
            Process(target=self.ai, args=[temp, inside]),
            Process(target=self.multi_thread, args=[temp, inside]),
        ]

        for j in self.jobs:
            j.start()

    def __del__(self):

        for j in self.jobs:
            j.join()


if __name__ == '__main__':

    sim = Simulate()

    sim.main()

