#!/user/bin/env python3

############################################################
### LIBRARIES
############################################################
import sys
import socket
import time
import threading

#private libraries
import message

############################################################
### CONFIG
############################################################
IP_ADDR = '192.168.242.239' # IP ADDRESS
PORT = 12345 # PORT NUMBER
DATA_SIZE = 1024 # MAX BYTE TRANSMISSION SIZE

############################################################
### GLOBALS
############################################################
RUNNING = True
CONNECTION_TIMEOUT_SECONDS = 4
timeout_timer = 4

############################################################
### MANAGE CLI ARGUMENTS
############################################################
if len(sys.argv) == 3:
    IP_ADDR = sys.argv[1]
    PORT = int(sys.argv[2])

# ping loop sends a ping to the server
# periodically. If we dont get a ping
# back after a timeout time we shut the
# connection
def ping_loop(socket):
    try:
        while RUNNING:
            time.sleep(3)
            ping_msg = message.Message()
            ping_msg.set_type('ping')
            bmsg = message.pack(ping_msg)
            socket.sendall(bmsg)
    except:
        pass

#the main listening loop for the client
def listen_loop(socket):
    try:
        #receive data
        msg_data = socket.recv(DATA_SIZE)
        while RUNNING and msg_data:
            #msg = message.Message(data=message.unpack(data))
            #msg.print()
            msg_recv = message.Message(data=message.unpack(msg_data))

            #print the message if it isnt a ping
            if msg_recv.get_type() != 'ping':
                print(msg_recv)

            #continue to receive data
            msg_data = socket.recv(DATA_SIZE)
    except Exception as e:
        #handle exceptions
        print(e)
        print('Connection to server lost!!!')

def main():
    print('\033[1;37;40mType \'/quit\' to leave')

    global RUNNING

    #specify connection attempts loop
    for connection_attempts in range(0, 10):
        try:
            #create socket and connect to the server
            s = socket.socket()
            s.connect((IP_ADDR, PORT))
            s.settimeout(10)

            #if we havent failed yet then reset out connection_attempts counter
            connection_attempts = 0

            #start a thread to listen for messages from the server
            listen_thread = threading.Thread(target=listen_loop, args=(s,))
            listen_thread.start()

            #start a thread to listen for pings from the server to verify connection
            ping_thread = threading.Thread(target=ping_loop, args=(s,))
            ping_thread.start()

            #listen for CLI input
            while RUNNING:
                input_text = input()

                #if the user wants to quit, we should quit
                if input_text == '/quit':
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

            #cleanup
            listen_thread.join()
            ping_thread.join()
            s.shutdown()
        except:
            #handle exceptions
            print('No Connection.. Retrying')
            time.sleep(10)

    #say goodbye depending on how it shut down
    if RUNNING:
        print('Connection Failed!!!')
    else:
        print('Good bye!')

if __name__ == '__main__':
    main()
