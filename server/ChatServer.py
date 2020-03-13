#!/user/bin/env python3

import sys
import socket
import threading
import time

import message

IP_ADDR = '192.168.242.239'
PORT = 12345
DATA_SIZE = 1024
CLIENTS = []
RUNNING = True

MSG_SIZE_MAX = 200
NAME_SIZE_LIMIT = 20

LOG_FILE = open('logs.txt', 'w+')

USER_COMMANDS = ['/name', '/color', '/clan']

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

# def client_timeout():
#     while RUNNING:
#         for c in CLIENTS:
#             c.timeout_timer -= 1
#             if c.timeout_timer == 0:
#                 #c.leave()
#                 pass
#         time.sleep(3)


class Client:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.name = ''
        self.name_color = ' '
        self.timeout_timer = 4

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

    def handle_ping(self):
        print('ping from {}'.format(self.address))
        msg_ping_resp = message.Message()
        msg_ping_resp.set_type('ping')
        self.send(message.pack(msg_ping_resp))

    #called when making the client leave the SERVER
    # either by request or timeout
    def leave(self):
        CLIENTS.remove(self)
        msg_user_left = message.Message()
        msg_user_left.set_time(get_time())
        msg_user_left.set_text('{} left the chat'.format(self.name))
        broadcast(message.pack(msg_user_left))

    #get the client name from the client
    def get_name(self):
        #do this until we have a name
        while self.name == '':
            #prompt user
            msg_name_prompt = message.Message()
            msg_name_prompt.clear()
            msg_name_prompt.set_text('Please input your name')
            self.send(message.pack(msg_name_prompt))
            #get name from socket
            msg_client_name = message.Message(data=message.unpack(self.conn.recv(DATA_SIZE)))
            while msg_client_name.get_type() == 'ping':
                self.handle_ping()
                msg_client_name = message.Message(data=message.unpack(self.conn.recv(DATA_SIZE)))
            name_from_client = msg_client_name.get_text()
            #check name length
            if len(name_from_client) > NAME_SIZE_LIMIT:
                msg_name_too_long = message.Message()
                msg_name_too_long.set_text('That name is too long')
                self.send(message.pack(msg_name_too_long))
            else:
                #check name isnt already taken
                name_taken = False
                for c in CLIENTS:
                    if name_from_client == c.name:
                        name_taken = True
                if name_taken:
                    msg_name_taken = message.Message()
                    msg_name_taken.set_text('That name is already taken')
                    self.send(message.pack(msg_name_taken))
                else:
                    #if we pass all the tests then set the clien name
                    self.name = name_from_client

    #main client thread function
    def run(self):
        try:
            #get the name from the client
            self.get_name()

            #tell everyone there is a new client
            msg_user_join = message.Message()
            msg_user_join.set_type('text')
            msg_user_join.set_text('{} has joined the chat!'.format(self.name))
            msg_user_join.set_time(get_time())
            print(message.pack(msg_user_join))
            broadcast(message.pack(msg_user_join))

            #add this client to the client list
            CLIENTS.append(self)

            msg_data = self.conn.recv(DATA_SIZE)
            while msg_data:
                msg = message.Message(data=message.unpack(msg_data))
                if msg.get_text() != None:
                    msg.set_time(time.strftime('%H:%M:%S', time.localtime()))
                    msg.set_sender(self.name)

                    if msg.get_type() == 'ping':
                        self.handle_ping()
                    elif msg.get_type() == 'leave':
                        self.leave()
                    elif msg.get_type() == 'text':
                        if msg.get_text().split()[0] in USER_COMMANDS:
                            handle_user_command(self, msg)
                        else:
                            if len(msg.get_text()) > MSG_SIZE_MAX:
                                error_msg = message.Message()
                                error_msg.set_type('error')
                                error_msg.set_sender('[SERVER]')
                                error_msg.set_time(get_time())
                                error_msg.set_text('Your message was too long. Max is 200 characters.')
                                self.send(message.pack(error_msg))
                                print('{} attempted to send a LARGE message'.format(self.address))
                            else:
                                #the formatted message as it will be sent to all users
                                msg.print()
                                broadcast(message.pack(msg))
                    else:
                        print('Unknown message type: {}'.format(message.unpack(msg)))
                msg_data = self.conn.recv(DATA_SIZE)
        except Exception as e:
            print(e)
            print("Connection Lost to {}".format(self.address))
            self.leave()

def accept_clients():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP_ADDR, PORT))
    s.listen()
    while RUNNING:
        conn, address = s.accept()
        conn.settimeout(10)
        new_conn_msg = "{} Connection from {}".format(get_time(), address)
        print(new_conn_msg)
        LOG_FILE.write(new_conn_msg)
        new_client = Client(conn, address)
        new_client_thread = threading.Thread(target=new_client.run)
        new_client_thread.start()

def tcp_server():

    # client_timeout_thread = threading.Thread(target=client_timeout)
    # client_timeout_thread.start()

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
