import tornado
from oauth2client import client
import httplib2


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie('user')
        if user:
            credentials = client.OAuth2Credentials.from_json(user)
            credentials.revoke(httplib2.Http())
            self.clear_all_cookies()
        self.redirect('/')
