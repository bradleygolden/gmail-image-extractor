import os
import config
import PIL
from PIL import Image
import StringIO
from hashlib import sha256
import hmac
import base64
import pygmail.errors
# from .fs import sanatize_filename, unique_filename
from pygmail.account import Account
import zipfile
import time


ATTACHMENT_MIMES = ('image/jpeg', 'image/png', 'image/gif')


class GmailImageExtractor(object):
    """Image extracting class which handles connecting to gmail on behalf of
    a user over IMAP, extracts images from messages in a Gmail account,
    sends them over websockets to be displayed on a web page, allows users, and
    then syncronizes the messages in the gmail account by deleting the
    images the user selected in the web interface.
    """

    def __init__(self, dest, email, access_token, limit=None, batch=10, replace=False):
        """
        Args:
            dest     -- the path on the file system where images should be
                        extracted and written to.
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
        self.dest = dest

        if not self.validate_path():
            raise ValueError("{0} is not a writeable directory".format(dest))

        self.limit = limit
        self.batch = batch
        self.replace = replace
        self.email = email
        self.access_token = access_token

    def validate_path(self):
        """Checks to see the currently selected destiation path, for where
        extracted images should be written, is a valid path that we can
        read and write from.

        Return:
            A boolean description of whether the currently selected destination
            is a valid path we can read from and write to.
        """
        if not os.path.isdir(self.dest):
            return False
        elif not os.access(self.dest, os.W_OK):
            return False
        else:
            return True

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

    def get_resize_img(self, img, img_type, basewidth=300, supported_formats=('jpeg', 'gif',
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

    def extract(self, callback=None):
        """Extracts images from Gmail messages, encodes them into strings,
        and sends them via websocket to the frontend.

        Keyword Args:
            callback -- An optional function that will be called with updates
            about the image extraction process. If provided,
            will be called with either the following arguments

                        ('image', message id, image id, hmac key)
                        when sending an image via websocket, where
                        `message_id` is the unqiue id of the message,
                        image_id is the unque id of a given image, and
                        hmac key concatenates the message and image id.

                        ('message', first)
                        when fetching messages from Gmail, where `first` is the
                        index of the current message being downloaded.

        Returns:
            The number of attachments found
        """

        def _cb(*args):
            if callback:
                callback(*args)

        attachment_count = 0
        num_messages = 0
        offset = 0
        per_page = min(self.batch, self.limit) if self.limit else self.batch
        # Keep track of which attachments belong to which messages.  Do this
        # by keeping track of all attachments downloaded to the filesystem
        # (used as the dict key) and pairing it with two values, the gmail
        # message id and the hash of the attachment (so that we can uniquely
        # identify the attachment again)
        self.mapping = {}
        hit_limit = False
        while True and not hit_limit:
            _cb('message', offset + 1)
            messages = self.inbox.search("has:attachment", full=True,
                                         limit=per_page, offset=offset)
            if len(messages) == 0:
                break

            # STEP 1 - Scan entire inbox for images
            for msg in messages:
                for att in msg.attachments():
                    if att.type in ATTACHMENT_MIMES:

                        img_name = att.name()

                        # STEP 2 - Note: unique gmail_id for each message
                        msg_id = msg.gmail_id

                        # unique id for each attachment
                        # uses the attachment's hex memory value
                        img_identifier = hex(id(att))

                        # create map to use later for linking
                        # each message with each attachment
                        if img_identifier in self.mapping:
                            self.mapping[msg_id].append(msg)
                        else:
                            self.mapping[msg_id] = [msg]

                        # STEP 3 - Scale down images and encode into base64

                        # Scale down image before encoding
                        try:
                            img = self.get_resize_img(att.body(), att.type, 500)
                        except:
                            img = att.body()

                        if len(img) == 0:  # no img was resized
                            continue

                        # Encode image into base64 format for sending via websocket
                        encoded_img = base64.b64encode(img)

                        # STEP 4 - Build hmac with gmail_id and img_identifier
                        # hmac_req = self.sign_request(msg_id + " " + img_identifier)

                        # STEP 5 - Send message via websockets containing:
                        #          --msg_id: unique id for gmail message
                        #          --image_identifier: hash of image body
                        #          --encoded_img: image in string format encoded
                        #                         in base 64 format
                        #          --hmac: autheticated hash
                        # _cb('image', msg_id, img_identifier, encoded_img, hmac_req)

                        _cb('image', msg_id, img_identifier, encoded_img, img_name)

                        attachment_count += 1
                        num_messages += 1

                        if self.limit > 0 and num_messages >= self.limit:
                            hit_limit = True
                            break

            offset += per_page

        return attachment_count

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

    def save_zip(self, messages_to_save, email, callback=None):

        def _cb(*args):
            if callback:
                callback(*args)

        file_name = email + ".zip"

        try:
            # curr_path = os.path.dirname(os.path.abspath(__file__))
            # app_path = os.path.dirname(curr_path)
            # abs_path = "~/gmail-images/" + email
            abs_path = self.get_abs_path()

            if not os.path.exists(abs_path):
                os.makedirs(abs_path)

            file_path = os.path.join(abs_path, file_name)

            with zipfile.ZipFile(file_name, mode='w') as zf:
                for message, some_images in messages_to_save.iteritems():
                    for an_image in some_images:
                        zf.writestr(an_image.name(), an_image.body())

            os.rename(file_name, file_path)

            _cb('saved-zip', True, file_name)

        except:

            return False

        finally:

            zf.close()

        return True

    def countdown(self, seconds):
        while seconds >= 0:
            seconds -= 1
            time.sleep(1)
        self.remove_zip("gmail_images.zip")

    def countdown_remove_zip(self, seconds, file_name):
        self.countdown(seconds)
        self.remove_zip(file_name)

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
                # shutil.rmtree(abs_path)
                os.remove(file_w_ext)
                if callback:
                    try:
                        _cb('removed-zip', True)
                    except:
                        pass
            finally:
                return

    def get_attachment_count(self, some_messages):

        attachment_count = 0

        for a_message, some_attachments in some_messages.iteritems():
            for an_attachment in some_attachments:
                attachment_count += 1

        return attachment_count

    def do_save(self, messages_to_save, callback=None, max_packet_size=10):
        """
        Sends images in packets of 10 to the front-end
        """

        def _cb(*args):
            if callback:
                callback(*args)

        encoded_images = []
        image_names = []
        packet_size = 0
        images_packaged = 0
        attachment_count = self.get_attachment_count(messages_to_save)

        _cb("image-packet", [], [], 0, 0, attachment_count)

        # loop through each message and extract attachments
        for message, some_images in messages_to_save.iteritems():
            # loop through each image
            for an_image in some_images:
                # encode the image
                encoded_image = base64.b64encode(an_image.body())
                # add encoded image to array of encoded images
                encoded_images.append(encoded_image)
                # save image name
                image_names.append(an_image.name())
                packet_size += 1
                images_packaged += 1

                # packet of images to front-end
                if packet_size == max_packet_size:
                    _cb("image-packet", encoded_images, image_names, packet_size, images_packaged,
                        attachment_count)
                    encoded_images = []
                    image_names = []
                    packet_size = 0

                # print "packaged: %d, total: %d" % (images_packaged, attachment_count)

        # send remaining images
        if packet_size > 0:
            _cb("image-packet", encoded_images, image_names,
                packet_size, images_packaged, attachment_count)

        return

    def save(self, msg, email, callback=None):
        """
        Arranges msg by gmailid and attachment
        Wrapper for do_save function
        """

        def _cb(*args):
            if callback:
                return callback(*args)

        try:
            messages = self.parse_selected_images(msg)
        except:
            print("Couldn't parse selected images.")

        try:
            self.save_zip(messages, email, callback)
            # self.do_save(messages, callback)
            # passed, zip_file = self.zip_images(messages)

            # if(passed):
            #     self.write_zip(zip_file, callback)
            # else:
            #     print("Failed to write zip to disk")
            # _cb("save-passed", packaged_images, image_names)

        except:
            _cb("save_failed", [])

        finally:
            return

    def check_deletions(self):
        """Checks the filesystem to see which image attachments, downloaded
        in the self.extract() step, have been removed since extraction, and
        thus should be removed from Gmail.

        Returns:
            The number of attachments that have been deleted from the
            filesystem.
            """

        # Now we can find the attachments the user wants removed from their
        # gmail account by finding every file in the mapping that is not
        # still on the file system
        #
        # Here we want to group attachments by gmail_id, so that we only act on
        # a single email message once, instead of pulling it down multiple times
        # (which would change its gmail_id and ruin all things)

        self.to_delete = {}
        self.to_delete_subjects = {}
        self.num_deletions = 0
        for a_name, (gmail_id, a_hash, msg_subject) in self.mapping.items():
            if not os.path.isfile(os.path.join(self.dest, a_name)):
                if gmail_id not in self.to_delete:
                    self.to_delete[gmail_id] = []
                    self.to_delete_subjects[gmail_id] = msg_subject
                    self.to_delete[gmail_id].append(a_hash)
                    self.num_deletions += 1
                    return self.num_deletions

    def sync_old(self, label='"Images redacted"', callback=None):
        """Finds image attachments that were downloaded during the
        self.extract() step, and deletes any attachments that were deleted
        from disk from their corresponding images in Gmail.

        Keyword Args:
            label    -- Gmail label to use either as a temporary work label
            (if instatiated with replace=True) or where the altered
            images will be stored (if instatiated with
            replace=False). Note that this label should be in valid
            ATOM string format.
            callback -- An optional funciton that will be called with updates
            about the message update process. If provided,
            will be called with the following sets of arguments:

                        ('fetch', subject, num_attach)
                        Called before fetching a message from gmail. `subject`
                        is the subject of the email message to download, and
                        `num_attach` is the number of attachments to be removed
                        from that message.

                        ('write', subject)
                        Called before writing the altered version of the message
                        back to Gmail.

        Returns:
            Two values, first being the number of attachments that were removed
            from messages in Gmail, and second is the number of messages that
            were altered.
            """

        # try:
        # num_to_delete = self.num_deletions
        # except AttributeError:
        # num_to_delete = self.check_deletions()

        def _cb(*args):
            if callback:
                callback(*args)

        num_msg_changed = 0
        num_attch_removed = 0
        for gmail_id, attch_to_remove in self.to_delete.items():
            msg_sbj = self.to_delete_subjects[gmail_id]

            _cb('fetch', msg_sbj, len(attch_to_remove))
            msg_to_change = self.inbox.fetch_gm_id(gmail_id, full=True)
            attach_hashes = {a.sha1(): a for a in msg_to_change.attachments()}
            removed_attachments = 0
            for attachment_hash in attch_to_remove:
                attach_to_delete = attach_hashes[attachment_hash]
                if attach_to_delete.remove():
                    removed_attachments += 1
                    num_attch_removed += 1

            if removed_attachments:
                num_msg_changed += 1
                _cb('write', msg_sbj)
                if self.replace:
                    msg_to_change.save(self.trash_folder.name, safe_label=label)
                else:
                    msg_to_change.save_copy(label)
                    return num_attch_removed, num_msg_changed
