#!usr/bin/env python
# -*- coding : utf-8 -*-

"""
Usage:

    >>>
"""

import json

# 保存全局的RedisValue
_redis_value_hub = dict()


class RedisValue(dict):
    def __new__(cls, conn, key, *args, **kwargs):
        """使得redis value全局共享，即相同key值的RedisValue都指向同一个对象

        :param cls:
        :param conn:
        :param key:
        :param args:
        :param kwargs:
        :return:
        """
        if key in _redis_value_hub:
            obj = _redis_value_hub[key]
        else:
            obj = dict.__new__(cls, *args, **kwargs)
            _redis_value_hub[key] = obj
        return obj

    def __init__(self, conn, key):
        """Value stored in redis and accessed like python dict.

        :param conn: A redis connection.
        :param key: A string, key of the value.
        """
        super(RedisValue, self).__init__()
        self.conn = conn
        self.key = key

    def _load_from_redis(self, key):
        if self.conn.hexists(self.key, key):
            data = self.conn.hget(self.key, key)
            super(RedisValue, self).__setitem__(key, json.loads(data))

    def _save_to_redis(self, key):
        if super(RedisValue, self).__contains__(key):
            data = super(RedisValue, self).__getitem__(key)
            self.conn.hset(self.key, key, json.dumps(data))

    def _del_from_redis(self, key):
        self.conn.hdel(self.key, key)

    def set(self, key, value):
        """Act like dict.set(), but will synchronize to redis.

        :param key: A string.
        :param value: An object which can be dumped by json.
        :return: None.
        """
        super(RedisValue, self).__setitem__(key, value)
        self._save_to_redis(key)

    def __getitem__(self, key):
        if not super(RedisValue, self).__contains__(key):
            self._load_from_redis(key)
        return super(RedisValue, self).__getitem__(key)

    def __contains__(self, key):
        return super(RedisValue, self).__contains__(key) or self.conn.hexists(self.key, key)

    def pop(self, key):
        if key not in self:
            self._load_from_redis(key)
        value = super(RedisValue, self).pop(key)
        self._del_from_redis(key)
        return value

    def get(self, key, default=None, refresh=False):
        """Act like dict.get(), but can synchronize from redis.

        :param key: A string.
        :param default:
        :param refresh: A bool, will synchronize from redis if True.
        :return:
        """
        if refresh or not super(RedisValue, self).__contains__(key):
            self._load_from_redis(key)
        return super(RedisValue, self).get(key, default)

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

    def clear(self):
        self.conn.delete(self.key)
        super(RedisValue, self).clear()

    def delete(self):
        self.clear()
        del self

    def __nonzero__(self):
        return len(self) > 0 or self.conn.exists(self.key)
