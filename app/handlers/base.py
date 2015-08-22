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

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        if not user:
            return None
