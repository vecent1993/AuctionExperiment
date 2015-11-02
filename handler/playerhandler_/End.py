# -*- coding: utf-8 -*-
from playerhandler import PlayerHandler, onWs


class End(PlayerHandler):
    def __init__(self, env):
        super(End, self).__init__(env)

    @onWs
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/end.html', redirecturl=href))