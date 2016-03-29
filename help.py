# -*- coding: utf-8 -*-
"""
这个模块包含：帮助页面
"""

from utils.web import BaseHandler


class HelpHandler(BaseHandler):
    def get(self):
        self.render('help.html')