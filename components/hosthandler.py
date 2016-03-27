# -*- coding: utf-8 -*-
import os
import traceback
import json

from utils.exprv import *
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


class HostHandler(WSMessageHandler):
    def __init__(self, env):
        super(HostHandler, self).__init__(env)

        self.host = env.host
        self.exp = env.exp
        self.pool = Pool(self.env.redis, self.exp['id'])

        self.msg_channel = 'exp:' + str(self.exp['id'])
        self.host_domain = 'host:' + str(self.exp['id'])
        self.pool_domain = 'pool:' + str(self.exp['id'])
        self.settings = self.host.get('settings', dict(), True)
        self.sub = None

        self.RemotePool = RemotePool(self.msg_channel, self.pool_domain,
                                     self.env.redis.publish)

        self.loader = components.hs.loader

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
                if domain == self.host_domain:
                    if hasattr(self, msg['cmd']):
                        getattr(self, msg['cmd'])(msg.get('data'))
            except:
                self.RemoteWS.error(str(traceback.format_exc()))

    def render(self, template_name, *args, **kwargs):
        return self.loader.load(template_name).generate( *args, **kwargs)

    @on_redis
    def switch_handler(self, msg=None):
        if 'stage' not in self.host:
            self.env.msg_handler = components.hs.handlers['HostInit'](self.env)
            return

        stage = self.host.get('stage', refresh=True).split(':')[0]
        self.close()
        self.env.msg_handler = components.hs.handlers[stage](self.env)
        if msg:
            self.env.on_message(json.dumps(msg))

    @on_ws
    def heartbeat(self, data):
        pass

    def close(self):
        if self.sub:
            self.sub.stop()