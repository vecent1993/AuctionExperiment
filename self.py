# -*- coding: utf-8 -*-
import tornado.web

from util.web import BaseHandler


class SelfHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        exp_established = self.db.query('select exp_id, exp_title from exp where host_id=%s',
                                        self.current_user['user_id'])
        exp_participated = self.db.query('select exp.exp_id, exp.exp_title from player join exp '
                                         'on player.exp_id = exp.exp_id where player.user_id=%s',
                                         self.current_user['user_id'])
        self.render('self.html', exp_established=exp_established, exp_participated=exp_participated)