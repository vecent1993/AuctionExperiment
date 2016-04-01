# -*- coding: utf-8 -*-
import time

from utils.exprv import *
import components.grouphandler as grouphandler
import components.playerhandler as playerhandler


class PlayerInfoAcquiSequence(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerInfoAcquiSequence, self).__init__(env)

        self.group = Group(self.env.redis, self.env.exp['id'], self.player['sid'], self.player['gid'])
        self.group_domain = 'group:%s:%s' % (self.player['sid'], self.player['gid'])
        self.RemoteGroup = playerhandler.RemoteGroup(self.msg_channel, self.group_domain,
                                                     self.env.redis.publish)

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def get(self, data):
        if not self.exp:
            self.RemoteWS.error('实验尚未开始或已经结束。')

        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) == 1:
            self.RemoteWS.replace('')
            return
        if stages[1] == 'end':
            self.RemoteWS.replace(self.render('InfoAcquiSequence/sealed.html', mainstage='end',
                                              player=self.player, substage=None, settings=self.settings,
                                              group=self.group))
            return

        mainstage, substage = stages[-2], stages[-1]
        self.RemoteWS.replace(self.render('InfoAcquiSequence/sealed.html', mainstage=mainstage,
                                          player=self.player, substage=substage, settings=self.settings,
                                          group=self.group))

    @playerhandler.on_ws
    def sealed_bid(self, data):
        stages = self.player.get('stage', refresh=True).split(':')
        if stages[-1] != 'run':
            return

        bid = round(float(data['bid']), 1)
        self.RemoteGroup.report_sealed_bid(dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @playerhandler.on_ws
    def get_timeout(self, data=None):
        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) < 3:
            return
        if stages[-1] == 'wait':
            tid = '%s:%s%s' % (self.group.key, stages[-2], 'run')
        else:
            tid = '%s:%s%s' % (self.group.key, stages[-2], stages[-1])
        runtime = grouphandler.GroupHandler.get_runtime(self.env.redis, tid)
        if runtime:
            seconds = round(runtime - time.time())
            if seconds >= 0:
                self.RemoteWS.timeout({'name': tid, 'seconds': seconds})

    @playerhandler.on_ws
    def get_result(self, data=None):
        stages = self.player.get('stage', refresh=True).split(':')
        if stages[-1] == 'end':
            result = self.group.get('results', refresh=True).get('a')
            if result['winner'] == self.player.pid:
                text = '<li>恭喜你赢得了A物品拍卖。</li><li>你将不再参加B物品拍卖。本轮实验即将结束！</li>'
            self.RemoteWS.showresult('拍卖结果：<ul>%s</ul>' % text)

        if len(stages) != 3 or stages[-1] != 'result':
            return
        result = self.group.get('results', refresh=True).get(stages[1])
        if not result:
            return

        if stages[1] == 'info':
            if result['winner'] == self.player.pid:
                text = '<li>恭喜你赢得了信息获取拍卖，你在下一阶段（A物品拍卖）将会得知B物品估价。' \
                       '</li><li>下一阶段A物品拍卖即将开始，请做好准备！</li>'
            else:
                text = '<li>很遗憾，你并未赢得信息获取拍卖！</li><li>下一阶段A物品拍卖即将开始，请做好准备！</li>'
        elif stages[1] == 'a':
            if result['winner'] == self.player.pid:
                text = '<li>恭喜你赢得了A物品拍卖。</li><li>你将不再参加B物品拍卖。本轮实验即将结束！</li>'
            else:
                text = '<li>很遗憾，你并未赢得A物品拍卖，且获胜者的报价为%s！</li><li>' \
                       '下一阶段B物品拍卖即将开始，请做好准备！</li>' % result['winprice']
        else:
            if result['winner'] == self.player.pid:
                text = '<li>恭喜你赢得了B物品拍卖。</li><li>本轮实验即将结束！</li>'
            else:
                text = '<li>很遗憾，你并未赢得B物品拍卖，且获胜者的报价为%s！</li><li>' \
                       '本轮实验即将结束！</li>' % result['winprice']
        self.RemoteWS.showresult('拍卖结果：<ul>%s</ul>' % text)

    @playerhandler.on_redis
    def change_substage(self, data=None):
        old_stages = self.player['stage'].split(':')
        new_stages = self.player.get('stage', refresh=True).split(':')
        if len(old_stages) != len(new_stages):
            self.RemoteWS.refresh()
        else:
            if old_stages[-2] != new_stages[-2]:
                self.RemoteWS.refresh()
            else:
                getattr(self.RemoteWS, new_stages[-1])()
