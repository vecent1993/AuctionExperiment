# -*- coding: utf-8 -*-
import random
import datetime

from tornado.template import Template

import utils.exprv
import components.grouphandler as grouphandler
import components.playerhandler as playerhandler


_qs = ((5, 10), (10, 10), (5, 5), (10, 5))


class GroupInfoAcquiSequence(grouphandler.GroupHandler):
    def __init__(self, exp, sid, gid):
        super(GroupInfoAcquiSequence, self).__init__(exp)

        self.sid, self.gid = map(str, (sid, gid))
        self.value = utils.exprv.Group(self.redis, self.expid, self.sid, self.gid)
        self.settings = self.value.get('settings', dict(), True)
        self.RemoteGroup = grouphandler.RemoteGroup(self.expid, self.sid, self.gid, self.redis.publish)

        self.init_tasks()

        stages = self.value.get('stage', refresh=True).split(':')
        if len(stages) == 1:
            self.start()
        elif stages[1] == 'info':
            if stages[2] == 'run':
                self.start()
                self.add_delay('inforun', 180, self.info_run_timeout)
            else:
                self.add_delay('inforesult', 10, self.info_result_timeout)
        elif stages[1] == 'a':
            if stages[2] == 'run':
                self.add_delay('arun', 180, self.a_run_timeout)
            else:
                self.add_delay('aresult', 10, self.a_result_timeout)
        elif stages[1] == 'b':
            if stages[2] == 'run':
                self.add_delay('brun', 180, self.b_run_timeout)
            else:
                self.add_delay('bresult', 10, self.b_result_timeout)

    def start(self, data=None):
        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'info', 'run')
        self.value.set('stage', group_stage)
        self.value.set('infobids', {})
        self.value.set('abids', {})
        self.value.set('bbids', {})
        self.value.set('results', {})
        self.value.set('aq', {})
        self.value.set('bq', {})
        self.value.set('round_', int(self.value['stagecode'].split(':')[0]))

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'info', 'run')
        prob = float(self.settings['prob'])
        if 'fixed' in self.settings:
            for pid in self.value['players'].keys():
                temp = _qs[int(pid) % len(_qs)]
                self.value['aq'][pid] = temp[0]
                self.value['bq'][pid] = temp[1]
        else:
            for pid in self.value['players'].keys():
                aq = 10 if random.uniform(0, 1) <= prob else 5
                bq = 10 if random.uniform(0, 1) <= prob else 5
                self.value['aq'][pid] = aq
                self.value['bq'][pid] = bq
        self.value.save('aq')
        self.value.save('bq')

        self.add_delay('inforun', 180, self.info_run_timeout)
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                self.add_delay('infoagentbid'+pid, random.uniform(5, 30), self.info_agent_bid, pid)
            else:
                player = utils.exprv.Player(self.redis, self.expid, pid)
                player.set('stage', player_stage)
                self.RemotePlayer.change_substage(pid)

        self.init_database()

    def init_database(self):
        round_ = self.value['round_']
        for pid in self.value['players'].keys():
            aq, bq = self.value['aq'][pid], self.value['bq'][pid]
            self.db.execute('delete from info_sequence where exp_id=%s and user_id=%s and round=%s and '
                            'session=%s and `group`=%s', self.expid, pid, round_, self.sid, self.gid)
            self.db.insert('insert into info_sequence(exp_id, user_id, round, session, `group`, aq, bq) '
                           'values(%s,%s,%s,%s,%s,%s,%s)', self.expid, pid, round_, self.sid, self.gid, aq, bq)
            self.db.execute('delete from result_info_sequence where exp_id=%s and user_id=%s and round=%s',
                            self.expid, pid, round_)

    def second_sealed_result(self, bidshistory):
        winner, winprice, pay = None, 0, 0
        history = bidshistory.values()
        random.shuffle(history)
        if bidshistory:
            win = sorted(history, key=lambda a: a['bid'], reverse=True)
            winner, winprice = win[0]['pid'], win[0]['bid']
            if len(win) > 1:
                pay = win[1]['bid']
        return {'winner': winner, 'winprice': winprice, 'pay': pay}

    def info_run_timeout(self, data=None):
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                self.execute_delay('infoagentbid'+pid)

        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'info', 'result')
        self.value.set('stage', group_stage)

        bidshistory = self.value.get('infobids', {}, True)
        result = self.second_sealed_result(bidshistory)

        self.value['results']['info'] = result
        self.value.save('results')

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'info', 'result')

        self.add_delay('inforesult', 10, self.info_result_timeout)
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                continue

            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            self.RemotePlayer.change_substage(pid)

        self.save_result('info', result)

    def save_result(self, main_stage, result):
        if not result:
            return
        round_ = self.value['round_']
        sql_info_sequence = 'update info_sequence set {}_bid=%s where exp_id=%s and user_id=%s and ' \
                            'round=%s and session=%s and `group`=%s'.format(main_stage)
        for pid in self.value['players'].keys():
            bid = self.value['%sbids' % main_stage][pid]['bid'] if pid in self.value['%sbids' % main_stage] else 0
            self.db.update(sql_info_sequence, bid, self.expid, pid, round_, self.sid, self.gid)

            if int(pid) <= 5:
                continue
            pay, price = result['pay'], result['winprice']
            if pid == result['winner']:
                win = 1
                profit = -pay if main_stage == 'info' else self.value['%sq' % main_stage][pid] - pay
            else:
                win, profit = 0, 0

            if main_stage == 'info':
                t = 0
            else:
                t = 1 if main_stage == 'a' else 2
            self.db.insert('insert into result_info_sequence values(%s,%s,%s,%s,%s,%s,%s,%s)',
                           self.expid, pid, round_, t, win, price, pay, profit)

    def info_result_timeout(self, data=None):
        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'a', 'run')
        self.value.set('stage', group_stage)

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'a', 'run')

        self.add_delay('arun', 180, self.a_run_timeout)
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                self.add_delay('aagentbid'+pid, random.uniform(5, 30), self.a_agent_bid, pid)
            else:
                player = utils.exprv.Player(self.redis, self.expid, pid)
                player.set('stage', player_stage)
                self.RemotePlayer.change_substage(pid)

    def a_run_timeout(self, data=None):
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                self.execute_delay('aagentbid'+pid)

        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'a', 'result')
        self.value.set('stage', group_stage)

        bidshistory = self.value.get('abids', {}, True)
        result = self.second_sealed_result(bidshistory)

        self.value['results']['a'] = result
        self.value.save('results')

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'a', 'result')

        self.add_delay('aresult', 10, self.a_result_timeout)
        for pid in self.value['players'].keys():
            if int(pid) <= 5:
                continue
            player = utils.exprv.Player(self.redis, self.expid, pid)
            if pid == result['winner']:
                player.set('stage', '%s:%s' % ('PlayerInfoAcquiSequence', 'end'))
            else:
                player.set('stage', player_stage)
            self.RemotePlayer.change_substage(pid)

        self.save_result('a', result)

    def a_result_timeout(self, data=None):
        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'b', 'run')
        self.value.set('stage', group_stage)

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'b', 'run')

        self.add_delay('brun', 180, self.b_run_timeout)
        for pid in self.value['players'].keys():
            if pid == self.value['results'].get('a', {}).get('winner'):
                continue
            elif int(pid) <= 5:
                self.add_delay('bagentbid'+pid, random.uniform(5, 30), self.b_agent_bid, pid)
            else:
                player = utils.exprv.Player(self.redis, self.expid, pid)
                player.set('stage', player_stage)
                self.RemotePlayer.change_substage(pid)

    def b_run_timeout(self, data=None):
        for pid in self.value['players'].keys():
            if int(pid) <= 5 and pid != self.value['results'].get('a', {}).get('winner'):
                self.execute_delay('bagentbid'+pid)

        group_stage = '%s:%s:%s' % ('GroupInfoAcquiSequence', 'b', 'result')
        self.value.set('stage', group_stage)

        bidshistory = self.value.get('bbids', {}, True)
        result = self.second_sealed_result(bidshistory)

        self.value['results']['b'] = result
        self.value.save('results')

        player_stage = '%s:%s:%s' % ('PlayerInfoAcquiSequence', 'b', 'result')

        self.add_delay('bresult', 10, self.b_result_timeout)
        for pid in self.value['players'].keys():
            if int(pid) <= 5 or pid == self.value['results'].get('a', {}).get('winner'):
                continue
            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.set('stage', player_stage)
            self.RemotePlayer.change_substage(pid)

        self.save_result('b', result)

    def b_result_timeout(self, data=None):
        self.end()

    def info_agent_bid(self, pid):
        if pid not in self.value['players']:
            return
        infoq = round(random.uniform(0, 0.5), 1)
        self.report_sealed_bid({'pid': pid, 'bid': infoq, 'username': 'AGENT'})

    def a_agent_bid(self, pid):
        if pid not in self.value['players']:
            return
        aq = self.value['aq'][pid]
        self.report_sealed_bid({'pid': pid, 'bid': aq, 'username': 'AGENT'})

    def b_agent_bid(self, pid):
        if pid not in self.value['players']:
            return
        bq = self.value['bq'][pid]
        self.report_sealed_bid({'pid': pid, 'bid': bq, 'username': 'AGENT'})

    @grouphandler.on_redis
    def report_sealed_bid(self, data):
        data['bid'] = round(float(data.get('bid', 0)), 1)
        if data['bid'] < 0:
            return

        data['bidtime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        stages = self.value['stage'].split(':')
        if stages[-1] != 'run':
            return

        tmp = '%sbids' % stages[1]
        if int(data['pid']) <= 5:
            self.value[tmp][data['pid']] = data
        elif data['pid'] in self.value['players']:
            self.value[tmp][data['pid']] = data
            player = utils.exprv.Player(self.redis, self.expid, data['pid'])
            player.set('stage', '%s:%s:%s' % ('PlayerInfoAcquiSequence', stages[1], 'wait'))
            self.RemotePlayer.change_substage(data['pid'])
        else:
            return
        self.value.save(tmp)

        if stages[1] == 'b':
            if len(self.value[tmp]) >= len(self.value['players']) - 1:
                self.execute_delay('%srun' % stages[1])
        else:
            if len(self.value[tmp]) >= len(self.value['players']):
                self.execute_delay('%srun' % stages[1])

    @staticmethod
    def render_info(group):
        group.clear()
        return Template('''
            当前阶段：<br/>
                {{ group['stage'] }}<br/>
            <table class="table">
                <thead>
                    {% set pids = group['players'].keys() %}
                    <tr>
                        <th>#</th>
                        {% for p in pids %}
                        <th>{{ p }}</th>
                        {% end %}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>用户名</td>
                        {% for p in pids %}
                        <td>{{ group['players'][p]['username'] }}</td>
                        {% end %}
                    </tr>
                    <tr>
                        <td>a价值</td>
                        {% for p in pids %}
                        <td>{{ group.get('aq', {}).get(p) }}</td>
                        {% end %}
                    </tr>
                    <tr>
                        <td>b价值</td>
                        {% for p in pids %}
                        <td>{{ group.get('bq', {}).get(p) }}</td>
                        {% end %}
                    </tr>
                    {% if group.get('infobids', {}, refresh=True) %}
                    <tr>
                        <td>信息报价</td>
                        {% for p in pids %}
                        <td>{{ group.get('infobids', {}).get(p, {}).get('bid', '') }}</td>
                        {% end %}
                    </tr>
                    {% end %}
                    {% if group.get('abids', {}, refresh=True) %}
                    <tr>
                        <td>a报价</td>
                        {% for p in pids %}
                        <td>{{ group.get('abids', {}).get(p, {}).get('bid', '') }}</td>
                        {% end %}
                    </tr>
                    {% end %}
                    {% if group.get('bbids', {}, refresh=True) %}
                    <tr>
                        <td>b报价</td>
                        {% for p in pids %}
                        <td>{{ group.get('bbids', {}).get(p, {}).get('bid', '') }}</td>
                        {% end %}
                    </tr>
                    {% end %}
                </tbody>
            </table>
        ''').generate(group=group)