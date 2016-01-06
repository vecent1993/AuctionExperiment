# -*- coding: utf-8 -*-
from tornado.template import Template

from . import PlayerHandler, on_ws, on_redis


class Report(PlayerHandler):
    def __init__(self, env):
        super(Report, self).__init__(env)

        self.listen(self.msg_channel, self.on_message)

    @on_ws
    def get(self, data):
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/profile.html'))

    @on_ws
    def profile(self, data):
        # player = self.env.db.get('select user_id from player where exp_id=%s and user_id=%s',
        #                 self.player.expid, self.player.pid)
        # if player:
        #     self.writeCmd('deny', '您已完成实验')
        #     return
        self.player.update(data)
        self.player.save_all()
        try:
            self.env.db.insert('insert into player(user_id,exp_id,player_no,player_isskilled) '
                               'values(%s,%s,%s,%s)', self.player.pid, self.player.expid,
                                data['studentno'], 1 if 'skilled' in data else 0)
        except:
            pass
        self.publish('add_player', 'pool', dict(pid=self.player.pid, username=self.player['username']))

    @on_redis('player')
    def change_stage(self, data):
        super(Report, self).change_stage({'cmd': 'get'})

    @on_redis('player')
    def deny(self, data):
        self.write_cmd('deny', '实验已开始')

    @staticmethod
    def render_info(player):
        return Template("""
            用户名：{{ player['username'] }}<br/>
        """).generate(player=player)