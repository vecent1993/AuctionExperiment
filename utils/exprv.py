# -*- coding: utf-8 -*-
from redisvalue import RedisValue


class RedisExp(RedisValue):
    def __init__(self, connection, exp_id):
        self.expid = str(exp_id)
        self.key = ":".join(('exp', self.expid))
        super(RedisExp, self).__init__(connection, self.key)


class Player(RedisValue):
    def __init__(self, connection, exp_id, player_id):
        self.pid = str(player_id)
        self.expid = str(exp_id)
        self.key = ":".join(('player', self.expid, self.pid))
        super(Player, self).__init__(connection, self.key)


class Host(RedisValue):
    def __init__(self, connection, expid, hid):
        self.hid = str(hid)
        self.expid = str(expid)
        self.key = ":".join(('host', self.expid, self.hid))
        super(Host, self).__init__(connection, self.key)


class Pool(RedisValue):
    def __init__(self, connection, exp_id):
        self.expid = str(exp_id)
        self.key = ":".join(('pool', self.expid))
        super(Pool, self).__init__(connection, self.key)


class Group(RedisValue):
    def __init__(self, connection, exp_id, session_id, group_id):
        self.expid = str(exp_id)
        self.sid = str(session_id)
        self.gid = str(group_id)
        self.key = ':'.join(('group', self.expid, self.sid, self.gid))
        super(Group, self).__init__(connection, self.key)