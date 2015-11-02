# -*- coding: utf-8 -*-
from ..hosthandler import HostHandler, onWs


class End(HostHandler):
    def __init__(self, env):
        super(End, self).__init__(env)

    @onWs
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['exp_id'])
        self.writeCmd('redirect', href)
