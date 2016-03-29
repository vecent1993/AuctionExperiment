# -*- coding: utf-8 -*-

import uuid
from utils.redisvalue import RedisValue


class RedisSession(RedisValue):
    def __init__(self, conn, sid=None):
        if not sid:
            sid = uuid.uuid4()
        self.sid = str(sid)
        self.key = 'session:%s' % self.sid
        super(RedisSession, self).__init__(conn, self.key)