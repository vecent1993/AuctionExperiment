# -*- coding: utf-8 -*-
"""
这个模块包含： 私人价值第二价格密封拍卖训练处理服务。
"""

import random
import time

from tornado.template import Template

from components.trainhandler import TrainHandler, on_ws
import components.treatment

class PlayerTrainPrivateSecondSealed(TrainHandler):
    def __init__(self, env):
        super(PlayerTrainPrivateSecondSealed, self).__init__(env)

        self.settings = dict(
            maxQ=10,
            minQ=5,
            sealed_run_time=60 * 3,
        )

        self.player['q'] = round(random.uniform(self.settings['minQ'], self.settings['maxQ']), 1)
        self.player['aq'] = round(random.uniform(self.settings['minQ'], self.settings['maxQ']), 1)

        self.end = False

    @on_ws
    def get(self, data):
        self.sealedbids = []

        self.RemoteWS.replace(self.render('thandler/trainprivatesecondsealed.html', player=self.player,
                                  settings=self.settings, bids=[]))

    @on_ws
    def get_timeout(self, name):
        self.RemoteWS.timeout(self.settings['sealed_run_time'])

    @on_ws
    def get_result(self, data):
        self.end = True

        if len(self.sealedbids) < 2:
            res = '你未出价，本次实验无效。'
        else:
            res = Template('''
                此次密封拍卖中，你的估价q为{{ q }}，对方的估价为{{ aq }}。
                结果你出价{{ bids[0]['bid'] }}, 对方出价{{ bids[1]['bid'] }}。
                由于{% if bids[0]['bid'] < bids[1]['bid']  %}对方出价更高，对方赢得物品，
                但只需要支付你的报价{{ bids[0]['bid'] }}（因为你的报价是次高价），也就是说对方获得收益为
                {{ aq }} - {{ bids[0]['bid'] }} = {{ aq-bids[0]['bid'] }}；
                而你并未获胜，本阶段收益为0。
                {% else %}你出价更高，你赢得物品，
                但只需要支付对方的报价{{ bids[1]['bid'] }}（因为对方的报价是次高价），
                也就是说你获得收益为{{ q }} - {{ bids[1]['bid'] }} = {{ q - bids[1]['bid'] }}，
                而对方并未获胜，本阶段收益为0。
                {% end %}
                ''').generate(bids=self.sealedbids, q=self.player['q'], aq=self.player['aq'])

        self.RemoteWS.showresult(res)

    @on_ws
    def sealed_bid(self, data):
        bid = round(float(data['bid']), 1)
        msg = {'bid': bid, 'username': self.player['username']}
        self.sealedbids.append(msg)

        msg = {'bid': round(self.player['aq'], 1), 'username': 'AGENT'}
        self.sealedbids.append(msg)


class TrainPrivateSecondSealed(components.treatment.Train):
    title = '私人价值第二价格密封拍卖'
    description = '训练私人价值第二价格密封拍卖'

    @staticmethod
    def get_stage(*args, **kwargs):
        return 'PlayerTrainPrivateSecondSealed'