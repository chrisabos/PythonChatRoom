import json

def pack(msg):
    return json.dumps(msg.msg).encode('utf-8')

def unpack(msg):
    return json.loads(msg.decode('utf-8'))

class Message:
    def __init__(self, data={}):
        self.msg = data

    def print(self):
        print(pack(self))

    def clear(self):
        self.msg = {}

    ####################
    #    GETTERS       #
    ####################
    def get_type(self):
        return self.msg.get('type')

    def get_text(self):
        return self.msg.get('text')

    def get_sender(self):
        return self.msg.get('sender')

    def get_time(self):
        return self.msg.get('time')

    ####################
    #    SETTERS       #
    ####################
    def set_type(self, type):
        self.msg['type'] = type

    def set_text(self, text):
        self.msg['text'] = text

    def set_sender(self, name, color=None, clan=None):
        self.msg['sender'] = {}
        self.msg['sender']['name'] = name
        self.msg['sender']['color'] = color
        self.msg['sender']['clan'] = clan

    def set_time(self, time):
        self.msg['time'] = time
