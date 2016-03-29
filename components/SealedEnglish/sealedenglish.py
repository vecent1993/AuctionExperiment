# -*- coding: utf-8 -*-

import components.treatment
from ph import PlayerSealedEnglish
from gh import GroupSealedEnglish


class SealedEnglish(components.treatment.PlayerGroup):
    title = '公开-密封拍卖对比'
    description = '...'

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        stage_code_split = stage_code.split('-')
        if stage_code_split[1] == '0':
            return 'PlayerWait', 'SessionHostMonitor', None, settings

        return 'PlayerSealedEnglish', 'SessionHostMonitor', 'GroupSealedEnglish', settings