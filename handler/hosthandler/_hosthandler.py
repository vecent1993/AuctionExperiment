# -*- coding: utf-8 -*-
import traceback
import json

from util.pool import *
from util.redissub import RedisSub
from util.wshandler import WSMessageHandler, on_ws, on_redis
from .. import get_handler
from treatments_ import getTreatment


class HostHandler(WSMessageHandler):
    def __init__(self, env):
        super(HostHandler, self).__init__(env)

        self.host = env.host
        self.exp = env.exp
        self.pool = Pool(self.env.redis, self.exp['id'])

        self.msg_channel = 'exp:' + str(self.exp['id'])
        self.host_domain = ':'.join(('host', str(self.exp['id'])))
        self.pool_domain = ':'.join(('pool', str(self.exp['id'])))
        self.sub = None

    def listen(self, channel, callback):
        self.sub = RedisSub(channel, callback)
        self.sub.start()

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        super(HostHandler, self).publish(self.msg_channel, msg)

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if 'domain' not in msg:
                return

            domain = msg['domain']
            try:
                if domain == self.host_domain:
                    name = '_'.join(('@', 'redis', 'host', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
            except:
                print str(traceback.format_exc())

    @on_redis('host')
    def switch_handler(self, msg=None):
        if 'stage' not in self.host:
            HostHandler.next_stage(self.env.redis, self.exp['id'], self.host.hid)

        stage = self.host.get('stage', refresh=True).split(':')[0]
        self.close()
        self.env.msg_handler = get_handler('host', stage)(self.env)
        if msg:
            self.env.on_message(json.dumps(msg))

    @on_redis('host')
    def change_stage(self, msg=None):
        HostHandler.next_stage(self.env.redis, self.exp['id'], self.host.hid)
        self.switch_handler(msg)

    @on_ws
    def heartbeat(self, data):
        pass

    def close(self):
        if self.sub:
            self.sub.stop()

    @staticmethod
    def next_stage(redis, expid, userid):
        host = Host(redis, expid, userid)

        if not host.get('handlers', []):
            host.set('stage', 'End')
        else:
            host.set('stage', host['handlers'][0])
            host.set('handlers', host['handlers'][1:])