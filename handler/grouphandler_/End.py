# -*- coding: utf-8 -*-
from tornado.template import Template

import util.pool
from grouphandler import GroupHandler, db, redisclient, onRedis
from ..playerhandler_.playerhandler import PlayerHandler


class End(GroupHandler):
    def __init__(self, expid, sid, gid):
        super(End, self).__init__()

        self.expid, self.sid, self.gid = map(str, (expid, sid, gid))
        self.redis = redisclient
        self.value = util.pool.Group(self.redis, self.expid, self.sid, self.gid)

        for pid in filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys()):
            PlayerHandler.nextStage(self.redis, self.expid, pid)
            self.publish('switchHandler', ':'.join(('player', self.expid, pid)), dict(cmd='get'))

        self.publish('closeGroup', data=dict(sid=self.sid, gid=self.gid))

    @staticmethod
    def renderInfo(group):
        return '当前阶段： End'