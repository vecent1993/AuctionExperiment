# -*- coding: utf-8 -*-
import random

from playerhandler import TrainHandler, onWs


class Train(TrainHandler):
    def __init__(self, env):
        super(Train, self).__init__(env)
        self.player['cost'] = round(random.uniform(0.1, 4), 1)
        self.player['q'] = round(random.uniform(6, 10), 1)

    @onWs
    def get(self, data):
        res = ''
        if data is None:
            res = self.env.render('handlers/SealedEnglish/train.html')
        elif data == 'sealed':
            res = self.env.render('handlers/SealedEnglish/sealed.html', train=True, player=self.player,
                                  bids=[], substage='run')
            self.sealedbids = []
        elif data == 'english':
            res = self.env.render('handlers/SealedEnglish/english.html', train=True, q=None,
                                  player=self.player, bids=[], substage='run')
            self.englishbids = []
        elif data == 'englishopen':
            res = self.env.render('handlers/SealedEnglish/english.html', train=True, q=8,
                                  player=self.player, bids=[], substage='run')
            self.englishbids = []
        else:
            self.writeCmd('error', '')

        self.writeCmd('replace', res)

    @onWs
    def gettimeout(self, data):
        name = data.get('name')
        seconds = 30
        if name == 'englishtotal' or name == 'sealedrun':
            seconds = 60 * 3
        elif name == 'englisheach':
            seconds = 30
        else:
            return

        self.writeCmd('timeout', {'name': name, 'seconds': seconds})

    @onWs
    def getresult(self, data):
        if data == 'sealed':
            res = str(self.sealedbids)
        elif data == 'english':
            res = str(self.englishbids)
        elif data == 'englishopen':
            res = str(self.englishbids)
        self.writeCmd('showresult', res)

    @onWs
    def sealedbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = {'pid': self.player.pid, 'bid': bid, 'username': self.player['username']}
        self.sealedbids.append(msg)

        msg = {'pid': '0', 'bid': round(random.uniform(4, 7), 1), 'username': 'AGENT'}
        self.sealedbids.append(msg)

    def _anonymous(self, data):
        data = dict(data)
        if data.get('pid') == str(self.player.pid):
            data['username'] = '您'
            data['self'] = True
            data['pid'] = ''
        else:
            data['username'] = '某竞拍者'
            data['pid'] = ''
        return data

    @onWs
    def englishbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = dict(pid=self.player.pid, bid=bid, username=self.player['username'])
        self.englishbids.append(msg)
        self.writeCmd('englishbid', self._anonymous(msg))

        msg = dict(pid='0', bid=round(bid+.1, 1), username='AGENT')
        self.englishbids.append(msg)
        self.writeCmd( 'englishbid', self._anonymous(msg))