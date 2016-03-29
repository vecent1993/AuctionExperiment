# -*- coding: utf-8 -*-
import utils.exprv

import components.playerhandler as playerhandler
import components.hosthandler as hosthandler
import components.treatment


class HostEnd(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostEnd, self).__init__(env)

    @hosthandler.on_ws
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.RemoteWS.replace(self.render('End/redirect.html',
                                                 redirecturl=href, redirecttitle='统计结果', delay=5))


class PlayerEnd(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerEnd, self).__init__(env)

        if len(self.player.get('stage').split(':')) == 1:
            self.RemotePool.report_exp_end(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        self.RemoteWS.replace(self.render('End/redirect.html',
                                                 redirecturl=href, redirecttitle='收益查看', delay=5))


class End(components.treatment.PlayerOnly):
    title = '实验结束'
    description = '告知实验结束并跳转到收益（结果分析）页面'

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        return 'PlayerEnd', 'HostEnd', None, settings