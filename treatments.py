# -*- coding: utf-8 -*-
"""
这个模块包含：组件列表、组件展示
"""

import tornado.web

from utils.web import BaseHandler
import components


class TreatmentListHandler(BaseHandler):
    def get(self):
        self.render('treatments/treatmentlist.html', treatments=components.hub.treatments.values(),
                    PlayerOnly=components.treatment.PlayerOnly, PlayerGroup=components.treatment.PlayerGroup,
                    Container=components.treatment.Container, Train=components.treatment.Train)


class TreatmentHandler(BaseHandler):
    def get(self, treatment):
        try:
            t = components.hub.treatments[treatment]
            self.render('treatments/treatment.html', treatment=t, Train=components.treatment.Train)
        except:
            raise tornado.web.HTTPError(404)