# -*- coding: utf-8 -*-

import tornado.web

from util.web import BaseHandler


class NewExpHelpHandler(BaseHandler):
    def get(self):
        self.render('help/newexp.html')


class ExpHelpHandler(BaseHandler):
    def get(self):
        self.render('help/exp.html')