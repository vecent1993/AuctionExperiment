# -*- coding: utf-8 -*-
import time
import random
import json

from util.pool import *
from ..playerhandler import PlayerHandler, TrainHandler


class Profile(PlayerHandler):
    def __init__(self, env):
        super(Profile, self).__init__(env)

        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.listen(self.msgchannel, self.on_message)

    def get(self, data):
        return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/profile.html'))

    def profile(self, data):
        self.player.update(data)
        self.player.saveAll()
        try:
            self.env.db.insert('insert into player(user_id,exp_id,player_no,player_isskilled) '
                               'values(%s,%s,%s,%s)', self.player.pid, self.player.expid,
                                data['studentno'], 1 if 'skilled' in data else 0)
        except:
            pass
        self.publish('addPlayer', 'pool', dict(pid=self.player.pid, username=self.player['username']))

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if msg.get('domain') == self.playerdomain and msg.get('cmd') == 'changeStage':
                self.nextStage({'cmd': 'get'})


class Intro(PlayerHandler):
    def __init__(self, env):
        super(Intro, self).__init__(env)

        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.listen(self.msgchannel, self.on_message)

    def ready(self, data):
        self.groupdomain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.player.set('stage', 'Intro:Ready')
        self.write({'cmd': 'Ready'})
        self.publish('ready', self.groupdomain, self.player.pid)

    def get(self, data):
        stages = self.player.get('stage').split(':')
        substage = None
        if len(stages) > 1:
            substage = stages[1]
        return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/intro.html',
                                                          exp=self.env.exp, substage=substage))

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if msg.get('domain') == self.playerdomain and msg.get('cmd') == 'changeStage':
                stage = self.player.get('stage', refresh=True)

                if not stage.startswith('INTRO'):
                    self.switchHandler({'cmd': 'get'})
                    return

                stages = stage.split(':')
                if len(stages) > 1:
                    self.write({'cmd': stages[1]})


class End(PlayerHandler):
    def __init__(self, env):
        super(End, self).__init__(env)

    def get(self, data):
        href = '/exp/{}/result'.format(self.env.exp['id'])
        return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/end.html', redirecturl=href))


class SealedEnglish(PlayerHandler):
    def __init__(self, env):
        super(SealedEnglish, self).__init__(env)

        if not ('sid' in self.player and 'gid' in self.player):
            self.write({'error': 'not ready'})
            return

        self.group = Group(self.env.redis, self.env.exp['id'], self.player['sid'], self.player['gid'])
        self.groupdomain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.playerdomain = ':'.join(('player', str(self.env.exp['id']), str(self.player.pid)))
        self.listen(self.msgchannel, self.on_message)

    def get(self, data):
        if not self.exp:
            return dict(error='experiment not exists')
        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) < 4:
            return dict(error='not ready')

        round, mainstage, substage = stages[1:4]
        if mainstage == 'sealed':
            return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/sealed.html', train=False,
                player=self.player, bids=self.group.get('sealedbids', [], True), substage=substage))
        elif mainstage == 'english':
            bids = map(self._anonymous, self.group.get('englishbids', [], True))
            q = None
            return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/english.html', train=False,
                q=q, player=self.player, bids=bids, substage=substage))
        elif mainstage == 'englishopen':
            bids = map(self._anonymous, self.group.get('englishopenbids', [], True))
            q = self.group.get('q', refresh=True)
            return dict(cmd='replace', data=self.env.render('baseexp/SealedEnglish/english.html', train=False,
                q=q, player=self.player, bids=bids, substage=substage))

    def sealedbid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('sealedBid', self.groupdomain,
                     dict(pid=self.player.pid, bid=bid, username=self.player['username']))
        return dict(cmd='ok')

    def englishbid(self, data):
        bid = round(float(data['bid']), 1)
        self.publish('englishBid', self.groupdomain,
                    dict(pid=self.player.pid, bid=bid, username=self.player['username']))
        return dict(cmd='ok')

    def gettimeout(self, data):
        stages = self.player.get('stage', '', refresh=True).split(':')
        name = data.get('name')
        if name in self.group.get('tasks', {}, True):
            seconds = round(self.group['tasks'][name]['runtime'] - time.time())
            if seconds > 0:
                return dict(cmd='timeout', data={'name': name, 'seconds': seconds})

    def getresult(self, data):
        return dict(cmd='showresult', data='马上进入下一轮公开拍卖阶段，请耐心等待并做好准备')

    def _anonymous(self, data):
        if data.get('pid') == str(self.player.pid):
            data['username'] = '您'
            data['pid'] = ''
        else:
            data['username'] = '某竞拍者'
            data['pid'] = ''
        return data

    def on_message(self, msg):
        if msg['type'] == 'message':
            msg = json.loads(msg['data'])
            if msg.get('domain') == self.groupdomain and msg.get('cmd') == 'englishBidOpen':
                self.write({'cmd': 'englishbid', 'data': self._anonymous(msg['data'])})

            elif msg.get('domain') == self.playerdomain and msg.get('cmd') == 'changeStage':
                mainstage, substage = self.player.get('stage').split(':')[2:4]
                stage = self.player.get('stage', refresh=True)
                if not stage.startswith('SealedEnglish'):
                    self.switchHandler({'cmd': 'get'})
                    return

                newmainstage, newsubstage = stage.split(':')[2:4]
                if(mainstage == newmainstage):
                    self.write({'cmd': newsubstage})
                else:
                    self.write({'cmd': 'refresh'})


class Train(TrainHandler):
    def __init__(self, env):
        super(Train, self).__init__(env)
        self.player['cost'] = round(random.uniform(0, 4), 1)
        self.player['q'] = round(random.uniform(6, 10), 1)

    def get(self, data):
        res = ''
        if data is None:
            res = self.env.render('baseexp/SealedEnglish/train.html')
        elif data == 'sealed':
            res = self.env.render('baseexp/SealedEnglish/sealed.html', train=True, player=self.player,
                                  bids=[], substage='run')
            self.sealedbids = []
        elif data == 'english':
            res = self.env.render('baseexp/SealedEnglish/english.html', train=True, q=None,
                                  player=self.player, bids=[], substage='run')
            self.englishbids = []
        elif data == 'englishopen':
            res = self.env.render('baseexp/SealedEnglish/english.html', train=True, q=8,
                                  player=self.player, bids=[], substage='run')
            self.englishbids = []
        else:
            return dict(cmd='error', data='')

        return dict(cmd='replace', data=res)

    def gettimeout(self, data):
        name = data.get('name')
        seconds = 30
        if name == 'englishtotal' or name == 'sealedrun':
            seconds = 60 * 3
        elif name == 'englisheach':
            seconds = 30
        else:
            return

        return dict(cmd='timeout', data={'name': name, 'seconds': seconds})

    def getresult(self, data):
        if data == 'sealed':
            res = str(self.sealedbids)
        elif data == 'english':
            res = str(self.englishbids)
        elif data == 'englishopen':
            res = str(self.englishbids)
        return dict(cmd='showresult', data=res)

    def sealedbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = {'pid': self.player.pid, 'bid': bid, 'username': self.player['username']}
        self.sealedbids.append(msg)

        msg = {'pid': '0', 'bid': round(random.uniform(4, 7), 1), 'username': 'AGENT'}
        self.sealedbids.append(msg)
        return dict(cmd='ok')

    def _anonymous(self, data):
        data = dict(data)
        if data.get('pid') == str(self.player.pid):
            data['username'] = '您'
            data['pid'] = ''
        else:
            data['username'] = '某竞拍者'
            data['pid'] = ''
        return data

    def englishbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = dict(pid=self.player.pid, bid=bid, username=self.player['username'])
        self.englishbids.append(msg)
        self.write({'cmd': 'englishbid', 'data': self._anonymous(msg)})

        msg = dict(pid=self.player.pid, bid=round(bid+.1, 1), username='AGENT')
        self.englishbids.append(msg)
        self.write({'cmd': 'englishbid', 'data': self._anonymous(msg)})
        return dict(cmd='ok')