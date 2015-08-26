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
from extractor import GmailImageExtractor
import config


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
