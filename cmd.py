# -*- coding: utf-8 -*-
from redis import client

from util.redisvalue import RedisValue, _redis_value_hub

r = client.Redis()
rv1 = RedisValue(r, 'host:1:1')
rv1.set('a', 1)
print len(_redis_value_hub)

rv2 = RedisValue(r, 'host:1:1')
print rv2 is rv1
print len(_redis_value_hub)
print rv2.get('a')
rv2.set('a', 2)

print rv1.get('a')