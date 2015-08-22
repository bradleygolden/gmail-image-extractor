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

import base

class MainHandler(base.BaseHandler):
    def get(self):
        self.render('index.html', site_name=config.site_name, site_description=config.description)
