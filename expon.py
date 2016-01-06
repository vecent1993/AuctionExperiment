# -*- coding: utf-8 -*-
import traceback
import json

from util.web import BaseSocketHandler
from util.pool import *
from handler import get_handler
from handler.playerhandler import PlayerHandler
from handler.hosthandler import HostHandler


class ExpSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(ExpSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.player = None
        self.host = None
        self.msg_handler = None
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
                if 'username' not in self.host:
                    self.host.set('username', self.current_user['user_name'])
                if 'handlers' not in self.host:
                    self.host.set('handlers', ['Report', 'Shuffle', 'Monitor', 'Shuffle', 'Monitor', 'End'])
                    # self.host.set('handlers', ['Report', 'Shuffle', 'Monitor', 'End'])

                self.msg_handler = HostHandler(self)
                self.msg_handler.switch_handler()
            else:
                self.player = Player(self.redis, self.exp['id'], self.current_user['user_id'])
                if 'username' not in self.player:
                    self.player.set('username', self.current_user['user_name'])
                if 'handlers' not in self.player:
                    self.player.set('handlers', ['Intro', 'Result', 'End'])
                    # self.player.set('handlers', ['Intro', 'End'])

                self.msg_handler = PlayerHandler(self)
                self.msg_handler.switch_handler()
        except:
            self.write_message(json.dumps({'error': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msg_handler.handle(msg)

    def on_close(self):
        if self.msg_handler:
            self.msg_handler.close()


class TrainSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(TrainSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.player = None
        self.msg_handler = None
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

            self.msg_handler = get_handler('train', treatment)(self)
        except:
            self.write_message(json.dumps({'error': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msg_handler.handle(msg)

    def on_close(self):
        if self.msg_handler:
            self.msg_handler.close()
