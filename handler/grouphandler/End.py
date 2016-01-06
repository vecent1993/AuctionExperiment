# -*- coding: utf-8 -*-
from tornado.template import Template

import util.pool
from . import GroupHandler, on_redis
from ..playerhandler import PlayerHandler


class End(GroupHandler):
    def __init__(self, expid, sid, gid):
        super(End, self).__init__()

        self.expid, self.sid, self.gid = map(str, (expid, sid, gid))
        self.value = util.pool.Group(self.redis, self.expid, self.sid, self.gid)

        for pid in filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys()):
            PlayerHandler.next_stage(self.redis, self.expid, pid)
            self.publish('switch_handler', ':'.join(('player', self.expid, pid)), dict(cmd='get'))

        self.publish('close_group', data=dict(sid=self.sid, gid=self.gid))

    @staticmethod
    def render_info(group):
        return '当前阶段： End'