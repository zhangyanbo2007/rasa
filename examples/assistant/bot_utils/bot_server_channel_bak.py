from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime

from flask_cors import CORS

from rasa_core.channels.channel import UserMessage
from rasa_core.channels.channel import InputChannel, OutputChannel
from rasa_core.events import SlotSet

import logging
logger = logging.getLogger()
#########################################################################
import inspect
import json
import uuid
from uuid import uuid4
from multiprocessing import Queue
from threading import Thread

from typing import Text, List, Dict, Any, Optional, Callable, Iterable

from flask import Blueprint, jsonify, request, Flask, Response, make_response

from rasa_core import utils

#########################################################################

def button_to_string(button, idx=0):
    """Create a string representation of a button."""

    title = button.pop('title', '')

    if 'payload' in button:
        payload = " ({})".format(button.pop('payload'))
    else:
        payload = ""

    # if there are any additional attributes, we append them to the output
    if button:
        details = " - {}".format(json.dumps(button, sort_keys=True))
    else:
        details = ""

    button_string = "{idx}: {title}{payload}{details}".format(
        idx=idx + 1,
        title=title,
        payload=payload,
        details=details)

    return button_string

def element_to_string(element, idx=0):
    """Create a string representation of an element."""

    title = element.pop('title', '')

    element_string = "{idx}: {title} - {element}".format(
        idx=idx + 1,
        title=title,
        element=json.dumps(element, sort_keys=True))

    return element_string


class CollectingOutputChannel(OutputChannel):
    """Output channel that collects send messages in a list

    (doesn't send them anywhere, just collects them)."""

    def __init__(self):
        self.messages = []

    @classmethod
    def name(cls):
        return "collector"

    @staticmethod
    def _message(recipient_id,
                 text=None,
                 image=None,
                 buttons=None,
                 attachment=None):
        """Create a message object that will be stored."""

        obj = {
            "recipient_id": recipient_id,
            "text": text,
            "image": image,
            "buttons": buttons,
            "attachment": attachment
        }

        # filter out any values that are `None`
        return utils.remove_none_values(obj)

    def latest_output(self):
        if self.messages:
            return self.messages[-1]
        else:
            return None

    def _persist_message(self, message):
        self.messages.append(message)

    def send_text_message(self, recipient_id, message):
        for message_part in message.split("\n\n"):
            self._persist_message(self._message(recipient_id,
                                                text=message_part))

    def send_text_with_buttons(self, recipient_id, message, buttons, **kwargs):
        self._persist_message(self._message(recipient_id,
                                            text=message,
                                            buttons=buttons))

    def send_image_url(self, recipient_id: Text, image_url: Text) -> None:
        """Sends an image. Default will just post the url as a string."""

        self._persist_message(self._message(recipient_id,
                                            image=image_url))

    def send_attachment(self, recipient_id: Text, attachment: Text) -> None:
        """Sends an attachment. Default will just post as a string."""

        self._persist_message(self._message(recipient_id,
                                            attachment=attachment))

class QueueOutputChannel(CollectingOutputChannel):
    """Output channel that collects send messages in a list

    (doesn't send them anywhere, just collects them)."""

    @classmethod
    def name(cls):
        return "queue"

    def __init__(self, message_queue: Queue = None) -> None:
        super(QueueOutputChannel).__init__()
        self.messages = Queue() if not message_queue else message_queue

    def latest_output(self):
        raise NotImplemented("A queue doesn't allow to peek at messages.")

    def _persist_message(self, message):
        self.messages.put(message)


class FileMessageStore:

    DEFAULT_FILENAME = "message_store.json"

    def __init__(self, filename=DEFAULT_FILENAME):
        self._store = defaultdict(list)
        self._filename = filename
        try:
            for k, v in json.load(open(self._filename, "r")).items():
                self._store[k] = v
        except IOError:
            pass

    def log(self, cid, username, message, uuid=None):
        if uuid is None:
            uuid = str(uuid4())
        self._store[cid].append(
            {
                "time": datetime.utcnow().isoformat(),
                "username": username,
                "message": message,
                "uuid": uuid,
            }
        )
        self.save()

    def clear(self, cid):
        self._store[cid] = []
        self.save()

    def save(self):
        json.dump(self._store, open(self._filename, "w"))

    def __getitem__(self, key):
        return self._store[key]

class BotServerOutputChannel(OutputChannel):
    def __init__(self, message_store):
        self.message_store = message_store

    def send_text_message(self, recipient_id, message):
        for message_part in message.split("\n\n"):
            self.message_store.log(
                recipient_id, "bot", {"type": "text", "text": message_part}
            )

    def send_text_with_buttons(self, recipient_id, message, buttons, **kwargs):
        # type: (Text, Text, List[Dict[Text, Any]], **Any) -> None
        """Sends buttons to the output.
        Default implementation will just post the buttons as a string."""

        self.send_text_message(recipient_id, message)
        self.message_store.log(
            recipient_id, "bot", {"type": "button", "buttons": buttons}
        )

    def send_image_url(self, recipient_id, image_url):
        # type: (Text, Text) -> None
        """Sends an image. Default will just post the url as a string."""

        self.message_store.log(
            recipient_id, "bot", {"type": "image", "image": image_url}
        )

class BotServerInputChannel(InputChannel):

    def __init__(
        self, agent=None, preprocessor=None, port=5002, message_store=FileMessageStore()
    ):
        logging.basicConfig(level="DEBUG")
        logging.captureWarnings(True)
        self.message_store = message_store
        self.on_message = lambda x: None
        self.cors_origins = [u'*']
        self.agent = agent
        self.port = port
        self.preprocessor = preprocessor

    @classmethod
    def name(cls):
        return "chatbox"


    @staticmethod
    def on_message_wrapper(on_new_message, text, queue, sender_id):
        collector = QueueOutputChannel(queue)

        message = UserMessage(text, collector, sender_id,
                              input_channel=BotServerInputChannel.name())
        on_new_message(message)

        queue.put("DONE")

    def _extract_sender(self, req):
        return req.json.get("sender", None)

    # noinspection PyMethodMayBeStatic
    def _extract_message(self, req):
        return req.json.get("message", None)

    def stream_response(self, on_new_message, text, sender_id):
        from multiprocessing import Queue

        q = Queue()

        t = Thread(target=self.on_message_wrapper,
                   args=(on_new_message, text, q, sender_id))
        t.start()
        while True:
            response = q.get()
            if response == "DONE":
                break
            else:
                yield json.dumps(response) + "\n"


    def blueprint(self, on_new_message):
        bot_server_webhook = Blueprint('bot_server_webhook', __name__)
        CORS(bot_server_webhook)

        @bot_server_webhook.route("/health", methods=["GET"])
        def health():
            return "healthy"

        @bot_server_webhook.route("/webhook", methods=['POST'])
        def receive():
            sender_id = self._extract_sender(request)
            text = self._extract_message(request)
            should_use_stream = utils.bool_arg("stream", default=False)

            if should_use_stream:
                return Response(
                    self.stream_response(on_new_message, text, sender_id),
                    content_type='text/event-stream')
            else:
                collector = CollectingOutputChannel()
                on_new_message(UserMessage(text, collector, sender_id,
                                           input_channel=self.name()))
                return jsonify(collector.messages)

        @bot_server_webhook.route("/conversations/<cid>/log", methods=["GET"])
        def show_log(cid):
            return json.dumps(self.message_store[cid])

        # zyb 此函数目前不好使，待测试
        @bot_server_webhook.route("/conversations/<cid>/tracker", methods=["GET"])
        def tracker(cid):
            if self.agent:
                tracker = self.agent.tracker_store.get_or_create_tracker(cid)
                tracker_state = tracker.current_state(
                    should_include_events=True,
                    only_events_after_latest_restart=True
                )

                return json.dumps(tracker_state)
            else:
                return make_response("Could not access agent", 400)

        @bot_server_webhook.route("/conversations/<cid>/say", methods=["GET"])
        def say(cid):
            message = bytes(request.args.get("message", default=""), "utf8")
            _payload = bytes(request.args.get("payload", default=""), "utf8")
            _display_name = bytes(request.args.get("display_name", default=""), "utf8")
            _uuid = bytes(request.args.get("uuid", default=""), "utf8")
            logger.info(message)

            if len(_display_name) > 0 and self.agent:
                display_name, = _display_name
                tracker = self.agent.tracker_store.get_or_create_tracker(cid)
                if (
                    "display_name" in tracker.current_slot_values()
                    and tracker.get_slot("display_name") != display_name
                ):
                    tracker.update(SlotSet("display_name", display_name.decode("utf-8")))
                    self.agent.tracker_store.save(tracker)

            if message == b"_restart":
                self.message_store.clear(cid)
            else:
                if len(_uuid) > 0:
                    self.message_store.log(
                        cid,
                        cid,
                        {"type": "text", "text": message.decode("utf-8")},
                        _uuid.decode("utf-8"),
                    )
            if len(_payload) > 0:
                on_new_message(
                    UserMessage(
                        _payload.decode("utf-8"),
                        output_channel=BotServerOutputChannel(self.message_store),
                        sender_id=cid,
                    ),
                    preprocessor=self.preprocessor
                )
            else:
                on_new_message(
                    UserMessage(
                        message.decode("utf-8"),
                        output_channel=BotServerOutputChannel(self.message_store),
                        sender_id=cid,
                    ),
                    preprocessor=self.preprocessor
                )
            return make_response("OK", 200)

        return bot_server_webhook
