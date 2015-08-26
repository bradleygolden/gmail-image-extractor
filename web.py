#!/usr/bin/env python

import os.path
import tornado
import tornado.httpserver
import config

import app.handlers
import app

from tornado.options import define, options
define("port", default=config.port, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            (r"/", app.handlers.main.MainHandler),
            (r"/login", app.handlers.login.LoginHandler),
            (r"/logout", app.handlers.logout.LogoutHandler),
            (r"/auth/login", app.handlers.google_oauth.GoogleOAuth2LoginHandler),
            (r"/extractor", app.handlers.extract.ExtractHandler),
            (r"/oauth_alert", app.handlers.google_oauth_alert.GoogleOAuth2LoginAlertHandler),
            (r"/ws", app.handlers.socket.SocketHandler),
            (r'/download/(.*)', tornado.web.StaticFileHandler,
             {'path': config.root_path + '/Gmail-Image-Extractor/download'}),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            ui_modules={'DeleteModal': app.modules.DeleteModalModule,
                        'ImageModal': app.modules.ImageModalModule,
                        'ImageThumbnail': app.modules.ImageThumbnailModule,
                        'ImageMenu': app.modules.ImageMenuModule},
            debug=config.debug,
            login_url=config.oauth2_login_url,
            redirect_uri=config.oauth2_redirect_url,
            cookie_secret=config.cookie_secret,
            xsrf_cookies=config.xsrf_cookies,
            google_oauth={"key": config.oauth2_client_id, "secret": config.oauth2_client_secret},
            default_handler_class=app.handlers.error.ErrorHandler,
            default_handler_args=dict(status_code=404),
        )

        tornado.web.Application.__init__(self, handlers, **settings)


def server_prompt():
    print ("-------------------------------------")
    print ("Base Url: {0}".format(config.base_url))
    print ("Port: {0}".format(options.port))
    print ("View at: {0}".format(config.base_url + ":" + str(options.port)))
    print ("-------------------------------------")


def main():
    tornado.options.parse_command_line()
    application = Application()
    server_prompt()
    application.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
