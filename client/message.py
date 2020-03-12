import json

def pack():
    return json.dumps(self.msg).encode('utf-8')

def unpack():
    return json.loads()

class Message:
    def __init__(self, data={}):
        self.msg = data

    def get_text(self):
        return self.msg.get('text')

    def get_sender(self):
        return self.msg.get('sender')

    def get_time(self):
        return self.msg.get('time')

    def set_text(self, text):
        self.msg['text'] = text

    def set_sender(self, name, color=None, clan=None):
        self.msg['sender'] = {}
        self.msg['sender']['name'] = name
        self.msg['sender']['color'] = color
        self.msg['sender']['clan'] = clan

    def set_time(self, time):
        self.msg['time'] = time

    def print(self):
        print()
