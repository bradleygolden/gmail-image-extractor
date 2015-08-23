import base
import config


class GoogleOAuth2LoginAlertHandler(base.BaseHandler):
    def get(self):
        self.render('oauth_alert.html', site_name=config.site_name)
