# https://www.devdungeon.com/content/curses-programming-python
import curses
import socket
import pyModeS as pms
import traceback
from datetime import datetime
import math
from conf import OBSERVER_LAT, OBSERVER_LON, PORT
from common import get_dst, get_heading, get_time, empty_msg

ICAO_COL = 1
CALLSIGN_COL = 10
POS_COL = CALLSIGN_COL + 15
ALT_COL = POS_COL + 20
SPEED_COL = ALT_COL + 10
NUM_COL = SPEED_COL + 30
LAST_SEEN_COL = NUM_COL + 10
HEADING_ROW = 1



messages = {}  # {icao: {callsign:"", position:"", alt:"", speed:"", num_msg:"", num_df11:"", time:""}}

# callsign position alt speed (num_msg,num_df11) time}


def update_messages(screen, msg, ref_lat=OBSERVER_LAT, ref_lon=OBSERVER_LON):
    try:
        crc = pms.crc(msg, encode=False)

        # print("crc",crc)
        if crc != 0:
            return

        icao = pms.icao(msg)
        df = pms.df(msg)
        log("msg", msg, "icao", icao, "df", df)
        if messages.get(icao) is None:
            messages[icao] = empty_msg()

        messages[icao]["num_msg"] += 1
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
                    messages[icao]["position"] = "({:.2f},{:.2f})/{:.1f}".format(lat,lon,dst) #str(position) + "/" + "{:.1f}".format(dst)

                alt = pms.adsb.altitude(msg)
                if alt is not None:
                    alt = "{:.1f}".format(alt * 0.3)
                else:
                    alt = ""
                messages[icao]["alt"] = alt
            if df == 17 and typecode == 19:
                velocity = pms.adsb.velocity(msg)
                try:
                    (v, heading, vrate, type) = velocity
                    m = "{:.1f}".format(v * 1.852) + "/" + get_heading(heading) + "/" + "{:.1f}".format(
                        0.3 * vrate) + "/" + type
                    messages[icao]["speed"] = str(m)
                except:
                    if velocity is not None:
                        messages[icao]["speed"] = str(velocity)
            if df == 4 or df == 20:
                alt = pms.common.altcode(msg)
                if alt is not None:
                    alt = "{:.1f}".format(alt * 0.3)
                else:
                    alt = ""
                messages[icao]["alt"] = alt
    except Exception as e:
        # log("Exception", e)
        pass
    log("messages", messages)
    if screen is not None:
        draw(screen)
        screen.refresh()


def draw(screen):
    screen.addstr(HEADING_ROW, ICAO_COL, "ICAO", curses.A_BOLD)
    screen.addstr(HEADING_ROW, CALLSIGN_COL, "Callsign", curses.A_BOLD)
    screen.addstr(HEADING_ROW, POS_COL, "Pos", curses.A_BOLD)
    screen.addstr(HEADING_ROW, ALT_COL, "Alt", curses.A_BOLD)
    screen.addstr(HEADING_ROW, SPEED_COL, "Speed", curses.A_BOLD)
    screen.addstr(HEADING_ROW, NUM_COL, "Msgs", curses.A_BOLD)
    screen.addstr(HEADING_ROW, LAST_SEEN_COL, "Last seen", curses.A_BOLD)
    row = HEADING_ROW + 1
    alist = []
    for icao, board in messages.items():
        alist.append((icao, board))

    if len(alist) > 0:
        alist.sort(key=lambda x: x[1]["order"])
    for item in alist:
        screen.addstr(row, ICAO_COL, item[0])
        board = item[1]
        screen.addstr(row, CALLSIGN_COL, board["callsign"])
        screen.addstr(row, POS_COL, board["position"])
        screen.addstr(row, ALT_COL, board["alt"])
        screen.addstr(row, SPEED_COL, board["speed"])
        screen.addstr(row, NUM_COL, str(board["num_msg"]) + "/" + str(board["num_df11"]))
        screen.addstr(row, LAST_SEEN_COL, get_time(board["time"]))
        row += 1
    pass


screen = curses.initscr()
max_y,max_x = screen.getmaxyx()
if max_x < LAST_SEEN_COL:
    print("Small screen width", max_x,"Required:", LAST_SEEN_COL)
    exit(0)

def log(*args):
    with open("log.txt", "a") as f:
        f.write(get_time(datetime.now()))
        f.write(" ")
        for arg in args:
            f.write(str(arg))
            f.write(" ")
        f.write("\n")


def main(screen):
    if screen is not None:
        draw(screen)
        screen.refresh()
    c = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", PORT))
        s.listen(5)
        while True:

            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode("utf-8")
                    msg = msg.replace("\n", "")
                    update_messages(screen, msg)


try:
    main(screen)
except Exception as e:
    curses.endwin()
    traceback.print_exc()

curses.endwin()
