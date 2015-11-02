# -*- coding: utf-8 -*-
import traceback

import tornado.web

from util.web import BaseHandler
from treatments_ import getTreatment


class TreatmentListHandler(BaseHandler):
    def get(self):
        self.render('treatments/treatmentlist.html', treatments=None)


class TreatmentHandler(BaseHandler):
    def get(self, treatment):
        try:
            t = getTreatment(treatment)()
            self.render('treatments/treatment.html', treatment=t)
        except:
            raise tornado.web.HTTPError(404)