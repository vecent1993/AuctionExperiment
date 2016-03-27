# -*- coding: utf-8 -*-
import json

from tornado.template import Template

import components.playerhandler as playerhandler
import components.treatment


class PlayerWait(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerWait, self).__init__(env)

        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def ready(self, data):
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.RemoteGroup = playerhandler.RemoteGroup(self.msg_channel, self.group_domain,
                                                     super(PlayerWait, self).publish)
        self.player.set('stage', 'Wait:Ready')
        self.RemoteWS.Ready()
        self.RemoteGroup.ready(self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        sub_stage = None
        if len(stages) > 1:
            sub_stage = stages[1]
        self.RemoteWS.replace(self.render('Wait/wait.html', substage=sub_stage,
                                              message='主持人正在努力分组，请耐心等待。。。'))

    @playerhandler.on_redis
    def change_substage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Wait'):
            self.switch_handler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            getattr(self.RemoteWS, stages[1])()

    @staticmethod
    def render_info(player):
        return Template("""
            用户 {{ player['username'] }} 正在等待<br/>
        """).generate(player=player)