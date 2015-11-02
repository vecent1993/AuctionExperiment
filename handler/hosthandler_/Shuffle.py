# -*- coding: utf-8 -*-
import time

from util.pool import *
from hosthandler import HostHandler, onWs, onRedis
from .. import getHandler


class Shuffle(HostHandler):
    def __init__(self, env):
        super(Shuffle, self).__init__(env)
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
        super(Shuffle, self).changeStage(dict(cmd='get'))

    @onWs
    def get(self, data):
        if not self.exp:
            self.writeCmd('error', 'no experiment')

        if 'sessions' not in self.pool:
            self.pool['sessions'] = []
            for i, _ in enumerate(self.exp['settings']['treatments'][2]['sessions']):
                self.pool['sessions'].append(dict(id=i))
            self.pool.save('sessions')


        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/shuffle.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @onWs
    def shuffle(self, data):
        self.pool.set('players', data['players'])
        self.pool.set('sessions', data['sessions'])
        self.publish('shuffle', self.pooldomain)

    @onWs
    def getInfo(self, data):
        if not 'pid' in data:
            self.writeCmd('error', 'error input when request data')

        pid = data['pid']
        if pid not in self.players:
            player = Player(self.env.redis, self.exp['id'], pid)
            if player:
                self.players[pid] = player
            else:
                self.writeCmd('error', 'player not exists')
                return

        info = getHandler('player', 'Report').renderInfo(self.players[pid])
        self.writeCmd('showInfo', info)
