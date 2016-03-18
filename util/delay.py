# -*- coding: utf-8 -*-
"""This module contains delay task hub system.

Usage:

th = TaskHub()
th.start()

def print11(a):
    print time.time(), a

def print22(a):
    th.remove_task('2')

now = time.time()
print now

th.add_task('1', now + 10, print11, 1)
th.add_task('2', now + 5.1, print11, 2)
th.add_task('3', now + 5, print11, 3)
th.run_task('1')
th.add_task('4', now + 17.6, print11, 4)

th.run()

"""
import traceback
import time
import json
import heapq

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
        # self.kill(block=False)


class TaskHub(Greenlet):
    """Hub of Tasks.

    """
    def __init__(self):
        super(TaskHub, self).__init__()

        self._tasks = []
        self._task_finder = {}
        self._delay_executor = None

    def add_task(self, tid, runtime, function, context=None):
        """

        :param tid: str of task id/name.
        :param runtime: int of task run time. e.g. time.time() + 20.
        :param function: function needed ran.
        :param context: function arguments.
        :return:
        """
        if tid in self._task_finder:
            self.remove_task(tid)
        task = [runtime, tid, 0, function, context]
        self._task_finder[tid] = task
        heapq.heappush(self._tasks, task)

        self.schedule()

    def remove_task(self, tid):
        """

        :param tid: str of task id.
        :return:
        """
        if tid not in self._task_finder:
            return
        task = self._task_finder.pop(tid)
        task[-2], task[-1] = empty_func, None

    def schedule(self):
        if not self._tasks:
            return
        if self._delay_executor:
            self._delay_executor.cancel()

        delay = self._tasks[0][0] - time.time()
        self._delay_executor = DelayExecutor(delay, self.execute_task)
        self._delay_executor.start()

    def run_task(self, tid):
        if tid not in self._task_finder:
            return

        task = self._task_finder[tid]
        function, context = task[-2], task[-1]
        self.remove_task(tid)
        if task[2] == 0:
            try:
                task[2] = 1
                function(context)
                task[2] = 2
            except:
                print traceback.format_exc()

    def execute_task(self):
        if not self._tasks:
            return

        task = heapq.heappop(self._tasks)
        function, context = task[-2], task[-1]
        if task[2] == 0:
            try:
                task[2] = 1
                function(context)
                task[2] = 2
            except:
                print traceback.format_exc()
        self.schedule()

    def _run(self):
        while True:
            gevent.sleep(100000)
