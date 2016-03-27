# -*- coding: utf-8 -*-

import components.treatment
from ph import PlayerSealedEnglish
from gh import GroupSealedEnglish


class SealedEnglish(components.treatment.PlayerGroup):
    title = '公开-密封拍卖对比'
    description = '...'

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        return 'PlayerSealedEnglish', 'SessionHostMonitor', 'GroupSealedEnglish', settings