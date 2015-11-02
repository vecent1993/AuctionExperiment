# -*- coding: utf-8 -*-
from treatment import Treatment


class Intro(Treatment):
    def __init__(self, settings=None):
        super(Intro, self).__init__(Intro.__name__, '实验说明', '详细地告知被试实验流程', settings)