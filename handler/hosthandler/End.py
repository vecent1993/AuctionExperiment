# -*- coding: utf-8 -*-
from . import HostHandler, on_ws


class End(HostHandler):
    def __init__(self, env):
        super(End, self).__init__(env)

    @on_ws
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/redirect.html',
                                                 redirecturl=href, redirecttitle='统计结果', delay=5))
