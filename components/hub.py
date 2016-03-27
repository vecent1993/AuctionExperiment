# -*- coding: utf-8 -*-

from tornado.template import Loader

# from util.loader import MultiDirLoader

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

loader = Loader('handler')


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
    PlayerWait=Wait.wait.PlayerWait,
    HostReport=Report.report.HostReport,

    PlayerTrainPrivateSecondSealed=thandler.privatesecondsealed.PlayerTrainPrivateSecondSealed,
)


treatments = dict(
    Intro=Intro.intro.Intro,
    End=End.end.End,

    Sessions=treatment.Sessions,
    Repeat=treatment.Repeat,

    SealedEnglish=SealedEnglish.sealedenglish.SealedEnglish,
    InfoAcquiSequence=InfoAcquiSequence.infoacquisequence.InfoAcquiSequence,

    TrainPrivateSecondSealed=thandler.privatesecondsealed.TrainPrivateSecondSealed,
)