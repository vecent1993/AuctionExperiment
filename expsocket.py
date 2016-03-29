# -*- coding: utf-8 -*-
"""
这个模块包含：正式试验和测试的websocket处理对象。
"""

import traceback
import json

from utils.web import BaseSocketHandler
from utils.exprv import *
from components.playerhandler import PlayerHandler
from components.hosthandler import HostHandler
import components.hub


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

                self.msg_handler = HostHandler(self)
                self.msg_handler.switch_handler()
            else:
                self.player = Player(self.redis, self.exp['id'], self.current_user['user_id'])
                if 'username' not in self.player:
                    self.player.set('username', self.current_user['user_name'])

                self.msg_handler = PlayerHandler(self)
                self.msg_handler.switch_handler()
        except:
            self.write_message(json.dumps({'cmd': 'error', 'data': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msg_handler.handle(msg)

    def on_close(self):
        if self.msg_handler:
            self.msg_handler.close()


class TrainSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(TrainSocketHandler, self).__init__(*args, **kwargs)
        self.player = None
        self.msg_handler = None

    def open(self, treatment_code):
        super(TrainSocketHandler, self).open()
        if not self.get_current_user():
            self.close(403, 'Forbidden')
            return

        try:
            self.player = dict(username=self.current_user['user_name'])

            self.msg_handler = components.hub.handlers[treatment_code](self)
        except:
            self.write_message(json.dumps({'cmd': 'error', 'data': str(traceback.format_exc())}))

    def on_message(self, msg):
        msg = json.loads(msg)
        self.msg_handler.handle(msg)

    def on_close(self):
        if self.msg_handler:
            self.msg_handler.close()
