import config
import base


class MainHandler(base.BaseHandler):
    def get(self):
        self.render('index.html', site_name=config.site_name, site_description=config.description)
