# -*- coding: utf-8 -*-

from redisvalue import RedisValue

class RedisExp(RedisValue):
    def __init__(self, connection, exp_id):
        self.expid = str(exp_id)
        self.key = ":".join(('exp', self.expid))
        super(RedisExp, self).__init__(connection, self.key)