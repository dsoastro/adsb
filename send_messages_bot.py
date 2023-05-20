# rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 send_messages_bot.py

import numpy as np
import sys
from datetime import datetime
import math
import requests
from common import process, get_heading, log, save, get_dst, empty_msg
from conf import OBSERVER_LAT, OBSERVER_LON, MAX_PROXIMITY_DST, TOKEN, CHAT_ID
import pyModeS as pms
import traceback

class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def send_message(self, chat_id, text):
        params = {'chat_id': str(chat_id), 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

botHandler = BotHandler(TOKEN)

# {icao: {callsign:"", position:"", alt:"", speed:"", num_msg:"", num_df11:"", time:""}}
messages = {}

def get_min_expected_dst(icao, lat, lon, speed, heading):
    '''

    :param lat:
    :param lon:
    :param speed:
    :param heading:
    :return: min dst in km, min time in seconds
    '''
    v_meridian = speed * math.cos(heading * math.pi / 180) / 3.6  # m/s
    v_lon = speed * math.sin(heading * math.pi / 180) / 3.6
    min_dst = 10000
    min_t = 10000
    for t in range(300):
        lat_ = lat + v_meridian / 1000 / 110 * t
        lon_ = lon + v_lon / 1000 / 110 * t / (110 * math.cos(lat * math.pi / 180))
        dst = get_dst(lat_, lon_, OBSERVER_LAT, OBSERVER_LON)
        if dst < min_dst:
            min_dst = dst
            min_t = t
    log(icao, messages[icao].get("callsign", ""), "get_min_expected_dst", "{:.1f}".format(min_dst), min_t)
    return min_dst, min_t

# {icao: {callsign:"", position:"", alt:"", speed:"", num_msg:"", num_df11:"", time:""}}
messages = {}

def update_messages(msg, ref_lat=OBSERVER_LAT, ref_lon=OBSERVER_LON):
    def send_proximity_message(msg):
        if messages[icao].get("proximity_count") is None:
            messages[icao]["proximity_count"] = 0
        messages[icao]["proximity_count"] += 1
        if messages[icao]["proximity_count"] < 4:
            botHandler.send_message(CHAT_ID, msgt)

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
            return

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
                    messages[icao]["position_exact"] = (lat, lon)
                    log(icao, messages[icao].get("callsign", ""), pos_str)
                    speed_exact = messages[icao].get("speed_exact")
                    if speed_exact is not None:
                        speed, heading = speed_exact
                        dst_, time_ = get_min_expected_dst(icao, lat, lon, speed, heading)
                        if dst_ < MAX_PROXIMITY_DST:
                            msgt = "in " + str(time_) + "s " + "{:.1f}".format(dst_) + " km " + icao + " " + messages[
                                icao].get("callsign", "") + " " + pos_str + " " + messages[icao].get("speed", "")
                            send_proximity_message(msgt)

                    if dst < MAX_PROXIMITY_DST:
                        msgt = icao + " " + messages[icao].get("callsign", "") + " " + pos_str + " " + messages[
                            icao].get("speed", "")
                        send_proximity_message(msgt)

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
                    messages[icao]["speed_exact"] = (v * 1.852, heading)
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
        # log(e)
        # traceback.print_exc()
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
