from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import asyncio
import inspect
import json
import logging
import uuid
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

import rasa.utils.endpoints
from rasa.constants import DOCS_BASE_URL
from rasa.core import utils

try:
    from urlparse import urljoin  # pytype: disable=import-error
except ImportError:
    from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from rasa.core.channels.channel import UserMessage
from rasa.core.channels.channel import InputChannel, OutputChannel
from rasa.core.events import SlotSet
#
# from flask import Blueprint, jsonify, request, Flask, Response, make_response
# from rasa.core import utils

import jieba
import os
import re
from pypinyin import pinyin, lazy_pinyin, Style


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


class BotAppOutputChannel(OutputChannel):
    def __init__(self):
        self.message_store = []
        self.return_message = []
    @classmethod
    def name(cls):
        return "bot_app_collector"

    @staticmethod
    def _message(recipient_id,
                 text=None,
                 image=None,
                 buttons=None,
                 attachment=None):
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
        # return utils.remove_none_values(obj)
        return obj

    def _persist_message(self, message):
        self.message_store.append(message)

    def send_text_message(self, recipient_id, message):
        for message_part in message.split("\n\n"):
            self._persist_message(message_part)  # 拼接输出字符串

        self.return_message = self._message(recipient_id, text="<br/>".join(self.message_store)) #输出到数组中,因为要在html中显示，换行符用<br/>


class BotAppGetID(OutputChannel):
    def __init__(self):
        self.messages = []

    @classmethod
    def name(cls):
        return "bot_app_get_id"

    @staticmethod
    def _message(recipient_id,
                 text=None,
                 image=None,
                 buttons=None,
                 attachment=None):
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
        # return utils.remove_none_values(obj)
        return obj

    def _persist_message(self, message):
        self.messages = message

    def send_text_message(self, recipient_id, message):
        self._persist_message(self._message(recipient_id, text=message))


class BotServerInputChannel(InputChannel):

    def __init__(self):
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

    async def _extract_sender(self, req) -> Optional[Text]:
        return req.json.get("sender", None)

    async def _extract_sender_uid(self, req) -> Optional[Text]:
        return req.json.get("fromUserId", None)

    # noinspection PyMethodMayBeStatic
    def _extract_message(self, req):
        return req.json.get("message", None)

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

    # zyb-change: start -> 暂时在这里做错别字纠正，后续再观察看。
    def _extract_text_message(self, req):
        message = req.json.get("textMessage", None)
        message = self._pinyin_correct(message)
        return message

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[None]]):
        bot_server_webhook = Blueprint(
            "bot_server_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        @bot_server_webhook.route("/", methods=["GET"])
        async def health(request: Request):
            return response.json({"status": "ok"})

        @bot_server_webhook.route("/webhook", methods=['POST'])
        async def receive(request: Request):
            sender_id = self._extract_sender(request)
            text = self._extract_message(request)
            should_use_stream = utils.bool_arg(
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
                return response.json(collector.messages)

        @bot_server_webhook.route("/conversations/<cid>/log", methods=["GET"])
        async def show_log(cid):
            return json.dumps(self.message_store[cid])

        @bot_server_webhook.route("/conversations/<cid>/say", methods=["GET"])
        async def say(request: Request, cid):
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
            return response.json({"status": "ok"})

        @bot_server_webhook.route("/seq2seq_chatbot/<cid>", methods=["GET"])
        async def bot_exist(cid):
            bot_app_get_id = BotAppGetID()
            bot_app_get_id.send_text_message('bot', 'ok')
            return response.json(bot_app_get_id.messages)

        # zyb 对话接口
        @bot_server_webhook.route("/seq2seq_chatbot/<cid>/conversation/query", methods=["POST"])
        async def query(request: Request, cid):
            _uuid = self._extract_sender_uid(request)
            message = self._extract_text_message(request)
            should_use_stream = utils.bool_arg("stream", default=False)

            logger.info(message)

            if should_use_stream:
                return response.stream(
                    self.stream_response(on_new_message, message, _uuid),
                    content_type='text/event-stream')
            else:
                bot_app_collector = BotAppOutputChannel()
                # zyb-note: -> 在这个地方做手脚，优先FAQ匹配，FAQ匹配走不动再进入INTENT+CORE
                # 这个地方没有衔接好，后续考虑两块看怎么做融合，现在之间缺少数据交互的桥梁
                # zyb-add:start -> 增加FAQ匹配，先进行预判断再处理
                # 1判断是否是命令（就好比离线中的聚类的筛选过程，这一步可省略因为FAQ可进行判断）
                # 2判断是否是广告（就好比离线中的聚类的筛选过程）
                ans_dict = {"type": "", "intent": "", "match_item": "", "ans_list": [],
                            "entity": "", "confidence": 0}
                # flow_flag = 0
                # if (re.findall(r".*(?:为你推荐|请问您需要了解吗|办卡套现|本店专业|亲，|谢谢|亲爱的，|不闲聊|在家创业|"
                #                r"为您推荐|你好|包邮|早安|不好意思|点击|新老客户|免费|打扰了|上午好|"
                #                r"下午好|您好|亲们|在吗|一键转发|在抖音|朋友圈|"
                #                r"复制此条|复制这条).*", message) != [] and len(message) >= 20) \
                #         or re.findall(r".*(?:朋友圈.*点个赞|转发.*朋友圈|朋友圈第一条|第一条朋友圈|"
                #                       r"你好，欢迎关注|您好，欢迎关注|在抖音|旺季来了|私信我|感谢关注).*", message) != []:
                #     ans_dict["type"] = "ad"
                #     ans_dict["confidence"] = "1"
                #     ans_dict["ans_list"] = ["针对用户发的广告可以做点儿什么"]
                #     # bot_app_collector.return_message = ans_dict
                #     bot_app_collector.send_text_message("bot", str(ans_dict))
                # else:
                #     match_value = get_qa(message)
                #     # match_value = []
                #     # 3判断是否是FAQ匹配
                #     if len(match_value) >= 1 and match_value[0]["confidence"] >= 0.7:
                #             temp_dict = json.loads(match_value[0]["answer"].replace("\'", "\""))
                #             temp_dict["confidence"] = match_value[0]["confidence"]
                #             # bot_app_collector.return_message = match_value[0]["answer"]
                #             if temp_dict["type"] != "task":
                #                 bot_app_collector.send_text_message("bot", str(temp_dict))
                #             else:
                #                 flow_flag = 1
                #     elif len(message) >= 20 and judge_item(message) > 0.1:
                #             ans_dict["type"] = "item"
                #             ans_dict["confidence"] = "1"
                #             ans_dict["ans_list"] = ["可直接访问关联推荐商品API:taobao.tbk.dg.material.optional返给对应商品"]
                #             bot_app_collector.return_message = bot_app_collector._message("bot", str(ans_dict))
                #     else:
                #         flow_flag = 1
                #     # 4走TASK流程（注意下面流程只能返回TASK）
                #     if flow_flag == 1:
                #         on_new_message(UserMessage(message, bot_app_collector, _uuid,
                #                                    input_channel=self.name()))
                #         temp_string = bot_app_collector.return_message["data"]["string"]
                #         if temp_string == "other_chit":
                #             ans_dict["type"] = "other_chit"
                #             ans_dict["confidence"] = 1  # 测试中，暂不开放
                #             ans_dict["ans_list"] = ["建议拒识"]
                #             bot_app_collector.return_message = bot_app_collector._message("bot", str(ans_dict))
                #         else:
                #             temp_string = temp_string.replace("\'", "\"")
                #             temp_dict = json.loads(temp_string.replace("None", "\"none\""))
                #             bot_app_collector.return_message = bot_app_collector._message("bot", str(temp_dict))
                #     # zyb-add:end
                try:
                    await on_new_message(
                        UserMessage(
                            message, bot_app_collector, _uuid, input_channel=self.name()
                        )
                    )
                except CancelledError:
                    logger.error(
                        "Message handling timed out for "
                        "user message '{}'.".format(message)
                    )
                except Exception:
                    logger.exception(
                        "An exception occured while handling "
                        "user message '{}'.".format(message)
                    )

                temp_string = bot_app_collector.return_message["data"]["string"]
                if temp_string.find("task") != -1 or temp_string.find("question") != -1 or \
                   temp_string.find("cmd") != -1 or temp_string.find("ad_data") != -1 or \
                   temp_string.find("item_data") != -1:
                    # 对收到的数据进行解码(字典转换为字符串)
                    temp_string = temp_string.replace("\'", "\"")
                    temp_dict = json.loads(temp_string.replace("None", "\"none\""))
                    bot_app_collector.return_message = bot_app_collector._message("bot", str(temp_dict))
                else:
                    ans_dict["type"] = "other_chit"
                    ans_dict["confidence"] = 1  # 测试中，暂不开放
                    ans_dict["ans_list"] = ["建议拒识"]
                    bot_app_collector.return_message = bot_app_collector._message("bot", str(ans_dict))
                return response.json(bot_app_collector.return_message)

        return bot_server_webhook
