# -*- coding: utf-8 -*-
from util.web import BaseHandler


class HelpHandler(BaseHandler):
    def get(self):
        self.render('help.html')