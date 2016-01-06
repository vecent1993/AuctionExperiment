# -*- coding: utf-8 -*-
import traceback
import time
import json

from util.pool import Player
from util.redissub import RedisSub
from util.wshandler import WSMessageHandler, on_ws, on_redis
from .. import get_handler
from treatments_ import getTreatment


class PlayerHandler(WSMessageHandler):
    def __init__(self, env):
        super(PlayerHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

        self.player.set('heartbeat', time.time())
        self.player.set('online', True)

        self.msg_channel = 'exp:' + str(self.env.exp['id'])
        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.group_domain = None

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
                if domain == self.player_domain:
                    name = '_'.join(('@', 'redis', 'player', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
                elif domain == self.group_domain:
                    name = '_'.join(('@', 'redis', 'group', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
            except:
                print str(traceback.format_exc())

    @on_redis('player')
    def switch_handler(self, msg=None):
        if 'stage' not in self.player:
            PlayerHandler.next_stage(self.env.redis, self.exp['id'], self.player.pid)

        stage = self.player.get('stage', refresh=True).split(':')[0]
        self.close()
        self.env.msg_handler = get_handler('player', stage)(self.env)
        if msg:
            self.env.on_message(json.dumps(msg))

    @on_redis('player')
    def change_stage(self, msg=None):
        PlayerHandler.next_stage(self.env.redis, self.exp['id'], self.player.pid)
        self.switch_handler(msg)

    @on_ws
    def heartbeat(self, data):
        self.player.set('heartbeat', time.time())

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        super(PlayerHandler, self).publish(self.msg_channel, msg)

    def close(self):
        if self.sub:
            self.sub.stop()

    @staticmethod
    def next_stage(redis, expid, pid):
        player = Player(redis, expid, pid)

        if not player.get('handlers', []):
            player.set('stage', 'End')
        else:
            player.set('stage', player['handlers'][0])
            player.set('handlers', player['handlers'][1:])
