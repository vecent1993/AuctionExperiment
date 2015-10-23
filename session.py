# -*- coding: utf-8 -*-

import uuid
from util.redisvalue import RedisValue


class RedisSession(RedisValue):

    def __init__(self, connection, sid=None):
        if not sid:
            sid = uuid.uuid4()
        self.sid = str(sid)
        self.key = ':'.join(('session', self.sid))
        super(RedisSession, self).__init__(connection, self.key)