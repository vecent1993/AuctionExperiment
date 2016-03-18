# -*- coding: utf-8 -*-
import json

from tornado.template import Template

import handler.playerhandler as playerhandler
import handler.hosthandler as hosthandler
import handler.treatment


class PlayerInit(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerInit, self).__init__(env)

        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def get(self, data):
        self.write_cmd('replace', self.render('init.html'))

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在准备实验组件<br/>
        """).generate(player=player)


class HostInit(hosthandler.HostHandler):
    def __init__(self, env):
        super(HostInit, self).__init__(env)

        self.players = {}
        self.listen(self.msg_channel, self.on_message)

    @hosthandler.on_ws
    def get(self, data):
        self.write_cmd('replace', self.render('init.html'))


class Init(handler.treatment.Treatment):
    ph = PlayerInit
    hh = HostInit

    title = '准备实验组件'
    description = '准备实验组件'