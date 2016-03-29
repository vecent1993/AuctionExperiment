# -*- coding: utf-8 -*-
"""
这个模块包含：用于参与人、主持人端的等待处理服务。
"""

import json

from tornado.template import Template

import components.playerhandler as playerhandler
import components.treatment


class PlayerSessionWait(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerSessionWait, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)

        if len(self.player.get('stage').split(':')) == 1:
            self.RemotePool.report_wait_session(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        self.RemoteWS.replace(self.render('Wait/wait.html', substage=None,
                                              message='主持人正在努力分组，请耐心等待。'))

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在等待<br/>
        """).generate(player=player)


class PlayerShuffleWait(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerShuffleWait, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)

        if len(self.player.get('stage').split(':')) == 1:
            self.RemotePool.report_wait_shuffle(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        self.RemoteWS.replace(self.render('Wait/wait.html', substage=None,
                                              message='主持人正在努力分组，请耐心等待。'))

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在等待<br/>
        """).generate(player=player)


class PlayerGroupWait(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerGroupWait, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def ready(self, data):
        self.RemoteWS.Ready()
        self.RemotePool.report_wait_group(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        sub_stage = stages[1] if len(stages) > 1 else 'GroupReady'
        self.RemoteWS.replace(self.render('Wait/wait.html', substage=sub_stage, message='是否做好准备？'))

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在等待<br/>
        """).generate(player=player)