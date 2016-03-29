# -*- coding: utf-8 -*-
import time

from utils.exprv import *
import components.hosthandler as hosthandler


class HostReport(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostReport, self).__init__(env)

        self.players = {}
        self.listen(self.msg_channel, self.on_message)

    @hosthandler.on_redis
    def online(self, data):
        self.RemoteWS.online(data)

    @hosthandler.on_redis
    def offline(self, data):
        self.RemoteWS.offline(data)

    @hosthandler.on_redis
    def new_player(self, data):
        self.RemoteWS.addplayer(data)

    @hosthandler.on_ws
    def get(self, data):
        if not self.exp:
            self.RemoteWS.error('no experiment')

        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:
                    self.players[pid] = player
        now = time.time()
        self.RemoteWS.replace(self.render('Report/report.html', now=now, exp=self.exp,
                                          pool=self.pool, players=self.players))

    @hosthandler.on_ws
    def start(self, data=None):
        self.RemotePool.close_pool()