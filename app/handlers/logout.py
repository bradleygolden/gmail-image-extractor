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


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie('user')
        if user:
            credentials = client.OAuth2Credentials.from_json(user)
            credentials.revoke(httplib2.Http())
            self.clear_all_cookies()
        self.redirect('/')
