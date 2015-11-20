# -*- coding: utf-8 -*-
import random
import time

from tornado.template import Template
from tornado.ioloop import IOLoop

from trainhandler import TrainHandler, onWs


class Sealed(TrainHandler):
    def __init__(self, env):
        super(Sealed, self).__init__(env)

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
        res = self.env.render('handlers/SealedEnglish/sealed.html', train=True, player=self.player,
                                  settings=self.settings, bids=[], substage='run')
        self.sealedbids = []

        self.writeCmd('replace', res)

    @onWs
    def gettimeout(self, data):
        name = data.get('name')
        self.writeCmd('timeout', {'name': name, 'seconds': 60*3})

    @onWs
    def getresult(self, data):
        self.end = True

        if len(self.sealedbids) < 2:
            res = '你未出价，本次实验无效。'
        else:
            res = Template('''
                此次密封拍卖中，物品的价值q为{{ q }}，你和对方的成本分别为{{ cost }}, {{ agentcost }}。
                你出价{{ bids[0]['bid'] }}, 对方出价{{ bids[1]['bid'] }}。
                由于{% if bids[0]['bid'] < bids[1]['bid']  %}对方出价更高，对方赢得物品，
                但只需要支付你的报价{{ bids[0]['bid'] }}（因为你的报价是次高价），也就是说对方获得收益为
                {{ q }} - {{ agentcost }} - {{ bids[0]['bid'] }}= {{ q-agentcost-bids[0]['bid'] }}；
                而你并未获胜，本阶段收益为0。
                {% else %}你出价更高，你赢得物品，
                但只需要支付对方的报价{{ bids[1]['bid'] }}（因为对方的报价是次高价），
                也就是说你获得收益为{{ q }} - {{ cost }} - {{ bids[1]['bid'] }}= {{ q-cost-bids[1]['bid'] }}，
                而对方并未获胜，本阶段收益为0。
                {% end %}
                ''').generate(bids=self.sealedbids, cost=self.player['cost'],
                              agentcost=self.player['agentcost'], q=self.player['q'])

        self.writeCmd('showresult', res)

    @onWs
    def sealedbid(self, data):
        bid = round(float(data['bid']), 1)
        msg = {'pid': self.player.pid, 'bid': bid, 'username': self.player['username']}
        self.sealedbids.append(msg)

        eq = (self.settings['minQ'] + self.settings['maxQ']) / 2.
        msg = {'pid': '0', 'bid': round(random.uniform(.1, eq-self.player['agentcost']), 1), 'username': 'AGENT'}
        self.sealedbids.append(msg)