# -*- coding: utf-8 -*-
import json

from tornado.template import Template

import util.exprv
import playerhandler
import grouphandler


class GroupReady(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupReady, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = util.exprv.Group(self.redis, self.expid, self.sid, self.gid)

        self.init_tasks()

        for pid in filter(lambda pid: not pid.startswith('agent'),  self.value['players'].keys()):
            player = util.exprv.Player(self.redis, self.expid, pid)
            stage = player['stage'].split(':')[0]
            player.set('stage', stage+':GroupReady')
            self.publish('change_stage', ':'.join(('player', self.expid, pid)))

    @grouphandler.on_redis
    def ready(self, data):
        pid = data
        if 'ready' not in self.value:
            self.value.set('ready', [])
        if pid not in self.value['ready']:
            self.value['ready'].append(pid)
            self.value.save('ready')
            if len(self.value['ready']) == \
                    len(filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys())):
                self.exp.change_stage(dict(sid=self.sid, gid=self.gid))
