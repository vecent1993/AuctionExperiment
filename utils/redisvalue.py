# -*- coding: utf-8 -*-
"""This module contains dict-like Redis Value.

Usage:

import redis

rc = redis.Redis()

rv = RedisValue(rc, 'group:3:3')
rv.set('name', 'JKiriS')
print rv.get('name')

rv.sandbox = True
"""

import json
import functools

from gevent import Greenlet

import redissub


def on_redis(func):
    @functools.wraps(func)
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


class RemoteRedis(object):
    def __init__(self, publish):
        self.publish = publish
        self.channel = 'redisvalue'

    def __getattr__(self, cmd):
        def _wrap(data=None, **kwargs):
            msg = dict(cmd=cmd)
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.publish(self.channel, json.dumps(msg))
        return _wrap


class RedisValueHub(Greenlet):
    def __init__(self):
        super(RedisValueHub, self).__init__()

        self._hub = dict()

    @on_redis
    def refresh(self, key):
        if key in self._hub:
            self._hub[key].clear()

    def handler(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))

    def _run(self):
        rs = redissub.RedisSub('redisvalue', self.handler)
        rs.start()


class _RedisValue(dict):
    def __init__(self, conn, key):
        """Value stored in redis and accessed like python dict.

        :param conn: A redis connection.
        :param key: A string, key of the value.
        """
        super(_RedisValue, self).__init__()
        self.conn = conn
        self.key = key

    def _load_from_redis(self, key):
        if self.conn.hexists(self.key, key):
            data = self.conn.hget(self.key, key)
            super(_RedisValue, self).__setitem__(key, json.loads(data))

    def _save_to_redis(self, key):
        if super(_RedisValue, self).__contains__(key):
            data = super(_RedisValue, self).__getitem__(key)
            self.conn.hset(self.key, key, json.dumps(data))

    def _del_from_redis(self, key):
        self.conn.hdel(self.key, key)

    def set(self, key, value):
        """Act like dict.set(), but will synchronize to redis.

        :param key: A string.
        :param value: An object which can be dumped by json.
        :return: None.
        """
        super(_RedisValue, self).__setitem__(key, value)
        self._save_to_redis(key)

    def __getitem__(self, key):
        if not super(_RedisValue, self).__contains__(key):
            self._load_from_redis(key)
        return super(_RedisValue, self).__getitem__(key)

    def __contains__(self, key):
        return super(_RedisValue, self).__contains__(key) or self.conn.hexists(self.key, key)

    def pop(self, key):
        if key not in self:
            self._load_from_redis(key)
        value = super(_RedisValue, self).pop(key)
        self._del_from_redis(key)
        return value

    def get(self, key, default=None, refresh=False):
        """Act like dict.get(), but can synchronize from redis.

        :param key: A string.
        :param default:
        :param refresh: A bool, will synchronize from redis if True.
        :return:
        """
        if refresh or not super(_RedisValue, self).__contains__(key):
            self._load_from_redis(key)
        return super(_RedisValue, self).get(key, default)

    def expire(self, expires=24*60*60):
        self.conn.expire(self.key, expires)

    def save_all(self):
        for key in self:
            self._save_to_redis(key)

    def save(self, key):
        """Save item to redis

        :param key:
        :return:
        """
        self._save_to_redis(key)

    def clear(self, remote=False):
        if remote:
            self.conn.delete(self.key)
        super(_RedisValue, self).clear()

    def delete(self):
        self.clear()
        del self

    def __nonzero__(self):
        return len(self) > 0 or self.conn.exists(self.key)


_redis_value_hub = RedisValueHub()


class RedisValue(dict):
    def __init__(self, conn, key, sandbox=False):
        """Value stored in redis and accessed like python dict.

        :param conn: A redis connection.
        :param key: A string, key of the value.
        """
        super(RedisValue, self).__init__()

        if key in _redis_value_hub._hub:
            self.obj = _redis_value_hub._hub[key]
        else:
            self.obj = _RedisValue(conn, key)
            _redis_value_hub._hub[key] = self.obj
        self.conn = conn
        self.key = key
        self.sandbox = sandbox

    def __setitem__(self, key, value):
        if self.sandbox:
            return super(RedisValue, self).__setitem__(key, value)
        return self.obj.__setitem__(key, value)

    def set(self, key, value):
        """Act like dict.set(), but will synchronize to redis.

        :param key: A string.
        :param value: An object which can be dumped by json.
        :return: None.
        """
        if self.sandbox:
            return super(RedisValue, self).__setitem__(key, value)
        return self.obj.set(key, value)

    def __getitem__(self, key):
        if self.sandbox and super(RedisValue, self).__contains__(key):
            return super(RedisValue, self).__getitem__(key)
        return self.obj.__getitem__(key)

    def get(self, key, default=None, refresh=False):
        """Act like dict.get(), but can synchronize from redis.

        :param key: A string.
        :param default:
        :param refresh: A bool, will synchronize from redis if True.
        :return:
        """
        if self.sandbox and super(RedisValue, self).__contains__(key):
            return super(RedisValue, self).__getitem__(key)
        return self.obj.get(key, default, refresh)

    def __contains__(self, key):
        if self.sandbox:
            return super(RedisValue, self).__contains__(key)
        return self.obj.__contains__(key)

    def pop(self, key):
        if self.sandbox:
            return super(RedisValue, self).pop(key)
        return self.obj.pop(key)

    def expire(self, expires=24*60*60):
        return self.obj.expire(expires)

    def save_all(self):
        return self.obj.save_all()

    def save(self, key):
        """Save item to redis

        :param key:
        :return:
        """
        return self.obj.save(key)

    def clear(self, remote=False):
        return self.obj.clear(remote)

    def delete(self):
        return self.obj.delete()

    def __nonzero__(self):
        return self.obj.__nonzero__()

_redis_value_hub.start()