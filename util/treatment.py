# -*- coding: utf-8 -*-
from item import Item

class Treatment(object):
    def __init__(self, code, title, settings):
        self.code, self.title, self.settings = code, title, settings


class SingleItemTreatment(Treatment):
    def __init__(self, settings=None):
        _settings = { 'groupsize': 3, 'code': 'SingleItem',
                         'items': [
                             {'id': 0, 'duration': 30, 'num': 1, 'distribution': 'TwoPointDistribution', 'title': u'提拉米苏',
                              'description': u'提拉米苏（Tiramisu）是一种带咖啡酒味儿的意大利甜点，由马斯卡邦尼奶酪、意式咖啡、手指饼干与咖啡酒/朗姆酒制成的。',
                              'images': [
                                  {'id': 0, 'url': 'http://img1.cache.netease.com/catchpic/B/B5/B5A44ADCC03AA55693322015F967C0A3.jpg'},
                                  ],
                              'distributions': (
                                  {'id': '0', 'code': 'TwoPointDistribution', 'least': 0, 'most': 1, 'p': .5},
                                  {'id': '1', 'code': 'UniformDistribution', 'least': 0, 'most': 1},
                                  {'id': '2', 'code': 'ExponentialDistribution', 'lambd': 1},
                              )},
                         ]
                         }
        if isinstance(settings, dict):
            _settings.update(settings)

        super(SingleItemTreatment, self).__init__(_settings['code'], u'单一物品', _settings)
        self.groupsize = self.settings['groupsize']
        self.item = Item(self.settings['items'][0])
        self.template = 'treatment/singleitem.html'