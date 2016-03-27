# -*- coding: utf-8 -*-
import random

from utils.exprv import *
import components.hosthandler as hosthandler
import components


class AutoHostShuffle(hosthandler.HostHandler):
    def __init__(self, env):
        super(AutoHostShuffle, self).__init__(env)
        self.players = {}

        # self.listen(self.msg_channel, self.on_message)
        self.auto_shuffle()

    @hosthandler.on_ws
    def get(self, data):
        self.RemoteWS.replace(self.render('AutoShuffle/autoshuffle.html'))

    def auto_shuffle(self):
        if self.settings['code'] == 'Sessions':
            pids = filter(lambda pid: not pid.startswith('agent'), self.pool.get('pool', [], True))
            random.shuffle(pids)
            players, sessions = self.auto_session_shuffle(pids)

            self.pool.set('players', players)
            self.pool.set('sessions', sessions)

            self.RemotePool.shuffle()
        elif self.settings['code'] == 'Repeat':
            sid = 0
            pids = self.pool.get('sessions', refresh=True)[sid]['players']
            for group in self.pool.get('sessions', refresh=True)[sid]['groups']:
                pids += group
            random.shuffle(pids)
            session = self.auto_group_shuffle(pids, int(self.settings['gplayers']))
            self.pool['sessions'][sid] = session
            self.pool.save('sessions')

            self.RemotePool.shuffle()
        else:
            return

    def auto_session_shuffle(self, pids):
        ratios = map(lambda s: int(s['ratio']), self.settings['sessions'])
        gplayers = map(lambda s: int(s['gplayers']), self.settings['sessions'])
        ratios_sum = sum(ratios)
        ratios = map(lambda r: int(float(r) / ratios_sum * len(pids)), ratios)
        sessions = []
        pi = 0
        for i, r in enumerate(ratios):
            sessions.append(self.auto_group_shuffle(pids[pi:pi+r], group_size=gplayers[i]))
            pi += r
        players = pids[sum(ratios):]
        return players, sessions

    def auto_group_shuffle(self, pids, group_size):
        session = {'players': [], 'groups':[]}
        for i in range(len(pids) / group_size):
            session['groups'].append(pids[i * group_size:(i + 1) * group_size])
        session['players'] = pids[len(pids) / group_size * group_size:]
        return session