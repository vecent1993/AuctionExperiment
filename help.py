# -*- coding: utf-8 -*-
from utils.web import BaseHandler


class HelpHandler(BaseHandler):
    def get(self):
        self.render('help.html')