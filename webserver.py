# -*- coding: utf-8 -*-
"""
这个模块包含：网页服务器启动。
需要手动运行！！！
"""

import os

from redis import client
import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import torndb

from account import *
from treatments import *
from expmanage import *
from expsocket import *
from train import *
from self import *
from help import *


class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="---HUST-ISE---",
            login_url="/",
            autoload=False,
        )

        handlers = [
            (r"/", IndexHandler),

            (r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),

            (r"/account/login", LoginHandler),
            (r"/account/logout", LogoutHandler),
            (r"/account/register", RegisterHandler),
            (r"/account/(\d*)", AccountHandler),

            (r"/self", SelfHandler),

            (r"/treatmentlist", TreatmentListHandler),
            (r"/treatment/(.*)", TreatmentHandler),

            (r"/exp/new", NewExpHandler),
            (r"/exp/newtreatment", NewTreatmentHandler),
            (r"/explist", ExpListHandler),

            (r"/exp/(\d+)", ExpIndexHandler),
            (r"/exp/(\d+)/settings", ExpSettingsHandler),
            (r"/exp/(\d+)/activate", ActivateExpHandler),
            (r"/exp/(\d+)/result", ExpResultHandler),
            (r"/exp/(\d+)/close", CloseExpHandler),

            (r"/exp/(\d+)/socket", ExpOnHandler),
            (r"/exp/(\d+)/train", ExpTrainHandler),

            (r"/exp/(\d+)/websocket", ExpSocketHandler),

            (r"/trainlist", TrainListHandler),
            (r"/train/([a-zA-Z0-9]*)", TrainHandler),
            (r"/train/([a-zA-Z0-9]*)/websocket", TrainSocketHandler),

            (r"/help", HelpHandler),
        ]

        super(Application, self).__init__(handlers, **settings)

        self.redis = client.Redis()
        self.db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')

define("port", default=8000, help="run on the given port", type=int)

tornado.options.parse_command_line()


http_server = tornado.httpserver.HTTPServer(Application())
http_server.listen(options.port)
tornado.ioloop.IOLoop.current().start()
