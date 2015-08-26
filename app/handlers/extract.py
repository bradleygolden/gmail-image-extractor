import config
import base


class ExtractHandler(base.BaseHandler):
    def get(self):
        access_token = self.get_secure_cookie('access_token')
        if access_token:
            self.render('extract.html', site_name=config.site_name)
        else:
            self.redirect('/')
