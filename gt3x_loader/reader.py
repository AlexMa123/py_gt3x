import zipfile
from .tools import set_data, dotnetstr2tick, load_actigraph, read_uint12
import numpy as np


data_types = [
    'activity',
    '',
    'battery',
    'event',
    'heart_rate_bpm',
    'lux',
    'metadata',
    'tag',
    '',
    'epoch',
    '',
    'heart_rate_ant',
    'epoch2',
    'capsense',
    'heart_rate_ble',
    'epoch3',
    'epoch4',
    '',
    '',
    '',
    '',
    'parameters',
    '',
    '',
    'sensor_schema',
    'sensor_data',
    'activity2'
]


def get_datainfo(filepath):
    with zipfile.ZipFile(filepath) as f:
        with f.open("info.txt") as f_info:
            infos = f_info.read().decode('utf-8')
            file_info = {}
            for info in infos.split("\n"):
                try:
                    key, value = info.split(":", 1)
                    value = value[:-1]
                    file_info[key] = value
                except ValueError:
                    continue
    file_info['Sample Rate'] = set_data(file_info, "Sample Rate", int)
    file_info['Acceleration Min'] = set_data(file_info, "Acceleration Min", float)
    file_info['Acceleration Max'] = set_data(file_info, "Acceleration Max", float)
    file_info['Acceleration Scale'] = set_data(file_info, "Acceleration Scale", float)
    file_info['Start Date'] = set_data(file_info, "Start Date", dotnetstr2tick)
    file_info['Stop Date'] = set_data(file_info, "Stop Date", dotnetstr2tick)
    file_info['Last Sample Time'] = set_data(file_info, "Last Sample Time", dotnetstr2tick)
    file_info['DateOfBirth'] = set_data(file_info, "DateOfBirth", dotnetstr2tick)
    file_info['Age'] = set_data(file_info, 'Age', int)
    return file_info


class GT3XReader:

    def __init__(self, filepath):
        # Read info.txt
        self.file_info = get_datainfo(filepath)
        with zipfile.ZipFile(filepath) as f:
            # Read the data
            with f.open("log.bin") as log:
                self.times, self.datas = load_actigraph(log)

        self.sample_rate = self.file_info['Sample Rate']
        self.acc_min = self.file_info['Acceleration Min']
        self.acc_max = self.file_info['Acceleration Max']
        self.scale = self.file_info['Acceleration Scale']
        self.startdate = self.file_info['Start Date']
        self.stopdate = self.file_info['Stop Date']
        self.last_sampledate = self.file_info['Last Sample Time']
        self.birthdate = self.file_info['DateOfBirth']
        self.age = self.file_info['Age']
        self.sex = set_data(self.file_info, 'Sex', lambda x: x)

        try:
            if len(self.datas[0][-1]) != len(self.datas[0][0]):
                self.datas[0].pop()
                self.times[0].pop()
            actigraphy = b''.join(self.datas[0])
            actigraphy = read_uint12(actigraphy)
            index = np.where(actigraphy > 2047)
            actigraphy[index] = np.bitwise_or(actigraphy[index], 0xF000)
            actigraphy = actigraphy.astype(np.int16)
            actigraphy = actigraphy / self.scale
            actigraphy = actigraphy.reshape(-1, 3)
            self.datas[0] = actigraphy[:, [1, 0, 2]]

        except KeyError:
            print("No activity data found in file")
        try:
            lux = b''.join(self.datas[5])
            lux = np.frombuffer(lux, dtype=np.uint16)
            self.datas[5] = lux
        except KeyError:
            print("No lux data found in file")

        try:
            battery = b''.join(self.datas[2])
            battery = np.frombuffer(battery, dtype=np.uint16)
            self.datas[2] = battery
        except KeyError:
            print("No battery data found in file")

    def signalnames(self):
        return [data_types[i] for i in self.datas.keys()]

    def get_signal(self, signalname):
        try:
            i = data_types.index(signalname)
        except Exception:
            raise KeyError("Signal not found, Only has the following signals: ", self.signalnames())
        return self.datas[i]

    def get_signaltime(self, signalname):
        try:
            i = data_types.index(signalname)
        except Exception:
            raise KeyError("Signal not found, Only has the following signals: ", self.signalnames())
        return np.array(self.times[i])


if __name__ == "__main__":
    # test_file = r"D:\Aktigraphie\Aktigraph GT3X+\SL001 - neu52726 (2017-04-05).gt3x"
    test_file = r"./11171.gt3x"
    my_file = GT3XReader(test_file)
    acc = my_file.get_signal('activity')
    battery = my_file.get_signal('battery')
    # t1 = time.time()
    # with FileReader(test_file) as f:
    #     df = f.to_pandas()
    # t2 = time.time()
    # print(t2 - t1)
    i = input()
