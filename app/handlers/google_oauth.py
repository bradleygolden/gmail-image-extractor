import tornado
from oauth2client.client import OAuth2WebServerFlow

import app.objects


class GoogleOAuth2LoginHandler(tornado.web.RequestHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):

        # check if user is already logged in
        user = self.get_secure_cookie('user')
        if user:
            # create already logged in page and give user option to log out
            self.redirect('/oauth_alert')
            return

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
            user_info = app.objects.user.get_user_info(credentials)
            access_token = credentials.access_token
            email = user_info['email']

            self.set_secure_cookie('user', credentials.to_json())
            self.set_secure_cookie('email', email)
            self.set_secure_cookie('access_token', access_token)
            self.redirect('/extractor')
