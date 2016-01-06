# -*- coding: utf-8 -*-
import traceback
import time
import json

from util.wshandler import WSMessageHandler, on_ws, on_redis


class TrainHandler(WSMessageHandler):
    def __init__(self, env):
        super(TrainHandler, self).__init__(env)

        self.player = env.player
        self.exp = self.env.exp

    @on_ws
    def heartbeat(self, data):
        pass
