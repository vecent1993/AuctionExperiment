# -*- coding: utf-8 -*-
import json

from tornado.template import Template

import handler.playerhandler as playerhandler
import handler.treatment


class PlayerWait(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerWait, self).__init__(env)

        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def ready(self, data):
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Wait:Ready')
        self.write_cmd('Ready')
        self.publish('ready', self.group_domain, self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        sub_stage = None
        if len(stages) > 1:
            sub_stage = stages[1]
        self.write_cmd('replace', self.render('wait.html', substage=sub_stage))

    @playerhandler.on_redis('player')
    def change_substage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Wait'):
            self.switch_handler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.write_cmd(stages[1])

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在等待<br/>
        """).generate(player=player)


class Wait(handler.treatment.Treatment):
    ph = PlayerWait
    GROUPREADY = True

    title = '等待'
    description = '等待主持人分组或其他参与者做好准备'