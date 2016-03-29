# -*- coding: utf-8 -*-
"""
这个模块包含：所有组件和处理服务的声明配置。
"""

from tornado.template import Loader

import End.end
import Intro.intro
import Init.init
import Wait.wait
import AutoShuffle.autoshuffle
import Monitor.monitor
import SealedEnglish.sealedenglish
import InfoAcquiSequence.infoacquisequence
import Shuffle.shuffle
import Report.report
import thandler.privatesecondsealed
import treatment

loader = Loader('components')


handlers = dict(
    PlayerEnd=End.end.PlayerEnd,
    HostEnd=End.end.HostEnd,

    HostMonitor=Monitor.monitor.HostMonitor,
    SessionHostMonitor=Monitor.monitor.SessionHostMonitor,

    PlayerSealedEnglish=SealedEnglish.sealedenglish.PlayerSealedEnglish,
    GroupSealedEnglish=SealedEnglish.sealedenglish.GroupSealedEnglish,

    PlayerInfoAcquiSequence=InfoAcquiSequence.infoacquisequence.PlayerInfoAcquiSequence,
    GroupInfoAcquiSequence=InfoAcquiSequence.infoacquisequence.GroupInfoAcquiSequence,

    HostShuffle=Shuffle.shuffle.HostShuffle,
    AutoHostShuffle=AutoShuffle.autoshuffle.AutoHostShuffle,

    PlayerIntro=Intro.intro.PlayerIntro,

    PlayerInit=Init.init.PlayerInit,
    HostInit=Init.init.HostInit,

    PlayerSessionWait=Wait.wait.PlayerSessionWait,
    PlayerShuffleWait=Wait.wait.PlayerShuffleWait,
    PlayerGroupWait=Wait.wait.PlayerGroupWait,

    HostReport=Report.report.HostReport,

    PlayerTrainPrivateSecondSealed=thandler.privatesecondsealed.PlayerTrainPrivateSecondSealed,
)


treatments = dict(
    Intro=Intro.intro.Intro,
    End=End.end.End,

    Sessions=treatment.Sessions,
    Repeat=treatment.Repeat,

    # SealedEnglish=SealedEnglish.sealedenglish.SealedEnglish,
    InfoAcquiSequence=InfoAcquiSequence.infoacquisequence.InfoAcquiSequence,

    TrainPrivateSecondSealed=thandler.privatesecondsealed.TrainPrivateSecondSealed,
)