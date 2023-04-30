from datetime import datetime, timedelta
import numpy as np


def dotnet2tick(ticks):
    """
    Convert .NET ticks to datetime object
    """
    return datetime(1, 1, 1) + timedelta(microseconds=ticks / 10)


def dotnetstr2tick(ticks):
    return dotnet2tick(int(ticks))


def set_data(dict, key, map_func):
    try:
        return map_func(dict[key])
    except KeyError:
        return None


def read_uint12(data_chunk):
    data = np.frombuffer(data_chunk, dtype=np.uint8)
    fst_int8, mid_int8, lst_int8 = np.reshape(data, (data.shape[0] // 3, 3)).astype(np.uint16).T
    fst_int12 = (fst_int8 << 4) + (mid_int8 >> 4)
    snd_int12 = ((mid_int8 % 16) << 8) + lst_int8
    return np.reshape(np.concatenate((fst_int12[:, None], snd_int12[:, None]), axis=1), 2 * fst_int12.shape[0])


def header_processor(header):
    seperator = header[0]
    if seperator != 30:
        raise Exception("Invalid seperator")
    datatype = header[1]

    timestamp = int.from_bytes(header[2:6], byteorder='little')
    size = int.from_bytes(header[6:], byteorder='little')
    return datatype, timestamp, size


def read_block(f):
    header = f.read(8)
    datatype, time, size = header_processor(header)
    data = f.read(size)
    f.read(1)
    return datatype, time, data


def load_actigraph(f):
    datas = {}
    times = {}
    while True:
        try:
            datatype, t, data = read_block(f)
        except IndexError:
            break

        try:
            datas[datatype].append(data)
            times[datatype].append(t)
        except KeyError:
            datas[datatype] = [data]
            times[datatype] = [t]

    return times, datas
