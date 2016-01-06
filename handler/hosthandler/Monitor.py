# -*- coding: utf-8 -*-
import time

from util.pool import *
from . import HostHandler, on_ws, on_redis
from .. import get_handler


class Monitor(HostHandler):
    def __init__(self, env):
        super(Monitor, self).__init__(env)

        self.players = {}
        self.groups = {}

        self.listen(self.msg_channel, self.on_message)

    @on_ws
    def get(self, data):
        if not self.exp:
            self.write_cmd('error', 'no experiment')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/monitor.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @on_ws
    def getInfo(self, data):
        if not ('sid' in data and 'gid' in data):
            self.write_cmd('error', 'error input when request group data')

        sid, gid = data['sid'], data['gid']
        key = ':'.join(['group', str(self.exp['id']), str(sid), str(gid)])
        if key not in self.groups:
            group = Group(self.env.redis, self.exp['id'], sid, gid)
            if group:
                self.groups[group.key] = group
            else:
                self.write_cmd('error', 'group not exists')
                return

        handler = self.groups[key].get('stage', refresh=True).split(':')[0]
        info = get_handler('group', handler).render_info(self.groups[key])
        self.write_cmd('showInfo', info)

    @on_redis('host')
    def online(self, data):
        self.write_cmd('online', data)

    @on_redis('host')
    def offline(self, data):
        self.write_cmd('offline', data)
