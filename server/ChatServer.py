#!/user/bin/env python3

import sys
import socket
import threading
import time

IP_ADDR = '192.168.242.239'
PORT = 12345
DATA_SIZE = 1024
CLIENTS = []
RUNNING = True

MSG_SIZE_MAX = 200
NAME_SIZE_LIMIT = 20

LOG_FILE = open('logs.txt', 'w+')

USER_COMMANDS = ['name', 'color', 'clan']

if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

def broadcast(msg):
    for c in CLIENTS:
        try:
            c.send(msg)
        except:
            pass

def get_time():
    return '{}'.format(time.strftime('%H:%M:%S', time.localtime()))

def handle_user_command(client, msg):
    cmds = msg.split()
    if cmds[0] == '/name':
        prev_name = client.name_color + client.name
        client.name = ''
        client.get_name()
        name_change_msg = '{} {} changed their name to {}'.format(get_time(), prev_name, client.name_color + client.name)
        broadcast(name_change_msg)
        LOG_FILE.write(name_change_msg)
        return True
    elif cmds[0] == '/color':
        if cmds[1] == 'red':
            print('set {} color to red'.format(client))
            client.name_color = '\033[1,31,40m '
        elif cmds[1] == 'green':
            client.name_color = '\033[1,32,40m '
        elif cmds[1] == 'yellow':
            client.name_color = '\033[1,33,40m '
        elif cmds[1] == 'blue':
            client.name_color = '\033[1,34,40m '
        elif cmds[1] == 'purple':
            client.name_color = '\033[1,35,40m '
        elif cmds[1] == 'cyan':
            client.name_color = '\033[1,36,40m '
        else:
            client.name_color = ' '
        return True
    return False


class Client:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.name = ''
        self.name_color = ' '

    #send a message to this client
    def send(self, msg):
        self.conn.sendall(msg)

    #send a message to all cleint but yourself
    def send_to_others(self, msg):
        for c in CLIENTS:
            if c != self:
                try:
                    c.send(msg)
                except:
                    pass

    #get the client name from the client
    def get_name(self):
        #do this until we have a name
        while self.name == '':
            #prompt user
            self.send('Please input your name: '.encode())
            #get name from socket
            name_from_client = self.conn.recv(DATA_SIZE).decode('utf-8')
            #check name length
            if len(self.name) > NAME_SIZE_LIMIT:
                self.send('That name is too long'.encode())
            else:
                #check name isnt already taken
                name_taken = False
                for c in CLIENTS:
                    if name_from_client == c.name:
                        name_taken = True
                if name_taken:
                    self.send('That name is already taken'.encode())
                else:
                    #if we pass all the tests then set the clien name
                    self.name = name_from_client

    #main client thread function
    def run(self):
        try:
            #get the name from the client
            self.get_name()

            #tell everyone there is a new client
            join_msg = '{} [SERVER]: {} has joined the chat!'.format(get_time(), self.name)
            broadcast(join_msg.encode())
            LOG_FILE.write('{} from {}'.format(join_msg, self.address))

            #add this client to the client list
            CLIENTS.append(self)

            data = self.conn.recv(DATA_SIZE)
            while data:
                msg = data.decode()

                if msg.split()[0][1:] in USER_COMMANDS:
                    handle_user_command(self, msg)
                else:
                    msg_time = '{}'.format(time.strftime('%H:%M:%S', time.localtime()))
                    if len(msg) > MSG_SIZE_MAX:
                        error = msg_time + '[ERROR]: Your message was too long. Max is 200 characters.'
                        LOG_FILE.write(error)
                        self.send(error.encode())
                        print('{} attempted to send a LARGE message'.format(self.address))
                    else:
                        #the formatted message as it will be sent to all users
                        format_msg = '{}{}: {}'.format(msg_time, self.name_color + self.name, data.decode())
                        LOG_FILE.write(format_msg)
                        print(format_msg)
                        broadcast(format_msg.encode())
                data = self.conn.recv(DATA_SIZE)
        except:
            print("Connection Lost to {}".format(self.address))
            broadcast("{} {} has disconnected".format(get_time(), self.name).encode())
            CLIENTS.remove(self)

def accept_clients():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP_ADDR, PORT))
    s.listen()
    while RUNNING:
        conn, address = s.accept()
        new_conn_msg = "{} Connection from {}".format(get_time(), address)
        print(new_conn_msg)
        LOG_FILE.write(new_conn_msg)
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
        elif user_input.startswith('/say '):
            broadcast(user_input[5:].encode())

    accept_thread.stop()
    LOG_FILE.close()

if __name__ == '__main__':
    print("Starting server on {}:{}".format(IP_ADDR, PORT))
    tcp_server()
    #udp_echo()
