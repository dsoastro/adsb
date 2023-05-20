# rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 log_messages.py

import numpy as np
import sys
from datetime import datetime
import pyModeS as pms
from common import process, get_heading, log, save, get_dst, empty_msg
from conf import OBSERVER_LAT, OBSERVER_LON

# {icao: {callsign:"", position:"", alt:"", speed:"", num_msg:"", num_df11:"", time:""}}
messages = {}


def update_messages(msg, ref_lat=OBSERVER_LAT, ref_lon=OBSERVER_LON):
    try:
        crc = pms.crc(msg, encode=False)
        if crc != 0:
            return
        save(msg)
        icao = pms.icao(msg)
        df = pms.df(msg)

        if messages.get(icao) is None:
            messages[icao] = empty_msg()

        messages[icao]["num_msg"] += 1
        if messages[icao]["num_msg"] % 10 == 0:
            log(icao, messages[icao].get("callsign", ""), messages[icao]["num_msg"])
        messages[icao]["time"] = datetime.now()
        if df == 11:
            messages[icao]["num_df11"] += 1

        typecode = pms.adsb.typecode(msg)

        if typecode >= 0:
            if typecode < 5:
                try:
                    callsign = pms.adsb.callsign(msg)
                    messages[icao]["callsign"] = callsign
                except:
                    pass
            if df == 17 and 9 <= typecode <= 18:
                position = pms.adsb.position_with_ref(msg, ref_lat, ref_lon)
                if position is not None:
                    lat, lon = position
                    dst = get_dst(lat, lon, OBSERVER_LAT, OBSERVER_LON)
                    pos_str = str(position) + "/" + "{:.1f}".format(dst)
                    messages[icao]["position"] = pos_str
                    log(icao, messages[icao].get("callsign", ""), pos_str)
                alt = pms.adsb.altitude(msg)
                if alt is not None:
                    alt = "{:.1f}".format(alt * 0.3)
                else:
                    alt = ""
                messages[icao]["alt"] = alt
                log(icao, messages[icao].get("callsign", ""), "alt", alt)
            if df == 17 and typecode == 19:
                velocity = pms.adsb.velocity(msg)
                try:
                    (v, heading, vrate, type) = velocity
                    m = "{:.1f}".format(v * 1.852) + "/" + get_heading(heading) + "/" + "{:.1f}".format(
                        0.3 * vrate) + "/" + type
                    messages[icao]["speed"] = str(m)
                    log(icao, messages[icao].get("callsign", ""), "speed", str(m))
                except:
                    if velocity is not None:
                        messages[icao]["speed"] = str(velocity)
                        log(icao, messages[icao].get("callsign", ""), "speed", str(velocity))
            if df == 4 or df == 20:
                alt = pms.common.altcode(msg)
                if alt is not None:
                    alt = "{:.1f}".format(alt * 0.3)
                else:
                    alt = ""
                messages[icao]["alt"] = alt
                log(icao, messages[icao].get("callsign", ""), "alt", alt)
    except Exception as e:
        pass


while True:
    buffer = sys.stdin.buffer.read(1024 * 1024)
    data = np.frombuffer(buffer, dtype='uint8')
    data = data.astype(float).reshape((-1, 2))
    data = data - 127
    I, Q = data[:, 0], data[:, 1]
    A = np.sqrt(I * I + Q * Q)
    msg = process(A, 5, 0.7)
    if msg is not None:
        update_messages(msg)
