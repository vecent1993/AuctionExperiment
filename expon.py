# -*- coding: utf-8 -*-
import traceback
import json

from util.web import BaseSocketHandler
from util.core import *
from util.pool import *
from handler.playerhandler_.playerhandler import PlayerHandler, getHandler
from handler.hosthandler_.hosthandler import HostHandler


class ExpSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(ExpSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.msghandler = None
        self.train = False

    def open(self, expid):
        super(ExpSocketHandler, self).open()
        if not self.get_current_user():
            self.close(403, 'Forbidden')
            return

        try:
            self.exp = RedisExp(self.redis, expid)
            if self.exp['host'] == self.current_user['user_id']:
                self.host = Host(self.redis, self.exp['id'], self.current_user['user_id'])
                if not self.host:
                    self.host.set('username', self.current_user['user_name'])

                self.msghandler = HostHandler(self)
                self.msghandler.switchHandler()
            else:
                self.player = Player(self.redis, self.exp['id'], self.current_user['user_id'])
                if not self.player:
                    self.player.set('username', self.current_user['user_name'])

                self.msghandler = PlayerHandler(self)
                self.msghandler.switchHandler()
        except Exception, e:
            self.write_message(json.dumps({'error': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msghandler.handle(msg)

    def on_close(self):
        if self.msghandler:
            self.msghandler.close()


class TrainSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(TrainSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.msghandler = None
        self.train = True

    def open(self, expid, treatment):
        super(TrainSocketHandler, self).open()
        if not self.get_current_user():
            self.close(403, 'Forbidden')
            return

        try:
            self.exp = RedisExp(self.redis, expid)
            self.player = Player(self.redis, self.exp['id'], self.current_user['user_id'])
            if not self.player:
                self.player.set('username', self.current_user['user_name'])

            self.msghandler = getHandler('train', treatment)(self)
        except Exception, e:
            self.write_message(json.dumps({'error': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msghandler.handle(msg)

    def on_close(self):
        if self.msghandler:
            self.msghandler.close()
