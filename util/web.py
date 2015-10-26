# -*- coding: utf-8 -*-

import tornado.web

from util.session import RedisSession


class BaseHandler(tornado.web.RequestHandler):

    @property
    def redis(self):
        return self.application.redis

    @property
    def db(self):
        return self.application.db

    def initialize(self):
        session_id = self.get_secure_cookie("_session_id")
        self.session = RedisSession(self.redis, session_id)

    def get_current_user(self):
        return self.session.get('user')

    def on_finish(self):
        pass

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('errors/404.html', kwargs=kwargs)
        elif status_code == 503:
            self.render('errors/503.html', kwargs=kwargs)
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)