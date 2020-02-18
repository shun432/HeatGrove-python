import os
import time
import subprocess


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
            time.sleep(0.2)
            lines = self.read_temp_raw(folder_name)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f


if __name__ == '__main__':

    sensor1 = '28-011438d141aa'
    sensor2 = '28-0213265d51aa'

    temperature = DS18B20()

    while True:
        temp1, _ = temperature.read(sensor1)
        temp2, _ = temperature.read(sensor2)
        print(sensor1 + ":" + str(temp1) + " / " + sensor2 + ":" + str(temp2))
        time.sleep(3)
