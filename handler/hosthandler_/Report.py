# -*- coding: utf-8 -*-
import time

from util.pool import *
from hosthandler import HostHandler, onWs, onRedis


class Report(HostHandler):
    def __init__(self, env):
        super(Report, self).__init__(env)

        self.players = {}
        self.listen(self.msgchannel, self.on_message)

    @onRedis('host')
    def online(self, data):
        self.writeCmd('online', data)

    @onRedis('host')
    def offline(self, data):
        self.writeCmd('offline', data)

    @onRedis('host')
    def newPlayer(self, data):
        self.writeCmd('addplayer',data)

    @onRedis('host')
    def changeStage(self, data):
        super(Report, self).changeStage(dict(cmd='get'))

    @onWs
    def get(self, data):
        if not self.exp:
            self.writeCmd('error', 'no experiment')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/report.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @onWs
    def start(self, data=None):
        self.publish('closePool', self.pooldomain)
