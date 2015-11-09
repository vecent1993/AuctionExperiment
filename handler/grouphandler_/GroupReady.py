# -*- coding: utf-8 -*-
import json

import util.pool
from grouphandler import GroupHandler, db, redisclient, onRedis


class GroupReady(GroupHandler):
    def __init__(self, expid, sid, gid):
        super(GroupReady, self).__init__()

        self.expid, self.sid, self.gid = map(str, (expid, sid, gid))
        self.redis = redisclient
        self.value = util.pool.Group(self.redis, self.expid, self.sid, self.gid)

        self.initTasks()

        for pid in filter(lambda pid: not pid.startswith('agent'),  self.value['players'].keys()):
            player = util.pool.Player(self.redis, self.expid, pid)
            stage = player['stage'].split(':')[0]
            player.set('stage', stage+':GroupReady')
            self.publish('changeStage', ':'.join(('player', self.expid, pid)))

    @onRedis
    def ready(self, data):
        pid = data
        if 'ready' not in self.value:
            self.value.set('ready', [])
        if pid not in self.value['ready']:
            self.value['ready'].append(pid)
            self.value.save('ready')
            if len(self.value['ready']) == len(filter(lambda pid: not pid.startswith('agent'),
                                                      self.value['players'].keys())):
                self.publish('changeStage', data=dict(sid=self.sid, gid=self.gid))