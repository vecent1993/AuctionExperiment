# -*- coding: utf-8 -*-
import time

from util.pool import *
from . import HostHandler, on_ws, on_redis
from .. import get_handler


class Shuffle(HostHandler):
    def __init__(self, env):
        super(Shuffle, self).__init__(env)
        self.players = {}

        self.listen(self.msg_channel, self.on_message)

    @on_redis('host')
    def online(self, data):
        self.write_cmd('online', data)

    @on_redis('host')
    def offline(self, data):
        self.write_cmd('offline', data)

    @on_redis('host')
    def new_player(self, data):
        self.write_cmd('addplayer',data)

    @on_redis('host')
    def change_stage(self, data):
        super(Shuffle, self).change_stage(dict(cmd='get'))

    @on_ws
    def get(self, data):
        if not self.exp:
            self.write_cmd('error', 'no experiment')

        if 'sessions' not in self.pool:
            self.pool['sessions'] = []
            for i, _ in enumerate(self.exp['settings']['treatments'][1]['sessions']):
                self.pool['sessions'].append(dict(id=i))
            self.pool.save('sessions')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/shuffle.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @on_ws
    def shuffle(self, data):
        self.pool.set('players', data['players'])
        self.pool.set('sessions', data['sessions'])
        self.publish('shuffle', self.pool_domain)

    @on_ws
    def getInfo(self, data):
        if not 'pid' in data:
            self.write_cmd('error', 'error input when request data')

        pid = data['pid']
        if pid not in self.players:
            player = Player(self.env.redis, self.exp['id'], pid)
            if player:
                self.players[pid] = player
            else:
                self.write_cmd('error', 'player not exists')
                return

        info = get_handler('player', 'Intro').renderInfo(self.players[pid])
        self.write_cmd('showInfo', info)
