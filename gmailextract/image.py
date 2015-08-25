class Image(object):

    def __init__(self, msg_id, img_id, name, body, extension):
        self.img_id = img_id
        self.name = name
        self.body = body
        self.type = extension

    def resize_img(self, img, img_type, basewidth=300, supported_formats=('jpeg', 'gif',
                                                                              'png')):
        """Constrains proportions of an image object. The max width and support image formats are
        predefined by this function by default.

        Returns:
            A new image with contrained proportions specified by the max basewidth
        """

        img_type = img_type.split("/")[1]

        if img_type in supported_formats:
            img_buffer = StringIO.StringIO()
            img = Image.open(StringIO.StringIO(img))
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            img_format = img_type
            img.save(img_buffer, img_format)

            return img_buffer.getvalue()
        else:
            return ""

    def b64_preview(self):
        preview = self.resize_img(self.body, self.extension, 300)

        return base64.b64encode(preview)
