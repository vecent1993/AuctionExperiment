# -*- coding : utf-8 -*-
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

pool = redis.ConnectionPool()
conn = redis.Redis(connection_pool=pool)


class _RedisSub(Greenlet):
    def __init__(self, channel):
        """Asynchronous redis subscribe based on gevent Greenlet

        """
        Greenlet.__init__(self)

        self._channel = channel
        self._callbacks = dict()
        self._pub_sub = conn.pubsub()

    def add_callback(self, obj, callback):
        self._callbacks[hash(obj)] = callback

    def _run(self):
        self._pub_sub.subscribe(self._channel)
        for msg in self._pub_sub.listen():
            for callback in self._callbacks.values():
                callback(msg)

    def remove_callback(self, obj):
        if hash(obj) in self._callbacks:
            self._callbacks.pop(hash(obj))


_redissubs = dict()


class RedisSub(object):
    def __init__(self, channel, callback):
        """same channel will bound to same _RedisSub.

        :param channel:
        :param callback:
        :return:
        """
        if channel not in _redissubs:
            _redissubs[channel] = _RedisSub(channel)
            _redissubs[channel].start()
            print 'listening channel: %s' % channel

        self._redissub = _redissubs[channel]
        self._redissub.add_callback(self, callback)

    def start(self):
        pass
        # print self._redissub._channel, self._redissub._callbacks

    def stop(self):
        self._redissub.remove_callback(self)