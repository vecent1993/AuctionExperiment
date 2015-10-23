# -*- coding: utf-8 -*-
import traceback
import json

import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen

from session import RedisSession
from util.web import BaseHandler
from util.core import *
from util.pool import *
from handler.playerhandler import PlayerHandler
from handler.hosthandler import HostHandler


class ExpInProgressHandler(BaseHandler):
    def initialize(self, train=False):
        super(ExpInProgressHandler, self).initialize()
        self.train = train

    @tornado.web.authenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)
        settings = json.loads(exp['exp_settings'])

        if exp['host_id'] == self.current_user['user_id']:
            self.render('dashboard.html', exp=exp, settings=settings)
        else:
            self.render('expinprogress.html', exp=exp, settings=settings, train=self.train)


class BaseSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(BaseSocketHandler, self).__init__(*args, **kwargs)
        self.loader = tornado.template.Loader(self.application.settings['template_path'])

    @property
    def redis(self):
        return self.application.redis

    @property
    def db(self):
        return self.application.db

    def open(self):
        session_id = self.get_secure_cookie("_session_id")
        self.session = RedisSession(self.redis, session_id)

    def render(self, template_name, *args, **kwargs):
        return self.loader.load(template_name).generate(*args, **kwargs)

    def get_current_user(self):
        return self.session.get('user')

    def on_close(self):
        pass


class ExpSocketHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(ExpSocketHandler, self).__init__(*args, **kwargs)
        self.exp = None
        self.msghandler = None

    def open(self, expid, mode):
        super(ExpSocketHandler, self).open()

        try:
            self.exp = RedisExp(self.redis, expid)
            if self.exp['host'] == self.current_user['user_id']:
                self.host = Host(self.redis, self.exp['id'], self.current_user['user_id'])
                self.host['username'] = self.current_user['user_name']
                self.host.saveAll()
                self.msghandler = HostHandler(self)
                self.msghandler.switchHandler()
            else:
                self.player = Player(self.redis, self.exp['id'], self.current_user['user_id'])
                if not 'username' in self.player:
                    self.player['username'] = self.current_user['user_name']
                    self.player.saveAll()

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
        result = self.msghandler.handle(msg)
        if result is not None:
            self.write_message( json.dumps(result) )

    def on_close(self):
        if self.msghandler:
            self.msghandler.close()
