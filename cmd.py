# -*- coding: utf-8 -*-
import json
import random
import sys

import components
import components.hub


def auto_shuffle():
    pids = filter(lambda pid: not pid.startswith('agent'), map(str, range(1)))
    random.shuffle(pids)

    sessions = [{'players': [], 'groups':[]}, ]
    for i in range(len(pids) / 3):
        sessions[0]['groups'].append(pids[i:i+3])
    players = pids[len(pids) / 3 * 3:]
    print sessions
    print players

# auto_shuffle()

def _next_stage_code(settings, stage_code=None, round_=0):
    if stage_code is None:
        stage_code = '0'

    stage_code_split = stage_code.split(':')
    cur = int(stage_code_split[0].split('-')[0])
    if cur >= len(settings):
        print 'experiment finished'
        sys.exit()
    treatment_code = settings[cur]['code']
    treatment = components.hub.treatments[treatment_code]
    new_stage_code = treatment.next_stage_code(settings[cur], stage_code, round_)
    if not new_stage_code:
        return _next_stage_code(settings, str(cur+1), round_)
    else:
        return new_stage_code


def _get_stage(settings, stage_code, cur_stage=None):
    stage_code_split = stage_code.split(':')
    cur = int(stage_code_split[0].split('-')[0])
    treatment_code = settings[cur]['code']
    treatment = components.hub.treatments[treatment_code]
    return treatment.get_stage(settings[cur], stage_code, cur_stage)

def next_stage_code(settings, stage_code=None):
    if not stage_code:
        new_stage_code, round_ = _next_stage_code(settings)
    else:
        splits = stage_code.split(':')
        new_stage_code, round_ = _next_stage_code(settings, ':'.join(splits[1:]), int(splits[0]))
    return '%s:%s' % (round_, new_stage_code)

def get_stage(settings, stage_code, cur_stage=None):
    splits = stage_code.split(':')
    return _get_stage(settings, ':'.join(splits[1:]), cur_stage)

def test_next_stage():
    # test Sessions
    treatments = [
        {u'code': u'Intro', u'id': 0},
        {u'code': u'Sessions', u'id': 1, u'sessions':
            [{u'des': u'', u'id': 0, u'treatments':
                [
                    {u'code': u'SealedEnglish', u'id': 0},
                    {u'code': u'SealedEnglish', u'id': 0},
                 ]
              }]
         },
        {u'code': u'End', u'id': 2}
    ]

    # test Repeat
    # treatments = [
    #     {u'code': u'Intro', u'id': 0},
    #     {u'code': u'Repeat', u'id': 0, u'repeat': u'3', u'treatments':
    #         [
    #             {u'code': u'SealedEnglish', u'id': 0}
    #          ]
    #     },
    #     {u'code': u'Repeat', u'id': 0, u'repeat': u'2', u'treatments':
    #         [
    #             {u'code': u'SealedEnglish', u'id': 0}
    #          ]
    #     },
    #     {u'code': u'End', u'id': 2}
    # ]


    # test Sessions & Repeat
    treatments = [
        {u'code': u'Intro', u'id': 0},
        {u'code': u'Sessions', u'id': 1, u'sessions':
            [{u'des': u'', u'id': 0, u'treatments':
                [{u'code': u'Repeat', u'id': 0, u'repeat': u'3', u'treatments':
                    [
                        {u'code': u'SealedEnglish', u'id': 0},
                    ]
                  },
                 {u'code': u'Repeat', u'id': 0, u'repeat': u'2', u'shuffle': u'on', u'treatments':
                    [
                        {u'code': u'SealedEnglish', u'id': 0},
                    ]
                  }]
              }]
         },
        {u'code': u'End', u'id': 2}
    ]
    sc = None
    s = None
    for i in range(20):
        sc = next_stage_code(treatments, sc)
        s = get_stage(treatments, sc, s)
        print sc, s


# test_next_stage()


def test_redis_value():
    from utils.redisvalue import RedisValue, RemoteRedis
    import redis
    import time

    rc = redis.Redis()
    rr = RemoteRedis(rc.publish)

    a = RedisValue(rc, 'aaa')
    time.sleep(5)

    rr.refresh('aaa')

    time.sleep(5)


class AutoShuffle(object):
    def __init__(self):
        self.settings = dict(sessions=[dict(ratio=100, gplayers=2), dict(ratio=50, gplayers=3)])

    def auto_shuffle(self):
        # pids = filter(lambda pid: not pid.startswith('agent'), self.pool.get('pool', [], True))
        pids = filter(lambda pid: not pid.startswith('agent'), map(str, range(10)))
        random.shuffle(pids)

        players, sessions = self.auto_session_shuffle(pids)
        print players
        print sessions
        # self.pool.set('players', players)
        # self.pool.set('sessions', sessions)
        # self.RemotePool.shuffle()

    def auto_session_shuffle(self, pids):
        ratios = map(lambda s: int(s['ratio']), self.settings['sessions'])
        gplayers = map(lambda s: int(s['gplayers']), self.settings['sessions'])
        ratios_sum = sum(ratios)
        ratios = map(lambda r: int(float(r) / ratios_sum * len(pids)), ratios)
        sessions = []
        pi = 0
        for i, r in enumerate(ratios):
            sessions.append(self.auto_group_shuffle(pids[pi:pi+r], group_size=gplayers[i]))
            pi += r
        players = pids[sum(ratios):]
        return players, sessions

    def auto_group_shuffle(self, pids, group_size):
        session = {'players': [], 'groups':[]}
        for i in range(len(pids) / group_size):
            session['groups'].append(pids[i * group_size:(i + 1) * group_size])
        session['players'] = pids[len(pids) / group_size * group_size:]
        return session


# a = AutoShuffle()
# a.auto_shuffle()

import torndb

# db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')
# expid = 8
# print db.query("""
#             select user_email, round, GROUP_CONCAT(profit order by t) as profits from result_info_sequence join user using(user_id)
#             where exp_id=%s group by user_id, round;
#         """, expid)
