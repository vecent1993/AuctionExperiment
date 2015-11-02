# -*- coding : utf-8 -*-

import json


class RedisValue(dict):
    def __init__(self, conn, key):
        super(RedisValue, self).__init__()
        self.conn = conn
        self.key = key

    def _loadFromRedis(self, key):
        if self.conn.hexists(self.key, key):
            data = self.conn.hget(self.key, key)
            super(RedisValue, self).__setitem__(key, json.loads(data))

    def _saveToRedis(self, key):
        if super(RedisValue, self).__contains__(key):
            data = super(RedisValue, self).__getitem__(key)
            self.conn.hset(self.key, key, json.dumps(data))

    def _delFromRedis(self, key):
        self.conn.hdel(self.key, key)

    def update(self, d):
        if isinstance(d, dict):
            for key, value in d.items():
                self[key] = value

    def set(self, key, value):
        super(RedisValue, self).__setitem__(key, value)
        self._saveToRedis(key)

    def __getitem__(self, key):
        if not super(RedisValue, self).__contains__(key):
            self._loadFromRedis(key)
        return super(RedisValue, self).__getitem__(key)

    def __contains__(self, key):
        return super(RedisValue, self).__contains__(key) or self.conn.hexists(self.key, key)

    def pop(self, key):
        if key not in self:
            self._loadFromRedis(key)
        value = super(RedisValue, self).pop(key)
        self._delFromRedis(key)
        return value

    def get(self, key, default=None, refresh=False):
        if refresh or not super(RedisValue, self).__contains__(key):
            self._loadFromRedis(key)
        return super(RedisValue, self).get(key, default)

    def expire(self, expires=24*60*60):
        self.conn.expire(self.key, expires)

    def saveAll(self):
        for key in self:
            self._saveToRedis(key)

    def save(self, key):
        self._saveToRedis(key)

    def clear(self):
        self.conn.delete(self.key)
        super(RedisValue, self).clear()

    def delete(self):
        self.clear()
        del self

    def __nonzero__(self):
        return len(self) > 0 or self.conn.exists(self.key)
