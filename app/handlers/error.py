import tornado
import base


class ErrorHandler(tornado.web.ErrorHandler, base.BaseHandler):
    """
    Default handler gonna to be used in case of 404 error
    """
    pass
