# -*- coding: utf-8 -*-

from treatment import SingleItemTreatment


class BaseExp(object):
    def __init__(self, code, title, description, introduction):
        self.code, self.title, self.description, self.introduction = code, title, description, introduction

    def new_treatment(self):
        pass


class SingleItemEnglish(BaseExp):
    def __init__(self):
        super(SingleItemEnglish, self).__init__(self.__class__.__name__, u'单物品英式升价拍卖',
             u'在拍卖过程中，拍卖标的物的竞价按照竞价阶梯由低至高、依次递增，当到达拍卖截止时间时，出价最高者成为竞买的赢家（即由竞买人变成买受人）',
             u'在拍卖过程中，拍卖标的物的竞价按照竞价阶梯由低至高、依次递增，当到达拍卖截止时间时，出价最高者成为竞买的赢家（即由竞买人变成买受人）')

    def new_treatment(self, settings=None):
        t = SingleItemTreatment(settings)
        t.code = self.code
        t.title = self.title
        return t


class SingleItemDutch(BaseExp):
    def __init__(self):
        super(SingleItemDutch, self).__init__(self.__class__.__name__, u'单物品荷式升价拍卖',
             u'拍卖标的的竞价由高到低依次递减直到第一个竞买人应价（达到或超过底价）时击槌成交的一种拍卖。',
             u'拍卖标的的竞价由高到低依次递减直到第一个竞买人应价（达到或超过底价）时击槌成交的一种拍卖。')

    def new_treatment(self, settings=None):
        t = SingleItemTreatment(settings)
        t.code = self.code
        t.title = self.title
        return t


class SingleItemFirstPriceSealed(BaseExp):
    def __init__(self):
        super(SingleItemFirstPriceSealed, self).__init__(self.__class__.__name__, u'单物品一价密封拍卖',
             u'每一个投标人都将出价记录在一张纸上，并密封在一个信封中，最终所有的信封集中在一起，出价最高的人将获得商品，如果存在保留价格（即出卖者的底价），并且所有出价都低于这个保留价格，则商品不出售给任何人。',
             u'每一个投标人都将出价记录在一张纸上，并密封在一个信封中，最终所有的信封集中在一起，出价最高的人将获得商品，如果存在保留价格（即出卖者的底价），并且所有出价都低于这个保留价格，则商品不出售给任何人。',)

    def new_treatment(self, settings=None):
        t = SingleItemTreatment(settings)
        t.code = self.code
        t.title = self.title
        return t


class SingleItemSecondPriceSealed(BaseExp):
    def __init__(self):
        super(SingleItemSecondPriceSealed, self).__init__(self.__class__.__name__, u'单物品二价密封拍卖',
             u'每个投标者提交密封的交易价格，出价最高者赢得商品，但交易却以所有出价中的第二高价进行。',
             u'每个投标者提交密封的交易价格，出价最高者赢得商品，但交易却以所有出价中的第二高价进行。',)

    def new_treatment(self, settings=None):
        t = SingleItemTreatment(settings)
        t.code = self.code
        t.title = self.title
        return t

baseexp_list = []
baseexp_list.append(SingleItemEnglish())
baseexp_list.append(SingleItemDutch())
baseexp_list.append(SingleItemFirstPriceSealed())
baseexp_list.append(SingleItemSecondPriceSealed())