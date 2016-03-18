# -*- coding: utf-8 -*-
import time

from util.exprv import *
import handler.hosthandler as hosthandler


class HostReport(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostReport, self).__init__(env)

        self.players = {}
        self.listen(self.msg_channel, self.on_message)

    @hosthandler.on_redis('host')
    def online(self, data):
        self.write_cmd('online', data)

    @hosthandler.on_redis('host')
    def offline(self, data):
        self.write_cmd('offline', data)

    @hosthandler.on_redis('host')
    def new_player(self, data):
        self.write_cmd('addplayer',data)

    @hosthandler.on_redis('host')
    def change_stage(self, data):
        super(HostReport, self).change_stage(dict(cmd='get'))

    @hosthandler.on_ws
    def get(self, data):
        if not self.exp:
            self.write_cmd('error', 'no experiment')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.write_cmd('replace', self.render('report.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players))

    @hosthandler.on_ws
    def start(self, data=None):
        self.publish('close_pool', self.pool_domain)


class Report(object):
    hh = HostReport