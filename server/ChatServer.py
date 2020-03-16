#!/user/bin/env python3

############################################################
### LIBRARIES
############################################################
import sys
import socket
import threading
import time

#Private library
import message

############################################################
### CONFIG
############################################################
IP_ADDR = '192.168.242.239' # IP ADDRESS
PORT = 12345 # PORT NUMBER
DATA_SIZE = 1024 # MAX BYTE TRANSMISSION SIZE
MSG_SIZE_MAX = 200 # MAX TEXT SIZE -- maximum number of characters in the text portion of the message
NAME_SIZE_LIMIT = 20 # MAX CLIENT NAME SIZE
SHOW_CLIENT_MESSAGES = True # display the client messages in the server CLI

############################################################
### GLOBAL VARIABLES
############################################################
global RUNNING
CLIENTS = [] # a list of all connected clients
RUNNING = True # true while the server is running - set to false to terminate
USER_COMMANDS = ['/name', '/color', '/clan', '/help'] # a list of user commands
USER_COLORS = ['red', 'green', 'yellow', 'blue', 'purple', 'cyan'] # list of client name colors

############################################################
### MANAGE CLI ARGUMENTS
############################################################
if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

# Function: broadcast
# Desc: a function that sends the same message to all connected clients
# Args: byte array of message
# Returns: None
def broadcast(msg):
    for c in CLIENTS:
        try:
            c.send(msg)
        except:
            pass
    return None

# Function: get_time
# Desc: a function that returns a formatted string represening the current local time
# Returns: time as string
def get_time():
    return '{}'.format(time.strftime('%H:%M:%S', time.localtime()))

# Function: handle_user_command
# Desc: this function takes a sending client and a command message and executes the command
# Args: sending client, the message text
# Returns: True/ False if the command is valid/ not valid
def handle_user_command(client, msg):
    # break the text into components of the command
    cmds = msg.get_text().split()

    ## NAME COMMAND
    if cmds[0] == '/name':
        prev_name = client.name_color + client.name
        client.name = ''
        client.get_name()
        # this code tells the chat room that a user changed their name
        # by popular demand this was removed
        # msg_name_change = message.Message()
        # msg_name_change.set_time(get_time())
        # msg_name_change.set_type('text')
        # msg_name_change.set_text('{} changed their name to {}'.format(prev_name, client.name))
        # broadcast(message.pack(msg_name_change))
        return True

    ## NAME COLOR COMMAND
    elif cmds[0] == '/color':
        if len(cmds) > 1:
            if cmds[1] in USER_COLORS:
                #print('set {} color to red'.format(client.name))
                client.name_color = cmds[1]
            else:
                client.name_color = None
        else:
            client.name_color = None
        return True

    ## CLAN COMMAND
    elif cmds[0] == '/clan':
        if len(cmds) > 1:
            if cmds[1] == 'leave':
                client.clan = None
                return True
            elif len(cmds[1]) <= 4:
                client.clan = cmds[1]
                return True
        return False

    ## HELP COMMAND
    elif cmds[0] == '/help':
        msg_help = message.Message()
        msg_help.set_type('text')
        msg_help.set_text('\n\t/help - show help\n\t/name <new name> - change your name\n\t/color [red, green, yellow, blue, purple, cyan] - change name color WIP\n\t/clan leave/<4 characters> - leave or join a clan')
        client.send(message.pack(msg_help))
        return True
    return False


## CLIENT CLASS - each connecting client gets assigned a class
class Client:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.name = ''
        self.name_color = None
        self.clan = None
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

    #manages ping messages sent to this client
    def handle_ping(self):
        #print('ping from {}'.format(self.address))
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

            try:
                #get name from socket while the message received is not a ping
                msg_client_name = message.Message(data=message.unpack(self.conn.recv(DATA_SIZE)))
                while msg_client_name.get_type() == 'ping':
                    self.handle_ping()
                    msg_client_name = message.Message(data=message.unpack(self.conn.recv(DATA_SIZE)))
                name_from_client = msg_client_name.get_text()
            except:
                #if the data from the client is malformed then restart this process
                break

            #verify name length
            if len(name_from_client) > NAME_SIZE_LIMIT:
                # if the name is too long restart
                msg_name_too_long = message.Message()
                msg_name_too_long.set_type('text')
                msg_name_too_long.set_text('That name is too long. Max: {} characters'.format(NAME_SIZE_LIMIT))
                self.send(message.pack(msg_name_too_long))
            else:
                #verify name isnt already taken
                name_taken = False
                for c in CLIENTS:
                    if name_from_client == c.name:
                        name_taken = True

                # if the name is taken then restart
                if name_taken:
                    msg_name_taken = message.Message()
                    msg_name_taken.set_type('text')
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
            broadcast(message.pack(msg_user_join))

            #add this client to the client list
            CLIENTS.append(self)

            # main data listen loop
            msg_data = self.conn.recv(DATA_SIZE)
            while msg_data:
                # turn the data into a message
                msg = message.Message(data=message.unpack(msg_data))
                if msg.get_text() != None:
                    # set the values of the message such as the time and the sender
                    msg.set_time(get_time())
                    msg.set_sender(self.name, color=self.name_color, clan=self.clan)

                    #handle message types
                    if msg.get_type() == 'ping':
                        self.handle_ping()
                    elif msg.get_type() == 'leave':
                        self.leave()
                    elif msg.get_type() == 'text':
                        #check if the msg the user sent is a command
                        if msg.get_text().split()[0] in USER_COMMANDS:
                            #handle the user command
                            if not handle_user_command(self, msg):
                                #if the user command fails
                                #tell the user
                                msg_invalid_command = message.Message()
                                msg_invalid_command.set_type('text')
                                msg_invalid_command.set_text('Invalid command. view /help')
                                self.send(message.pack(msg_invalid_command))
                        else:
                            #check the text from the user is smaller than the max acceptable size
                            if len(msg.get_text()) > MSG_SIZE_MAX:
                                error_msg = message.Message()
                                error_msg.set_type('error')
                                error_msg.set_sender('[SERVER]')
                                error_msg.set_time(get_time())
                                error_msg.set_text('Your message was too long. Max is 200 characters.')
                                self.send(message.pack(error_msg))
                                print('{} attempted to send a LARGE message'.format(self.address))
                            else:
                                #broadcast the message to the clients
                                broadcast(message.pack(msg))
                                if SHOW_CLIENT_MESSAGES:
                                    print(msg)
                    else:
                        #handle unknown cases
                        print('Unknown message type: {}'.format(message.unpack(msg)))
                #continue to listen for data from the client
                msg_data = self.conn.recv(DATA_SIZE)
        except Exception as e:
            #handle exceptions
            #i am not the most familiar with the python exceptions
            #so im printing as much information to both learn and debug
            #this does lead to a messy server console
            exc_information = sys.exc_info()
            print(exc_information)
            print("Connection Lost to {}".format(self.address))
            self.leave()


#Function: start_server
#Desc: starts the server by creating the default connection socket for users to connect to
#Return: the server socket
def start_server():
    print("\033[1;37;40mStarting server on {}:{}".format(IP_ADDR, PORT))
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP_ADDR, PORT))
    s.listen()
    return s

#Function: accept_clients
#Desc: a loop for listening and establishing clients to the server
#Args: the server socket
def accept_clients(s):
    while RUNNING:
        conn, address = s.accept()
        conn.settimeout(10)
        new_conn_msg = "{} Connection from {}".format(get_time(), address)
        print(new_conn_msg)
        new_client = Client(conn, address)
        new_client_thread = threading.Thread(target=new_client.run)
        new_client_thread.start()

def main():
    #start the server
    server_socket = start_server()

    global RUNNING

    #start the client accept thread
    accept_thread = threading.Thread(target=accept_clients, args=(server_socket, ))
    accept_thread.start()

    #handle server command line input
    while RUNNING:
        user_input = input()
        if user_input.startswith('/stop'):
            RUNNING = False
            break
        elif user_input.startswith('/say'):
            msg_server_broadcast = message.Message()
            msg_server_broadcast.set_type('text')
            msg_server_broadcast.set_text(user_input[5:])
            msg_server_broadcast.set_sender('[SERVER]')
            broadcast(message.pack(msg_server_broadcast))

    accept_thread.stop()

if __name__ == '__main__':
    main()
    #udp_echo()
