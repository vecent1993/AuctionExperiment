# -*- coding: utf-8 -*-
from tornado.template import Template

from . import PlayerHandler, on_ws, on_redis


class Result(PlayerHandler):
    def __init__(self, env):
        super(Result, self).__init__(env)

        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))

        self.listen(self.msg_channel, self.on_message)

    @on_ws
    def ready(self, data):
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Result:Ready')
        self.write_cmd('Ready')
        self.publish('ready', self.group_domain, self.player.pid)

    @on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        sub_stage = None
        if len(stages) > 1:
            sub_stage = stages[1]

        results = self.env.db.query('select * from result where exp_id=%s and user_id=%s and round=1',
                                self.exp['id'], self.player.pid)
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/result.html', exp=exp, results=results,
                                                 substage=sub_stage))

    @on_redis('player')
    def change_stage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Result'):
            self.switch_handler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.write_cmd(stages[1])

    @staticmethod
    def render_info(player):
        return '当前阶段：Result<br/>'
