import base


class LoginHandler(base.BaseHandler):
    def get(self):
        self.redirect(self.settings['login_url'])
