# -*- coding: utf-8 -*-

import traceback
import json

import tornado.web

from util.web import BaseHandler
from util.core import *
from util.baseexp import baseexp_list
from util.pool import Player, Pool


class NewExpHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        settings = Experiment()
        self.render('expmanage/newexp.html', settings=settings, baseexp_list=baseexp_list)

    @tornado.web.authenticated
    def post(self):
        try:
            settings = json.loads(self.get_argument('data'))
            expid = self.db.insert('insert into exp(exp_title,exp_des,exp_intro,exp_settings,host_id) '
                           'values (%s,%s,%s,%s,%s)', settings['title'], settings['description'],
                            settings['introduction'], json.dumps(settings), self.current_user['user_id'])
            self.redirect('/exp/' + str(expid))
        except:
            self.write(str(traceback.format_exc()))


class ExpIndexHandler(BaseHandler):
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        self.render('expmanage/expindex.html', exp=exp)


class ExpSettingsHandler(BaseHandler):
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        settings = Experiment(json.loads(exp['exp_settings']))
        self.render('expmanage/expsettings.html', exp=exp, settings=settings, baseexp_list=baseexp_list)


class NewTreatmentHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            treatment_type = self.get_argument('code')
            base_exp = filter(lambda a: a.code == treatment_type, baseexp_list)[0]
            treatment = base_exp.new_treatment()
        except:
            raise tornado.web.HTTPError(404)
        self.render(treatment.template, treatment=treatment)


class ExpListHandler(BaseHandler):
    def get(self):
        explist = self.db.query('select exp_id, exp_title, exp_status, host_id, user_name '
                                'from exp join user on host_id = user_id limit 10')
        self.render('expmanage/explist.html', explist=explist)


class ActivateExpHandler(BaseHandler):
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if not exp['exp_status'] == '0':
            raise tornado.web.HTTPError(503)

        self.initRedis(exp)
        self.db.update('update exp set exp_status=1 where exp_id=%s', expid)

        expurl = '/exp/{}/inprogress'.format(expid)
        self.redirect(expurl)

    def initRedis(self, exp):
        settings = json.loads(exp['exp_settings'])

        re = RedisExp(self.redis, exp['exp_id'])
        re.set('host', self.get_current_user()['user_id'])
        re.set('id', exp['exp_id'])
        re.set('title', exp['exp_title'])

        pool = Pool(self.redis, exp['exp_id'])
        pool.set('pool', [])
        pool.set('sessions', [])
        for sid, s in enumerate(settings['sessions']):
            pool['sessions'].append({'id': sid})

        pool.save('sessions')


class CloseExpHandler(BaseHandler):
    def get(self, expid):
        exp = self.db.get('select id, status from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)
        self.clearRedis(expid)
        self.db.update('update exp set exp_status=2 where exp_id=%s', expid)
        self.redirect('/exp/%s/result' % expid)

    def clearRedis(self, expid):
        pass


class ExpResultHandler(BaseHandler):
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