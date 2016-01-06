# -*- coding: utf-8 -*-
import traceback
import time
import json

import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from util.pool import Group

rc = redis.Redis()

db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')


def on_redis(func):
    def _wrap(*args, **kwargs):
        func(*args, **kwargs)
    return _wrap


class Delay(Greenlet):
    def __init__(self, timeout, callback, data):
        super(Delay, self).__init__()

        self.timeout = timeout
        self.callback = callback
        self.data = data
        self.start_later(self.timeout)

    def _run(self):
        self.callback(self.data)


class GroupHandler(object):
    def __init__(self):
        self.redis = rc
        self.db = db
        self.tasks = {}
        self.value = None
        self._close = False

    def init_tasks(self):
        if not self.value:
            return
        if 'tasks' not in self.value:
            return
        tasks_old = self.value.get('tasks', refresh=True)
        self.value.set('tasks', {})
        now = time.time()
        for key, value in tasks_old.items():
            if value['runtime'] >= now:
                self.add_delay(value['name'], value['runtime'] - now, value['cmd'], value.get('data'))

    def add_delay(self, name, delay, cmd, data=None):
        if delay <= 0:
            return False
        if self.value and not 'tasks' in self.value:
            self.value.set('tasks', {})
        if name in self.tasks:
            self.cancel_delay(name)

        task = dict(name=name, runtime=time.time()+delay, cmd=cmd)
        if data is not None:
            task['data'] = data
        self.value['tasks'][name] = task
        self.value.save('tasks')
        self.tasks[name] = Delay(delay, self.execute_task, task)

    def execute_task(self, msg):
        self.handle(msg)
        if msg['name'] in self.tasks:
            self.tasks.pop(msg['name'])
        if self.value and msg['name'] in self.value['tasks']:
            self.value['tasks'].pop(msg['name'])
            self.value.save('tasks')

    def execute_delay(self, task_name):
        if task_name in self.tasks:
            task = self.tasks.pop(task_name)
            task.kill()
            self.execute_task(task.data)

    def cancel_delay(self, task_name):
        if task_name in self.tasks:
            task = self.tasks.pop(task_name)
            task.kill()
            if self.value and task_name in self.value['tasks']:
                self.value['tasks'].pop(task_name)
                self.value.save('tasks')

    def handle(self, msg):
        try:
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))
        except:
            print str(traceback.format_exc())

    def close(self):
        self._close = True
        for task_name in self.tasks.keys():
            self.cancel_delay(task_name)

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
            group.set('stage', 'End')
        else:
            group.set('stage', group['handlers'][0])
            group.set('handlers', group['handlers'][1:])

    @staticmethod
    def render_info(group):
        return ''