import tornado


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        if not user:
            return None

    def write_error(self, status_code, **kwargs):
        if status_code in [403, 404, 500, 503]:
            self.write('Error %s' % status_code)
        else:
            self.write('It''s your lucky day, you''ve discovered an uknown error...')
