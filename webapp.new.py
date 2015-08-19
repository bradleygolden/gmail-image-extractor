#!/usr/bin/env python

import os.path

import tornado
import tornado.web
import tornado.template
import tornado.websocket
import tornado.gen
import tornado.auth
import tornado.escape

import logging
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import client
from apiclient.discovery import build
from apiclient import errors

import httplib2

from gmailextract.extractor import GmailImageExtractor
import config

from tornado.options import define, options
define("port", default=config.port, help="run on the given port", type=int)

attr_dir = os.path.dirname(os.path.abspath(__file__))
state = {}
images = []


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
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/auth/login", GoogleOAuth2LoginHandler),
            (r"/extractor", ExtractorHandler),
            (r"/ws", SocketHandler),
            # TODO - Serve files outside of namespace of server
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "/user_downloads"}),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            ui_modules={'DeleteModal': DeleteModalModule,
                        'ImageModal': ImageModalModule,
                        'ImageThumbnail': ImageThumbnailModule,
                        'ImageMenu': ImageMenuModule},
            debug=config.debug,
            login_uri=config.oauth2_login_url,
            redirect_uri=config.oauth2_redirect_url,
            cookie_secret=config.cookie_secret,
            xsrf_cookies=config.xsrf_cookies,
            google_oauth={"key": config.oauth2_client_id, "secret": config.oauth2_client_secret},
        )

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        if not user:
            return None

        # TODO - Implement after clicking "begin"
        # credentials = client.OAuth2Credentials.from_json(user)
        # if credentials.access_token_expired:
            # self.redirect(self.settings['login_uri'])


class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html', site_name=config.site_name, site_description=config.description)


# TODO - Make SocketHandler instead
class LoginHandler(BaseHandler):
    def get(self):
        self.redirect(self.settings['login_uri'])


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie('user')
        credentials = client.OAuth2Credentials.from_json(user)
        credentials.revoke(httplib2.Http())
        self.clear_all_cookies()
        self.redirect('/')


class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        flow = OAuth2WebServerFlow(client_id=self.settings['google_oauth']['key'],
                                   client_secret=self.settings['google_oauth']['secret'],
                                   scope=['email', 'https://mail.google.com'],
                                   redirect_uri=self.settings['redirect_uri'])

        if not self.get_argument('code', False):
            auth_uri = flow.step1_get_authorize_url()
            self.redirect(auth_uri)
        else:
            auth_code = self.get_argument('code')
            credentials = flow.step2_exchange(auth_code)
            user_info = get_user_info(credentials)
            # TODO - save user email
            access_token = credentials.access_token
            email = user_info['email']

            self.set_secure_cookie('user', credentials.to_json())
            self.set_secure_cookie('email', email)
            self.set_secure_cookie('access_token', access_token)
            # TODO - set to redirect to extract process
            self.redirect('/extractor')


class ExtractorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('extract.html', site_name=config.site_name)


class SocketHandler(tornado.websocket.WebSocketHandler):

    def on_message(self, message):
        msg = tornado.escape.json_decode(message)
        if 'type' not in msg:
            return
        elif msg['type'] == 'connect':
            self._handle_connect(msg)
        # elif msg['type'] == 'sync':
        #    self._handle_sync(msg)
        # elif msg['type'] == 'confirm':
        #    self._handle_confirmation(msg)
        elif msg['type'] == 'delete':
            self._handle_delete(msg)
        elif msg['type'] == 'save':
            self._handle_save(msg)
        else:
            return

    def _handle_connect(self, msg, callback=None):

        access_token = self.get_secure_cookie('access_token')
        email = self.get_secure_cookie('email')

        state['extractor'] = GmailImageExtractor(attr_dir, email,
                                                 access_token, limit=int(msg['limit']),
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
                    image = {
                        "message_id": args[1],
                        "image_id": args[2],
                        "body": args[3],
                        "name": args[4]
                    }
                    images.append(image)

                    # return self.render_string('modules/image_thumbnail.html', image)
                    self.write_message({"ok": True,
                                        "type": "image",
                                        "msg_id": args[1],
                                        "img_id": args[2],
                                        "enc_img": args[3],
                                        "img_name": args[4]})

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
                # file_name = args[2]
                save_path = args[3]

                if write_zip_passed:
                    self.write_message({"ok": True,
                                        "link": u"""<a href="{0}"
                                         target="_blank" download>"""
                                        "Click Here to Download Your Gmail Images"
                                        "</a><span> (This link will be available for"
                                        " {2} {1})</span>"
                                        "".format(save_path,
                                                  plural(u"minute",
                                                         config.zip_removal_countdown/60),
                                                  config.zip_removal_countdown/60),
                                        "type": "zip"})
                else:
                    self.write_message(self.write(
                        "<span> Failed to create zip file :( </span>"))

            if update_type == "erased-zip":
                erase_zip_passed = args[1]

                if erase_zip_passed:
                    self.write_message({"ok": True,
                                        "type": "zip",
                                        "msg": "Please check all attachments that you want to"
                                        " remove from your Gmail account."})

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


class Modal:
    def get(self, id, title):
        self.render('modal.html', id=id, title=title)


class DeleteModalModule(tornado.web.UIModule):
    def render(self, id):
        return self.render_string('modules/delete_modal.html', id=id)


class ImageModalModule(tornado.web.UIModule):
    def render(self, id):
        return self.render_string('modules/image_modal.html', id=id)


class ImageThumbnailModule(tornado.web.UIModule):
    def render(self, image):
        return self.render_string('modules/image_thumbnail.html', image=image)


class ImageMenuModule(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/images_menu.html')


class NoUserIdException(Exception):
    """Error raised when no user ID could be retrieved."""
    # print "No UserID could be retreived"


def get_user_info(credentials):
    """Send a request to the UserInfo API to retrieve the user's information.

    Argss:
        credentials: oauth2client.client.OAuth2Credentials instance to authorize the
        request.

    Returns:
        User information as a dict.
        """

    user_info_service = build(
        serviceName='oauth2', version='v2',
        http=credentials.authorize(httplib2.Http()))
    user_info = None
    try:
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    except errors.HttpError, e:
        logging.error('An error occurred: %s', e)
        if user_info and user_info.get('id'):
            return user_info
        else:
            raise NoUserIdException()


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
