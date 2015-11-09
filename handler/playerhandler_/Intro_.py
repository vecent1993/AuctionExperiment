# -*- coding: utf-8 -*-
from playerhandler import PlayerHandler, onWs, onRedis


class Intro(PlayerHandler):
    def __init__(self, env):
        super(Intro, self).__init__(env)

        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
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
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/intro.html',
                                                          exp=exp, substage=substage))

    @onRedis('player')
    def changeStage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Intro'):
            self.switchHandler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.writeCmd(stages[1])
