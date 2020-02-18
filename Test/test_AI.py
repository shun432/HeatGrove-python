from time import sleep
import random
from matplotlib import pyplot as plt


class PredictTemperature:

    def __init__(self, battery_ampere=2.0, k_atm=0.2, k_out=0.03):

        self.batt_a = battery_ampere

        self.atm_temp = None
        self.duty = None

        self.inner_temp = 10
        self.before_pred = self.inner_temp

        self.k_atm = k_atm        # impact of atmosphere temperature
        self.k_out = k_out        # impact of heating temperature

    def update(self, atm_temp, duty):

        self.atm_temp = atm_temp
        self.duty = duty

        self.before_pred = self.inner_temp
        self.inner_temp = self.fit(self.k_atm, self.k_out, self.before_pred)

    def fit(self, k_a, k_o, before_temp):

        return before_temp + k_a * (self.atm_temp - before_temp) + k_o * (self.duty * self.batt_a * 50 + before_temp)

    def learn(self, truth_inner_temp, learn_rate=0.01):

        loss = self.inner_temp - truth_inner_temp
        self.monte_carlo(loss, learn_rate, truth_inner_temp)

    def monte_carlo(self, loss, learn_rate, truth_inner_temp):

        ave = self.k_atm + self.k_out / 2
        k_atm = self.k_atm + learn_rate * random.uniform(-1, 1) * ave / self.k_atm
        k_out = self.k_out + learn_rate * random.uniform(-1, 1) * ave / self.k_out

        new_loss = self.fit(k_atm, k_out, self.before_pred) - truth_inner_temp

        if abs(new_loss) < abs(loss):
            self.k_atm = k_atm
            self.k_out = k_out

    def simulate_max_temp(self, atm_temp):

        for i in range(500):
            before_pred = self.inner_temp
            self.update(atm_temp, 1.0)
            if abs(self.inner_temp - before_pred) < 0.01:
                break

        return self.inner_temp


class DutyController:

    def __init__(self, battery_ampere=2.0):
        self.target_temp = 26
        self.current_duty = 0
        self.before_duty = [0] * 100

        self.e_prev = [0.0, 0.0]  # [older, newer]

        # how quick varying
        self.k_p = 0.1
        self.k_i = 0.1
        self.k_d = 0.1

    def get_duty(self, atm_temp, inner_temp, button_status, target_temp):

        self.target_temp = target_temp
        new_duty = self.pid_control(inner_temp)

        return new_duty

    def pid_control(self, temp):
        e = self.target_temp - temp
        p = self.k_p * (e - self.e_prev[1])
        i = self.k_i * e
        d = self.k_d * ((e - self.e_prev[1]) - (self.e_prev[1] - self.e_prev[0]))
        duty = self.before_duty[-1] + p + i + d

        new_duty = max([0.0, min([duty, 1.0])])

        # update
        del self.before_duty[0]
        self.before_duty.append(new_duty)
        del self.e_prev[0]
        self.e_prev.append(e)

        return new_duty


# information: atm_temp, inner_temp, button_status, bending,
#              app_gauge, app_self_sett, app_bending_sett


# in: atm_temp           tea: target_power
# in: target_temp        tea: user_temp


def update(list, new_val):

    del list[0]
    list.append(new_val)


if __name__ == '__main__':

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

    while True:

        # atm_t = input("atmosphere temp :")
        # user_temp = input("user temp :")
        #
        # if atm_t is not '':
        #     atm_temp = atm_t
        #
        # if user_temp is '':
        #     user_temp = None

        button_status = 0

        new_duty = controller.get_duty(atm_temp, truth_inner_temp, button_status, 26)

        pred.update(atm_temp, new_duty)

        truth_inner_temp = pred.fit(0.2, 0.03, before_inner_temp)     # for simulation

        pred.learn(truth_inner_temp, 0.01)

        update(target_temp_list, controller.target_temp)
        update(inner_temp_list, truth_inner_temp)
        update(atm_temp_list, atm_temp)

        plt.clf()
        plt.plot(x, target_temp_list, marker="o", color="r")
        plt.plot(x, inner_temp_list, color="g")
        plt.plot(x, atm_temp_list, color="b")
        plt.xlim(0, 10)
        plt.ylim(0, 40)
        plt.pause(0.002)

        print("truth temp :" + str(truth_inner_temp) + "| pred temp :" + str(pred.inner_temp) + "| duty :" + str(new_duty))
        print("k_atm :" + str(pred.k_atm) + "| k_out :" + str(pred.k_out))

        before_inner_temp = truth_inner_temp


        sleep(0.3)

