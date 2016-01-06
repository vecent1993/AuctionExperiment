# -*- coding: utf-8 -*-
import sys
import functools
import traceback
import datetime


class Redirection(object):
    def __init__(self):
        pass

    def write(self, msg, level):
        pass

    def close(self):
        pass


class FileRedirection(Redirection):
    def __init__(self, fname):
        self._f = open(fname, 'a+')

    def write(self, msg, level='INFO'):
        if not msg.strip():
            return
        output = (datetime.datetime.now(), level, msg.strip(), '\r\n')
        self._f.write(' '.join(map(str, output)))

    def close(self):
        self._f.close()


class Logger(object):
    def __init__(self):
        pass

    def log(self, func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                self.write(traceback.format_exc(), 'ERROR')
        return wrap

    def write(self, msg, level):
        print msg


class FileLogger(Logger):
    def __init__(self, fname):
        self._redirection = FileRedirection(fname)
        self._stdout = sys.stdout

    def log(self, func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            sys.stdout = self._redirection
            try:
                func(*args, **kwargs)
            except:
                self.write(traceback.format_exc(), 'ERROR')
            sys.stdout = self._stdout
        return wrap

    def write(self, msg, level):
        self._redirection.write(msg, level)

