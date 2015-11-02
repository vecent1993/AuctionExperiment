# -*- coding: utf-8 -*-
import traceback
import json
import time

import torndb
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
import redis

from util.redissub import RedisSub
import util.pool
from util.core import RedisExp
from handler import getHandler
from handler.grouphandler_.grouphandler import Delay, GroupHandler

explist = {}
redisclient = redis.Redis()

db = torndb.Connection("localhost", 'exp', user='JKiriS', password='910813gyb')


class Server(Greenlet):
    def __init__(self, channel='experiment'):
        super(Server, self).__init__()

        self.sub = RedisSub(channel, self.on_message)

    def run(self):
        self.sub.start()

    def on_message(self, msg):
        if msg['type'] == 'message':
            data = json.loads(msg['data'])
            try:
                if hasattr(self, data['cmd']):
                    getattr(self, data['cmd'])(data.get('data'))
            except Exception, e:
                print str(traceback.format_exc())

    def loadExp(self, data):
        expid = data
        if expid in explist:
            return

        exp = Experiment(expid)
        exp.start()
        explist[expid] = exp

    def closeExp(self, data):
        expid = data
        if expid not in explist:
            return

        explist[expid].close()
        explist.pop(expid)

    def stop(self):
        self.sub.stop()
        # self.kill()


class Exp(Greenlet):
    def __init__(self, expid):
        super(Exp, self).__init__()

        self.redis = redisclient
        self.exp = RedisExp(self.redis, expid)
        self.sub = RedisSub('exp:'+str(self.exp['id']), self.on_message)

        self.groups = {}
        self.host = None

    def init(self, data=None):
        pass

    def on_message(self, msg):
        print msg
        if msg['type'] == 'message':
            data = json.loads(msg['data'])
            domain = data.get('domain', '')
            if domain.startswith('pool') and self.host:
                self.host.handle(data)
            elif domain.startswith('group'):
                _, sid, gid = domain.strip().split(':')
                groupkey = ':'.join(('group', str(self.exp['id']), str(sid), str(gid)))
                if groupkey in self.groups:
                    self.groups[groupkey].handle(data)
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
        self.redis.publish('exp:'+str(self.exp['id']), json.dumps(data))

    def stop(self):
        self.sub.stop()
        # self.kill()


class Experiment(Exp):
    def __init__(self, expid):
        super(Experiment, self).__init__(expid)
        self.host = getHandler('group', 'AutoHost')(self.exp['id'], self.exp['host'])

        Delay(2, self.init, None).start()

    def init(self, data=None):
        p = util.pool.Pool(self.redis, self.exp['id'])

        for sid, session in enumerate(p.get('sessions', [])):
            for gid, group in enumerate(session.get('groups', [])):
                self.switchHandler(dict(sid=sid, gid=gid))

    def switchHandler(self, data=None):
        if 'sid' not in data or 'gid' not in data:
            return

        sid, gid = data['sid'], data['gid']
        group = util.pool.Group(self.redis, self.exp['id'], sid, gid)
        if 'stage' not in group:
            return
            # GroupHandler.nextStage(self.redis, self.exp['id'], sid, gid)

        groupkey = ':'.join(('group', str(self.exp['id']), str(sid), str(gid)))
        if groupkey in self.groups:
            self.groups[groupkey].close()

        self.groups[groupkey] = getHandler('group', group.get('stage', refresh=True))(self.exp['id'], sid, gid)

    def changeStage(self, data=None):
        sid, gid = data['sid'], data['gid']
        GroupHandler.nextStage(self.redis, self.exp['id'], sid, gid)
        self.switchHandler(data)

    def closeGroup(self, data=None):
        groupkey = ':'.join(('group', str(self.exp['id']), str(data['sid']), str(data['gid'])))
        self.groups[groupkey].close()
        self.groups.pop(groupkey)

    def close(self):
        p = util.pool.Pool(self.redis, self.exp['id'])
        p.delete()
        h = util.pool.Host(self.redis, self.exp['id'], self.exp['host'])
        h.delete()


server = Server()
server.start()
time.sleep(1)

runexps = db.query('select exp_id from exp where exp_status="1" limit 10')
for exp in runexps:
    redisclient.publish('experiment', json.dumps({'cmd': 'loadExp', 'data': exp['exp_id']}))

while True:
    time.sleep(100000000)