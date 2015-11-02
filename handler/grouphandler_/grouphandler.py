# -*- coding: utf-8 -*-
import traceback
import time
import json

import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from util.pool import Group

redisclient = redis.Redis()

db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')

def onRedis(func):
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
        self.tasks = {}
        self.value = None
        self._close = False

    def initTasks(self):
        if not self.value:
            return
        if 'tasks' not in self.value:
            return
        oldtasks = self.value.get('tasks', refresh=True)
        self.value.set('tasks', {})
        now = time.time()
        for key, value in oldtasks.items():
            if value['runtime'] >= now:
                self.addDelay(value['name'], value['runtime']-now, value['cmd'], value.get('data'))

    def addDelay(self, name, delay, cmd, data=None):
        if delay <= 0:
            return False
        if self.value and not 'tasks' in self.value:
            self.value.set('tasks', {})
        if name in self.tasks:
            self.cancelDelay(name)

        task = dict(name=name, runtime=time.time()+delay, cmd=cmd)
        if data is not None:
            task['data'] = data
        self.value['tasks'][name] = task
        self.value.save('tasks')
        self.tasks[name] = Delay(delay, self.executeTask, task)

    def executeTask(self, msg):
        self.handle(msg)
        if msg['name'] in self.tasks:
            self.tasks.pop(msg['name'])
        if self.value and msg['name'] in self.value['tasks']:
            self.value['tasks'].pop(msg['name'])
            self.value.save('tasks')

    def executeDelay(self, taskname):
        if taskname in self.tasks:
            task = self.tasks.pop(taskname)
            task.kill()
            self.executeTask(task.data)

    def cancelDelay(self, taskname):
        if taskname in self.tasks:
            task = self.tasks.pop(taskname)
            task.kill()
            if self.value and taskname in self.value['tasks']:
                self.value['tasks'].pop(taskname)
                self.value.save('tasks')

    def handle(self, msg):
        try:
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))
        except Exception, e:
            print str(traceback.format_exc())

    def close(self):
        self._close = True
        for taskname in self.tasks.keys():
            self.cancelDelay(taskname)

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        self.redis.publish('exp:'+str(self.expid), json.dumps(msg))

    @staticmethod
    def nextStage(redis, expid, sid, gid):
        group = Group(redis, expid, sid, gid)

        handlers = ['GroupReady', 'SealedEnglish', 'End']
        if not 'stage' in group:
            group.set('stage', handlers[0])
        else:
            currentstage = group.get('stage', refresh=True).split(':')[0]
            for i in range(len(handlers)):
                if handlers[i] == currentstage:
                    i += 1
                    break
            else:
                return

            if i < len(handlers):
                group.set('stage', handlers[i])

    @staticmethod
    def renderInfo(group):
        return ''