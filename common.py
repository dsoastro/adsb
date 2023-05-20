import numpy as np
import math
import datetime
import pyModeS as pms


def detectPreambleXcorr(chunk, corrthresh=0.5):
    '''
    The function accepts an array of 16 samples, e.g.,  x[n]⋯x[n+15] . It evaluates the normalized cross correlation with an ideal preamble, and returns a True if it is greater than corrthresh
    '''
    preamble = np.array([75, 25, 70, 30, 5, 5, 1, 75, 20, 70, 25, 5, 3, 1, 1, 3])
    preamble_av = np.average(preamble)

    chunk_av = np.average(chunk)
    sum = 0
    for i in range(16):
        sum += (chunk[i] - chunk_av) * (preamble[i] - preamble_av)

    sum = sum / norm(chunk - chunk_av) / norm(preamble - preamble_av)
    return (sum > corrthresh)


def get_packet(A, pos, size=112):
    '''
    pos - the start of preamble
    size - the number of bits
    '''
    if pos + 16 + size * 2 > len(A):
        return
    pos = pos + 16
    i = 0
    sym_flag = False
    syms = []
    while i < size * 2:
        if sym_flag:
            second = A[pos]
            if second > first:
                syms.append('0')
            else:
                syms.append('1')
        else:
            first = A[pos]
        pos += 1
        sym_flag = not sym_flag
        i += 1
    return hex(int("".join(syms), 2))[2:]


def process(A, noise_threshold, cov_threshold):
    idx = np.nonzero(A > noise_threshold)
    res = []
    for pos in idx[0]:
        if pos + 16 < len(A):
            if detectPreambleXcorr(A[pos:pos + 16], cov_threshold):
                res.append(pos)
    # log("potential preamble position list", len(res), "\n")
    for pos in res:
        msg1 = get_packet(A, pos, 112)
        msg2 = get_packet(A, pos, 56)
        crc1 = 1
        crc2 = 1
        try:
            crc1 = 1 if msg1 is None else pms.crc(msg1, encode=False)
        except Exception as e:
            pass
        try:
            crc2 = 1 if msg2 is None else pms.crc(msg2, encode=False)
        except Exception as e:
            pass
        msg = None
        if crc1 == 0:
            # print("msg 112 bit:", msg1)
            msg = msg1
        if crc2 == 0:
            # print("msg 56 bit:", msg2)
            msg = msg2
        return msg


def norm(vector):
    sum = 0
    for v in vector:
        sum += v * v
    return np.sqrt(sum)


def get_name(icao, callsigns):
    name = callsigns.get(icao)
    if name:
        return icao + " " + name
    else:
        return icao


def get_heading(h):
    if h < 45:
        return "{:.1f}".format(h) + "N"
    if h < 90 + 45:
        return "{:.1f}".format(h) + "E"
    if h < 180 + 45:
        return "{:.1f}".format(h) + "S"
    if h < 270 + 45:
        return "{:.1f}".format(h) + "W"
    return "{:.1f}".format(h) + "N"


def get_dst(lat, lon, OBSERVER_LAT, OBSERVER_LON):
    dlon = lon - OBSERVER_LON
    dlat = lat - OBSERVER_LAT
    a = math.sin(dlat / 2 * math.pi / 180) ** 2 + \
        math.cos(lat * math.pi / 180) * math.cos(OBSERVER_LAT * math.pi / 180) * \
        math.sin(dlon / 2 * math.pi / 180) ** 2
    c = 2 * math.asin(min(1, math.sqrt(a)))
    R = 6367
    d = R * c
    return d


global_order = 0  # for message ordering

def empty_msg():
    global global_order
    global_order += 1
    return {"callsign": "", "position": "", "alt": "", "speed": "", "num_msg": 0, "num_df11": 0, "time": "",
            "order": global_order}


def get_time(time):
    return str(time.hour) + ":" + str(time.minute) + ":" + str(time.second)


def log(*args):
    print(*args, flush=True)


def save(text):
    with open("full.txt", "a") as f:
        f.write(str(datetime.datetime.now()) + " " + text)
        f.write("\n")
