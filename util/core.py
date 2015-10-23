# -*- coding: utf-8 -*-

import baseexp
from redisvalue import RedisValue


class Session(object):
    def __init__(self, settings=None):
        self.settings = {'description': u'实验组', 'ratio': 100, 'treatments': []}
        if isinstance(settings, dict):
            self.settings.update(settings)

        self.description = self.settings['description']
        self.ratio = float(self.settings['ratio'])
        self.treatments = []
        for treatment in self.settings['treatments']:
            base_exp = filter(lambda a: a.code == treatment['code'], baseexp.baseexp_list)[0]
            self.add_treatment(base_exp.new_treatment(treatment))
        self.groups = []

    def add_treatment(self, treatment):
        self.treatments.append(treatment)


class Experiment(object):
    def __init__(self, settings=None):
        self.settings = {'id': 0, 'host': '', 'title': u'单物品一价密封拍卖', 'description': u'每一个投标人都将出价记录在一张纸上，并密封在一个信封中，最终所有的信封集中在一起，出价最高的人将获得商品，如果存在保留价格（即出卖者的底价），并且所有出价都低于这个保留价格，则商品不出售给任何人。',
                         'introduction': u'每一个投标人都将出价记录在一张纸上，并密封在一个信封中，最终所有的信封集中在一起，出价最高的人将获得商品，如果存在保留价格（即出卖者的底价），并且所有出价都低于这个保留价格，则商品不出售给任何人。',
                         'sessions': [
                             {'id': 0, 'description': u'实验组', 'ratio': 100, 'treatments': []},
                             ]
                         }
        if isinstance(settings, dict):
            self.settings.update(settings)

        self.id = self.settings['id']
        self.title = self.settings['title']
        self.description = self.settings['description']
        self.introduction = self.settings['introduction']
        self.host = self.settings['host']
        self.sessions = []
        for session in self.settings['sessions']:
            self.add_session(Session(session))

    def add_session(self, session):
        self.sessions.append(session)


class RedisExp(RedisValue):
    def __init__(self, connection, exp_id):
        self.expid = str(exp_id)
        self.key = ":".join(('exp', self.expid))
        super(RedisExp, self).__init__(connection, self.key)