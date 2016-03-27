# -*- coding: utf-8 -*-
import random
import datetime

from tornado.template import Template

import utils.exprv
import components.grouphandler as grouphandler
import components.playerhandler as playerhandler


class GroupSealedEnglish(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupSealedEnglish, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = utils.exprv.Group(self.redis, self.expid, self.sid, self.gid)
        self.settings = self.value.get('settings', dict(), True)
        self.RemoteGroup = grouphandler.RemoteGroup(self.expid, self.sid, self.gid, self.redis.publish)

        self.settings.update(dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0,
            sealed_run_time=60 * 3,
            result_time=10,
            english_run_time=40,
        ))

        if not self.value.get('players'):
            self.load_players()

        self.init_tasks()

        stages = self.value.get('stage', refresh=True).split(':')
        if len(stages) == 1:
            self.prepare()
        elif stages[-2] == 'sealed':
            if stages[-1] == 'run':
                self.start()
            else:
                self.sealed_run_timeout()
        else:
            if stages[-1] == 'run':
                self.sealed_result_timeout()
            else:
                self.english_run_timeout()

    def load_players(self):
        p = utils.exprv.Pool(self.redis, self.expid)
        pids = p['sessions'][int(self.sid)]['groups'][int(self.gid)]
        players = {}
        for pid in pids:
            if pid.startswith('agent'):
                players[pid] = {'pid': pid, 'username': 'AGENT'}
            else:
                player = utils.exprv.Player(self.redis, self.expid, pid)
                if not player:
                    continue
                player.set('gid', self.gid)
                player.set('sid', self.sid)
                players[pid] = {'pid': pid, 'username': player['username']}
        self.value.set('players', players)

    def start(self, data=None):
        self.value.set('stage', '%s:%s:%s' % ('GroupSealedEnglish', 'sealed', 'run'))
        self.value.set('q', round(random.uniform(self.settings['minQ'], self.settings['maxQ']), 1))
        self.value.set('sealedbids', {})
        self.value.set('englishbids', [])
        self.value.set('englishopenbids', [])

        player_stage = '%s:%s:%s' % ('PlayerSealedEnglish', 'sealed', 'run')

        self.add_delay('sealedrun', self.settings['sealed_run_time'], self.sealed_run_timeout)
        for pid in self.value['players'].keys():
            cost = round(random.uniform(self.settings['minC']+.1, self.settings['maxC']), 1)
            self.value['players'][pid]['cost'] = cost
            if pid.startswith('agent'):
                self.add_delay('sealedagentbid'+pid, random.uniform(5, 30), self.sealed_agent_bid, pid)
            else:
                player = utils.exprv.Player(self.redis, self.expid, pid)
                player.set('stage', player_stage)
                player.set('cost', cost)
                self.RemotePlayer.change_substage(pid)
            self.value.save('players')


    def sealed_run_timeout(self, data=None):
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.execute_delay('sealedagentbid'+pid)

        self.value.set('stage', '%s:%s:%s' % ('GroupSealedEnglish', 'sealed', 'result'))

        bidshistory = self.value.get('sealedbids', {}, True)
        winner, winprice, pay = None, 0, 0
        if bidshistory:
            win = sorted(bidshistory.values(), key=lambda a: a['bid'], reverse=True)
            winner, winprice = win[0]['pid'], win[0]['bid']
            if len(win) > 1:
                pay = win[1]['bid']

        self.value.set('sealedresult', {'winner': winner, 'winprice': winprice, 'pay': pay})

        # sql = 'insert into result(exp_id,user_id,round,session,type,win,win_price,strike_price,profit) ' \
        #       'values({},%s,{},{},0,%s,%s,%s,%s)'.format(self.expid, self.sid)

        player_stage = '%s:%s:%s' % ('PlayerSealedEnglish', 'sealed', 'result')

        self.add_delay('sealedresult', self.settings['result_time'], self.sealed_result_timeout)

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            if pid == winner:
                profit = self.value.get('q') - player['cost'] - pay
                player.set('result', {'win': True, 'profit': round(profit, 1)})
                try:
                    pass
                    # self.db.insert(sql, pid, '1', winprice, pay, profit)
                except:
                    pass
            else:
                player.set('result', {'win': False, 'profit': 0})
                try:
                    pass
                    # self.db.insert(sql, pid, '0', winprice, pay, 0)
                except:
                    pass
            self.RemotePlayer.change_substage(pid)

    def sealed_result_timeout(self, data=None):
        # sql = 'insert into bid(exp_id,user_id,round,session,`group`,value,cost,type,bidding,bid_time) ' \
        #       'values({},%s,{},{},{},%s,%s,0,%s,%s)'.format(self.expid, round_, self.sid, self.gid)
        sealedbids = []
        for key, value in self.value.get('sealedbids', refresh=True).items():
            if key.startswith('agent'):
                sealedbids.append([1, self.value['q'], self.value['players'][key]['cost'],
                                   value['bid'], value['bidtime']])
            else:
                sealedbids.append([value['pid'], self.value['q'], self.value['players'][key]['cost'],
                                   value['bid'], value['bidtime']])
        # self.db.insertmany(sql, sealedbids)

        self.value.set('stage', '%s:%s:%s' % ('GroupSealedEnglish', 'english', 'run'))
        player_stage = '%s:%s:%s' % ('PlayerSealedEnglish', 'english', 'run')

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            self.RemotePlayer.change_substage(pid)

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.add_delay('englishagentbid'+pid, random.uniform(5, 20), self.english_agent_bid, pid)

    def english_run_timeout(self, data=None):
        stages = self.value.get('stage', refresh=True).split(':')
        stages[-1] = 'result'
        self.value.set('stage', ':'.join(stages))

        if stages[-2] == 'english':
            # sql = 'insert into result(exp_id,user_id,round,session,type,win,win_price,strike_price,profit) ' \
            #         'values({},%s,{},{},1,%s,%s,%s,%s)'.format(self.expid, round_, self.sid)
            bidshistory = self.value.get('englishbids', [], True)
        elif stages[-2] == 'englishopen':
            # sql = 'insert into result(exp_id,user_id,round,session,type,win,win_price,strike_price,profit) ' \
            #         'values({},%s,{},{},2,%s,%s,%s,%s)'.format(self.expid, round_, self.sid)
            bidshistory = self.value.get('englishopenbids', [], True)

        winner, pay = None, 0
        if bidshistory:
            winner, pay = bidshistory[-1]['pid'], round(float(bidshistory[-1]['bid']), 1)

        self.value.set('englishresult', {'winner': winner, 'winprice': pay, 'pay': pay})

        stages[0] = 'PlayerSealedEnglish'
        player_stage = ':'.join(stages)

        self.add_delay('englishresult', self.settings['result_time'], self.english_result_timeout)

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            if pid == winner:
                profit = self.value.get('q') - player['cost'] - pay
                player.set('result', {'win': True, 'profit': round(profit, 1)})
                try:
                    pass
                    # self.db.insert(sql, pid, '1', pay, pay, profit)
                except:
                    pass
            else:
                player.set('result', {'win': False, 'profit': 0})
                try:
                    pass
                    # self.db.insert(sql, pid, '0', pay, pay, 0)
                except:
                    pass
            self.RemotePlayer.change_substage(pid)

    def english_result_timeout(self, data=None):
        stages = self.value.get('stage', refresh=True).split(':')
        if stages[-2] == 'english':
            # sql = 'insert into bid(exp_id,user_id,round,session,`group`,value,cost,type,bidding,bid_time)' \
            #       'values({},%s,{},{},{},%s,%s,1,%s,%s)'.format(self.expid, round_, self.sid, self.gid)
            history = self.value.get('englishbids', refresh=True)
        elif stages[-2] == 'englishopen':
            # sql = 'insert into bid(exp_id,user_id,round,session,`group`,value,cost,type,bidding,bid_time)' \
            #       'values({},%s,{},{},{},%s,%s,2,%s,%s)'.format(self.expid, round_, self.sid, self.gid)
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
        # self.db.insertmany(sql, englishbids)

        if stages[-2] == 'englishopen':
            self.end()
            return

        stages = self.value.get('stage', refresh=True).split(':')
        stages[-2], stages[-1] = 'englishopen', 'run'
        self.value.set('stage', ':'.join(stages))
        stages[0] = 'PlayerSealedEnglish'
        player_stage = ':'.join(stages)
        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                continue

            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            self.RemotePlayer.change_substage(pid)

        for pid in self.value['players'].keys():
            if pid.startswith('agent'):
                self.add_delay('englishagentbid'+pid, random.uniform(5, 20), self.english_agent_bid, pid)

    def sealed_agent(self, cost):
        eq = (self.settings['minQ'] + self.settings['maxQ']) / 2.
        return round(eq - cost, 1)

    def sealed_agent_bid(self, data):
        pid = data
        if pid not in self.value['players']:
            return

        cost = self.value['players'][pid]['cost']
        bid = self.sealed_agent(cost)

        self.report_sealed_bid({'pid': data, 'bid': bid, 'username': 'AGENT'})

    @grouphandler.on_redis
    def report_sealed_bid(self, data):
        """triggered when player/agent submit a sealed bid. Finished when everyone had bid.

        :param data:
        :return:
        """
        data['bid'] = round(float(data.get('bid', 0)), 1)
        if data['bid'] <= 0:
            return

        stages = self.value.get('stage', refresh=True).split(':')
        if not (stages[-2] == 'sealed' and stages[-1] == 'run') or 'pid' not in data or \
                        data['pid'] in self.value['sealedbids']:
            return

        data['bidtime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")

        stages[0] = 'PlayerSealedEnglish'
        if data['pid'].startswith('agent'):
            self.value['sealedbids'][data['pid']] = data
        elif data['pid'] in self.value['players']:
            self.value['sealedbids'][data['pid']] = data
            player = utils.exprv.Player(self.redis, self.expid, data['pid'])
            stages[-1] = 'wait'
            player.set('stage', ':'.join(stages))
            # self.publish({'cmd': 'change_substage', 'domain': ':'.join(('player', data['pid']))})
        else:
            return
        self.value.save('sealedbids')

        if len(self.value['sealedbids']) >= len(self.value['players']):
            self.execute_delay('sealedrun')

    def _f(self, x):
        fx = random.gauss(0, 1) * x / 3.
        if fx < 0: fx = -fx
        return min(round(max(.1, fx), 1), x)

    def english_agent_bid(self, pid):
        if pid not in self.value['players']:
            return

        stages = self.value.get('stage', refresh=True).split(':')

        if stages[-2] == 'english':
            bidhistory = self.value.get('englishbids', refresh=True)
            q = 8.
        if stages[-2] == 'englishopen':
            bidhistory = self.value.get('englishopenbids', refresh=True)
            q = self.value.get('q')

        bid = round(random.random(), 1)

        if bidhistory:
            bi = float(bidhistory[-1]['bid'])
            if stages[-2] == 'english':
                s = self.settings['minQ']
                t = self.settings['minC']
                delta = self.settings['maxQ'] - self.settings['minQ']
                if s - t - delta <= bi <= s - t:
                    q = (delta*(s+delta)**2 + s**2*(t+bi) - 2*s**3/3 - (t+delta+bi)**3/3) \
                            / (2*delta**2 - (t+delta+bi-s)**2)
                elif s - t <= bi <= s-t-delta:
                    q = (2*(s+delta)+t+bi) / 3.

            cj = self.value['players'][pid]['cost']
            if bi >= q - cj:
                return

            bid = bi + self._f(q-cj-bi)

        self.report_english_bid({'pid': pid, 'bid': bid, 'username': 'AGENT'})

    @grouphandler.on_redis
    def report_english_bid(self, data):
        stages = self.value.get('stage', refresh=True).split(':')
        if not ((stages[-2] == 'english' or stages[-2] == 'englishopen') and stages[-1] == 'run') or \
                        'pid' not in data:
            return

        data['bid'] = round(float(data.get('bid', 0)), 1)
        if data['bid'] <= 0:
            return
        if stages[-2] == 'english' and self.value['englishbids'] and \
                                        data['bid'] <= self.value['englishbids'][-1]['bid']:
            return
        if stages[-2] == 'englishopen' and self.value['englishopenbids'] and \
                                        data['bid'] <= self.value['englishopenbids'][-1]['bid']:
            return

        data['bidtime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")

        if not(data['pid'].startswith('agent') or data['pid'] in self.value['players']):
            return
        elif data['pid'].startswith('agent'):
            if stages[-2] == 'english':
                self.value['englishbids'].append(data)
                self.value.save('englishbids')
            elif stages[-2] == 'englishopen':
                self.value['englishopenbids'].append(data)
                self.value.save('englishopenbids')
        else:
            if stages[-2] == 'english':
                self.value['englishbids'].append(data)
                self.value.save('englishbids')
            elif stages[-2] == 'englishopen':
                self.value['englishopenbids'].append(data)
                self.value.save('englishopenbids')

            for pid in filter(lambda pid: pid.startswith('agent'), self.value['players'].keys()):
                self.add_delay('englishagentbid'+pid, random.uniform(5, 20), self.english_agent_bid, pid)
        self.add_delay('englishrun', self.settings['english_run_time'], self.english_run_timeout)

        self.RemoteGroup.english_bid_open(data)

    @staticmethod
    def render_info(group):
        group.clear()
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