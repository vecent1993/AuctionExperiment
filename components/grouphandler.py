# -*- coding: utf-8 -*-
import traceback
import time
import json

import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis
import functools

from utils.exprv import Group, Player
from utils.delay import TaskHub

_task_hub = TaskHub()


def on_redis(func):
    @functools.wraps(func)
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


class RemotePlayer(object):
    def __init__(self, expid, publish):
        self.publish = publish
        self.channel = 'exp:' + str(expid)
        self.domain_prefix = 'player:' + str(expid) + ':'

    def __getattr__(self, cmd):
        def _wrap(pid, data=None, **kwargs):
            msg = dict(cmd=cmd, domain=self.domain_prefix + str(pid))
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.publish(self.channel, json.dumps(msg))
        return _wrap


class RemoteGroup(object):
    def __init__(self, expid, sid, gid, publish):
        self.publish = publish
        self.channel = 'exp:' + str(expid)
        self.group_domain = ':'.join(('group', str(sid), str(gid)))

    def __getattr__(self, cmd):
        def _wrap(data=None, **kwargs):
            msg = dict(cmd=cmd, domain=self.group_domain)
            if data is not None:
                msg['data'] = data
            msg.update(kwargs)

            self.publish(self.channel, json.dumps(msg))
        return _wrap


class GroupHandler(object):
    def __init__(self, exp):
        self.redis = exp.redis
        self.db = exp.db
        self.exp = exp
        self.expid = self.exp.expid

        self.value = None
        self.RemotePool = self.exp.host
        self.RemotePlayer = RemotePlayer(self.expid, self.redis.publish)
        self.RemoteGroup = None
        self._close = False

    def init_tasks(self):
        pass

    def start(self):
        pass

    def end(self):
        for pid in self.value.get('ready', []):
            self.RemotePool.next_player_stage(pid)

        settings = self.value.get('settings', {})
        stage_code = self.value['stagecode']
        stage = self.value['stage']
        players = self.value['players']
        self.value.clear(True)
        self.value.set('settings', settings)
        self.value.set('stagecode', stage_code)
        self.value.set('stage', stage)
        self.value.set('players', players)
        self.exp.close_group(dict(sid=self.sid, gid=self.gid))

    def close(self):
        self._close = True

    def wrap_func(self, tid, function):
        def _wrap(*args, **kwargs):
            function(*args, **kwargs)
            self.redis.hdel('tasks', tid)
        return _wrap

    def add_delay(self, task_name, delay, function, data=None):
        runtime = time.time() + delay
        tid = self.value.key + ':' + task_name if self.value else task_name
        self.redis.hset('tasks', tid, runtime)
        _task_hub.add_task(tid, runtime, self.wrap_func(tid, function), data)

    def cancel_delay(self, task_name):
        tid = self.value.key + ':' + task_name if self.value else task_name
        _task_hub.remove_task(tid)
        self.redis.hdel('tasks', tid)

    def execute_delay(self, task_name):
        tid = self.value.key + ':' + task_name if self.value else task_name
        _task_hub.run_task(tid)

    def handle(self, msg):
        try:
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))
        except:
            print str(traceback.format_exc())

    @staticmethod
    def render_info(group):
        """used in host monitor

        :param group: A redis dict value, group information stored in redis.
        :return: A html string.
        """
        return ''

    @staticmethod
    def get_runtime(conn, tid):
        try:
            return float(conn.hget('tasks', tid))
        except:
            pass


_task_hub.start()