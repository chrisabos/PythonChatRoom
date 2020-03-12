#!/user/bin/env python3

import sys
import socket
import threading

IP_ADDR = '192.168.242.239'
PORT = 12345
DATA_SIZE = 1024
CLIENTS = []
RUNNING = True

if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

def broadcast(msg):
    for c in CLIENTS:
        try:
            c.send(msg)
        except:
            pass

class Client:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.name = ''

    def send(self, msg):
        self.conn.sendall(msg)

    def run(self):
        try:
            self.send('Please input your name: '.encode())
            self.name = self.conn.recv(DATA_SIZE).decode('utf-8')
            broadcast('[SERVER]: {} has joined the chat!'.format(self.name).encode())
            CLIENTS.append(self)

            data = self.conn.recv(DATA_SIZE)
            while data:
                print('{}: {}'.format(self.name, data.decode()))
                broadcast('{}: {}'.format(self.name, data.decode()).encode())
                data = self.conn.recv(DATA_SIZE)
        except:
            print("Connection Lost to {}".format(self.address))
            broadcast("{} has disconnected".format(self.name).encode())
            CLIENTS.remove(self)

def accept_clients():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP_ADDR, PORT))
    s.listen()
    while RUNNING:
        conn, address = s.accept()
        print("Connection from {}".format(address))
        new_client = Client(conn, address)
        new_client_thread = threading.Thread(target=new_client.run)
        new_client_thread.start()

def tcp_server():
    accept_thread = threading.Thread(target=accept_clients)
    accept_thread.start()

    #command input
    while RUNNING:
        user_input = input()
        if user_input == 'quit':
            #RUNNING = False
            break

    accept_thread.stop()

if __name__ == '__main__':
    print("Starting server on {}:{}".format(IP_ADDR, PORT))
    tcp_server()
    #udp_echo()
