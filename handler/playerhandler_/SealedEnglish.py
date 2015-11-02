# -*- coding: utf-8 -*-
import time

from util.pool import *
from playerhandler import PlayerHandler, onWs, onRedis


class SealedEnglish(PlayerHandler):
    def __init__(self, env):
        super(SealedEnglish, self).__init__(env)

        if not ('sid' in self.player and 'gid' in self.player):
            self.write({'error': 'not ready'})
            return

        self.group = Group(self.env.redis, self.env.exp['id'], self.player['sid'], self.player['gid'])
        self.groupdomain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))

        self.listen(self.msgchannel, self.on_message)

    @onWs
    def get(self, data):
        if not self.exp:
            self.writeCmd('error', 'experiment not exists')

        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) < 4:
            self.writeCmd('error', 'not ready')

        round, mainstage, substage = stages[1:4]
        if mainstage == 'sealed':
            self.writeCmd('replace', self.env.render('handlers/SealedEnglish/sealed.html', train=False,
                player=self.player, bids=self.group.get('sealedbids', [], True), substage=substage))
        elif mainstage == 'english':
            bids = map(self._anonymous, self.group.get('englishbids', [], True))
            q = None
            self.writeCmd('replace', self.env.render('handlers/SealedEnglish/english.html', train=False,
                q=q, player=self.player, bids=bids, substage=substage))
        elif mainstage == 'englishopen':
            bids = map(self._anonymous, self.group.get('englishopenbids', [], True))
            q = self.group.get('q', refresh=True)
            self.writeCmd('replace', self.env.render('handlers/SealedEnglish/english.html', train=False,
                q=q, player=self.player, bids=bids, substage=substage))

    @onWs
    def sealedbid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('sealedBid', self.groupdomain,
                     dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @onWs
    def englishbid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('englishBid', self.groupdomain,
                    dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @onWs
    def gettimeout(self, data):
        stages = self.player.get('stage', '', refresh=True).split(':')
        name = data.get('name')
        if name in self.group.get('tasks', {}, True):
            seconds = round(self.group['tasks'][name]['runtime'] - time.time())
            if seconds > 0:
                self.writeCmd('timeout', {'name': name, 'seconds': seconds})

    @onWs
    def getresult(self, data):
        self.writeCmd('showresult', '马上进入下一轮公开拍卖阶段，请耐心等待并做好准备')

    def _anonymous(self, data):
        if data.get('pid') == str(self.player.pid):
            data['username'] = '您'
            data['self'] = True
            data['pid'] = ''
        else:
            data['username'] = '某竞拍者'
            data['pid'] = ''
        return data

    @onRedis('group')
    def englishBidOpen(self, data):
        self.writeCmd('englishbid', self._anonymous(data))

    @onRedis('player')
    def changeStage(self, data):
        mainstage, substage = self.player.get('stage').split(':')[2:4]
        stage = self.player.get('stage', refresh=True)
        if not stage.startswith('SealedEnglish'):
            self.switchHandler({'cmd': 'get'})
            return

        newmainstage, newsubstage = stage.split(':')[2:4]
        if(mainstage == newmainstage):
            self.writeCmd(newsubstage)
        else:
            self.writeCmd('refresh')