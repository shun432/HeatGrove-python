from time import sleep
import random


#$ 温度予測用のクラス（シミュレータで使うやつ）
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


#$ アプリの設定情報やPID制御を使ってduty比を計算するクラス
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

    def get_duty(self, atm_temp, inner_temp, button_status, bending, app_setting):

        if app_setting is None:
            bending_ef = 1
            auto_control_ef = 1
            gauge = 100
            map_dist = 100      # fix
        else:
            if 'bending_ef' in app_setting:
                bending_ef = app_setting['bending_ef']
            else:
                bending_ef = 1

            if 'ai_control_ef' in app_setting:
                auto_control_ef = app_setting['ai_control_ef']
            else:
                auto_control_ef = 1

            if 'gauge' in app_setting:
                gauge = app_setting['gauge']
            else:
                gauge = 100

            if 'map_dist' in app_setting:
                map_dist = app_setting['map_dist']      # fix
            else:
                map_dist = 100

        return self.standard_algorithm(atm_temp, inner_temp, button_status, bending,
                                       bending_ef, auto_control_ef, gauge)

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

    def standard_algorithm(self, atm_temp, inner_temp, button_status, bending,
                           bending_ef, auto_control_ef, gauge):

        new_duty = self.pid_control(inner_temp)

        # atmosphere temperature
        if self.target_temp - atm_temp > 10:
            new_duty = 1

        # goal distance condition

        # bending condition
        if bending_ef == 1 and not bending:  # 1 is effective
            return 0.0

        # auto control effectiveness
        if auto_control_ef == 0:
            new_duty = gauge * 0.01

        # button status condition
        if button_status == 'g':
            return new_duty
        elif button_status == 'r':
            return min(new_duty + 0.2, 1)
        elif button_status == 'b':
            return max(0, new_duty - 0.3)

        print("not match any condition in standard rule")
        return new_duty


# information: atm_temp, inner_temp, button_status, bending,
#              app_gauge, app_self_sett, app_bending_sett

# in: atm_temp           tea: target_power
# in: target_temp        tea: user_temp


#$ 「python duty_control.py」の場合はこれを実行
if __name__ == '__main__':

    # pred = PredictTemperature(k_atm=0.5, k_out=0.5)

    pred = PredictTemperature(k_atm=0.53158313567, k_out=0.0784919)
    max_temp = pred.simulate_max_temp(10)
    print(max_temp)

    controller = DutyController()

    atm_temp = 10
    before_inner_temp = atm_temp
    truth_inner_temp = before_inner_temp

    while True:

        button_status = 'g'
        bending = False
        app_setting = None

        new_duty = controller.get_duty(atm_temp, truth_inner_temp, button_status, bending, app_setting)

        pred.update(atm_temp, new_duty)

        truth_inner_temp = pred.fit(0.2, 0.03, before_inner_temp)     # for simulation

        pred.learn(truth_inner_temp, 0.01)

        print("truth temp :" + str(truth_inner_temp) + "| pred temp :" + str(pred.inner_temp) + "| duty :" + str(new_duty))
        print("k_atm :" + str(pred.k_atm) + "| k_out :" + str(pred.k_out))

        before_inner_temp = truth_inner_temp
        sleep(0.3)

