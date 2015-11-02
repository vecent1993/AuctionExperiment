# -*- coding: utf-8 -*-
import traceback
import json

from util.core import RedisExp
from util.pool import *
from util.redissub import RedisSub
from util.wshandler import WSMessageHandler, onWs, onRedis
from .. import getHandler
from treatments_ import getTreatment


class HostHandler(WSMessageHandler):
    def __init__(self, env):
        super(HostHandler, self).__init__(env)

        self.host = env.host
        self.exp = env.exp
        self.pool = Pool(self.env.redis, self.exp['id'])

        self.msgchannel = 'exp:' + str(self.exp['id'])
        self.hostdomain = ':'.join(('host', str(self.exp['id'])))
        self.pooldomain = ':'.join(('pool', str(self.exp['id'])))
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

        super(HostHandler, self).publish(self.msgchannel, msg)

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if 'domain' not in msg:
                return

            domain = msg['domain']
            try:
                if domain == self.hostdomain:
                    name = '_'.join(('@', 'redis', 'host', msg['cmd']))
                    if hasattr(self, name):
                        getattr(self, name)(msg.get('data'))
            except Exception, e:
                str(traceback.format_exc())

    @onRedis('host')
    def switchHandler(self, msg=None):
        if 'stage' not in self.host:
            HostHandler.nextStage(self.env.redis, self.exp['id'], self.host.hid)

        stage = self.host.get('stage', refresh=True).split(':')[0]
        self.close()
        self.env.msghandler = getHandler('host', stage)(self.env)
        if msg:
            self.env.on_message(json.dumps(msg))

    @onRedis('host')
    def changeStage(self, msg=None):
        HostHandler.nextStage(self.env.redis, self.exp['id'], self.host.hid)
        self.switchHandler(msg)

    @onWs
    def heartbeat(self, data):
        pass

    def close(self):
        if self.sub:
            self.sub.stop()

    @staticmethod
    def nextStage(redis, expid, userid):
        host = Host(redis, expid, userid)
        handlers = ['Report', 'Shuffle', 'Monitor', 'End']
        if not 'stage' in host:
            host.set('stage', handlers[0])
        else:
            currentstage = host.get('stage', refresh=True).split(':')[0]
            for i in range(len(handlers)):
                if handlers[i] == currentstage:
                    i += 1
                    break
            else:
                return

            if i < len(handlers):
                host.set('stage', handlers[i])
        # exp = RedisExp(redis, expid)
        #
        # currentT = int(host.get('treatment', -1, refresh=True))
        # if currentT + 1 < len(exp['settings']['treatments']):
        #     nextT = currentT + 1
        # else:
        #     return
        #
        # host.set('treatment', str(nextT))
        # treatment = exp['settings']['treatments'][nextT]
        # host.set('settings', treatment)
        # t = getTreatment(treatment['code'])(treatment)
        # host.set('stage', t.getHostHandler())