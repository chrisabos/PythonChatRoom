#!/user/bin/env python3

import sys
import socket
import time
import threading

IP_ADDR = '192.168.242.239'
PORT = 12345
DATA_SIZE = 1024
RUNNING = True

if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

def listen_loop(socket):
    data = socket.recv(DATA_SIZE)
    while RUNNING and data:
        print(data.decode())
        data = socket.recv(DATA_SIZE)

if __name__ == '__main__':
    print('Type \'quit\' to leave')

    s = socket.socket()
    s.connect((IP_ADDR, PORT))

    listen_thread = threading.Thread(target=listen_loop, args=(s,))
    listen_thread.start()

    while RUNNING:
        input_text = input()
        if input_text == 'quit':
            RUNNING = False
            break

        #if it is a message to the server
        msg = message.Message()
        msg.set_text(input_text)
        s.sendall(message.pack(msg))

    listen_thread.join()
    s.shutdown()
