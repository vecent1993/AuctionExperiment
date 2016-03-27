# -*- coding: utf-8 -*-
import time

from utils.exprv import *
import components.grouphandler as grouphandler
import components.playerhandler as playerhandler


class PlayerSealedEnglish(playerhandler.PlayerHandler):
    def __init__(self, env):
        super(PlayerSealedEnglish, self).__init__(env)

        self.settings.update(dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        ))

        self.group = Group(self.env.redis, self.env.exp['id'], self.player['sid'], self.player['gid'])
        self.group_domain = ':'.join(('group', str(self.player['sid']), str(self.player['gid'])))
        self.RemoteGroup = playerhandler.RemoteGroup(self.msg_channel, self.group_domain,
                                                     self.env.redis.publish)

        self.listen(self.msg_channel, self.on_message)

    @playerhandler.on_ws
    def get(self, data):
        if not self.exp:
            self.RemoteWS.error('experiment not exists')

        stages = self.player.get('stage', refresh=True).split(':')
        if len(stages) == 1:
            self.RemoteWS.replace(self.render('Wait/wait.html', substage='GroupReady',
                                                  message="是否做好准备？"))
            return
        elif len(stages) == 2:
            self.RemoteWS.replace(self.render('Wait/wait.html', substage='Ready',
                                                  message="等待其他人做好准备，注意实验可能随时开始！"))
            return

        self.player.get('cost', refresh=True)
        mainstage, substage = stages[-2:]
        round = 0
        if mainstage == 'sealed':
            self.RemoteWS.replace(self.render('SealedEnglish/sealed.html', train=False, round=round,
                settings=self.settings, player=self.player, bids=self.group.get('sealedbids', [], True), substage=substage))
        elif mainstage == 'english':
            bids = map(self._anonymous, self.group.get('englishbids', [], True))
            q = None
            self.RemoteWS.replace(self.render('SealedEnglish/english.html', train=False, round=round,
                settings=self.settings, q=q, player=self.player, bids=bids, substage=substage))
        elif mainstage == 'englishopen':
            bids = map(self._anonymous, self.group.get('englishopenbids', [], True))
            q = self.group.get('q', refresh=True)
            self.RemoteWS.replace(self.render('SealedEnglish/english.html', train=False, round=round,
                settings=self.settings, q=q, player=self.player, bids=bids, substage=substage))

    @playerhandler.on_ws
    def ready(self, data):
        self.player.set('stage', 'PlayerSealedEnglish:Ready')
        self.RemoteWS.Ready()
        self.RemoteGroup.report_ready(self.player.pid)

    @playerhandler.on_ws
    def sealed_bid(self, data):
        bid = round(float(data['bid']), 1)
        self.RemoteGroup.report_sealed_bid(dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @playerhandler.on_ws
    def english_bid(self, data):
        bid = round(float(data['bid']), 1)
        self.RemoteGroup.report_english_bid(dict(pid=self.player.pid, bid=bid, username=self.player['username']))

    @playerhandler.on_ws
    def get_timeout(self, name=None):
        tid = self.group.key + ':' + name
        runtime = grouphandler.GroupHandler.get_runtime(self.env.redis, self.tid)
        if runtime:
            seconds = round(runtime - time.time())
            if seconds > 0:
                self.RemoteWS.timeout({'name': name, 'seconds': seconds})

    @playerhandler.on_ws
    def get_result(self, data):
        self.RemoteWS.showresult('马上进入下一部分，请耐心等待并做好准备。')

    def _anonymous(self, data):
        if data.get('pid') == str(self.player.pid):
            data['username'] = '你'
            data['self'] = True
            data['pid'] = ''
        else:
            data['username'] = '其他竞拍者'
            data['pid'] = ''
        return data

    @playerhandler.on_redis
    def english_bid_open(self, data):
        self.RemoteWS.englishbid(self._anonymous(data))

    @playerhandler.on_redis
    def change_substage(self, data):
        old_stages = self.player['stage'].split(':')
        new_stages = self.player.get('stage', refresh=True).split(':')
        if len(new_stages) == 2:
            getattr(self.RemoteWS, new_stages[-1])()
        else:
            if len(old_stages) < 3 or old_stages[-2] != new_stages[-2]:
                self.RemoteWS.refresh()
            else:
                getattr(self.RemoteWS, new_stages[-1])()