# -*- coding: utf-8 -*-
import traceback
import json
import time

import gevent
import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from util.redissub import RedisSub
import util.pool
from handler import get_handler
import handler
from util.log import FileLogger, Logger

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
        self.expid = expid
        self.value = util.pool.RedisExp(self.redis, expid)
        self.sub = RedisSub('exp:'+str(expid), self.on_message)

        self.groups = {}
        self.host = None

    @staticmethod
    def init_redis(expid):
        exp = db.get('select * from exp where exp_id=%s', expid)
        if exp['exp_status'] == '1':
            return

        settings = json.loads(exp['exp_settings'])

        re = util.pool.RedisExp(rc, exp['exp_id'])
        re.set('host', exp['host_id'])
        re.set('id', exp['exp_id'])
        re.set('title', exp['exp_title'])
        re.set('settings', settings)

        pool = util.pool.Pool(rc, exp['exp_id'])
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
        self.host = get_handler('group', 'AutoHost')(self.exp['id'], self.exp['host'])

        gevent.sleep(2)
        self.init()

    def init(self, data=None):
        p = util.pool.Pool(self.redis, self.exp['id'])

        for sid, session in enumerate(p.get('sessions', [])):
            for gid, group in enumerate(session.get('groups', [])):
                self.switch_handler(dict(sid=sid, gid=gid))

    def switch_handler(self, data=None):
        if 'sid' not in data or 'gid' not in data:
            return

        sid, gid = data['sid'], data['gid']
        group = util.pool.Group(self.redis, self.expid, sid, gid)
        if 'stage' not in group:
            return
            # GroupHandler.nextStage(self.redis, self.exp['id'], sid, gid)

        group_key = ':'.join(('group', str(self.expid), str(sid), str(gid)))
        stage = group.get('stage', refresh=True).split(':')[0]
        if group_key in self.groups:
            self.groups[group_key].close()

        self.groups[group_key] = get_handler('group', stage)(self, sid, gid)

    def change_stage(self, data=None):
        sid, gid = data['sid'], data['gid']
        handler.grouphandler.GroupHandler.next_stage(self.redis, self.expid, sid, gid)
        self.switch_handler(data)

    def close_group(self, data=None):
        group_key = ':'.join(('group', str(self.expid), str(data['sid']), str(data['gid'])))
        if group_key in self.groups:
            self.groups[group_key].close()
            self.groups.pop(group_key)
        else:
            return

        if not self.groups:
            handler.hosthandler.HostHandler.next_stage(self.redis, self.expid, self.value['host'])
            self.publish('switch_handler', ':'.join(('host', str(self.expid))), data=dict(cmd='get'))

    def publish(self, cmd, domain=None, data=None):
        msg = dict(cmd=cmd)
        if domain is not None:
            msg['domain'] = domain
        if data is not None:
            msg['data'] = data

        self.redis.publish('exp:'+str(self.expid), json.dumps(msg))

    def close(self):
        for group_key in self.groups.keys():
            self.groups[group_key].value.delete()
            self.groups[group_key].close()
            self.groups.pop(group_key)

        p = util.pool.Pool(self.redis, self.expid)
        for sid, session in enumerate(p.get('sessions', [])):
            for gid, group in enumerate(session.get('groups', [])):
                group = util.pool.Group(self.redis, self.expid, sid, gid)
                group.delete()

        for pid in p.get('pool', []):
            player = util.pool.Player(self.redis, self.expid, pid)
            player.delete()
        p.delete()

        h = util.pool.Host(self.redis, self.expid, self.value['host'])
        h.delete()

        e = util.pool.RedisExp(self.redis, self.expid)
        e.delete()

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