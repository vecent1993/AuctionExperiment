# -*- coding: utf-8 -*-

import tornado.web

from util.web import BaseHandler
from util.baseexp import baseexp_list


class BaseExpListHandler(BaseHandler):
    def get(self):
        self.render('baseexplist.html', baseexp_list=baseexp_list)


class BaseExpHandler(BaseHandler):
    def get(self, baseexpid):
        try:
            baseexpid = int(baseexpid)
            self.render('baseexp.html', baseexp=baseexp_list[baseexpid])
        except:
            raise tornado.web.HTTPError(404)