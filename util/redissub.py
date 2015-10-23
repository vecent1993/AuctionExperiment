# -*- coding : utf-8 -*-
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis
import time

pool = redis.ConnectionPool()
red = redis.Redis(connection_pool=pool)


class RedisSub(Greenlet):
    def __init__(self, channel, callback):
        Greenlet.__init__(self)

        self.channel = channel
        self.callback = callback
        self.pubsub = red.pubsub()

    def _run(self):
        self.pubsub.subscribe(self.channel)
        for msg in self.pubsub.listen():
            self.callback(msg)

    def stop(self):
        if self.pubsub and self.pubsub.subscribed:
            self.pubsub.unsubscribe()
        # self.kill()