# -*- coding: utf-8 -*-
import traceback
import json

from util.pool import *
from util.redissub import RedisSub
from util.wsmsghandler import WSMessageHandler
from . import getHandler


class HostHandler(WSMessageHandler):
    def __init__(self, env):
        super(HostHandler, self).__init__(env)

        self.host = env.host
        self.exp = env.exp
        self.pool = Pool(env.redis, env.exp['id'])

        self.sub = None

    def listen(self, channel, callback):
        self.sub = RedisSub(channel, callback)
        self.sub.start()

    def on_message(self, msg):
        if msg.type == 'message':
            pass

    def switchHandler(self, msg=None):
        handlers = [('SHUFFLE', 'Shuffle'), ('MONITOR', 'Monitor'), ('END', 'End')]
        if 'stage' not in self.host:
            self.host.set('stage', handlers[0][0])
        currentstage = self.host['stage'].split(':')[0]
        for stage, handler in handlers:
            if stage == currentstage:
                self.close()
                try:
                    self.env.msghandler = getHandler('SealedEnglish', 'host', handler)(self.env)
                    if msg:
                        self.env.on_message(json.dumps(msg))
                except Exception, e:
                    self.write({'error': str(traceback.format_exc())})
                break
        else:
            self.write({'error': 'stage error'})

    def nextStage(self, msg=None):
        handlers = [('SHUFFLE', 'Shuffle'), ('MONITOR', 'Monitor'), ('END', 'End')]
        if not 'stage' in self.host:
            self.host.set('stage', handlers[0][0])
        else:
            currentstage = self.host.get('stage', refresh=True).split(':')[0]
            for i in range(len(handlers)):
                if handlers[i][0] == currentstage:
                    i += 1
                    break
            else:
                return
            if i < len(handlers):
                self.host.set('stage', handlers[i][0])
                self.switchHandler(msg)

    def heartbeat(self, data):
        pass

    def close(self):
        if self.sub:
            self.sub.stop()