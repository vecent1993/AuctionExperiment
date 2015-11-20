# -*- coding: utf-8 -*-
import random
import time

from tornado.template import Template
from tornado.ioloop import IOLoop

from trainhandler import TrainHandler, onWs


class English(TrainHandler):
    def __init__(self, env):
        super(English, self).__init__(env)

        self.settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )

        self.player['cost'] = round(random.uniform(self.settings['minC']+.1, self.settings['maxC']), 1)
        self.player['q'] = round(random.uniform(self.settings['minQ'], self.settings['maxQ']), 1)
        self.player['agentcost'] = round(random.uniform(self.settings['minC']+1, self.settings['maxC']), 1)

        self.end = False

    @onWs
    def get(self, data):
        self.end = False
        res = self.env.render('handlers/SealedEnglish/english.html', train=True, q=None,
                                  settings=self.settings, player=self.player, bids=[], substage='run')
        self.englishbids = []

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
        self.end = True
        if not self.englishbids:
            res = '你未出价，本次实验无效。'
        else:
            res = Template('''
                此次公开拍卖中，物品的价值q为{{ q }}，你和对方的成本分别为{{ cost }}, {{ agentcost }}。
                由于最后出价的是{% if bids[-1]['pid'] == '0'  %}对方（出价{{ bids[-1]['bid'] }}），
                对方赢得物品，并支付其报价{{ bids[-1]['bid'] }}，也就是说对方获得收益为
                {{ q }} - {{ agentcost }} - {{ bids[-1]['bid'] }}= {{ q-agentcost-bids[-1]['bid'] }}；
                而你并未获胜，本阶段收益为0。
                {% else %}你（出价{{ bids[-1]['bid'] }}），你赢得物品，并支付你的报价{{ bids[-1]['bid'] }}，
                也就是说你获得收益为{{ q }} - {{ cost }} - {{ bids[-1]['bid'] }}= {{ q-cost-bids[-1]['bid'] }}；
                而对方并未获胜，本阶段收益为0。
                {% end %}
                ''').generate(bids=self.englishbids, cost=self.player['cost'],
                              agentcost=self.player['agentcost'], q=self.player['q'])
        self.writeCmd('showresult', res)

    def _anonymous(self, data):
        data = dict(data)
        if data.get('pid') == str(self.player.pid):
            data['username'] = '你'
            data['self'] = True
            data['pid'] = ''
        else:
            data['username'] = '其他竞拍者'
            data['pid'] = ''
        return data

    @onWs
    def englishbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = dict(pid=self.player.pid, bid=bid, username=self.player['username'])
        self.englishbids.append(msg)
        self.writeCmd('englishbid', self._anonymous(msg))

        IOLoop.instance().add_timeout(time.time() + random.uniform(2, 7), self.englishAgentBid, bid)


    def englishAgentBid(self, bid):
        eq = (self.settings['minQ'] + self.settings['maxQ']) / 2.
        if (not self.end) and eq - self.player['agentcost'] > bid:
            msg = dict(pid='0', bid=round(bid+.1, 1), username='AGENT')
            self.englishbids.append(msg)
            self.writeCmd( 'englishbid', self._anonymous(msg))