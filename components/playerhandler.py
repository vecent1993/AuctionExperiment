# -*- coding: utf-8 -*-
"""
这个模块包含：所有参与人端处理服务的父类。
"""

import traceback
import time
import json
import os

from utils.exprv import Player
from utils.redissub import RedisSub
from utils.wshandler import WSMessageHandler, on_ws, on_redis
import components


class RemotePool(object):
    def __init__(self, channel, pool_domain, publish):
        self.publish = publish
        self.pool_domain = pool_domain
        self.channel = channel

    def __getattr__(self, cmd):
        def _wrap(data=None, **kwargs):
            msg = dict(cmd=cmd, domain=self.pool_domain)
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.publish(self.channel, json.dumps(msg))
        return _wrap


class RemoteGroup(object):
    def __init__(self, channel, group_domain, publish):
        self.publish = publish
        self.group_domain = group_domain
        self.channel = channel

    def __getattr__(self, cmd):
        def _wrap(data=None, **kwargs):
            msg = dict(cmd=cmd, domain=self.group_domain)
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.publish(self.channel, json.dumps(msg))
        return _wrap


class PlayerHandler(WSMessageHandler):
    def __init__(self, env):
        super(PlayerHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

        self.player.set('heartbeat', time.time())
        self.player.set('online', True)

        self.msg_channel = 'exp:%s' % self.env.exp['id']
        self.pool_domain = 'pool:%s' % self.env.exp['id']
        self.player_domain = 'player:%s:%s' % (self.env.exp['id'], self.player.pid)
        self.group_domain = None
        self.settings = self.player.get('settings', dict(), True)

        self.RemotePool = RemotePool(self.msg_channel, self.pool_domain,
                                     self.env.redis.publish)
        self.RemoteGroup = None
        self.sub = None
        self.loader = components.hub.loader

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
                    if hasattr(self, msg['cmd']):
                        getattr(self, msg['cmd'])(msg.get('data'))
                elif domain == self.group_domain:
                    if hasattr(self, msg['cmd']):
                        getattr(self, msg['cmd'])(msg.get('data'))
            except:
                self.RemoteWS.error(str(traceback.format_exc()))

    @on_redis
    def switch_handler(self, msg=None):
        if 'stage' not in self.player:
            self.env.msg_handler = components.hub.handlers['PlayerInit'](self.env)
            return

        stage = self.player.get('stage', refresh=True).split(':')[0]
        self.close()
        try:
            self.env.msg_handler = components.hub.handlers[stage](self.env)
            if msg:
                self.env.on_message(json.dumps(msg))
        except:
            self.RemoteWS.error(str(traceback.format_exc()))

    @on_redis
    def change_substage(self, msg=None):
        pass

    @on_ws
    def heartbeat(self, data):
        self.player.set('heartbeat', time.time())

    def render(self, template_name, *args, **kwargs):
        return self.loader.load(template_name).generate( *args, **kwargs)

    def close(self):
        if self.sub:
            self.sub.stop()