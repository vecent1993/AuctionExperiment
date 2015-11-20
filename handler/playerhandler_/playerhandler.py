# -*- coding: utf-8 -*-
import traceback
import time
import json

from util.pool import Player
from util.core import RedisExp
from util.redissub import RedisSub
from util.wshandler import WSMessageHandler, onWs, onRedis
from .. import getHandler
from treatments_ import getTreatment


class PlayerHandler(WSMessageHandler):
    def __init__(self, env):
        super(PlayerHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

        self.player.set('heartbeat', time.time())
        self.player.set('online', True)

        self.msgchannel = 'exp:' + str(self.env.exp['id'])
        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.groupdomain = None

        self.sub = None

    def listen(self, channel, callback):
        self.sub = RedisSub(channel, callback)
        self.sub.start()

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if 'domain' not in msg:
                return

            domain = msg['domain']
            try:
                if domain == self.playerdomain:
                    name = '_'.join(('@', 'redis', 'player', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
                elif domain == self.groupdomain:
                    name = '_'.join(('@', 'redis', 'group', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
            except Exception, e:
                print str(traceback.format_exc())

    @onRedis('player')
    def switchHandler(self, msg=None):
        if 'stage' not in self.player:
            PlayerHandler.nextStage(self.env.redis, self.exp['id'], self.player.pid)

        stage = self.player.get('stage', refresh=True).split(':')[0]
        self.close()
        self.env.msghandler = getHandler('player', stage)(self.env)
        if msg:
            self.env.on_message(json.dumps(msg))

    @onRedis('player')
    def changeStage(self, msg=None):
        PlayerHandler.nextStage(self.env.redis, self.exp['id'], self.player.pid)
        self.switchHandler(msg)

    @onWs
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

    @staticmethod
    def nextStage(redis, expid, userid):
        player = Player(redis, expid, userid)
        handlers = ['Intro', 'SealedEnglish', 'End']
        if not 'stage' in player:
            player.set('stage', handlers[0])
        else:
            currentstage = player.get('stage', refresh=True).split(':')[0]
            for i in range(len(handlers)):
                if handlers[i] == currentstage:
                    i += 1
                    break
            else:
                return

            if i < len(handlers):
                player.set('stage', handlers[i])
        # exp = RedisExp(redis, expid)
        #
        # st = None
        # if 'treatment' not in player:
        #     nt = 0
        # else:
        #     currentT = map(int, player.get('treatment', refresh=True).split(':'))
        #     if len(currentT) == 1:
        #         nt = currentT[0] + 1
        #     else:
        #         sid = int(player.get('sid', refresh=True))
        #         session = exp['settings']['treatments'][currentT[0]]['sessions'][sid]
        #         if currentT[1] + 1 >= len(session['treatments']):
        #             nt = currentT[0] + 1
        #         else:
        #             nt, st = currentT[0], currentT[1] + 1
        #
        # if exp['settings']['treatments'][nt]['code'] == 'Sessions':
        #     if st is None:
        #         st = 0
        #     player.set('treatment', ':'.join(map(str, (nt, st))))
        #     sid = int(player.get('sid'))
        #     session = exp['settings']['treatments'][nt]['sessions'][sid]
        #     treatment = session['treatments'][st]
        #     player.set('settings', treatment)
        #     t = getTreatment(treatment['code'])(treatment)
        #     player.set('stage', t.getPlayerHandler())
        # else:
        #     player.set('treatment', str(nt))
        #     treatment = exp['settings']['treatments'][nt]
        #     player.set('settings', treatment)
        #     t = getTreatment(treatment['code'])(treatment)
        #     player.set('stage', t.getPlayerHandler())
