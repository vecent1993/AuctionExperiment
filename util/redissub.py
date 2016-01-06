# -*- coding : utf-8 -*-
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

pool = redis.ConnectionPool()
conn = redis.Redis(connection_pool=pool)


class RedisSub(Greenlet):
    """Asynchronous redis subscribe based on gevent Greenlet

    """
    def __init__(self, channel, callback):
        Greenlet.__init__(self)

        self._channel = channel
        self._callback = callback
        self._pub_sub = conn.pubsub()

    def _run(self):
        self._pub_sub.subscribe(self._channel)
        for msg in self._pub_sub.listen():
            self._callback(msg)

    def stop(self):
        if self._pub_sub and self._pub_sub.subscribed:
            self._pub_sub.unsubscribe()
        # self.kill()