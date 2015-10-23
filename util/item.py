# -*- coding: utf-8 -*-

from distribution import *


class Item(object):
    def __init__(self, settings=None):
        self.settings = {
            'id': 0, 'duration': 30, 'num': 1, 'distribution': 'TwoPointDistribution', 'title': u'提拉米苏',
            'description': u'提拉米苏（Tiramisu）是一种带咖啡酒味儿的意大利甜点，由马斯卡邦尼奶酪、意式咖啡、手指饼干与咖啡酒/朗姆酒制成的。',
            'images': [
                {'id': 0, 'url': 'http://img1.cache.netease.com/catchpic/B/B5/B5A44ADCC03AA55693322015F967C0A3.jpg'},
                ],
            'distributions': (
                    {'id': '0', 'code': 'TwoPointDistribution', 'least': 0, 'most': 1, 'p': .5},
                    {'id': '1', 'code': 'UniformDistribution', 'least': 0, 'most': 1},
                    {'id': '2', 'code': 'ExponentialDistribution', 'lambd': 1},
                ),
            }
        if isinstance(settings, dict):
            self.settings.update(settings)

        self.duration = self.settings['duration']
        self.title = self.settings['title']
        self.num = self.settings['num']
        self.description = self.settings['description']
        self.images = []
        for image in self.settings['images']:
            self.images.append(image['url'])
        self.distributions = []
        for distribution in self.settings['distributions']:
            self.distributions.append(eval(distribution['code'] + '(**distribution)'))
        self.distribution = filter(lambda a: a.code == self.settings['distribution'], self.distributions)[0]