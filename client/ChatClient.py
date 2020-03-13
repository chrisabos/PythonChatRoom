#!/user/bin/env python3

# libraries
import sys
import socket
import time
import threading

# my libraries
import message

IP_ADDR = '192.168.242.239'
PORT = 12345
DATA_SIZE = 1024
RUNNING = True

CONNECTION_TIMEOUT_SECONDS = 4
timeout_timer = 4

# read command line arguments
if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

# ping loop sends a ping to the server
# periodically. If we dont get a ping
# back after a timeout time we shut the
# connection
def ping_loop(socket):
    while RUNNING:
        time.sleep(3)
        ping_msg = message.Message()
        ping_msg.set_type('ping')
        bmsg = message.pack(ping_msg)
        socket.sendall(bmsg)

def listen_loop(socket):
    try:
        msg_data = socket.recv(DATA_SIZE)
        while RUNNING and msg_data:
            #msg = message.Message(data=message.unpack(data))
            #msg.print()
            msg_recv = message.Message(data=message.unpack(msg_data))
            if msg_recv.get_type() != 'ping':
                print(msg_recv)
            msg_data = socket.recv(DATA_SIZE)
    except Exception as e:
        print(e)
        print('Connection to server lost!!!')

if __name__ == '__main__':
    print('Type \'quit\' to leave')

    s = socket.socket()
    s.connect((IP_ADDR, PORT))
    s.settimeout(10)

    listen_thread = threading.Thread(target=listen_loop, args=(s,))
    listen_thread.start()

    ping_thread = threading.Thread(target=ping_loop, args=(s,))
    ping_thread.start()

    while RUNNING:
        input_text = input()
        if input_text == 'quit':
            msg_leave = message.Message()
            msg_leave.set_type('leave')
            s.sendall(message.pack(msg))
            RUNNING = False
            break

        #if it is a message to the server
        msg = message.Message()
        msg.set_type('text')
        msg.set_text(input_text)
        s.sendall(message.pack(msg))

    listen_thread.join()
    s.shutdown()
