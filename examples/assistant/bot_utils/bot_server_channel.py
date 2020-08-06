from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import asyncio
import inspect
import json
import logging
from asyncio import Queue, CancelledError
from sanic import Sanic, Blueprint, response
from sanic.request import Request
from typing import (
    Text,
    List,
    Dict,
    Any,
    Optional,
    Callable,
    Coroutine,
    Iterable,
    Awaitable,
)

from collections import defaultdict
import uuid
from uuid import uuid4
from datetime import datetime

import rasa.utils.endpoints
from rasa.constants import DOCS_BASE_URL
from rasa.core import utils

try:
    from urlparse import urljoin  # pytype: disable=import-error
except ImportError:
    from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from rasa.core.channels.channel import UserMessage
from rasa.core.channels.channel import InputChannel, OutputChannel, CollectingOutputChannel, QueueOutputChannel
from rasa.core.events import SlotSet

import jieba
import os
import re
from pypinyin import pinyin, lazy_pinyin, Style
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)) + '/api')
from qa_item_api import get_qa_item

class FileMessageStore:

    DEFAULT_FILENAME = "message_store.json"

    def __init__(self, filename=DEFAULT_FILENAME):
        self._store = defaultdict(list)
        self._filename = filename
        try:
            for k, v in json.load(open(self._filename, "r", encoding="utf-8")).items():
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
        with open(self._filename, "w", encoding="UTF-8") as f:
            json.dump(self._store, f, ensure_ascii=False, indent=2, sort_keys=True)

    def __getitem__(self, key):
        return self._store[key]


# zyb-add -> 对接chatbox网页接口-单独对话(message=_restart标示清除对话)
class BotServerCollectingOutputChannel(OutputChannel):
    def __init__(self, message_store):
        self.message_store = message_store

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        for message_part in text.split("\n\n"):
            temp_string = message_part.replace("\'", "\"")
            temp_dict = json.loads(temp_string.replace("None", "\"none\""))
            self.message_store.log(
                recipient_id, "bot", {"type": "text", "text": temp_dict["ans_list"][0]}
            )

    async def send_image_url(
        self, recipient_id: Text, image: Text, **kwargs: Any
    ) -> None:
        """Sends an image. Default will just post the url as a string."""
        self.message_store.log(
            recipient_id, "bot", {"type": "image", "image": image}
        )

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        **kwargs: Any
    ) -> None:
        """Sends buttons to the output.
        Default implementation will just post the buttons as a string."""

        self.send_text_message(recipient_id, text)
        self.message_store.log(
            recipient_id, "bot", {"type": "button", "buttons": buttons}
        )


# zyb-add -> 对接春松标准接口
class BotAppCollectingOutputChannel(OutputChannel):
    def __init__(self):
        self.message_store = []
        self.return_message = []
    @classmethod
    def name(cls):
        return "bot_app_collector"

    @staticmethod
    def _message(
        recipient_id, text=None, image=None, buttons=None, attachment=None, custom=None
    ):
        """Create a message object that will be stored."""

        obj = {
            "rc": 0,
            "data": {
                "state": "default",
                "createdAt": 1543559131688,
                "string": text,
                "topicName": None,
                "subReplies": [],
                "service": {
                    "provider": "conversation"
                },
                "logic_is_fallback": False,
                "logic_is_unexpected": False,
                "botName": "I ROBOT",
                "ergou_faq": [
                    {
                        "id": "AWdjRddmHR0CxALgXwY-",
                        "score": 0.75,
                        "post": "ask_question",
                        "reply": text
                    }
                ]
            }
        }

        # filter out any values that are `None`
        return utils.remove_none_values(obj)

    async def _persist_message(self, message):
        self.message_store.append(message)

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        for message_part in text.split("\n\n"):
            await self._persist_message(message_part)  # 拼接输出字符串

        self.return_message = self._message(recipient_id, text="<br/>".join(self.message_store)) #输出到数组中,因为要在html中显示，换行符用<br/>


# zyb-add -> 对接春松标准接口-判断机器人是否存在
class BotAppGetIDCollectingOutputChannel(OutputChannel):
    def __init__(self):
        self.messages = []

    @classmethod
    def name(cls):
        return "bot_app_get_id_collector"

    @staticmethod
    def _message(
        recipient_id, text=None, image=None, buttons=None, attachment=None, custom=None
    ):
        """Create a message object that will be stored."""

        obj = {
            "rc": 0,
            "data": {
                "chatbotID": recipient_id,
                "name": "小叮当",
                "fallback": "我不明白您的意思。",
                "description": "智能问答和对话任务",
                "welcome": "你好！我是机器人客服。",
                "primaryLanguage": "zh_CN"
            }
        }

        # filter out any values that are `None`
        return utils.remove_none_values(obj)

    async def _persist_message(self, message) -> None:
        self.messages = message

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        self._persist_message(self._message(recipient_id, text=text))


# zyb-add -> 输入接口
class BotServerInputChannel(InputChannel):

    def __init__(self):
        self.message_store = FileMessageStore()
        with open(os.path.dirname(os.path.dirname(__file__))+"/configs/domain_words/domain_words.txt", "r",
                  encoding="utf-8") as f:
            domain_words_list = []
            for line in f.readlines():
                data = line.split()
                if len(data) == 3:
                    domain_words_list.append(data[0])
        self.domain_words_pinyin_list = [{"domain_words": domain_words,
                                          "domain_words_pinyin": pinyin(domain_words,
                                                                        errors="ignore", style=Style.NORMAL)
                                          } for domain_words in domain_words_list]

    @classmethod
    def name(cls):
        return "chatbox"

    @staticmethod
    async def on_message_wrapper(
        on_new_message: Callable[[UserMessage], Awaitable[None]],
        text: Text,
        queue: Queue,
        sender_id: Text,
    ) -> None:
        collector = QueueOutputChannel(queue)

        message = UserMessage(
            text, collector, sender_id, input_channel=BotServerInputChannel.name()
        )
        await on_new_message(message)

        await queue.put("DONE")  # pytype: disable=bad-return-type

    # zyb-note: ->拼音替换，后续加上同义词替换
    def _pinyin_correct(self, message):
        new_message = message
        message_pinyin = pinyin(message, errors="ignore", style=Style.NORMAL)
        match_flag = 0
        last_index = 0
        for message_word_num, message_word_pinyin in enumerate(message_pinyin):
            for domain_words_pinyin in self.domain_words_pinyin_list:
                if len(domain_words_pinyin["domain_words_pinyin"]) >= 2:
                    for domain_word_num, domain_word_pinyin in enumerate(domain_words_pinyin["domain_words_pinyin"]):
                        if message_word_num + domain_word_num < len(message_pinyin):
                            if domain_word_pinyin != message_pinyin[message_word_num+domain_word_num]:
                                match_flag = 0
                                break  # 不匹配直接退出当前索引匹配
                            else:
                                match_flag = 1
                        else:
                            match_flag = 0
                            break  # 不匹配直接退出当前索引匹配
                else:
                    match_flag = 0

                # 当前匹配必须的索引必须大于上一次的末尾索引
                if match_flag == 1 and (message_word_num == 0 or message_word_num > last_index):
                    new1 = []
                    new2 = []
                    for s1 in new_message:
                        new1.append(s1)
                    for s2 in domain_words_pinyin["domain_words"]:
                        new2.append(s2)
                    new1[message_word_num:message_word_num+domain_word_num+1] = new2
                    new_message = "".join(new1)
                    last_index = message_word_num + domain_word_num
                    match_flag = 0
                    break  # 成功匹配上则退出别的关键词匹配
        return new_message

    # zyb-add: -> 新增
    # noinspection PyMethodMayBeStatic
    async def _extract_sender_uid(self, req) -> Optional[Text]:
        return req.json.get("fromUserId", None)

    # zyb-change: start -> 暂时在这里做错别字纠正，后续再观察看。
    def _extract_text_message(self, req):
        message = req.json.get("textMessage", None)
        message = self._pinyin_correct(message)
        return message

    # noinspection PyMethodMayBeStatic
    async def _extract_sender(self, req) -> Optional[Text]:
        return req.json.get("sender", None)

    # zyb-change: start -> 暂时在这里做错别字纠正，后续再观察看。
    # noinspection PyMethodMayBeStatic
    def _extract_message(self, req):
        message = req.json.get("message", None)
        message = self._pinyin_correct(message)
        return message

    def stream_response(
        self,
        on_new_message: Callable[[UserMessage], Awaitable[None]],
        text: Text,
        sender_id: Text,
    ) -> Callable[[Any], Awaitable[None]]:
        async def stream(resp: Any) -> None:
            q = Queue()
            task = asyncio.ensure_future(
                self.on_message_wrapper(on_new_message, text, q, sender_id)
            )
            while True:
                result = await q.get()  # pytype: disable=bad-return-type
                if result == "DONE":
                    break
                else:
                    await resp.write(json.dumps(result) + "\n")
            await task

        return stream  # pytype: disable=bad-return-type

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[None]]):
        bot_server_webhook = Blueprint(
            "bot_server_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        # noinspection PyUnusedLocal
        @bot_server_webhook.route("/", methods=["GET"])
        async def health(request: Request):
            return response.json({"status": "ok"})

        # zyb-add -> 对接标准rasa输出接口
        @bot_server_webhook.route("/webhook", methods=['POST'])
        async def receive(request: Request):
            sender_id = await self._extract_sender(request)
            text = self._extract_message(request)
            should_use_stream = rasa.utils.endpoints.bool_arg(
                request, "stream", default=False
            )

            if should_use_stream:
                return response.stream(
                    self.stream_response(on_new_message, text, sender_id),
                    content_type='text/event-stream')
            else:
                collector = CollectingOutputChannel()
                # noinspection PyBroadException
                try:
                    await on_new_message(
                        UserMessage(
                            text, collector, sender_id, input_channel=self.name()
                        )
                    )
                except CancelledError:
                    logger.error(
                        "Message handling timed out for "
                        "user message '{}'.".format(text)
                    )
                except Exception:
                    logger.exception(
                        "An exception occured while handling "
                        "user message '{}'.".format(text)
                    )
                for num, messages in enumerate(collector.messages):
                    collector.messages[num]["text"] = eval(messages["text"])
                    # 针对商品标题提取关键词实体信息
                    if collector.messages[num]["text"]["type"] == "item":
                        # tfidf关键词抽取
                        from jieba import analyse
                        keywords = analyse.extract_tags(text, topK=5, allowPOS='n', withWeight=True)
                        collector.messages[num]["text"]["entity"]["items_words"] = [keyword for keyword, w in keywords if w > 0.2]
                        # 相似商品链接提取
                        items_list = get_qa_item(text)
                        collector.messages[num]["text"]["match_list"] = \
                            [{item["answer"]: item["question"]} for item in items_list]
                return response.json(collector.messages)

        # zyb-add -> 对接春松标准接口
        @bot_server_webhook.route("/seq2seq_chatbot/<cid>/conversation/query", methods=["POST"])
        async def query(request: Request, cid):
            sender_id = cid
            text = self._extract_text_message(request)
            should_use_stream = rasa.utils.endpoints.bool_arg(
                request, "stream", default=False
            )

            # logger.info(message)

            if should_use_stream:
                return response.stream(
                    self.stream_response(on_new_message, text, sender_id),
                    content_type='text/event-stream')
            else:
                bot_app_collector = BotAppCollectingOutputChannel()
                # noinspection PyBroadException
                try:
                    await on_new_message(
                        UserMessage(
                            text, bot_app_collector, sender_id, input_channel=self.name()
                        )
                    )
                except CancelledError:
                    logger.error(
                        "Message handling timed out for "
                        "user message '{}'.".format(text)
                    )
                except Exception:
                    logger.exception(
                        "An exception occured while handling "
                        "user message '{}'.".format(text)
                    )

                temp_string = bot_app_collector.return_message["data"]["string"]
                temp_string = temp_string.replace("\'", "\"")
                temp_dict = json.loads(temp_string.replace("None", "\"none\""))
                bot_app_collector.return_message = bot_app_collector._message("bot", temp_dict["ans_list"][0])
                return response.json(bot_app_collector.return_message)

        # zyb-add -> 对接春松标准接口-判断机器人是否存在
        @bot_server_webhook.route("/seq2seq_chatbot/<cid>", methods=["GET"])
        async def bot_exist(request: Request, cid):
            # TODO:这个后续要修改下
            # bot_app_get_id_collector = BotAppGetIDCollectingOutputChannel()
            # bot_app_get_id_collector.send_text_message('bot', 'ok')
            return response.json({"status": "ok"})

        # zyb-add -> 对接chatbox网页接口-保存聊天日志(一般用于实时读取tracker数据)
        @bot_server_webhook.route("/conversations/<cid>/log", methods=["GET"])
        async def show_log(request: Request, cid):
            return response.json(self.message_store[cid])

        # zyb-add -> 对接chatbox网页接口-单独对话(message=_restart标示清除对话)
        @bot_server_webhook.route("/conversations/<cid>/say", methods=["GET"])
        async def say(request: Request, cid):
            message = bytes(request.args.get("message", default=""), "utf8")
            _payload = bytes(request.args.get("payload", default=""), "utf8")
            _display_name = bytes(request.args.get("display_name", default=""), "utf8")
            _uuid = bytes(request.args.get("uuid", default=""), "utf8")
            # logger.info(message)
            if message == b"_restart":
                self.message_store.clear(cid)
                return response.json({"status": "ok"})
            else:
                if len(_payload) > 0:
                    await on_new_message(
                        UserMessage(
                            _payload.decode("utf-8"),
                            output_channel=BotServerCollectingOutputChannel(self.message_store),
                            sender_id=cid,
                        )
                    )
                else:
                    await on_new_message(
                        UserMessage(
                            message.decode("utf-8"),
                            output_channel=BotServerCollectingOutputChannel(self.message_store),
                            sender_id=cid,
                        )
                    )
                return response.json({"status": "ok"})

        return bot_server_webhook
