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
from handler.grouphandler_.grouphandler import Delay

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
        settings = RedisExp(redisclient, data['id'])
        if settings and settings['id'] not in explist:
            exp = Experiment(settings['id'])
            exp.start()
            explist[settings['id']] = exp

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
        self.host = getHandler('group', 'AutoHost')(self.exp['host'], self.exp['id'])

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
        groupkey = ':'.join(('group', str(self.exp['id']), str(sid), str(gid)))
        if groupkey in self.groups:
            self.groups[groupkey].close()
        g = util.pool.Group(self.redis, self.exp['id'], sid, gid)
        if g.get('stage', '').startswith('SealedEnglish'):
            self.groups[groupkey] = getHandler('group', 'SealedEnglish')(gid, sid, self.exp['id'])
        elif g.get('stage', '').startswith('End'):
            pass

    def nextStage(self, data=None):
        sid, gid = data['sid'], data['gid']
        g = util.pool.Group(self.redis, self.exp['id'], sid, gid)
        if 'stage' not in g:
            g.set('stage', 'SealedEnglish')

        elif g['stage'].startswith('SealedEnglish'):
            g.set('stage', 'End')
            for pid in filter(lambda pid: not pid.startswith('agent'), g['players'].keys()):
                player = util.pool.Player(self.redis, self.exp['id'], pid)
                player.set('stage', 'End')
                self.publish({'cmd': 'changeStage', 'domain': ':'.join(('player', str(self.exp['id']), pid))})

            groupkey = ':'.join(('group', str(self.exp['id']), str(sid), str(gid)))
            if groupkey in self.groups:
                self.groups[groupkey].close()
                self.groups.pop(groupkey)

        self.switchHandler(data)


server = Server()
server.start()
time.sleep(1)

runexps = db.query('select exp_id from exp where exp_status="1" limit 10')
for exp in runexps:
    redisclient.publish('experiment', json.dumps({'cmd': 'loadExp', 'data': {'id': exp['exp_id']}}))

while True:
    time.sleep(100000000)