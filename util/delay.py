# -*- coding: utf-8 -*-
import traceback
import time
import json
import heapq
import datetime

import gevent
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet


def empty_func(*args, **kwargs):
    pass


class DelayExecutor(Greenlet):
    def __init__(self, delay, callback):
        super(DelayExecutor, self).__init__()

        self.delay = delay
        self.callback = callback
        self.canceled = False

    def _run(self):
        gevent.sleep(self.delay)
        if not self.canceled:
            self.callback()

    def cancel(self):
        self.canceled = True
        self.kill(block=False)


class TaskHub(Greenlet):
    def __init__(self):
        super(TaskHub, self).__init__()

        self._tasks = []
        self._task_finder = {}
        self._delay_executor = None

    def add_task(self, tid, runtime, function, context=None):
        if tid in self._task_finder:
            self.remove_task(tid)
        task = [runtime, tid, function, context]
        self._task_finder[tid] = task
        heapq.heappush(self._tasks, task)

        self.schedule()

    def remove_task(self, tid):
        if tid not in self._task_finder:
            return
        task = self._task_finder.pop(tid)
        task[-2], task[-1] = empty_func, None

    def schedule(self):
        if not self._tasks:
            return
        if self._delay_executor:
            self._delay_executor.cancel()

        delay = (self._tasks[0][0] - datetime.datetime.now()).total_seconds()
        self._delay_executor = DelayExecutor(delay, self.execute_task)
        self._delay_executor.start()

    def execute_task(self):
        if not self._tasks:
            return

        task = heapq.heappop(self._tasks)
        function, context = task[-2], task[-1]
        try:
            function(context)
        except:
            print traceback.format_exc()
        self.schedule()

    def _run(self):
        while True:
            gevent.sleep(100000)


th = TaskHub()
th.start()

def print11(a):
    print datetime.datetime.now(), a

def print22(a):
    th.remove_task('2')

now = datetime.datetime.now()
print now

th.add_task('1', now + datetime.timedelta(seconds=10), print11, 1)
th.add_task('2', now + datetime.timedelta(seconds=5.1), print11, 2)
th.add_task('3', now + datetime.timedelta(seconds=5), print22, 3)
th.add_task('1', now + datetime.timedelta(seconds=2), print11, 4)
th.add_task('4', now + datetime.timedelta(seconds=17.6), print11, 4)

time.sleep(10000)