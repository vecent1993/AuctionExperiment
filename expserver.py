#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import json
import time

import gevent
import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from utils.redissub import RedisSub
from utils.redisvalue import RemoteRedis
import utils.exprv
from components.autohost import AutoHost
from utils.log import FileLogger, Logger
import components.hub as hub
import components.hosthandler as hosthandler

DEBUG = True

if not DEBUG:
    logger = FileLogger('expserver.txt')
else:
    logger = Logger()

exp_list = {}
rc = redis.Redis()

db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')


class Server(Greenlet):
    def __init__(self, channel='experiment'):
        super(Server, self).__init__()

        self.redis = rc
        self.sub = RedisSub(channel, self.on_message)

    def run(self):
        self.sub.start()

    @logger.log
    def on_message(self, msg):
        if msg['type'] == 'message':
            print msg
            data = json.loads(msg['data'])
            if hasattr(self, data['cmd']):
                getattr(self, data['cmd'])(data.get('data'))

    def load_exp(self, expid):
        if expid in exp_list:
            return

        Experiment.init_redis(expid)
        exp = Experiment(expid)
        exp.start()
        exp_list[expid] = exp

    def close_exp(self, expid):
        if expid not in exp_list:
            return

        exp_list[expid].close()
        exp_list.pop(expid)

    def stop(self):
        self.sub.stop()
        # self.kill()


class Exp(Greenlet):
    def __init__(self, expid):
        super(Exp, self).__init__()

        self.redis = rc
        self.db = db
        self.expid = expid
        self.value = utils.exprv.RedisExp(self.redis, expid)
        self.sub = RedisSub('exp:'+str(expid), self.on_message)

        self.groups = {}
        self.host = None

    @staticmethod
    def init_redis(expid):
        exp = db.get('select * from exp where exp_id=%s', expid)
        if exp['exp_status'] == '1':
            return

        settings = json.loads(exp['exp_settings'])

        re = utils.exprv.RedisExp(rc, exp['exp_id'])
        re.set('host', exp['host_id'])
        re.set('id', exp['exp_id'])
        re.set('title', exp['exp_title'])
        re.set('treatments', settings['treatments'])

        pool = utils.exprv.Pool(rc, exp['exp_id'])
        pool.set('pool', [])
        pool.set('players', [])

        db.update('update exp set exp_status=1 where exp_id=%s', expid)

    def init(self, data=None):
        pass

    @logger.log
    def on_message(self, msg):
        if msg['type'] == 'message':
            print msg
            data = json.loads(msg['data'])
            domain = data.get('domain', '')
            if domain.startswith('pool') and self.host:
                self.host.handle(data)
            elif domain.startswith('group'):
                _, sid, gid = domain.strip().split(':')
                group_key = ':'.join(('group', str(self.expid), str(sid), str(gid)))
                if group_key in self.groups:
                    self.groups[group_key].handle(data)
            elif not domain:
                self.handle(data)

    def handle(self, msg):
        try:
            if hasattr(self, msg['cmd']):
                getattr(self, msg['cmd'])(msg.get('data'))
        except Exception, e:
            print str(traceback.format_exc())

    def run(self):
        self.sub.start()

    def publish(self, data):
        self.redis.publish('exp:'+str(self.expid), json.dumps(data))

    def close(self):
        if self.sub:
            self.sub.stop()


class Experiment(Exp):
    def __init__(self, expid):
        super(Experiment, self).__init__(expid)
        self.host = AutoHost(self, self.value['host'])

        gevent.sleep(2)
        self.init()

    def init(self, data=None):
        p = utils.exprv.Pool(self.redis, self.expid)

        for sid, session in enumerate(p.get('sessions', [])):
            for gid, group in enumerate(session.get('groups', [])):
                self.switch_handler(dict(sid=sid, gid=gid))

    def switch_handler(self, data=None):
        if 'sid' not in data or 'gid' not in data:
            return

        sid, gid = data['sid'], data['gid']
        group = utils.exprv.Group(self.redis, self.expid, sid, gid)
        if not group.get('stage'):
            return

        group_key = ':'.join(('group', str(self.expid), str(sid), str(gid)))
        stage = group.get('stage', refresh=True).split(':')[0]
        if group_key in self.groups:
            self.groups[group_key].close()

        self.groups[group_key] = hub.handlers[stage](self, sid, gid)

    def close_group(self, data=None):
        group_key = ':'.join(('group', str(self.expid), str(data['sid']), str(data['gid'])))
        if group_key in self.groups:
            self.groups[group_key].close()
            self.groups.pop(group_key)
            self.host.next_group_stage(data)
        else:
            return

        if not self.groups:
            self.host.next_host_stage()

    def close(self):
        remote_redis = RemoteRedis(self.redis.publish)
        for group_key in self.groups.keys():
            self.groups[group_key].value.clear(True)
            self.groups[group_key].close()
            self.groups.pop(group_key)

        p = utils.exprv.Pool(self.redis, self.expid)
        for sid, session in enumerate(p.get('sessions', [])):
            for gid, group in enumerate(session.get('groups', [])):
                group = utils.exprv.Group(self.redis, self.expid, sid, gid)
                group.clear(True)
                remote_redis.refresh(group.key)

        for pid in p.get('pool', []):
            player = utils.exprv.Player(self.redis, self.expid, pid)
            player.clear(True)
            remote_redis.refresh(player.key)
        p.clear(True)
        remote_redis.refresh(p.key)

        h = utils.exprv.Host(self.redis, self.expid, self.value['host'])
        h.clear(True)
        remote_redis.refresh(h.key)

        e = utils.exprv.RedisExp(self.redis, self.expid)
        e.clear(True)
        remote_redis.refresh(e.key)

        db.update('update exp set exp_status=2 where exp_id=%s', self.expid)

        super(Experiment, self).close()


server = Server()
server.start()
time.sleep(1)

exp_running = db.query('select exp_id from exp where exp_status="1" limit 10')
for exp in exp_running:
    rc.publish('experiment', json.dumps({'cmd': 'load_exp', 'data': str(exp['exp_id'])}))

while True:
    time.sleep(100000000)