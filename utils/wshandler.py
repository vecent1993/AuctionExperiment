# -*- coding: utf-8 -*-
import json
import functools
import traceback

from utils.log import FileLogger, Logger

DEBUG = True

if not DEBUG:
    logger = FileLogger('wshandler.txt')
else:
    logger = Logger()


def on_redis(func):
    @functools.wraps(func)
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


def on_ws(func):
    @functools.wraps(func)
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


class RemoteWS(object):
    def __init__(self, write):
        self.write = write

    def __getattr__(self, cmd):
        def _wrap(data=None, **kwargs):
            msg = dict(cmd=cmd)
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.write(json.dumps(msg))
        return _wrap


class WSMessageHandler(object):
    def __init__(self, env):
        self.env = env

        self.RemoteWS = RemoteWS(self.env.write_message)

    def on_message(self, msg):
        pass

    def get(self, data):
        pass

    @logger.log
    def handle(self, msg):
        if hasattr(self, msg['cmd']):
            try:
                getattr(self, msg['cmd'])(msg.get('data'))
            except:
                self.RemoteWS.error(traceback.format_exc())

    def publish(self, channel, msg):
        self.env.redis.publish(channel, msg)

    def close(self):
        pass
