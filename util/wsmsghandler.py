# -*- coding: utf-8 -*-
import traceback
import json

class WSMessageHandler(object):

    def __init__(self, env):
        self.env = env

    def on_message(self, msg):
        pass

    def get(self, data):
        pass

    def handle(self, msg):
        try:
            return getattr(self, msg['cmd'])(msg.get('data'))
        except Exception, e:
            return {'cmd': 'error', 'data': str(traceback.format_exc())}

    def publish(self, channel, msg):
        self.env.redis.publish(str(channel), json.dumps(msg))

    def write(self, msg):
        self.env.write_message(json.dumps(msg))

    def close(self):
        pass
