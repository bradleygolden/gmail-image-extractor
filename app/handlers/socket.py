import os
import tornado
from app.objects.extractor import GmailImageExtractor
import config

state = {}


def plural(msg, num):
    if num == 1:
        return msg
    else:
        return u"{0}s".format(msg)


class SocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        self.stop = False
        self.attachment_count = 0
        self.write_message({'ok': True,
                            "type": "ws-open",
                            "msg": u"Waiting for the server..."})
        self.timer = None

    def on_message(self, message):
        msg = tornado.escape.json_decode(message)
        if 'type' not in msg:
            return
        elif msg['type'] == 'connect':
            self._handle_connect(msg)
        elif msg['type'] == 'delete':
            self._handle_delete(msg)
        elif msg['type'] == 'save':
            self._handle_save(msg)
        elif msg['type'] == 'remove-zip':
            self._handle_remove_zip(msg)
        elif msg['type'] == 'stop':
            self._handle_stop(msg)
        else:
            return

    @tornado.web.asynchronous
    def _handle_connect(self, msg, callback=None):

        access_token = self.get_secure_cookie('access_token')
        email = self.get_secure_cookie('email')
        num_messages = 0
        self.extraction_complete = False

        state['extractor'] = GmailImageExtractor(email,
                                                 access_token, limit=int(msg['limit']),
                                                 batch=int(msg['simultaneous']),
                                                 replace=bool(msg['rewrite']))
        if not state['extractor'].connect():
            self.write_message({'ok': False,
                                "type": "connect",
                                'msg': u"Unable to connect to Gmail with provided credentials"})
        else:
            self.write_message({'ok': True,
                                "type": "connect",
                                "msg": u"Successfully connected with Gmail."})

            num_messages = state['extractor'].num_messages_with_attachments()
            self.write_message({'ok': True,
                                "type": "count",
                                "msg": u"Found {0} {1} with attachments"
                                "".format(num_messages, plural(u"message", num_messages)),
                                "num": num_messages})

            def _status(*args):
                if self.stop:
                    return
                else:
                    if args[0] == 'image':
                        self.write_message({"ok": True,
                                            "type": "image",
                                            "msg_id": args[1],
                                            "id": args[2],
                                            "name": args[3],
                                            "preview": args[4],
                                            "ext": args[5],
                                            "date": args[6]})

                    if args[0] == 'message':
                        status_msg = u"Scanning messages {1} of {2}".format(msg['simultaneous'],
                                                                           args[1], num_messages)
                        self.write_message({"ok": True,
                                            "type": "downloading",
                                            "msg": status_msg,
                                            "num": args[1]})

                    if args[0] == 'download-complete':
                        self.extraction_complete = True

                    if args[0] == 'attachment-count' and self.extraction_complete:
                        attachment_count = args[1] - 1
                        self.attachment_count = attachment_count
                        self.write_message({"ok": True,
                            "type": "download-complete",
                            "msg": "Succesfully found {0} {1}"
                            "".format(attachment_count, plural(u"image", attachment_count)),
                            "num": attachment_count})

            extractor = state['extractor']
            loop = tornado.ioloop.IOLoop.current()
            loop.add_callback(callback=lambda: extractor.async_extract(_status, num_messages=num_messages))

    def _handle_delete(self, msg):
        extractor = state['extractor']

        def _delete_status(*args):
            update_type = args[0]

            # don't write this message, the front end removes images
            # if update_type == "image-removed" and False:
            #     self.write_message({"ok": True,
            #                         "type": "image-removed",
            #                         "msg": u"Removed {0} out of {1} {2}."
            #                         "".format(args[1],
            #                                   args[2],
            #                                   plural(u"image", args[2])),
            #                         "gmail_id": args[3],
            #                         "image_id": args[4]})

        try:
            num_messages_changed, num_images_deleted = extractor.delete(msg, callback=_delete_status)
        except:
            # couldn't complete delete
            # this possibly occurred because the user tried to delete the same image twice
            pass
        self.write_message({"ok": True,
                            "type": "finished",
                            "msg": u"Removed {0} {1} total from {2} {3}."
                            "".format(num_images_deleted,
                                      plural(u"image", num_images_deleted),
                                      num_messages_changed,
                                      plural(u"message", num_messages_changed))})

    def _handle_save(self, msg):
        extractor = state['extractor']

        def _save_status(*args):
            update_type = args[0]

            if update_type == "save-passed":
                self.write_message({"ok": True,
                                    "type": "save",
                                    "images": args[1],
                                    "image_names": args[2]})

            if update_type == "saved-zip":
                save_zip_passed = args[1]
                file_name = args[2]
                file_link = file_name

                download_path = "/download/" + file_link

                if save_zip_passed:
                    self.write_message({"ok": True,
                                        "link": u"""<a href="{0}"
                                        target="_blank" download>"""
                                        "<h3>Click Here to Download Your Gmail Images</h3>"
                                        "</a></br></br>"
                                        "<span>"
                                        "Time left before your link dissapears or click the "
                                        "timer now to delete the link..."
                                        "</span></br>"
                                        "<a id=""remove-now"" href=""#"">"
                                        "<div id='circle' class='circle'>"
                                        "<strong class='circle-text'>{2}</strong></div></a>"
                                        "".format(download_path,
                                                  plural(u"minute",
                                                         config.zip_removal_countdown/60),
                                                  config.zip_removal_countdown/60),
                                        "type": "saved-zip",
                                        "time": config.zip_removal_countdown/60})

                    def _remove_link():
                        email = self.get_secure_cookie('email')
                        try:
                            extractor.remove_zip(email, _save_status)
                        except:
                            return
                        self.write_message({"ok": True,
                                            "type": "removed-zip",
                                            "msg": "Please check all attachments that"
                                            " you want to remove from your Gmail account."})

                    loop = tornado.ioloop.IOLoop.instance()

                    #now remove the link after n minutes + 1/3 n minutes
                    self.timer = loop.call_later(config.zip_removal_countdown + int(config.zip_removal_countdown/10), _remove_link)

                else:
                    self.write_message(self.write(
                        "<span> Failed to create zip file :( </span>"))

        email = self.get_secure_cookie('email')
        try:
            extractor.save(msg, email, _save_status)
        except:
            pass

    def _handle_remove_zip(self, msg):
        extractor = state['extractor']

        def _remove_status(*args):
            update_type = args[0]
            if update_type == "removed-zip":
                removed_zip_passed = args[1]

                if removed_zip_passed:
                    try:
                        self.write_message({"ok": True,
                                            "type": "removed-zip",
                                            "msg": "Please check all attachments that you want to"
                                            " remove from your Gmail account."})
                    except:
                        pass

        email = self.get_secure_cookie('email')

        # first clear any pending timeouts
        if self.timer:
            loop = tornado.ioloop.IOLoop.instance()
            loop.remove_timeout(self.timer)
            self.timer = None

        # remove the zip file upon timeout or user request
        extractor.remove_zip(email, _remove_status)

    def _handle_sync(self, msg):
        extractor = state['extractor']

        self.write_message({"ok": True,
                            "type": "file-checking",
                            "msg": u"Checking to see which files have been deleted."})
        num_deletions = extractor.check_deletions()
        self.write_message({"ok": True,
                            "type": "file-checked",
                            "msg": u"Found {0} {1} deleted"
                            "".format(num_deletions, plural(u"image", num_deletions)),
                            "num": num_deletions})

    def _handle_confirmation(self, msg):
        extractor = state['extractor']

        def _sync_status(*args):
            update_type = args[0]
            if update_type == "fetch":
                self.write_message({"ok": True,
                                    "type": "removing",
                                    "msg": u"Removing {0} {1} from message '{2}'."
                                    "".format(args[2], args[1], plural(u"image", args[2]))})
            elif update_type == "write":
                self.write_message({"ok": True,
                                    "type": "removed",
                                    "msg": u"Writing altered version of '{0}' to Gmail."
                                    "".format(args[1])})

        num_attch_removed, num_msg_changed = extractor.sync(callback=_sync_status)
        self.write_message({"ok": True,
                            "type": "finished",
                            "msg": u"Removed {0} {1} from {2} {3}."
                            "".format(num_attch_removed,
                                      plural(u"image", num_attch_removed),
                                      num_msg_changed,
                                      plural(u"message", num_msg_changed))})

    def _handle_stop(self, msg):
        extractor = state['extractor']
        extractor.stop = True
        self.stop = True
        attachment_count = self.attachment_count

        # allow front end to display status message to user
        # status messages are delayed to callbacks
        # this gives the apperance that the stop is immediate to the user

    def on_close(self):
        # remove the user's zip file
        try:
            email = self.get_secure_cookie('email')
            state['extractor'].remove_zip(email)
        except:
            pass

        state['extractor'] = None
