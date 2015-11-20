# -*- coding: utf-8 -*-
import traceback
import time
import json

from util.pool import Player
from util.core import RedisExp
from util.redissub import RedisSub
from util.wshandler import WSMessageHandler, onWs, onRedis
from .. import getHandler
from treatments_ import getTreatment


class TrainHandler(WSMessageHandler):
    def __init__(self, env):
        super(TrainHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

    @onWs
    def heartbeat(self, data):
        pass
