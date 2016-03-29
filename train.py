# -*- coding: utf-8 -*-

"""
这个模块包含：测试组件列表、测试入口
"""

import traceback
import json
import datetime

import tornado.web

from utils.web import BaseHandler, hostAuthenticated, userAuthenticated, expHostAuthenticated
import components


class TrainHandler(BaseHandler):
    @userAuthenticated
    def get(self, treatment_code=None):
        try:
            treatment = components.hub.treatments[treatment_code]
        except:
            raise tornado.web.HTTPError(404)

        self.render('train/train.html', treatment=treatment)


class TrainListHandler(BaseHandler):
    @userAuthenticated
    def get(self, treatment=None):
        trains = filter(lambda t: issubclass(t, components.treatment.Train), components.hub.treatments.values())
        self.render('train/trainlist.html', trains=trains)