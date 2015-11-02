# -*- coding: utf-8 -*-
from tornado.template import Template

from playerhandler import PlayerHandler, onWs, onRedis


class Report(PlayerHandler):
    def __init__(self, env):
        super(Report, self).__init__(env)

        self.listen(self.msgchannel, self.on_message)

    @onWs
    def get(self, data):
        self.writeCmd('replace', self.env.render('handlers/SealedEnglish/profile.html'))

    @onWs
    def profile(self, data):
        # player = self.env.db.get('select user_id from player where exp_id=%s and user_id=%s',
        #                 self.player.expid, self.player.pid)
        # if player:
        #     self.writeCmd('deny', '您已完成实验')
        #     return
        self.player.update(data)
        self.player.saveAll()
        try:
            self.env.db.insert('insert into player(user_id,exp_id,player_no,player_isskilled) '
                               'values(%s,%s,%s,%s)', self.player.pid, self.player.expid,
                                data['studentno'], 1 if 'skilled' in data else 0)
        except:
            pass
        self.publish('addPlayer', 'pool', dict(pid=self.player.pid, username=self.player['username']))

    @onRedis('player')
    def changeStage(self, data):
        super(Report, self).changeStage({'cmd': 'get'})

    @onRedis('player')
    def deny(self, data):
        self.writeCmd('deny', '实验已开始')

    @staticmethod
    def renderInfo(player):
        return Template("""
            用户名：{{ player['username'] }}<br/>
            学号：{{ player['studentno'] }}<br/>
            之前接触到此类实验：{% if 'skilled' in player %}是{% else %}否{% end %}<br/>
        """).generate(player=player)