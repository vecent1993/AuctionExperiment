# -*- coding: utf-8 -*-
import json

from tornado.template import Template

import util.exprv
import playerhandler


class Intro(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(Intro, self).__init__(env)

        self.player_domain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def ready(self, data):
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Intro:Ready')
        self.write_cmd('Ready')
        self.publish('ready', self.group_domain, self.player.pid)

    @playerhandler.on_ws
    def get(self, data):
        stages = self.player.get('stage').split(':')
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        sub_stage = None
        if len(stages) > 1:
            sub_stage = stages[1]
        self.write_cmd('replace', self.env.render('handlers/SealedEnglish/intro.html', exp=exp,
                                                 settings=self.settings, substage=sub_stage))

    @playerhandler.on_ws
    def register(self, data):
        try:
            self.env.db.insert('insert into player(user_id,exp_id) '
                               'values(%s,%s)', self.player.pid, self.player.expid,
                               )
        except:
            pass
            # self.writeCmd('deny', '你已经完成实验。')
        self.publish('add_player', 'pool', dict(pid=self.player.pid, username=self.player['username']))

    @playerhandler.on_redis('player')
    def change_stage(self, data):
        stage = self.player.get('stage', refresh=True)

        if not stage.startswith('Intro'):
            self.switch_handler({'cmd': 'get'})
            return

        stages = stage.split(':')
        if len(stages) > 1:
            self.write_cmd(stages[1])

    @playerhandler.on_redis('player')
    def deny(self, data):
        self.write_cmd('deny', '实验已开始')

    @staticmethod
    def render_info(player):
        return Template("""
            用户名：{{ player['username'] }}<br/>
        """).generate(player=player)

import grouphandler


class GroupReady(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupReady, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = util.exprv.Group(self.redis, self.expid, self.sid, self.gid)

        self.init_tasks()

        for pid in filter(lambda pid: not pid.startswith('agent'),  self.value['players'].keys()):
            player = util.exprv.Player(self.redis, self.expid, pid)
            stage = player['stage'].split(':')[0]
            player.set('stage', stage+':GroupReady')
            self.publish('change_stage', ':'.join(('player', self.expid, pid)))

    @grouphandler.on_redis
    def ready(self, data):
        pid = data
        if 'ready' not in self.value:
            self.value.set('ready', [])
        if pid not in self.value['ready']:
            self.value['ready'].append(pid)
            self.value.save('ready')
            if len(self.value['ready']) == \
                    len(filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys())):
                self.exp.change_stage(dict(sid=self.sid, gid=self.gid))
