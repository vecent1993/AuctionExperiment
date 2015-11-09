# -*- coding: utf-8 -*-
import random
import time

from tornado.template import Template
from tornado.ioloop import IOLoop

from playerhandler import TrainHandler, onWs


class Train(TrainHandler):
    def __init__(self, env):
        super(Train, self).__init__(env)
        self.player['cost'] = round(random.uniform(0.1, 4), 1)
        self.player['q'] = round(random.uniform(6, 10), 1)
        self.player['agentcost'] = round(random.uniform(0.1, 4), 1)

        self.end = False
        self.open = False

    @onWs
    def get(self, data):
        res = ''
        self.end = False
        self.open = False
        exp = self.env.db.get('select exp_intro from exp where exp_id=%s', self.exp['id'])
        if data is None:
            res = self.env.render('handlers/SealedEnglish/train.html', exp=exp)
        elif data == 'sealed':
            res = self.env.render('handlers/SealedEnglish/sealed.html', train=True, player=self.player,
                                  bids=[], substage='run')
            self.sealedbids = []
        elif data == 'english':
            res = self.env.render('handlers/SealedEnglish/english.html', train=True, q=None,
                                  player=self.player, bids=[], substage='run')
            self.englishbids = []
        elif data == 'englishopen':
            self.open = True
            res = self.env.render('handlers/SealedEnglish/english.html', train=True, q=self.player['q'],
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
        self.end = True
        if data == 'sealed':
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
        elif data == 'english' or data == 'englishopen':
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
        q = 8.
        if self.open:
            q = self.player['q']
        if (not self.end) and q - self.player['agentcost'] > bid:
            msg = dict(pid='0', bid=round(bid+.1, 1), username='AGENT')
            self.englishbids.append(msg)
            self.writeCmd( 'englishbid', self._anonymous(msg))