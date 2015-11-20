# -*- coding: utf-8 -*-
from tornado.template import Template

from playerhandler import PlayerHandler, onWs, onRedis


class Result(PlayerHandler):
    def __init__(self, env):
        super(Result, self).__init__(env)

        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))

        self.listen(self.msgchannel, self.on_message)

    @onWs
    def ready(self, data):
        self.groupdomain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Result:Ready')
        self.writeCmd('Ready')
        self.publish('ready', self.groupdomain, self.player.pid)

    @onWs
    def get(self, data):
        stages = self.player.get('stage').split(':')
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        substage = None
        if len(stages) > 1:
            substage = stages[1]

        results = self.db.query('select * from result where exp_id=%s and user_id=%s',
                                self.exp['id'], self.current_user['user_id'])
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/result.html', exp=exp, results=results,
                                                 settings=self.settings, substage=substage))

    @onRedis('player')
    def changeStage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Result'):
            self.switchHandler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.writeCmd(stages[1])

    @staticmethod
    def renderInfo(player):
        return Template("""
            阶段：Result<br/>
        """).generate(player=player)
