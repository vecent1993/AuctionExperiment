# -*- coding: utf-8 -*-
import functools
from urllib import urlencode
import urlparse
import json

import tornado.web
from tornado.web import HTTPError
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.gen

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
        elif status_code == 403:
            self.render('errors/403.html', kwargs=kwargs)
        elif status_code == 503:
            self.render('errors/503.html', kwargs=kwargs)
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)


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


def userAuthenticated(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise HTTPError(403)
        return func(self, *args, **kwargs)
    return wrapper


def hostAuthenticated(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.current_user and self.current_user['user_ishost'] == '1':
            return func(self, *args, **kwargs)
        raise HTTPError(403)
    return wrapper


def expHostAuthenticated(func):
    @functools.wraps(func)
    def wrapper(self, expid, *args, **kwargs):
        if self.current_user and self.current_user['user_ishost'] == '1':
            self.exp = self.db.get('select * from exp where exp_id=%s', expid)
            if not self.exp:
                raise HTTPError(404)
            if self.exp['host_id'] == self.current_user['user_id']:
                return func(self, expid, *args, **kwargs)
        raise HTTPError(403)
    return wrapper
