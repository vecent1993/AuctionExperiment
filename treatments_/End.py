# -*- coding: utf-8 -*-
from treatment import Treatment


class End(Treatment):
    def __init__(self, settings=None):
        super(End, self).__init__(End.__name__, '实验结束', '告知实验结束并跳转到收益（结果分析）页面', settings)
