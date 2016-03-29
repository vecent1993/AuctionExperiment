# -*- coding: utf-8 -*-
"""
这个模块包含：实验介绍组件和相应用于参与人端的处理服务。
"""

import json

from tornado.template import Template

import utils.exprv
import components.playerhandler as playerhandler
import components.treatment


class PlayerIntro(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerIntro, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        sub_stage = None
        if len(stages) > 1:
            sub_stage = stages[1]
        self.RemoteWS.replace(self.render('Intro/intro.html', exp=exp, substage=sub_stage))

    @playerhandler.on_ws
    def register(self, data):
        try:
            self.env.db.insert('insert into player(user_id,exp_id) '
                               'values(%s,%s)', self.player.pid, self.player.expid,
                               )
        except:
            pass
            # self.writeCmd('deny', '你已经完成实验。')
        self.RemotePool.add_player(dict(pid=self.player.pid, username=self.player['username']))

    @playerhandler.on_redis
    def change_substage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Intro'):
            self.switch_handler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            getattr(self.RemoteWS, stages[1])()

    @playerhandler.on_redis
    def deny(self, data):
        self.RemoteWS.deny('', '实验已开始')

    @staticmethod
    def render_info(player):
        return Template("""
            用户名：{{ player['username'] }}<br/>
        """).generate(player=player)


class Intro(components.treatment.PlayerOnly):
    title = '实验说明'
    description = '详细地告知被试实验流程'

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        return 'PlayerIntro', 'HostReport', None, settings