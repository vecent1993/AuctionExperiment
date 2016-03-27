# -*- coding: utf-8 -*-

import traceback
import json
import datetime

import tornado.web

from utils.web import BaseHandler, hostAuthenticated, userAuthenticated, expHostAuthenticated
from utils.redisvalue import RemoteRedis
from utils.exprv import Player, Pool, Host, RedisExp
import components


class NewExpHandler(BaseHandler):
    @hostAuthenticated
    def get(self):
        settings=dict(title='', des='', intro='', treatments=[])
        self.render('expmanage/newexp.html', settings=settings, treatments=components.hub.treatments,
                    PlayerOnly=components.treatment.PlayerOnly, PlayerGroup=components.treatment.PlayerGroup,
                    Container=components.treatment.Container, Train=components.treatment.Train)

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
                    treatments=components.hub.treatments, PlayerOnly=components.treatment.PlayerOnly,
                    PlayerGroup=components.treatment.PlayerGroup, Container=components.treatment.Container,
                    Train=components.treatment.Train)

    @expHostAuthenticated
    def post(self, expid):
        if self.exp['exp_status'] == '1':
            raise tornado.web.HTTPError(503)

        settings = json.loads(self.get_argument('data'))
        self.db.update('update exp set exp_title=%s, exp_des=%s, exp_intro=%s, '
                       'exp_settings=%s where exp_id=%s', settings['title'], settings['des'],
                       settings['intro'], json.dumps(settings), expid)

        exp = RedisExp(self.redis, expid)
        if exp:
            exp.set('title', settings['title'])
            exp.set('treatments', settings['treatments'])
            RemoteRedis(self.redis.publish).refresh()

        self.write(json.dumps(dict(redirect='/exp/' + str(expid))))


class NewTreatmentHandler(BaseHandler):
    @hostAuthenticated
    def post(self):
        try:
            target = self.get_argument('target')
            t = components.hub.treatments[target]
            treatment = dict(code=t.__name__, title=t.title, content=t.content(t.settings))
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
        if self.exp['exp_status'] == '1':
            raise tornado.web.HTTPError(503)

        self.redis.publish('experiment', json.dumps({'cmd': 'load_exp', 'data': expid}))
        self.redirect('/self')


class CloseExpHandler(BaseHandler):
    @expHostAuthenticated
    def get(self, expid):
        if self.exp['exp_status'] == '2':
            raise tornado.web.HTTPError(503)

        self.redis.publish('experiment', json.dumps({'cmd': 'close_exp', 'data': expid}))
        RedisExp(self.redis, expid).clear()
        self.redirect('/self')


class ExpResultHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)

        if exp['host_id'] == self.current_user['user_id']:
            host = Host(self.redis, expid, self.current_user['user_id'])
            if not(exp['exp_status'] == '2' or host.get('stage') == 'HostEnd'):
                raise tornado.web.HTTPError(503)

            result = components.hub.treatments['InfoAcquiSequence'].host_result(self.db, expid)
            self.render('expmanage/stat.html', exp=exp, result=result)
        else:
            player = Player(self.redis, expid, self.current_user['user_id'])
            if not(exp['exp_status'] == '2' or player.get('stage') == 'PlayerEnd'):
                raise tornado.web.HTTPError(503)

            result = components.hub.treatments['InfoAcquiSequence'].player_result(self.db,
                                                                              expid, self.current_user['user_id'])
            self.render('expmanage/result.html', exp=exp, result=result)


class ExpOnHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] != '1':
            raise tornado.web.HTTPError(503)

        if exp['host_id'] == self.current_user['user_id']:
            self.render('expon/dashboard.html', exp=exp)
        else:
            self.render('expon/expinprogress.html', exp=exp)


class ExpTrainHandler(BaseHandler):
    @userAuthenticated
    def get(self, expid):
        exp = self.db.get('select * from exp where exp_id=%s', expid)
        if not exp:
            raise tornado.web.HTTPError(404)
        if exp['exp_status'] == '2':
            raise tornado.web.HTTPError(503)

        settings = json.loads(exp['exp_settings'])

        self.render('expon/exptrain.html', exp=exp, settings=settings,
                    treatments=components.hub.treatments)