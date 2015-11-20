# -*- coding: utf-8 -*-
from tornado.template import Template

from playerhandler import PlayerHandler, onWs, onRedis


class Intro(PlayerHandler):
    def __init__(self, env):
        super(Intro, self).__init__(env)

        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )

        self.listen(self.msgchannel, self.on_message)

    @onWs
    def ready(self, data):
        self.groupdomain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Intro:Ready')
        self.writeCmd('Ready')
        self.publish('ready', self.groupdomain, self.player.pid)

    @onWs
    def get(self, data):
        stages = self.player.get('stage').split(':')
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        substage = None
        if len(stages) > 1:
            substage = stages[1]
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/intro.html', exp=exp,
                                                 settings=self.settings, substage=substage))

    @onWs
    def register(self, data):
        try:
            self.env.db.insert('insert into player(user_id,exp_id) '
                               'values(%s,%s)', self.player.pid, self.player.expid,
                               )
        except:
            self.writeCmd('deny', '你已经完成实验。')
        self.publish('addPlayer', 'pool', dict(pid=self.player.pid, username=self.player['username']))

    @onRedis('player')
    def changeStage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Intro'):
            self.switchHandler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.writeCmd(stages[1])

    @onRedis('player')
    def deny(self, data):
        self.writeCmd('deny', '实验已开始')

    @staticmethod
    def renderInfo(player):
        return Template("""
            用户名：{{ player['username'] }}<br/>
        """).generate(player=player)
