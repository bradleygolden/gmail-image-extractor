import os.path
import tornado
import tornado.web
import tornado.template
import tornado.websocket
import tornado.auth
import tornado.escape
import config


class DeleteModalModule(tornado.web.UIModule):
    def render(self, id):
        return self.render_string('modules/delete_modal.html', id=id)


class ImageModalModule(tornado.web.UIModule):
    def render(self, id):
        return self.render_string('modules/image_modal.html', id=id)


class ImageThumbnailModule(tornado.web.UIModule):
    def render(self, image):
        return self.render_string('modules/image_thumbnail.html', image=image)


class ImageMenuModule(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/images_menu.html')
