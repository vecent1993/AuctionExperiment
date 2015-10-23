# -*- coding: utf-8 -*-
import time
import json

from util.pool import *
from ..hosthandler import HostHandler


class Monitor(HostHandler):
    def __init__(self, env):
        super(Monitor, self).__init__(env)

        self.players = {}
        self.groups = {}

        self.msgchannel = 'exp:' + str(self.exp['id'])
        self.hostdomain = ':'.join(('host', str(self.exp['id'])))
        self.listen(self.msgchannel, self.on_message)

    def get(self, data):
        if not self.exp:
            return {'error': 'no experiment'}
        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:   self.players[pid] = player
        now = time.time()
        return {'cmd': 'replace', 'data': self.env.render('baseexp/SealedEnglish/monitor.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players)}

    def getgroupinfo(self, data):
        if not ('sid' in data and 'gid' in data):
            return {'cmd': 'error', 'data': 'error input when request group data'}
        sid, gid = data['sid'], data['gid']
        key = ':'.join(['group', str(self.exp['id']), str(sid), str(gid)])
        if key not in self.groups:
            group = Group(self.env.redis, self.exp['id'], sid, gid)
            if group:
                self.groups[group.key] = group
            else:
                return {'cmd': 'error', 'data': 'group not exists'}

        data = dict(sid=sid, gid=gid)
        data['stage'] = self.groups[key].get('stage', refresh=True)
        data['sealedbids'] = self.groups[key].get('sealedbids', {}, refresh=True).values()
        data['englishbids'] = self.groups[key].get('englishbids', {}, refresh=True)
        data['englishopenbids'] = self.groups[key].get('englishopenbids', {}, refresh=True)
        data['q'] = self.groups[key].get('q', refresh=True)
        data['players'] = self.groups[key].get('players', refresh=True)
        return {'cmd': 'showgroupinfo', 'data': data}

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'online':
                who = msg['data']
                self.write({'cmd': 'online', 'data': who})
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'offline':
                who = msg['data']
                self.write({'cmd': 'offline', 'data': who})
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'newgroup':
                data = msg.get('data', {})
                if not ('sid' in data and 'gid' in data):
                    return
                sid, gid = data['sid'], data['gid']
                key = ':'.join(['group', str(self.exp['id']), str(sid), str(gid)])
                if key in self.groups:
                    return
                group = Group(self.env.redis, self.exp['id'], sid, gid)
                self.groups[group.key] = group
                data = dict(sid=sid, gid=gid, players=[])

                for pid in self.groups[group.key].get('players', {}, True).keys():
                    player = dict(pid=pid)
                    if not pid.startswith('agent'):
                        self.players[pid] = Player(self.env.redis, self.exp['id'], pid)
                        player['username'] = self.players[pid]['username']
                    else:
                        player['username'] = 'AGENT'
                    data['players'].append(player)
                self.write({'cmd': 'addgroup', 'data': data})


class Shuffle(HostHandler):
    def __init__(self, env):
        super(Shuffle, self).__init__(env)

        self.msgchannel = 'exp:' + str(self.exp['id'])
        self.hostdomain = ':'.join(('host', str(self.exp['id'])))
        self.pooldomain = ':'.join(('pool', str(self.exp['id'])))
        self.pool = Pool(self.env.redis, self.exp['id'])
        self.players = {}

        self.listen(self.msgchannel, self.on_message)

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'newPlayer':
                if msg.get('data'):
                    self.write({'cmd': 'addplayer', 'data': msg['data']})
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'online':
                who = msg['data']
                self.write({'cmd': 'online', 'data': who})
            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'offline':
                who = msg['data']
                self.write({'cmd': 'offline', 'data': who})

            if msg.get('domain') == self.hostdomain and msg.get('cmd') == 'changeStage':
                self.nextStage({'cmd': 'get'})

    def get(self, data):
        if not self.exp:
            return {'error': 'no experiment'}
        for pid in self.pool.get('pool', [], True):
            if not pid.startswith('agent'):
                player = Player(self.env.redis, self.exp['id'], pid)
                if player:   self.players[pid] = player
        now = time.time()
        return {'cmd': 'replace', 'data': self.env.render('shuffle.html', now=now,
                                                          exp=self.exp, pool=self.pool, players=self.players)}

    def shuffle(self, data):
        self.pool.set('players', data['players'])
        self.pool.set('sessions', data['sessions'])
        self.publish(self.msgchannel, {'cmd': 'shuffle', 'domain': self.pooldomain})
        return {'cmd': 'ok'}


class End(HostHandler):
    def __init__(self, env):
        super(End, self).__init__(env)

    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        return {'cmd': 'redirect', 'data': href}
