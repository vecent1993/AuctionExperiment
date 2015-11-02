# -*- coding: utf-8 -*-
from redis import client

from handler.playerhandler_.playerhandler import PlayerHandler

r = client.Redis()
PlayerHandler.nextStage(r, '7', '8')