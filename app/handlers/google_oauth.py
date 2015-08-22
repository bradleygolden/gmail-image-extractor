import os
import tornado
import tornado.web
import tornado.template
import tornado.websocket
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

import app.objects


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
            user_info = app.objects.user.get_user_info(credentials)
            access_token = credentials.access_token
            email = user_info['email']

            self.set_secure_cookie('user', credentials.to_json())
            self.set_secure_cookie('email', email)
            self.set_secure_cookie('access_token', access_token)
            self.redirect('/extractor')
