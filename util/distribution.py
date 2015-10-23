# -*- coding: utf-8 -*-

__all__ = ('Distribution', 'TwoPointDistribution', 'UniformDistribution', 'ExponentialDistribution')

import random


class Distribution(object):

    def __init__(self, code, title, description):
        self.code, self.title, self.description = code, title, description

    def getValue(self):
        return 1


class TwoPointDistribution(Distribution):

    def __init__(self, least=0, most=1, p=.5, **kwargs):
        super(TwoPointDistribution, self).__init__(self.__class__.__name__,
            u'两点分布', u'两点分布')
        
        self.least, self.most, self.p = float(least), float(most), float(p)

    def get_value(self):
        if random.random() > self.p:
            return self.most

        return self.least

    def get_params(self):
        return (
            ('least', u'小值', self.least),
            ('most', u'大值', self.most),
            ('p', u'概率', self.p),
        )


class UniformDistribution(Distribution):

    def __init__(self, least=0, most=1, **kwargs):
        super(UniformDistribution, self).__init__(self.__class__.__name__,
            u'均匀分布', u'均匀分布')
        
        self.least, self.most = float(least), float(most)

    def get_value(self):
        return random.uniform(self.least, self.most)

    def get_params(self):
        return (
            ('least', u'最小值', self.least),
            ('most', u'最大值', self.most),
        )


class ExponentialDistribution(Distribution):

    def __init__(self, lambd=1, **kwargs):
        super(ExponentialDistribution, self).__init__(self.__class__.__name__,
            u'指数分布', u'指数分布')
        
        self.lambd = float(lambd)

    def get_value(self):
        return random.expovariate(self.lambd)

    def get_params(self):
        return (
            ('lambd', '&lambda;', self.lambd),
        )