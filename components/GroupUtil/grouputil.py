# -*- coding: utf-8 -*-
import utils.exprv

import components.grouphandler as grouphandler
import components.playerhandler as playerhandler


class GroupEnd(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupEnd, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = utils.exprv.Group(self.redis, self.expid, self.sid, self.gid)

        for pid in filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys()):
            playerhandler.PlayerHandler.next_stage(self.redis, self.redis, self.expid, pid)
            self.publish('switch_handler', ':'.join(('player', self.expid, pid)), dict(cmd='get'))

        self.exp.close_group(dict(sid=self.sid, gid=self.gid))

    @staticmethod
    def render_info(group):
        return '当前阶段： End'


class GroupReady(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupReady, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = utils.exprv.Group(self.redis, self.expid, self.sid, self.gid)

        self.init_tasks()

        for pid in filter(lambda pid: not pid.startswith('agent'),  self.value['players'].keys()):
            player = utils.exprv.Player(self.redis, self.expid, pid)
            stage = player['stage'].split(':')[0]
            player.set('stage', stage+':GroupReady')
            self.publish('change_substage', ':'.join(('player', self.expid, pid)))

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
                grouphandler.GroupHandler.next_stage(self.redis, self.expid, self.sid, self.gid)
                self.exp.switch_handler(dict(sid=self.sid, gid=self.gid))
