# -*- coding: utf-8 -*-
import json
import time
import random
import datetime

import util.pool
from grouphandler import GroupHandler, db, redisclient, Delay, onRedis
from ..hosthandler_.hosthandler import HostHandler
from ..playerhandler_.playerhandler import PlayerHandler


class AutoHost(GroupHandler):
    def __init__(self, expid, hostid):
        super(AutoHost, self).__init__()
        self.expid = str(expid)
        self.hid = str(hostid)
        self.redis = redisclient

        self.value = util.pool.Host(self.redis, self.expid, self.hid)
        self.pool = util.pool.Pool(self.redis, self.expid)

        self.initTasks()
        self.checkPlayer()

    @onRedis
    def initPool(self):
        if not self.value.get('sessions', refresh=True):
            self.pool.set('sessions', [{}])

    @onRedis
    def addPlayer(self, data):
        pid, username = data['pid'], data['username']
        if self.pool.get('closed', False):
            self.publish('deny', ':'.join(('player', self.expid, pid)))
            return

        if pid not in self.pool['pool']:
            self.pool['pool'].append(pid)
            self.pool.save('pool')

        self.publish('newPlayer', ':'.join(('host', self.expid)), data)
        PlayerHandler.nextStage(self.redis, self.expid, pid)
        self.publish('switchHandler', ':'.join(('player', self.expid, pid)), dict(cmd='get'))

    def checkPlayer(self, data=None):
        now = time.time()
        for pid in self.pool['pool']:
            player = util.pool.Player(self.redis, self.expid, pid)
            if now - player.get('heartbeat', 0) > 50 and player.get('online'):
                player.set('online', False)
                self.publish('offline', ':'.join(('host', self.expid)), pid)
            elif now - player.get('heartbeat', 0) <= 50 and not player.get('online', True):
                player.set('online', True)
                self.publish('online', ':'.join(('host', self.expid)), pid)
        if not self._close:
            Delay(45, self.checkPlayer, None).start()

    @onRedis
    def shuffle(self, data=None):
        for sid, session in enumerate(self.pool.get('sessions', refresh=True)):
            for gid, group in enumerate(session['groups']):
                players = {}
                for pid in filter(lambda pid: not pid.startswith('agent'), group):
                    player = util.pool.Player(self.redis, self.expid, pid)
                    player.set('sid', sid)
                    player.set('gid', gid)
                    players[pid] = {'pid': pid, 'username': player['username']}
                for agent in filter(lambda pid: pid.startswith('agent'), group):
                    players[agent] = {'pid': agent, 'username': 'AGENT'}
                rg = util.pool.Group(self.redis, self.expid, sid, gid)
                rg.clear()
                rg.set('players', players)

                self.publish('changeStage', data={'sid': sid, 'gid': gid})

        HostHandler.nextStage(self.redis, self.expid, self.hid)
        self.publish('switchHandler', ':'.join(('host', self.expid)), data=dict(cmd='get'))

    @onRedis
    def closePool(self, data):
        self.pool.set('closed', True)
        HostHandler.nextStage(self.redis, self.expid, self.hid)
        self.publish('switchHandler', ':'.join(('host', self.expid)), data=dict(cmd='get'))
