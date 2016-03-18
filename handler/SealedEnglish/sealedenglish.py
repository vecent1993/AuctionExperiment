# -*- coding: utf-8 -*-

import handler.treatment
from ph import PlayerSealedEnglish
from gh import GroupSealedEnglish


class SealedEnglish(handler.treatment.Treatment):
    gh = GroupSealedEnglish
    ph = PlayerSealedEnglish

    title = '公开-密封拍卖对比'
    description = '...'