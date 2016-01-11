# -*- coding: utf-8 -*-
import time

from util.pool import *
from . import PlayerHandler, on_ws, on_redis
from ..grouphandler import GroupHandler


class SealedEnglish(PlayerHandler):
    def __init__(self, env):
        super(SealedEnglish, self).__init__(env)

        if not ('sid' in self.player and 'gid' in self.player):
            self.write({'error': 'not ready'})
            return

        self.settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )

        self.group = Group(self.env.redis, self.env.exp['id'], self.player['sid'], self.player['gid'])
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))

        self.listen(self.msg_channel, self.on_message)

    @on_ws
    def get(self, data):
        if not self.exp:
            self.write_cmd('error', 'experiment not exists')

        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) < 4:
            self.write_cmd('error', 'not ready')

        self.player.get('cost', refresh=True)
        round, mainstage, substage = stages[1:4]
        if mainstage == 'sealed':
            self.write_cmd('replace', self.env.render('handlers/SealedEnglish/sealed.html', train=False, round=round,
                settings=self.settings, player=self.player, bids=self.group.get('sealedbids', [], True), substage=substage))
        elif mainstage == 'english':
            bids = map(self._anonymous, self.group.get('englishbids', [], True))
            q = None
            self.write_cmd('replace', self.env.render('handlers/SealedEnglish/english.html', train=False, round=round,
                settings=self.settings, q=q, player=self.player, bids=bids, substage=substage))
        elif mainstage == 'englishopen':
            bids = map(self._anonymous, self.group.get('englishopenbids', [], True))
            q = self.group.get('q', refresh=True)
            self.write_cmd('replace', self.env.render('handlers/SealedEnglish/english.html', train=False, round=round,
                settings=self.settings, q=q, player=self.player, bids=bids, substage=substage))

    @on_ws
    def sealed_bid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('sealed_bid', self.group_domain,
                     dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @on_ws
    def english_bid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('english_bid', self.group_domain,
                    dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @on_ws
    def get_timeout(self, name=None):
        tid = self.group.key + ':' + name
        runtime = GroupHandler.get_runtime(tid)
        if runtime:
            seconds = round(runtime - time.time())
            if seconds > 0:
                self.write_cmd('timeout', {'name': name, 'seconds': seconds})

    @on_ws
    def get_result(self, data):
        self.write_cmd('showresult', '马上进入下一部分，请耐心等待并做好准备')

    def _anonymous(self, data):
        if data.get('pid') == str(self.player.pid):
            data['username'] = '你'
            data['self'] = True
            data['pid'] = ''
        else:
            data['username'] = '其他竞拍者'
            data['pid'] = ''
        return data

    @on_redis('group')
    def english_bid_open(self, data):
        self.write_cmd('englishbid', self._anonymous(data))

    @on_redis('player')
    def change_stage(self, data):
        mainstage, substage = self.player.get('stage').split(':')[2:4]
        stage = self.player.get('stage', refresh=True)
        if not stage.startswith('SealedEnglish'):
            self.switch_handler({'cmd': 'get'})
            return

        newmainstage, newsubstage = stage.split(':')[2:4]
        if(mainstage == newmainstage):
            self.write_cmd(newsubstage)
        else:
            self.write_cmd('refresh')