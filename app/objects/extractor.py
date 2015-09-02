import os
import config
import PIL
from PIL import Image
import StringIO
from hashlib import sha256
import hmac
import base64
import pygmail.errors
from pygmail.account import Account
import zipfile
import time
import tornado
from app.objects.image import Image
import re


ATTACHMENT_MIMES = ('image/jpeg', 'image/png', 'image/gif')


class GmailImageExtractor(object):
    """Image extracting class which handles connecting to gmail on behalf of
    a user over IMAP, extracts images from messages in a Gmail account,
    sends them over websockets to be displayed on a web page, allows users, and
    then syncronizes the messages in the gmail account by deleting the
    images the user selected in the web interface.
    """

    def __init__(self, email, access_token, limit=None, batch=10, replace=False):
        """
        Args:
            email -- the username of the Gmail account to connect to
            access_token -- the access_token of the Gmail account to connect to

        Keyword Args:
            limit   -- an optional limit of the total number of messages to
                       download from the gmail account.
            batch   -- the maximum number of messages to download from Gmail
                       at the same time.
            replace -- whether to rewrite the messages in the Gmail account
                       in place (True) or to just write a second, parallel
                       copy of the altered message and leave the original
                       version alone.

        raise:
            ValueError -- If the given dest path to write extracted images to
                          is not writeable.
        """
        self.limit = limit
        self.batch = batch
        self.replace = replace
        self.email = email
        self.access_token = access_token
        self.stop = False
        self.num_attachments = 0
        self.attachment_count = 0

    def sign_request(self, raw):
        """Takes a predefined secret key and gmail's unique message id concatenated with
        the hash of the image within that message. Sha256 is used for hashing.

        Return:
            An authenticated hash using the specified hmac_key in
            config.py.
        """

        key = config.hmac_key
        self.raw = raw
        hashed = hmac.new(key, raw, sha256)

        return hashed.digest().encode("base64").rstrip('\n')

    def connect(self):
        """Attempts to connect to Gmail using the username and access_token provided
        at instantiation.

        Returns:
            Returns a boolean description of whether we were able to connect
            to Gmail using the current parameters.
        """

        mail = Account(self.email, oauth2_token=self.access_token)
        trash_folder = mail.trash_mailbox()
        if pygmail.errors.is_error(trash_folder):
            return False
        else:
            self.mail = mail
            self.trash_folder = trash_folder
            self.inbox = mail.all_mailbox()
            return True

    def num_messages_with_attachments(self):
        """Checks to see how many Gmail messages have attachments in the
        currently connected gmail account.

        This should only be called after having succesfully connected to Gmail.

        Return:
            The number of messages in the Gmail account that have at least one
            attachment (as advertised by Gmail).
        """

        limit = self.limit if self.limit > 0 else False
        gm_ids = self.inbox.search("has:attachment", gm_ids=True, limit=limit)
        return len(gm_ids)

    def image_generator(self, some_messages, callback=None):
        """Generator for images in a given mailbox"""
        offset = 0
        outer = 0
        inner = 0

        for a_message in some_messages:
            msg_id = a_message.gmail_id
            for att in a_message.attachments():
                if att.type in ATTACHMENT_MIMES:
                    att_type = att.type.split("/")[1]
                    an_image = Image(a_message, att)

                    # map each image id with a corresponding message id for later parsing
                    # TODO - fix mapping
                    if an_image.id in self.mapping:
                        self.mapping[msg_id].append(a_message)
                    else:
                        self.mapping[msg_id] = [a_message]

                    self.num_attachments = self.count_attachments(self.num_attachments)
                    yield an_image

    def count_attachments(self, num_att):
        return num_att + 1

    def message_batch(self, offset, per_page, search_string="has:attachment"):

        messages = self.inbox.search(search_string, full=True,
                                     limit=per_page, offset=offset)

        offset += len(messages)

        return messages, offset

    def async_extract(self, callback=None, num_messages=False):
        """Extracts attachments asyncronously from Gmail messages, encodes them into strings,
        and sends them via websocket to the frontend.

        Note: This is a wrapper for do_async_extract

        Keyword Args:
            callback -- An optional function that will be called with updates
            about the image extraction process.
        """

        def _cb(*args):
            if callback:
                callback(*args)

        if num_messages == False:
            num_messages = self.num_messages_with_attachments()

        offset = 0
        per_page = min(self.batch, self.limit) if self.limit else self.batch
        self.extracted_images = []
        self.mapping = {}
        self.num_messages_count = 0
        hit_limit = False

        #callback to begin extraction process asyncronously
        loop = tornado.ioloop.IOLoop.current()
        loop.add_callback(callback=lambda: self.do_async_extract(offset, per_page, callback, num_messages));

    def do_async_extract(self, offset, per_page, callback=None, num_messages=False):
        """Extracts attachments asyncronously from Gmail messages, encodes them into strings,
        and sends them via websocket to the frontend.

        Keyword Args:
            num_messages_with_attachments -- The total number of messages with attachments
            offset -- Same as the number of images extracted thus far.
            This argument also gives the Pygmail interface a reference
            point as to where to extract messages.
            per_page -- This program extracts messages in batches. This
            argument determines how many messages to extract per batch.
            callback -- An optional function that will be called with updates
            about the image extraction process. If provided,
            will be called with either the following arguments:
                            ('message', first)
                            when fetching messages from Gmail, where `first` is the
                            index of the current message being downloaded.
        """

        def _cb(*args):
            if callback:
                callback(*args)

        # check if user hit stop
        if self.stop == True:
            _cb('download-complete', num_messages)
            return

        # get messages for extraction, keep track of the offset for future batches
        messages, offset = self.message_batch(offset, per_page)

        if len(messages) == 0:
            _cb('download-complete', num_messages)
            return

        _cb('message', offset)

        #generator that produces images from given messages
        images = self.image_generator(messages, callback)

        loop = tornado.ioloop.IOLoop.current()

        # extract images from messages using image_generator
        loop.add_callback(callback=lambda: self.extract_images(images, callback))

        # send extracted images to front-end for display
        loop.add_callback(callback=lambda: self.output_images(self.extracted_images, callback))

        # get next batch of messages
        loop.add_callback(callback=lambda: self.do_async_extract(offset, per_page, callback, num_messages))


    def output_images(self, images, callback=None):

        def _cb(*args):
            if callback:
                callback(*args)
        try:
            image = images.pop(1) # remove the image as it's displayed to prevent duplicates
            _cb('image', image.msg_id, image.id, image.name, image.encode_preview(), image.type, image.date)
            loop = tornado.ioloop.IOLoop.current()
            loop.add_callback(callback=lambda: self.output_images(images, callback))
        except:
            #images list is now empty, no more images to output
            pass

    def extract_images(self, images, callback=None):

        def _cb(*args):
            if callback:
                callback(*args)
        try:
            #recursively call fn to get remaining images if they exists
            image = images.next()
            #send image to the frontend
            loop = tornado.ioloop.IOLoop.current()
            self.extracted_images.append(image)
            loop.add_callback(callback=lambda: self.extract_images(images, callback))
            self.attachment_count += 1
            _cb('attachment-count', self.attachment_count)

        except StopIteration:
            pass

    def order_by_g_id(self, selected_images):
        ordered_by_g_id = dict()

        for gmail_id, an_attachment in selected_images['image']:
                if gmail_id in ordered_by_g_id:
                    ordered_by_g_id[gmail_id].append(an_attachment)
                else:
                    ordered_by_g_id[gmail_id] = [an_attachment]

        return ordered_by_g_id

    def replace_att_id(self, ordered_by_gmail_id):
        messages_to_change = dict()

        for gmail_id in ordered_by_gmail_id:
            message_to_change = self.mapping[gmail_id][0]
            attach_ids = {hex(id(a)): a for a in message_to_change.attachments()}

            for an_attachment in ordered_by_gmail_id[gmail_id]:
                if gmail_id in messages_to_change:
                    messages_to_change[gmail_id].append(attach_ids[an_attachment])
                else:
                    messages_to_change[gmail_id] = [attach_ids[an_attachment]]

        return messages_to_change

    def parse_selected_images(self, selected_images):
        """Takes in a dictionary message containing both unique message
        identifiers and unique image identifiers and sorts them. This is
        done because multiple images can be selected for deletion and
        multiple images can be in the same message.

        Returns:
            A dict of message attachments sorted by gmail_id

            i.e. {"12345": [<pygmail.message.Attachment object at 0x321,
                            <pygmail.message.Attachment object at 0x331],
                  "98765": [<pygmail.message.Attachment object at 0x543]}
        """

        ordered_by_gmail_id = dict()

        # first group and order selected images by gmail_id and attachment_id
        ordered_by_gmail_id = self.order_by_g_id(selected_images)

        # replace attachment_id with attachment object from message with corresponding gmail_id
        parsed_selected = self.replace_att_id(ordered_by_gmail_id)

        return parsed_selected

    def do_delete(self, messages_to_change, callback=None):
        """
        Itereates through a dictionary of messages selected by the user
        and deletes attachments within those messages.

        This function must be used in conjuction with parse_selected_images.

        Returns:
            Number of messages where attachments were removed
        """

        label = "Images redacted"

        num_images_deleted = 0
        num_images_to_delete = 0
        image_id = ""

        # calculate total images that need to be deleted
        for message, some_images in messages_to_change.iteritems():
            for an_image in some_images:
                num_images_to_delete += 1

        num_messages_changed = 0

        def _cb(*args):
            if callback:
                callback(*args)

        for gmail_id, some_attachments in messages_to_change.iteritems():
            for an_attachment in some_attachments:
                image_id = hex(id(an_attachment))
                if an_attachment.remove():
                    num_images_deleted += 1
                    _cb('image-removed', num_images_deleted, num_images_to_delete, gmail_id,
                        image_id)
            some_attachments[0].message.save(self.trash_folder.name, safe_label=label)
            num_messages_changed += 1

        return num_messages_changed, num_images_deleted

    def delete(self, msg, label='"Images redacted"', callback=None):
        """
        Keyword Args:
            label    -- Gmail label to use either as a temporary work label
            (if instatiated with replace=True) or where the altered
            images will be stored (if instatiated with
            replace=False). Note that this label should be in valid
            ATOM string format.
            callback -- An optional funciton that will be called with updates
            about the message update process. If provided,
            will be called with the following sets of arguments:

                        ('write', subject)
                        Called before writing the altered version of the message
                        back to Gmail.

        Returns:
            Two values, first being the number of attachments that were removed
            from messages in Gmail, and second is the number of messages that
            were altered.
            """

        if len(msg) == 0:
            return 0, 0

        def _cb(*args):
            if callback:
                callback(*args)

        messages = {}

        try:
            messages = self.parse_selected_images(msg)
        except:
            # print "Couldn't parse selected images."
            pass

        num_messages_changed, num_images_deleted = self.do_delete(messages, callback)

        return num_messages_changed, num_images_deleted

    def zip_images(self, messages_to_save):
        """
        Creates a zip archive of images that were selected by the user.

        This function must be used in conjunction with the function parse_selected_images.
        """

        s = StringIO.StringIO()

        try:
            with zipfile.ZipFile(s, mode='w') as zf:
                for message, some_images in messages_to_save.iteritems():
                    for an_image in some_images:
                        zf.writestr(an_image.name(), an_image.body())

            return True, zf

        except:
            zf.close()

            return False

    def write_zip(self, zip_file, callback=None):
        """Writes a zip file to a specified save path
        """

        def _cb(*args):
            if callback:
                callback(*args)

        try:
            curr_path = os.path.dirname(os.path.abspath(__file__))

            save_path = curr_path + "/user_downloads"

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            name_of_file = "gmail_images.zip"

            full_file_name = os.path.join(save_path, name_of_file)

            fp = open(full_file_name, "w")

            fp.write(zip_file)

            fp.close()

            zip_file.close()

            _cb('write-zip', True, name_of_file)

            return True

        except:

            _cb('write-zip', False)

            return False

    def get_abs_path(self, file_name=None):
        home_path = os.path.expanduser("~")
        save_path = "/Gmail-Image-Extractor/download/"
        abs_path = home_path + save_path

        if file_name:
            abs_path = abs_path + file_name + ".zip"

        return abs_path

    def do_save(self, messages_to_save, email, callback=None):

        def _cb(*args):
            if callback:
                callback(*args)

        file_name = email + ".zip"
        name_dict = dict()

        try:
            abs_path = self.get_abs_path()

            if not os.path.exists(abs_path):
                os.makedirs(abs_path)

            file_path = os.path.join(abs_path, file_name)

            with zipfile.ZipFile(file_name, mode='w') as zf:
                for message, some_images in messages_to_save.iteritems():
                    for an_image in some_images:

                        # now we have to handle any duplicate file names
                        # before writing them to the zip file
                        att_type = an_image.name()[-4:]
                        att_name = an_image.name()[:-4]

                        # loop until duplicate is not found in the dictionary
                        count = 1
                        while att_name in name_dict:
                            #remove previous tag
                            att_name = re.split("\([0-9]*\)", att_name)[0]
                            att_name = att_name + "(" + str(count) + ")"
                            count += 1


                        #add name to the dictionary to track for later
                        name_dict[att_name] = [att_name]

                        #combine attachment name and attachment type
                        full_file_name = att_name + att_type

                        zf.writestr(full_file_name, an_image.body())

            os.rename(file_name, file_path)

            _cb('saved-zip', True, file_name)

        finally:
            zf.close()

    def remove_zip(self, file_no_ext=None, callback=None):

        if not file_no_ext:
            return

        def _cb(*args):
            if callback:
                callback(*args)

        file_w_ext = self.get_abs_path(file_no_ext)

        if file_w_ext:

            try:
                # remove folder and contents
                os.remove(file_w_ext)
                if callback:
                    try:
                        _cb('removed-zip', True)
                    except:
                        pass
            finally:
                return

    def save(self, msg, email, callback=None):
        """
        Arranges msg by gmailid and attachment
        Wrapper for do_save function
        """
        def _cb(*args):
            if callback:
                callback(*args)
        try:
            messages = self.parse_selected_images(msg)
            self.do_save(messages, email, callback)
        except:
            _cb("save_failed", [])
        finally:
            return
