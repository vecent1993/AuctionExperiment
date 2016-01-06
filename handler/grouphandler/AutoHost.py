# -*- coding: utf-8 -*-
import json
import time
import random
import datetime

import util.pool
from . import GroupHandler, Delay, on_redis
from ..hosthandler import HostHandler
from ..playerhandler import PlayerHandler


class AutoHost(GroupHandler):
    def __init__(self, expid, hostid):
        super(AutoHost, self).__init__()
        self.expid = str(expid)
        self.hid = str(hostid)

        self.value = util.pool.Host(self.redis, self.expid, self.hid)
        self.pool = util.pool.Pool(self.redis, self.expid)
        self.host_domain = ':'.join(('host', self.expid))

        if 'pool' not in self.pool:
            self.pool.set('pool', [])
        if 'players' not in self.pool:
            self.pool.set('players', [])

        self.init_tasks()
        self.check_player()

    @on_redis
    def init_pool(self):
        if not self.value.get('sessions', refresh=True):
            self.pool.set('sessions', [{}])

    @on_redis
    def add_player(self, data):
        pid, username = data['pid'], data['username']
        if self.pool.get('closed', False):
            self.publish('deny', ':'.join(('player', self.expid, pid)))
            return

        if pid not in self.pool['pool']:
            self.pool['pool'].append(pid)
            self.pool['players'].append(pid)
            self.pool.save('pool')
            self.pool.save('players')

        self.publish('new_player', self.host_domain, data)
        player = util.pool.Player(self.redis, self.expid, pid)
        player.set('stage', 'Intro:Inpool')
        self.publish('change_stage', ':'.join(('player', self.expid, pid)), dict(cmd='get'))

    def check_player(self, data=None):
        now = time.time()
        for pid in self.pool['pool']:
            player = util.pool.Player(self.redis, self.expid, pid)
            if now - player.get('heartbeat', 0) > 50 and player.get('online'):
                player.set('online', False)
                self.publish('offline', self.host_domain, pid)
            elif now - player.get('heartbeat', 0) <= 50 and not player.get('online', True):
                player.set('online', True)
                self.publish('online', self.host_domain, pid)
        if not self._close:
            Delay(45, self.check_player, None).start()

    @on_redis
    def shuffle(self, data=None):
        if 'round' not in self.value:
            self.value.set('round', 1)
        else:
            self.value.set('round', self.value.get('round', 1, True)+1)

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
                rg.set('handlers', ['GroupReady', 'SealedEnglish', 'End'])
                rg.set('round', self.value.get('round'))

                self.publish('change_stage', data={'sid': sid, 'gid': gid})

        HostHandler.next_stage(self.redis, self.expid, self.hid)
        self.publish('switch_handler', self.host_domain, data=dict(cmd='get'))

    @on_redis
    def close_pool(self, data):
        self.pool.set('closed', True)
        HostHandler.next_stage(self.redis, self.expid, self.hid)
        self.publish('switch_handler', self.host_domain, data=dict(cmd='get'))
