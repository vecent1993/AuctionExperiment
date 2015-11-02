# -*- coding: utf-8 -*-
from treatment import Treatment


class SealedEnglish(Treatment):
    def __init__(self, settings=None):
        super(SealedEnglish, self).__init__(SealedEnglish.__name__, '公开-密封拍卖对比', '。。。', settings)

