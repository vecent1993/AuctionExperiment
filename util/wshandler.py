# -*- coding: utf-8 -*-
import json
from util.log import FileLogger, Logger

DEBUG = True

if not DEBUG:
    logger = FileLogger('wshandler.txt')
else:
    logger = Logger()


def on_ws(func):
    # @functools.wraps(func)
    def _wrap1(*args, **kwargs):
        return func(*args, **kwargs)
    _wrap1.__name__ = '_'.join(('@', 'ws', func.__name__))
    return _wrap1


def on_redis(*domains):
    def _wrap(func):
        # @functools.wraps(func)
        def _wrap1(*args, **kwargs):
            func(*args, **kwargs)
        names = map(lambda domain: '_'.join(('@', 'redis', domain, func.__name__)), domains)
        _wrap1.__name__ = ':'.join(names)
        return _wrap1
    return _wrap


class WSMessageHandler(object):
    def __new__(cls, *args, **kwargs):
        for key in filter(lambda a: not a.startswith('__'), dir(cls)):
            attr = getattr(cls, key)
            if hasattr(attr, '__call__') and attr.__name__.startswith('@'):
                for name in attr.__name__.split(':'):
                    setattr(cls, name, attr)
        return object.__new__(cls, *args, **kwargs)

    def __init__(self, env):
        self.env = env

    def on_message(self, msg):
        pass

    def get(self, data):
        pass

    @logger.log
    def handle(self, msg):
        name = '_'.join(('@', 'ws', msg['cmd']))
        if hasattr(self, name):
            getattr(self, name)(msg.get('data'))

    def publish(self, channel, msg):
        self.env.redis.publish(str(channel), json.dumps(msg))

    def write(self, msg):
        self.env.write_message(json.dumps(msg))

    def write_cmd(self, cmd, data=None, **kwargs):
        msg = dict(cmd=cmd)
        if data is not None:
            msg['data'] = data
        msg.update(kwargs)

        self.write(msg)

    def close(self):
        pass
