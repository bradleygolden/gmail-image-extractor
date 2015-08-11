#!/usr/bin/env python

import os.path

import tornado
import tornado.web
import tornado.template
import tornado.websocket
import tornado.gen
import tornado.auth
import tornado.escape

# from gmailextract.extractor import GmailImageExtractor
import config

from tornado.options import define, options
define("port", default=config.port, help="run on the given port", type=int)


def plural(msg, num):
    if num == 1:
        return msg
    else:
        return u"{0}s".format(msg)


class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            # handlers
            (r"/", MainHandler),
            # (r"/ws", SocketHandler)
            (r"/login", LoginHandler),
            (r"/auth/login", GoogleOAuth2LoginHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            debug=config.debug,
            login_url=config.oauth2_login_url,
            # redirect_url=config.oauth2_redirect_url,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            xsrf_cookies=config.xsrf_cookies,
            google_oauth={"key": config.oauth2_client_id, "secret": config.oauth2_client_secret},
        )

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        if not user_json:
            return None
        return True


class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html', site_name=config.site_name, site_description=config.description)


class LoginHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('hello.html')


class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            user = yield self.get_authenticated_user(
                redirect_uri=config.oauth2_redirect_url,
                code=self.get_argument('code'))
            # Save the user with e.g. set_secure_cookie
            self.set_secure_cookie('user', tornado.escape.json_encode(user))
            self.redirect("/")

        else:
            yield self.authorize_redirect(
                redirect_uri='http://localhost:8888/auth/login',
                client_id=self.settings['google_oauth']['key'],
                # scope for full access to email:https://mail.google.com/
                # scope for modifying emails: https://www.googleapis.com/auth/userinfo.email
                scope=['email', 'https://mail.google.com/'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


def server_prompt():
    print ("-------------------------------------")
    print ("Base Url: {0}".format(config.base_url))
    print ("Port: {0}".format(config.port))
    print ("View at: {0}".format(config.full_url))
    print ("-------------------------------------")


def main():
    tornado.options.parse_command_line()
    application = Application()
    server_prompt()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
