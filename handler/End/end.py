# -*- coding: utf-8 -*-
import util.exprv

import handler.playerhandler as playerhandler
import handler.hosthandler as hosthandler
import handler.treatment


class HostEnd(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostEnd, self).__init__(env)

    @hosthandler.on_ws
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.write_cmd('replace', self.render('redirect.html',
                                                 redirecturl=href, redirecttitle='统计结果', delay=5))


class PlayerEnd(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerEnd, self).__init__(env)

    @playerhandler.on_ws
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.write_cmd('replace', self.render('redirect.html',
                                                 redirecturl=href, redirecttitle='收益查看', delay=5))


class End(handler.treatment.Treatment):
    ph = PlayerEnd
    hh = HostEnd

    title = '实验结束'
    description = '告知实验结束并跳转到收益（结果分析）页面'