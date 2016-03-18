# -*- coding: utf-8 -*-
import random

from util.exprv import *
import handler.hosthandler as hosthandler
import handler


class AutoHostShuffle(hosthandler.HostHandler):
    def __init__(self, env):
        super(AutoHostShuffle, self).__init__(env)
        self.players = {}

        # self.listen(self.msg_channel, self.on_message)
        self.auto_shuffle()

    @hosthandler.on_ws
    def get(self, data):
        self.write_cmd('replace', self.render('autoshuffle.html'))

    def auto_shuffle(self):
        pids = filter(lambda pid: not pid.startswith('agent'), self.pool.get('pool', [], True))
        random.shuffle(pids)
        sessions = [{'players': [], 'groups':[]}, ]
        group_size = 3
        for i in range(len(pids) / group_size):
            sessions[0]['groups'].append(pids[i:i+group_size])
        players = pids[len(pids) / group_size * group_size:]

        self.pool.set('players', players)
        self.pool.set('sessions', sessions)
        self.publish('shuffle', self.pool_domain)


class AutoShuffle(object):
    hh = AutoHostShuffle