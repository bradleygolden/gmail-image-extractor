import base64
from pygmail.message import Attachment
import StringIO
import PIL
from hashlib import sha256

EXTENSIONS = ('jpeg', 'png', 'gif')

class Image(Attachment):

    def __init__(self, msg, att):
        self.msg_id = msg.gmail_id
        self.id = self.get_att_id(att)
        self.name = self.get_att_name(att)
        self.type = self.get_att_type(att)
        self.body = self.get_body(att)
        self.date = self.get_msg_date(msg)
        self.preview = self.get_preview()

    def get_preview(self, basewidth=500):
        """Constrains proportions of an image object. The max width and support image formats are
        predefined by this function by default.

        Returns:
            A new image with contrained proportions specified by the max basewidth or
            false if the image preview process fails
        """

        img_type = self.type
        img = self.body

        if img_type in EXTENSIONS:
            try:
                img_buffer = StringIO.StringIO()
                img = PIL.Image.open(StringIO.StringIO(img))
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                img_format = img_type
                img.save(img_buffer, img_format)

                return img_buffer.getvalue()

            except:
                return False
        else:
            return False

    def encode_preview(self):
        return base64.b64encode(self.preview)

    def encode(self):
        return base64.b64encode(self.body)

    def get_att_type(self, att):
        return att.type.split("/")[1]

    def get_body(self, att):
        return att.body()

    def get_att_id(self, att):
        return hex(id(att))

    def get_secure_id(self, att):
        return sha256(self.get_att_id(att)).hexdigest()

    def get_att_name(self, att):
        return att.name()

    def get_msg_date(self, msg):
        date = msg.datetime()
        day = date[2]
        month = date[1]
        year = date[0]
        return {"day":day,"month":month,"year":year}
