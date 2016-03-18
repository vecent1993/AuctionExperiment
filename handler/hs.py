# -*- coding: utf-8 -*-

from util.loader import MultiDirLoader

import End.end
import GroupUtil.grouputil
import Intro.intro
import Init.init
import AutoShuffle.autoshuffle
import Monitor.monitor
import SealedEnglish.sealedenglish
import Shuffle.shuffle
import thandler.english
import thandler.englishopen
import thandler.sealed
import treatment

template_dirs = (
    'handler/thandler/template',
    'handler/End/template',
    'handler/GroupUtil/template',
    'handler/Intro/template',
    'handler/Monitor/template',
    'handler/SealedEnglish/template',
    'handler/Shuffle/template',
    'handler/AutoShuffle/template',
    'handler/Init/template',
)

loader = MultiDirLoader(template_dirs)

thandlers = dict(
    English=thandler.english.English,
    EnglishOpen=thandler.englishopen.EnglishOpen,
    Sealed=thandler.sealed.Sealed,
)

handlers = dict(
    End=End.end.End,
    Monitor=Monitor.monitor.Monitor,
    SealedEnglish=SealedEnglish.sealedenglish.SealedEnglish,
    Shuffle=Shuffle.shuffle.Shuffle,
    AutoHuffle=AutoShuffle.autoshuffle.AutoShuffle,
    Intro=Intro.intro.Intro,
    Init=Init.init.Init,

    GroupReady=GroupUtil.grouputil.GroupReady,
    GroupEnd=GroupUtil.grouputil.GroupEnd,
    Sessions=treatment.Sessions,
    Repeat=treatment.Repeat
)


treatments = []
for hey, value in handlers.items():
    if issubclass(value, treatment.Treatment):
        treatments.append(value)