from pybleno import *
import json

bleno = Bleno()

'''
参考にしたページ
BLEの通信方法について：　http://jellyware.jp/kurage/bluejelly/ble_guide.html

https://qiita.com/comachi/items/c494e0d6c6d1775a3748

http://blog.robotakao.jp/blog-entry-151.html
https://github.com/Adam-Langley/pybleno
'''


APPROACH_SERVICE_UUID = '13A28130-8883-49A8-8BDB-42BC1A7107F4'
APPROACH_CHARACTERISTIC_UUID = 'A2935077-201F-44EB-82E8-10CC02AD8CE1'


#$ アプリからの「データを読みたい」「データを書きたい」というリクエストを待ち受けるために必要なクラス
class ApproachCharacteristic(Characteristic):

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': APPROACH_CHARACTERISTIC_UUID,
            'properties': ['read', 'write', 'notify'],
            'value': None
        })

        self._value = [0]
        self.written_value = None
        self._updateValueCallback = None

    def onReadRequest(self, offset, callback):

        callback(Characteristic.RESULT_SUCCESS, self._value)

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        self.written_value = data

        # self._value = data
        if self._updateValueCallback:

            self._updateValueCallback(self._value)

        callback(Characteristic.RESULT_SUCCESS)

    def onSubscribe(self, maxValueSize, updateValueCallback):

        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):

        self._updateValueCallback = None


#$ 上のクラスを使って，簡単にBLE通信をできるようにするクラス（set関数とget関数を使うだけ）
class BleModule:

    def __init__(self):

        ###### set up ######
        bleno.on('stateChange', self.onStateChange)
        self.approachCharacteristic = ApproachCharacteristic()
        bleno.on('advertisingStart', self.onAdvertisingStart)
        bleno.start()

        return

    def onStateChange(self, state):

        if (state == 'poweredOn'):
            bleno.startAdvertising('Approach', [APPROACH_SERVICE_UUID])
        else:
            bleno.stopAdvertising()

    def onAdvertisingStart(self, error):

        if not error:
            bleno.setServices([
                BlenoPrimaryService({
                    'uuid': APPROACH_SERVICE_UUID,
                    'characteristics': [
                        self.approachCharacteristic
                    ]
                })
            ])

    def set(self, input_text):

        self.approachCharacteristic._value = utf_to_byte_array(input_text)

    def get(self):

        return byte_array_to_utf(self.approachCharacteristic.written_value)


def byte_array_to_utf(byte_array):
    if byte_array is None:
        return None
    return bytes.fromhex(byte_array.hex()).decode('utf-8')


def utf_to_byte_array(utf_text):
    b = utf_text.encode('utf-8')
    return [int('{:02x}'.format(x), 16) for x in b]


#$ 「python ble_io.py」の場合はこれを実行
if __name__ == '__main__':

    import time

    ble = BleModule()

    temp = 0

    while True:

        print(temp)

        get = ble.get()
        if get is not None:
            print("read :" + get)
        else:
            print("read :No data")

        ble.set(json.dumps({"temp": temp}))

        temp += 1
        time.sleep(3)

