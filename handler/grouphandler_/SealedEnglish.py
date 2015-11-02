# -*- coding: utf-8 -*-
import json
import time
import random
import datetime

from tornado.template import Template

import util.pool
from grouphandler import GroupHandler, db, redisclient, onRedis
from ..playerhandler_.playerhandler import PlayerHandler


class SealedEnglish(GroupHandler):
    def __init__(self, expid, sid, gid):
        super(SealedEnglish, self).__init__()

        self.expid, self.sid, self.gid = map(str, (expid, sid, gid))
        self.redis = redisclient
        self.value = util.pool.Group(self.redis, self.expid, self.sid, self.gid)

        if not self.value.get('players'):
            self.loadPlayers()

        self.initTasks()
        self.init()

    def init(self, data=None):
        stages = self.value.get('stage', refresh=True).split(':')
        round = 1

        if len(stages) == 1:
            if round > 0:
                self.value.set('stage', 'SealedEnglish:0:sealed:run')
                for pid in filter(lambda pid: not pid.startswith('agent'), self.value['players'].keys()):
                    PlayerHandler.nextStage(self.redis, self.expid, pid)
                self.handle({'cmd': 'startSealed'})
            else:
                self.publish('changeStage', data=dict(sid=self.sid, gid=self.gid))
            return

        if int(stages[1]) < round - 1:
            stages[1], stages[2], stages[3] = str(int(stages[1])+1), 'sealed', 'run'
            self.value.set('stage', ':'.join(stages))
            self.handle({'cmd': 'startSealed'})
        else:
            self.publish('changeStage', data=dict(sid=self.sid, gid=self.gid))

    def loadPlayers(self):
        p = util.pool.Pool(self.redis, self.expid)
        pids = p['sessions'][int(self.sid)]['groups'][int(self.gid)]
        players = {}
        for pid in pids:
            if pid.startswith('agent'):
                players[pid] = {'pid': pid, 'username': 'AGENT'}
            else:
                player = util.pool.Player(self.redis, self.expid, pid)
                if not player:
                    continue
                player.set('gid', self.gid)
                player.set('sid', self.sid)
                players[pid] = {'pid': pid, 'username': player['username']}
        self.value.set('players', players)

    def startSealed(self, data):
        self.value.set('q', round(random.uniform(6, 10), 1))
        self.value.set('sealedbids', {})
        self.value.set('englishbids', [])
        self.value.set('englishopenbids', [])

        for pid in self.value['players'].keys():
            cost = round(random.uniform(0, 4), 1)
            self.value['players'][pid]['cost'] = cost
            if pid.startswith('agent'):
                self.addDelay('sealedagentbid'+pid, random.uniform(5, 30), 'sealedAgentBid', pid)
            else:
                player = util.pool.Player(self.redis, self.expid, pid)
                player.set('stage', self.value['stage'])
                player.set('cost', cost)
                self.publish('changeStage', ':'.join(('player', self.expid, pid)))
            self.value.save('players')

        self.addDelay('sealedrun', 60 * 3, 'sealedRunTimeout')

    def sealedRunTimeout(self, data):
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.executeDelay('sealedAgentBid'+pid)

        stages = self.value.get('stage', refresh=True).split(':')
        stages[3] = 'result'
        self.value.set('stage', ':'.join(stages))

        bidshistory = self.value.get('sealedbids', {}, True)
        winner, winprice, pay = None, 0, 0
        if bidshistory:
            win = sorted(bidshistory.values(), key=lambda a: a['bid'], reverse=True)
            winner, winprice = win[0]['pid'], win[0]['bid']
            if len(win) > 1:
                pay = win[1]['bid']

        self.value.set('sealedresult', {'winner': winner, 'winprice': winprice, 'pay': pay})

        sql = 'insert into result(exp_id,user_id,session,type,win,win_price,strike_price,profit) ' \
              'values({},%s,{},0,%s,%s,%s,%s)'.format(self.expid, self.sid)

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = util.pool.Player(self.redis, self.expid, pid)
            player.set('stage', ':'.join(stages))
            if pid == winner:
                profit = self.value.get('q') - player['cost'] - pay
                player.set('result', {'win': True, 'profit': round(profit, 1)})
                try:
                    db.insert(sql, pid, '1', winprice, pay, profit)
                except:
                    pass
            else:
                player.set('result', {'win': False, 'profit': 0})
                try:
                    db.insert(sql, pid, '0', winprice, pay, 0)
                except:
                    pass
            self.publish('changeStage', ':'.join(('player', self.expid, pid)))

        self.addDelay('sealedresult', 10, 'sealedResultTimeout')

    def sealedResultTimeout(self, data):
        stages = self.value.get('stage', refresh=True).split(':')
        sql = 'insert into bid(exp_id,user_id,session,`group`,value,cost,type,bidding,bid_time) ' \
              'values({},%s,{},{},%s,%s,0,%s,%s)'.format(self.expid, self.sid, self.gid)
        sealedbids = []
        for key, value in self.value.get('sealedbids', refresh=True).items():
            if key.startswith('agent'):
                sealedbids.append([1, self.value['q'], self.value['players'][key]['cost'],
                                   value['bid'], value['bidtime']])
            else:
                sealedbids.append([value['pid'], self.value['q'], self.value['players'][key]['cost'],
                                   value['bid'], value['bidtime']])
        db.insertmany(sql, sealedbids)

        stages = self.value.get('stage', refresh=True).split(':')
        stages[2], stages[3] = 'english', 'run'
        self.value.set('stage', ':'.join(stages))
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = util.pool.Player(self.redis, self.expid, pid)
            player.set('stage', ':'.join(stages))
            self.publish('changeStage', ':'.join(('player', self.expid, pid)))

        self.addDelay('englishtotal', 60 * 3, 'englishTotalTimeout')
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.addDelay('englishagentbid'+pid, random.uniform(5, 20), 'englishAgentBid', pid)

    def englishTotalTimeout(self, data):
        self.cancelDelay('englisheach')
        self.englishRunTimeout(None)

    def englishEachTimeout(self, data):
        self.cancelDelay('englishtotal')
        self.englishRunTimeout(None)

    def englishRunTimeout(self, data):
        stages = self.value.get('stage', refresh=True).split(':')
        stages[3] = 'result'
        self.value.set('stage', ':'.join(stages))

        if stages[2] == 'english':
            sql = 'insert into result(exp_id,user_id,session,type,win,win_price,strike_price,profit) ' \
                    'values({},%s,{},1,%s,%s)'.format(self.expid, self.sid)
            bidshistory = self.value.get('englishbids', [], True)
        elif stages[2] == 'englishopen':
            sql = 'insert into result(exp_id,user_id,session,type,win,win_price,strike_price,profit) ' \
                    'values({},%s,{},2,%s,%s,%s,%s)'.format(self.expid, self.sid)
            bidshistory = self.value.get('englishopenbids', [], True)

        winner, pay = None, 0
        if bidshistory:
            winner, pay = bidshistory[-1]['pid'], round(float(bidshistory[-1]['bid']), 1)

        self.value.set('englishresult', {'winner': winner, 'winprice': pay, 'pay': pay})

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = util.pool.Player(self.redis, self.expid, pid)
            player.set('stage', ':'.join(stages))
            if pid == winner:
                profit = self.value.get('q') - player['cost'] - pay
                player.set('result', {'win': True, 'profit': round(profit, 1)})
                try:
                    db.insert(sql, pid, '1', pay, pay, profit)
                except:
                    pass
            else:
                player.set('result', {'win': False, 'profit': 0})
                try:
                    db.insert(sql, pid, '0', pay, pay, 0)
                except:
                    pass
            self.publish('changeStage', ':'.join(('player', self.expid, pid)))

        self.addDelay('englishresult', 10, 'englishResultTimeout')

    def englishResultTimeout(self, data):
        stages = self.value.get('stage', refresh=True).split(':')
        if stages[2] == 'english':
            sql = 'insert into bid(exp_id,user_id,session,`group`,value,cost,type,bidding,bid_time)' \
                  'values({},%s,{},{},%s,%s,1,%s,%s)'.format(self.expid, self.sid, self.gid)
            history = self.value.get('englishbids', refresh=True)
        elif stages[2] == 'englishopen':
            sql = 'insert into bid(exp_id,user_id,session,`group`,value,cost,type,bidding,bid_time)' \
                  'values({},%s,{},{},%s,%s,2,%s,%s)'.format(self.expid, self.sid, self.gid)
            history = self.value.get('englishopenbids', refresh=True)
        englishbids = []
        for item in history:
            key = item['pid']
            if key.startswith('agent'):
                englishbids.append([1, self.value['q'], self.value['players'][key]['cost'],
                                    item['bid'], item['bidtime']])
            else:
                englishbids.append([key, self.value['q'], self.value['players'][key]['cost'],
                                    item['bid'], item['bidtime']])
        db.insertmany(sql, englishbids)

        if stages[2] == 'englishopen':
            self.init(None)
            return

        stages = self.value.get('stage', refresh=True).split(':')
        stages[2], stages[3] = 'englishopen', 'run'
        self.value.set('stage', ':'.join(stages))
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = util.pool.Player(self.redis, self.expid, pid)
            player.set('stage', ':'.join(stages))
            self.publish('changeStage', ':'.join(('player', self.expid, pid)))

        self.addDelay('englishtotal', 60*3, 'englishTotalTimeout')
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.addDelay('englishagentbid'+pid, random.uniform(5, 20), 'englishAgentBid', pid)

    def sealedAgent(self, cost):
        return round(8. - cost, 1)

    def sealedAgentBid(self, data):
        pid = data
        if pid not in self.value['players']:
            return

        cost = self.value['players'][pid]['cost']
        bid = self.sealedAgent(cost)

        self.publish('sealedBid', ':'.join(('group',  str(self.sid), str(self.gid))),
                    {'pid': data, 'bid': bid, 'username': 'AGENT'})

    @onRedis
    def sealedBid(self, data):
        data['bid'] = round(float(data.get('bid', 0)), 1)
        if data['bid'] <= 0:
            return

        stages = self.value.get('stage', refresh=True).split(':')
        if not (stages[2] == 'sealed' and stages[3] == 'run') or 'pid' not in data or \
                        data['pid'] in self.value['sealedbids']:
            return

        data['bidtime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")

        if data['pid'].startswith('agent'):
            self.value['sealedbids'][data['pid']] = data
        elif data['pid'] in self.value['players']:
            self.value['sealedbids'][data['pid']] = data
            player = util.pool.Player(self.redis, self.expid, data['pid'])
            stages[3] = 'wait'
            player.set('stage', ':'.join(stages))
            # self.publish({'cmd': 'changeStage', 'domain': ':'.join(('player', data['pid']))})
        else:
            return
        self.value.save('sealedbids')

        if len(self.value['sealedbids']) >= len(self.value['players']):
            self.executeDelay('sealedrun')

    def _f(self, x):
        fx = random.gauss(0, 1) * x / 3.
        if fx < 0: fx = -fx
        return min(round(max(.1, fx), 1), x)

    def englishAgentBid(self, data):
        pid = data
        if pid not in self.value['players']:
            return

        stages = self.value.get('stage', refresh=True).split(':')

        if stages[2] == 'english':
            bidhistory = self.value.get('englishbids', refresh=True)
            q = 8.
        if stages[2] == 'englishopen':
            bidhistory = self.value.get('englishopenbids', refresh=True)
            q = self.value.get('q')

        bid = round(random.random(), 1)

        if bidhistory:
            bi = float(bidhistory[-1]['bid'])
            if stages[2] == 'english':
                s = 6.
                t = 0.
                delta = 4.
                if s - t - delta <= bi <= s - t:
                    q = (delta*(s+delta)**2 + s**2*(t+bi) - 2*s**3/3 - (t+delta+bi)**3/3) \
                            / (2*delta**2 - (t+delta+bi-s)**2)
                elif s - t <= bi <= s-t-delta:
                    q = (2*(s+delta)+t+bi) / 3.

            cj = self.value['players'][pid]['cost']
            if bi >= q - cj:
                return

            bid = bi + self._f(q-cj-bi)

        self.publish('englishBid', ':'.join(('group',  str(self.sid), str(self.gid))),
                    {'pid': pid, 'bid': bid, 'username': 'AGENT'})
        self.addDelay('englisheach', 30, 'englishEachTimeout')

    @onRedis
    def englishBid(self, data):
        stages = self.value.get('stage', refresh=True).split(':')
        if not ((stages[2] == 'english' or stages[2] == 'englishopen') and stages[3] == 'run') or 'pid' not in data:
            return

        data['bid'] = round(float(data.get('bid', 0)), 1)
        if data['bid'] <= 0:
            return
        if stages[2] == 'english' and self.value['englishbids'] and \
                                        data['bid'] <= self.value['englishbids'][-1]['bid']:
            return
        if stages[2] == 'englishopen' and self.value['englishopenbids'] and \
                                        data['bid'] <= self.value['englishopenbids'][-1]['bid']:
            return

        data['bidtime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")

        if data['pid'].startswith('agent'):
            if stages[2] == 'english':
                self.value['englishbids'].append(data)
                self.value.save('englishbids')
            elif stages[2] == 'englishopen':
                self.value['englishopenbids'].append(data)
                self.value.save('englishopenbids')
        elif data['pid'] in self.value['players']:
            if stages[2] == 'english':
                self.value['englishbids'].append(data)
                self.value.save('englishbids')
            elif stages[2] == 'englishopen':
                self.value['englishopenbids'].append(data)
                self.value.save('englishopenbids')
            self.addDelay('englisheach', 30, 'englishEachTimeout')

            for pid in filter(lambda pid: pid.startswith('agent'), self.value['players'].keys()):
                self.addDelay('englishagentbid'+pid, random.uniform(5, 20), 'englishAgentBid', pid)
        else:
            return

        self.publish('englishBidOpen', ':'.join(('group', self.sid, self.gid)), data)

    @staticmethod
    def renderInfo(group):
        return Template('''
            当前阶段：<br/>
                {{ group['stage'] }}<br/>
            参与人信息:<br/>
            <table class="table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>用户名</th>
                        <th>私人成本</th>
                        <th>共同价值</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in group['players'].values() %}
                    <tr>
                        <td>{{ p['pid'] }}</td>
                        <td>{{ p['username'] }}</td>
                        <td>{{ p['cost'] }}</td>
                        <td>{{ group['q'] }}</a></td>
                    </tr>
                    {% end %}
                </tbody>
            </table>
            {% if group.get('sealedbids', {}, refresh=True) %}
            密封拍卖:<br/>
            <table class="table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>用户名</th>
                        <th>出价</th>
                        <th>时间</th>
                    </tr>
                </thead>
                <tbody>
                    {% for bid in group['sealedbids'].values() %}
                    <tr>
                        <td>{{ bid['pid'] }}</td>
                        <td>{{ bid['username'] }}</td>
                        <td>{{ bid['bid'] }}</td>
                        <td>{{ bid['bidtime'] }}</a></td>
                    </tr>
                    {% end %}
                </tbody>
            </table>
            {% end %}
            {% if group.get('englishbids', [], refresh=True) %}
            英式拍卖（价值隐藏）:<br/>
            <table class="table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>用户名</th>
                        <th>出价</th>
                        <th>时间</th>
                    </tr>
                </thead>
                <tbody>
                    {% for bid in group['englishbids'] %}
                    <tr>
                        <td>{{ bid['pid'] }}</td>
                        <td>{{ bid['username'] }}</td>
                        <td>{{ bid['bid'] }}</td>
                        <td>{{ bid['bidtime'] }}</a></td>
                    </tr>
                    {% end %}
                </tbody>
            </table>
            {% end %}
            {% if group.get('englishopenbids', [], refresh=True) %}
            英式拍卖（价值公开）:<br/>
            <table class="table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>用户名</th>
                        <th>出价</th>
                        <th>时间</th>
                    </tr>
                </thead>
                <tbody>
                    {% for bid in group['englishopenbids'] %}
                    <tr>
                        <td>{{ bid['pid'] }}</td>
                        <td>{{ bid['username'] }}</td>
                        <td>{{ bid['bid'] }}</td>
                        <td>{{ bid['bidtime'] }}</a></td>
                    </tr>
                    {% end %}
                </tbody>
            </table>
            {% end %}
        ''').generate(group=group)