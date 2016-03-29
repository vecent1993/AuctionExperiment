# -*- coding: utf-8 -*-
"""
这个模块包含：用于参与人、主持人端的初始化处理服务。
"""

import json

from tornado.template import Template

import components.playerhandler as playerhandler
import components.hosthandler as hosthandler
import components.treatment


class PlayerInit(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerInit, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)
        self.RemotePool.next_player_stage(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        self.RemoteWS.replace(self.render('Init/init.html'))

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在准备实验组件<br/>
        """).generate(player=player)


class HostInit(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostInit, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)
        self.RemotePool.next_host_stage()

    @hosthandler.on_ws
    def get(self, data):
        self.RemoteWS.replace(self.render('Init/init.html'))