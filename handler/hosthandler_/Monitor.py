# -*- coding: utf-8 -*-
import time

from util.pool import *
from hosthandler import HostHandler, onWs, onRedis
from .. import getHandler


class Monitor(HostHandler):
    def __init__(self, env):
        super(Monitor, self).__init__(env)

        self.players = {}
        self.groups = {}

        self.listen(self.msgchannel, self.on_message)

    @onWs
    def get(self, data):
        if not self.exp:
            self.writeCmd('error', 'no experiment')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:   self.players[pid] = player
        now = time.time()
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/monitor.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @onWs
    def getInfo(self, data):
        if not ('sid' in data and 'gid' in data):
            self.writeCmd('error', 'error input when request group data')

        sid, gid = data['sid'], data['gid']
        key = ':'.join(['group', str(self.exp['id']), str(sid), str(gid)])
        if key not in self.groups:
            group = Group(self.env.redis, self.exp['id'], sid, gid)
            if group:
                self.groups[group.key] = group
            else:
                self.writeCmd('error', 'group not exists')
                return

        handler = self.groups[key].get('stage', refresh=True).split(':')[0]
        info = getHandler('group', handler).renderInfo(self.groups[key])
        self.writeCmd('showInfo', info)

    @onRedis('host')
    def online(self, data):
        self.writeCmd('online', data)

    @onRedis('host')
    def offline(self, data):
        self.writeCmd('offline', data)
