# rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 send_messages_tui.py

import numpy as np
import socket
import sys
import traceback
from common import process,save
from conf import SERVER, PORT

while True:
    buffer = sys.stdin.buffer.read(1024*1024)
    data = np.frombuffer(buffer, dtype='uint8')
    data = data.astype(float).reshape((-1, 2))
    data = data - 127
    I, Q = data[:, 0], data[:, 1]
    A = np.sqrt(I * I + Q * Q)
    msg = process(A, 5, 0.7)
    if msg is not None:
        save(msg)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (SERVER, PORT)
        try:
            sock.connect(server_address)
            sock.sendall(msg.encode())
            sock.close()
        except Exception as e:
            traceback.print_exc()