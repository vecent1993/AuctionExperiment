# -*- coding: utf-8 -*-

import traceback
import json
import datetime

import tornado.web

from util.web import BaseHandler, hostAuthenticated, userAuthenticated, expHostAuthenticated
from util.core import *
from util.pool import Player, Pool
from treatments_ import getTreatment


class NewExpHandler(BaseHandler):
    @hostAuthenticated
    def get(self):
        settings=dict(title='', des='', intro='', treatments=[])
        self.render('expmanage/newexp.html', settings=settings, treatments=None)

    @hostAuthenticated
    def post(self):
        try:
            settings = json.loads(self.get_argument('data'))
            expid = self.db.insert('insert into exp(exp_title,exp_des,exp_intro,exp_settings,'
                                   'host_id,exp_setuptime) values (%s,%s,%s,%s,%s,%s)',
                                   settings['title'], settings['des'], settings['intro'],
                                   json.dumps(settings), self.current_user['user_id'],
                                   datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
                            )
            self.write(json.dumps(dict(redirect='/exp/' + str(expid))))
        except:
            self.write(json.dumps(dict(error=str(traceback.format_exc()))))


class ExpIndexHandler(BaseHandler):
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        self.render('expmanage/expindex.html', exp=exp)


class ExpSettingsHandler(BaseHandler):
    @expHostAuthenticated
    def get(self, expid):
        settings = json.loads(self.exp['exp_settings'])
        self.render('expmanage/expsettings.html', exp=self.exp, settings=settings,
                    treatments=None, getTreatment=getTreatment)

    @expHostAuthenticated
    def post(self, expid):
        try:
            settings = json.loads(self.get_argument('data'))
            self.db.update('update exp set exp_title=%s, exp_des=%s, exp_intro=%s, '
                           'exp_settings=%s where exp_id=%s', settings['title'], settings['des'],
                            settings['intro'], json.dumps(settings), expid)

            exp = RedisExp(self.redis, expid)
            if exp:
                exp.set('title', settings['title'])
                exp.set('settings', settings)

            self.write(json.dumps(dict(redirect='/exp/' + str(expid))))
        except:
            self.write(json.dumps(dict(error=str(traceback.format_exc()))))


class NewTreatmentHandler(BaseHandler):
    @hostAuthenticated
    def post(self):
        try:
            target = self.get_argument('target')
            treatment = getTreatment(target)()
            treatment['content'] = treatment.content
        except:
            print traceback.format_exc()
            raise tornado.web.HTTPError(404)

        self.write(json.dumps(treatment))


class ExpListHandler(BaseHandler):
    def get(self):
        explist = self.db.query('select exp_id, exp_title, exp_status, host_id, user_name, exp_setuptime '
                                'from exp join user on host_id = user_id limit 10')
        self.render('expmanage/explist.html', explist=explist)


class ActivateExpHandler(BaseHandler):
    @expHostAuthenticated
    def get(self, expid):
        if not self.exp['exp_status'] == '0':
            raise tornado.web.HTTPError(503)

        self.initRedis(self.exp)
        self.db.update('update exp set exp_status=1 where exp_id=%s', expid)

        expurl = '/exp/{}/inprogress'.format(expid)
        self.redirect(expurl)

    def initRedis(self, exp):
        settings = json.loads(exp['exp_settings'])

        re = RedisExp(self.redis, exp['exp_id'])
        re.set('host', self.get_current_user()['user_id'])
        re.set('id', exp['exp_id'])
        re.set('title', exp['exp_title'])
        re.set('settings', settings)

        pool = Pool(self.redis, exp['exp_id'])
        pool.set('pool', [])
        pool.set('players', [])


class CloseExpHandler(BaseHandler):
    @expHostAuthenticated
    def get(self, expid):
        if self.exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)
        self.clearRedis(expid)
        self.db.update('update exp set exp_status=2 where exp_id=%s', expid)
        self.redirect('/exp/%s/result' % expid)

    def clearRedis(self, expid):
        pass


class ExpResultHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)

        if exp['host_id'] == self.current_user['user_id']:
            if exp['exp_status'] != '2':
                raise tornado.web.HTTPError(503)
            self.render('stat.html', exp=exp)
        else:
            player = Player(self.redis, expid, self.current_user['user_id'])
            if not(exp['exp_status'] == '2' or player.get('stage') == 'End'):
                raise tornado.web.HTTPError(503)

            results = self.db.query('select * from result where exp_id=%s and user_id=%s',
                                    expid, self.current_user['user_id'])

            self.render('expmanage/result.html', exp=exp, results=results)


class ExpInProgressHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid):
        settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)

        if exp['host_id'] == self.current_user['user_id']:
            self.render('expon/dashboard.html', exp=exp, settings=settings)
        else:
            self.render('expon/expinprogress.html', exp=exp, settings=settings)


class ExpTrainHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid, treatment=None):
        settings = dict(
            maxQ=10,
            minQ=6,
            maxC=4,
            minC=0
        )

        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)

        if not treatment:
            self.render('expon/exptrain.html', exp=exp, settings=settings)
        else:
            self.render('expon/train.html', exp=exp, settings=settings, treatment=treatment)