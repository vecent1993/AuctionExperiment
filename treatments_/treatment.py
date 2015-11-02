# -*- coding: utf-8 -*-


class Treatment(dict):
    def __init__(self, code, title, des, settings):
        super(Treatment, self).__init__()
        self['code'] = code
        self['title'] = title
        self['des'] = des
        self['settings'] = settings

    @property
    def content(self):
        return ''
