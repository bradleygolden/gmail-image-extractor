import tornado
import tornado.web
import tornado.template
import tornado.websocket
import tornado.gen
import tornado.auth
import tornado.escape
import os
from os.path import expanduser
from gmailextract.extractor import GmailImageExtractor
import config

from tornado.options import define, options
define("port", default=config.port, help="run on the given port", type=int)

root_dir = os.path.dirname(os.path.abspath(__file__))
attr_dir = os.path.join(expanduser("~"), "Gmail Images")
if not os.path.isdir(attr_dir):
    os.mkdir(attr_dir)

# tpl_loader = tornado.template.Loader(os.path.join(root_dir, 'templates'))
state = {}


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
            (r'/ws', SocketHandler),
            # (r"/auth/login", GoogleOAuth2LoginHandler),
            # (r"/login", LoginHandler),
            # (r"/logout", LogoutHandler),

            # static paths
            # (r"/assets/(.*)", tornado.web.StaticFileHandler, (dict(path=settings['static_path']))),
            # (r"/downloads/(.*)", tornado.web.StaticFileHandler, (dict(path=settings['static_path']))),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            login_url=config.oauth2_login_uri,
            redirect_uri=config.oauth2_redirect_uri,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            xsrf_cookies=config.xsrf_cookies,
            google_oauth={"key": config.oauth2_client_id, "secret": config.oauth2_client_secret},
            debug=config.debug,
        )

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        if not user_json:
            return None
        return True


class MainHandler(BaseHandler):
    # @tornado.web.authenticated

    def get(self):
        self.render('main.html')


class LoginHandler(BaseHandler):
    # @tornado.web.authenticated
    def get(self):
        self.render('main.html')

class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('user')
        self.redirect("/")


class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            user = yield self.get_authenticated_user(
                redirect_uri='http://localhost:8888/auth/login',
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


class SocketHandler(tornado.websocket.WebSocketHandler):

    def on_message(self, message):
        msg = tornado.escape.json_decode(message)
        if 'type' not in msg:
            return
        elif msg['type'] == 'connect':
            self._handle_connect(msg)
        elif msg['type'] == 'sync':
            self._handle_sync(msg)
        elif msg['type'] == 'confirm':
            self._handle_confirmation(msg)
        elif msg['type'] == 'delete':
            self._handle_delete(msg)
        elif msg['type'] == 'save':
            self._handle_save(msg)
        else:
            return

    def _handle_connect(self, msg, callback=None):

        # obtain user cookie
        user_json = self.get_secure_cookie('user')

        state['extractor'] = GmailImageExtractor(attr_dir, msg['email'],
                                                 msg['pass'], limit=int(msg['limit']),
                                                 batch=int(msg['simultaneous']),
                                                 replace=bool(msg['rewrite']))
        if not state['extractor'].connect():
            self.write_message({'ok': False,
                                "type": "connect",
                                'msg': u"Unable to connect to Gmail with provided credentials"})
        else:
            self.write_message({'ok': True,
                                "type": "connect",
                                "msg": u"Successfully connected with Gmail."})

            num_messages = state['extractor'].num_messages_with_attachments()
            self.write_message({'ok': True,
                                "type": "count",
                                "msg": u"Found {0} {1} with attachments"
                                "".format(num_messages, plural(u"message", num_messages)),
                                "num": num_messages})

            def _status(*args):

                if args[0] == 'image':
                    self.write_message({"ok": True,
                                        "type": "image",
                                        "msg_id": args[1],
                                        "img_id": args[2],
                                        "enc_img": args[3]})

                if args[0] == 'message':
                    status_msg = u"Fetching messages {1} - {2}".format(msg['simultaneous'],
                                                                       args[1], num_messages)
                    self.write_message({"ok": True,
                                        "type": "downloading",
                                        "msg": status_msg,
                                        "num": args[1]})

            attachment_count = state['extractor'].extract(_status)
            self.write_message({"ok": True,
                                "type": "download-complete",
                                "msg": "Succesfully found {0} {1}"
                                "".format(attachment_count, plural(u"image", attachment_count)),
                                "num": attachment_count})

    def _handle_delete(self, msg):
        extractor = state['extractor']

        def _delete_status(*args):
            update_type = args[0]

            if update_type == "image-removed":
                self.write_message({"ok": True,
                                    "type": "image-removed",
                                    "msg": u"Removed {0} out of {1} {2}."
                                    "".format(args[1],
                                              args[2],
                                              plural(u"image", args[2])),
                                    "gmail_id": args[3],
                                    "image_id": args[4]})

        num_messages_changed, num_images_deleted = extractor.delete(msg, callback=_delete_status)
        self.write_message({"ok": True,
                            "type": "finished",
                            "msg": u"Removed {0} {1} total from {2} {3}."
                            "".format(num_images_deleted,
                                      plural(u"image", num_images_deleted),
                                      num_messages_changed,
                                      plural(u"message", num_messages_changed))})

    def _handle_save(self, msg):
        extractor = state['extractor']

        def _save_status(*args):
            update_type = args[0]
            if update_type == "image-packet":
                self.write_message({"ok": True,
                                    "msg": u"{0} of {1} total {2} extracted from gmail..."
                                    "".format(args[4], args[5], plural(u"image", args[5])),
                                    "type": "image-packet",
                                    "images": args[1],
                                    "image_names": args[2],
                                    "packet_size": args[3],
                                    "packet_count": args[4],
                                    "total_images": args[5]})

            if update_type == "packet-progress":
                self.write_message({"ok": True,
                                    "msg": "Packaging images...",
                                    "type": "packet-progress",
                                    "num": args[1],
                                    "messages": args[2]})

            if update_type == "save-passed":
                self.write_message({"ok": True,
                                    "type": "save",
                                    "images": args[1],
                                    "image_names": args[2]})

            if update_type == "write-zip":
                write_zip_passed = args[1]
                file_name = args[2]

                if write_zip_passed:
                    self.write_message({"ok": True,
                                        "link": u"""<a href="gmailextract/user_downloads/{0}">"""
                                        "Click Here to Download Your Gmail Images"
                                        "</a>".format(file_name),
                                        "type": "zip"})
                else:
                    self.write_message(self.write(
                        "<span> Failed to create zip file :( </span>"))

        extractor.save(msg, _save_status)

    def _handle_sync(self, msg):
        extractor = state['extractor']

        self.write_message({"ok": True,
                            "type": "file-checking",
                            "msg": u"Checking to see which files have been deleted."})
        num_deletions = extractor.check_deletions()
        self.write_message({"ok": True,
                            "type": "file-checked",
                            "msg": u"Found {0} {1} deleted"
                            "".format(num_deletions, plural(u"image", num_deletions)),
                            "num": num_deletions})

    def _handle_confirmation(self, msg):
        extractor = state['extractor']

        def _sync_status(*args):
            update_type = args[0]
            if update_type == "fetch":
                self.write_message({"ok": True,
                                    "type": "removing",
                                    "msg": u"Removing {0} {1} from message '{2}'."
                                    "".format(args[2], args[1], plural(u"image", args[2]))})
            elif update_type == "write":
                self.write_message({"ok": True,
                                    "type": "removed",
                                    "msg": u"Writing altered version of '{0}' to Gmail."
                                    "".format(args[1])})

        num_attch_removed, num_msg_changed = extractor.sync(callback=_sync_status)
        self.write_message({"ok": True,
                            "type": "finished",
                            "msg": u"Removed {0} {1} from {2} {3}."
                            "".format(num_attch_removed,
                                      plural(u"image", num_attch_removed),
                                      num_msg_changed,
                                      plural(u"message", num_msg_changed))})

    def on_close(self):
        state['extractor'] = None


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
