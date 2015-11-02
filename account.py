# -*- coding: utf-8 -*-
import hashlib
import json

import tornado.web
import tornado.template
import concurrent.futures
import uuid
import email

from util.web import BaseHandler, userAuthenticated

# A thread pool to be used for sending email
executor = concurrent.futures.ThreadPoolExecutor(2)


class IndexHandler(BaseHandler):
    def get(self):
        self.render('index.html')

    def post(self):
        self.login_user(self.get_argument("email"), self.get_argument("password"))

    def login_user(self, email, password):
        user = self.db.get('select * from user where user_email=%s', email)
        if not user:
            res = {'errors':[{'name': 'email', 'reason': '账户尚未注册'}, ]}
        else:
            if self.check_password(password, user):
                user.pop('user_pwd')
                self.session.set('user', user)
                self.set_secure_cookie("_session_id", self.session.sid)
                res = {'redirect': self.get_argument("next", "/self")}
            else:
                res = {'errors':[{'name': 'password', 'reason': '密码错误'}, ]}
        self.write(json.dumps(res))

    def check_password(self, password, user):
        return hashlib.md5(password).hexdigest() == user['user_pwd']


class LoginHandler(BaseHandler):
    def get(self):
        self.redirect('/')


class LogoutHandler(BaseHandler):
    @userAuthenticated
    def get(self):
        self.logout()
        self.redirect(self.get_argument("next", "/"))

    def logout(self):
        self.session.pop('user')


class RegisterHandler(BaseHandler):
    def get(self):
        majors = self.db.query('select * from major')
        nations = self.db.query('select * from nation')
        self.render("account/register.html", majors=majors, nations=nations)

    def post(self):
        if self.db.get('select user_email from user where user_email=%s', self.get_argument('email')):
            res = {'errors': [{'name': 'email', 'reason': '账户已注册'}, ]}
        elif self.get_argument('password') != self.get_argument('re-password'):
            res = {'errors': [{'name': 're-password', 'reason': '密码必须一致'}, ]}
        else:
            if self.get_argument('identity') == '0':
                self.db.insert(
                    'INSERT INTO user(user_email,user_name,user_pwd,user_gender,user_age,nation_id,'
                    'user_identity,major_code,user_consumption,user_scholarship, user_grade) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    self.get_argument('email'), self.get_argument('username'),
                    hashlib.md5(self.get_argument('password')).hexdigest(),
                    self.get_argument('gender'), self.get_argument('age'), self.get_argument('nation'),
                    self.get_argument('identity'), self.get_argument('major'), self.get_argument('consumption'),
                    ','.join(self.get_arguments('scholarship')), self.get_argument('grade')
                )
            else:
                self.db.insert(
                    'INSERT INTO user(user_email,user_name,user_pwd,user_gender,user_age,nation_id,'
                    'user_identity,major_code,user_income) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    self.get_argument('email'), self.get_argument('username'),
                    hashlib.md5(self.get_argument('password')).hexdigest(),
                    self.get_argument('gender'), self.get_argument('age'), self.get_argument('nation'),
                    self.get_argument('identity'), self.get_argument('major'),
                    self.get_argument('income')
                )
            res = {'redirect': self.get_argument("next", self.get_login_url())}
        self.write(json.dumps(res))

    def sendActivationEmail(self, user):
        msg = email.Message(
            "激活拍卖试验系统账户",
            recipients=[user['email']],
        )
        loader = tornado.template.Loader("/home/btaylor")
        msg.html = loader.load("email/signup.html").generate(user=user)


class AccountHandler(BaseHandler):
    @userAuthenticated
    def get(self, userid):
        if userid:
            user = self.db.get('select * from user where user_id=' + userid)
        else:
            user = self.session.get('user')
        if not user:
            raise tornado.web.HTTPError(404)

        self.render('account/account.html', user=user)