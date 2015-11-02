# -*- coding: utf-8 -*-
from treatment import Treatment


class Report(Treatment):
    def __init__(self, settings=None):
        super(Report, self).__init__(Report.__name__, '注册报到', '填写报到信息并确认加入实验', settings)