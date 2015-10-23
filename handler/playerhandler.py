# -*- coding: utf-8 -*-
import traceback
import time
import json

from util.pool import *
from util.redissub import RedisSub
from util.wsmsghandler import WSMessageHandler
from . import getHandler


class PlayerHandler(WSMessageHandler):
    def __init__(self, env):
        super(PlayerHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

        self.player.set('heartbeat', time.time())
        self.player.set('online', True)

        self.msgchannel = 'exp:' + str(self.env.exp['id'])

        self.sub = None

    def listen(self, channel, callback):
        self.sub = RedisSub(channel, callback)
        self.sub.start()

    def on_message(self, msg):
        if msg['type'] == 'message':
            pass

    def switchHandler(self, msg=None):
        if self.env.train:
            self.env.msghandler = getHandler('SealedEnglish', 'player', 'Train')(self.env)
            return

        handlers = [('PROFILE', 'Profile'), ('INTRO', 'Intro'),
                    ('SealedEnglish', 'SealedEnglish'), ('END', 'End')]
        if 'stage' not in self.player:
            self.player.set('stage', handlers[0][0])
        currentstage = self.player.get('stage', refresh=True).split(':')[0]
        for stage, handler in handlers:
            if stage == currentstage:
                try:
                    self.close()
                    self.env.msghandler = getHandler('SealedEnglish', 'player', handler)(self.env)
                    if msg:
                        self.env.on_message(json.dumps(msg))
                except:
                    self.write({'error': str(traceback.format_exc())})
                break
        else:
            self.write({'error': 'stage error'})

    def refresh(self, data=None):
        self.write({'cmd': 'refresh'})

    def nextStage(self, msg=None):
        handlers = [('PROFILE', 'Profile'), ('INTRO', 'Intro'),
                    ('SealedEnglish', 'SealedEnglish'), ('END', 'End')]
        if not 'stage' in self.player:
            self.player.set('stage', handlers[0][0])
        else:
            currentstage = self.player.get('stage', refresh=True).split(':')[0]
            for i in range(len(handlers)):
                if handlers[i][0] == currentstage:
                    i += 1
                    break
            else:
                return
            if i < len(handlers):
                self.player.set('stage', handlers[i][0])
                self.switchHandler(msg)

    def heartbeat(self, data):
        self.player.set('heartbeat', time.time())

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        super(PlayerHandler, self).publish(self.msgchannel, msg)

    def close(self):
        if self.sub:
            self.sub.stop()


class TrainHandler(WSMessageHandler):
    def __init__(self, env):
        super(TrainHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

    def heartbeat(self, data):
        pass
