# -*- coding: utf-8 -*-
import traceback

import tornado.web

from util.web import BaseHandler
import handler


class TreatmentListHandler(BaseHandler):
    def get(self):
        self.render('treatments/treatmentlist.html', treatments=handler.hs.treatments)


class TreatmentHandler(BaseHandler):
    def get(self, treatment):
        try:
            t = handler.hs.handlers[treatment]
            self.render('treatments/treatment.html', treatment=t)
        except:
            raise tornado.web.HTTPError(404)