# -*- coding: utf-8 -*-
"""This module contains log system.

Useage:

DEBUG = True

if not DEBUG:
    logger = FileLogger('expserver.txt')
else:
    logger = Logger()

@logger.log
def on_message1(self, msg):
    print msg

@logger.log
def on_message2(self, msg):
    raise Exception(msg)

on_message1('test1')
on_message2('test2')
"""
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
    """ Redirect output str to file.

    """
    def __init__(self, fname):
        self._f = open(fname, 'a+')

    def write(self, msg, level='INFO'):
        msg = msg.strip()
        if not msg:
            return
        output = (datetime.datetime.now(), level, msg, '\r\n')
        self._f.write(' '.join(map(str, output)))

    def close(self):
        self._f.close()


class Logger(object):
    """Logger which output msg to sys.output(screen).
    hint: when logging Exceptions will be caught.
    """
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
    """Log information redirected to file

    """
    def __init__(self, fname):
        """

        :param fname:
        :return:
        """
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

