# -*- coding: utf-8 -*-
import json

import handler

# treatments = [
#     {u'code': u'Intro', u'id': 0},
#     {u'code': u'Sessions', u'id': 1, u'sessions':
#         [{u'des': u'', u'id': 0, u'treatments':
#             [
#                 {u'code': u'Repeat', u'id': 0, u'repeat': u'3', u'treatments':
#                     [{u'code': u'EXP2', u'id': 0}, {u'code': u'EXP2', u'id': 1}]
#                 },
#              ]
#           }]
#      },
#     {u'code': u'End', u'id': 2}
# ]
#
# print treatments

import random

def auto_shuffle():
    pids = filter(lambda pid: not pid.startswith('agent'), map(str, range(1)))
    random.shuffle(pids)

    sessions = [{'players': [], 'groups':[]}, ]
    for i in range(len(pids) / 3):
        sessions[0]['groups'].append(pids[i:i+3])
    players = pids[len(pids) / 3 * 3:]
    print sessions
    print players

auto_shuffle()