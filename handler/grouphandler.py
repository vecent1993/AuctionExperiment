# -*- coding: utf-8 -*-
import traceback
import time
import json

import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from util.exprv import Group
from util.delay import TaskHub

rc = redis.Redis()
db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')
_task_hub = TaskHub()


def on_redis(func):
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


class GroupHandler(object):
    def __init__(self, exp):
        self.redis = rc
        self.db = db
        self.exp = exp
        self.expid = self.exp.expid

        self.value = None
        self._close = False

    def init_tasks(self):
        pass

    def wrap_func(self, tid, function):
        def _wrap(*args, **kwargs):
            function(*args, **kwargs)
            rc.hdel('tasks', tid)
        return _wrap

    def add_delay(self, task_name, delay, function, data=None):
        runtime = time.time() + delay
        tid = self.value.key + ':' + task_name if self.value else task_name
        rc.hset('tasks', tid, runtime)
        _task_hub.add_task(tid, runtime, self.wrap_func(tid, function), data)

    def cancel_delay(self, task_name):
        tid = self.value.key + ':' + task_name if self.value else task_name
        _task_hub.remove_task(tid)
        rc.hdel('tasks', tid)

    def execute_delay(self, task_name):
        tid = self.value.key + ':' + task_name if self.value else task_name
        _task_hub.run_task(tid)

    def handle(self, msg):
        try:
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))
        except:
            print str(traceback.format_exc())

    def close(self):
        self._close = True

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        self.redis.publish('exp:'+str(self.expid), json.dumps(msg))

    @staticmethod
    def next_stage(conn, expid, sid, gid):
        group = Group(conn, expid, sid, gid)

        if not group.get('handlers', []):
            group.set('stage', 'GroupEnd')
        else:
            group.set('stage', group['handlers'][0])
            group.set('handlers', group['handlers'][1:])

    @staticmethod
    def render_info(group):
        """used in host monitor

        :param group: A redis dict value, group information stored in redis.
        :return: A html string.
        """
        return ''

    @staticmethod
    def get_runtime(tid):
        try:
            return float(rc.hget('tasks', tid))
        except:
            pass


_task_hub.start()