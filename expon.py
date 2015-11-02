# -*- coding: utf-8 -*-
import traceback
import json

import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen

from util.web import BaseHandler, userAuthenticated, BaseSocketHandler
from util.core import *
from util.pool import *
from handler.playerhandler_.playerhandler import PlayerHandler
from handler.hosthandler_.hosthandler import HostHandler


class ExpInProgressHandler(BaseHandler):
    def initialize(self, train=False):
        super(ExpInProgressHandler, self).initialize()
        self.train = train

    @userAuthenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)
        settings = json.loads(exp['exp_settings'])

        if exp['host_id'] == self.current_user['user_id']:
            self.render('expon/dashboard.html', exp=exp, settings=settings)
        else:
            self.render('expon/expinprogress.html', exp=exp, settings=settings, train=self.train)


class ExpSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(ExpSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.msghandler = None

    def open(self, expid, mode):
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

                if mode == 'train':
                    self.train = True
                elif mode == 'official':
                    self.train = False
                else:
                    self.write_message(json.dumps({'error': 'mode error'}))

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
