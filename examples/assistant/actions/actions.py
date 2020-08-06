#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：Zhang Yanbo time:2019/5/15

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import requests
import logging
# from tests.qachat import get_qa
from typing import Dict, Text, Any, List, Union

from rasa_sdk import ActionExecutionRejection
from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction, REQUESTED_SLOT, REQUESTED_CHANGE_SLOT, \
    REQUESTED_SUB_SLOT, REQUESTED_LAST_SUB_SLOT
from api.weather_api import get_weather
from api.constellation_api import get_constellation
from api.taobao_api import get_taobao
from api.qa_item_api import get_qa
from api.kg_api import get_kg

logger = logging.getLogger(__name__)


def extract_item(item):
    if item is None:
        return None
    for name in support_search:
        if name in item:
            return name
    return None


class ReportWeatherForm(FormAction):
    """A custom form action"""

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "report_weather_form"

    # zyb-change:区分关键槽值与非关键槽值
    @staticmethod
    def required_slots(tracker):
        # type: () -> List[Text]
        """A list of required slots that the form has to fill"""

        # return ["weather_ns", "weather_t"]
        return {"weather_ns": "KEY", "weather_t": "KEY", REQUESTED_CHANGE_SLOT: "NO_KEY"}

    def slot_mappings(self):
        # type: () -> Dict[Text: Union[Dict, List[Dict]]]
        """A domain_words to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {"weather_ns": self.from_entity(entity="ns",
                                               intent=["intent_task_ns",
                                                       "intent_no_valid",
                                                       "intent_task_query_weather"]),
                "weather_t": self.from_entity(entity="t",
                                              intent=["intent_task_time",
                                                      "intent_no_valid",
                                                      "intent_task_query_weather"]),
                REQUESTED_CHANGE_SLOT: self.from_entity(entity="attribute",
                                                        intent="intent_task_exchange_attribute")
                }

    @staticmethod
    def t_db():
        # type: () -> List[Text]
        """Database of supported cuisines"""
        return ["今天",
                "明天",
                "后天"]

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer"""
        try:
            int(string)
            return True
        except ValueError:
            return False

    @staticmethod
    def attribute_to_slot(sub_slot: Text, attribute: Text) -> Text:
        """"""
        attribute_to_slot = {"时间": "weather_t", "地点": "weather_ns"}
        if attribute in attribute_to_slot.keys():
            return attribute_to_slot[attribute]
        else:
            return None

    def validate(self, dispatcher, tracker, domain, form_is_exist):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any], int) -> List[Dict]
        """Validate extracted requested slot
            else reject the execution of the form action
        """
        # extract other slots that were not requested
        # but set by corresponding entity
        # zyb-note:首先解析没有被请求的其他槽值
        slot_values = self.extract_other_slots(dispatcher, tracker, domain)
        valid_slot_values = {}
        # extract requested slot
        slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
        if slot_to_fill or form_is_exist:
            # zyb-note: -> 然后解析被请求的其他槽值
            slot_values.update(self.extract_requested_slot(dispatcher,
                                                           tracker, domain))
            if not slot_values:
                # reject form action execution
                # if some slot was requested but nothing was extracted
                # it will allow other policies to predict another action
                raise ActionExecutionRejection(self.name(),
                                               "Failed to validate slot {0} "
                                               "with action {1}"
                                               "".format(slot_to_fill,
                                                         self.name()))

        # we'll check when validation failed in order
        # to add appropriate utterances
        for slot, value in slot_values.items():
            if slot == 'weather_t' or slot == 'weather_ns' or slot == 'change_requested_slot':
                if isinstance(value, list):
                    if slot == REQUESTED_CHANGE_SLOT:
                        value = [self.attribute_to_slot(None, value_value) for value_value in value]
                    data_temp = list(set(value))[0]
                    valid_slot_values[slot] = data_temp
                else:
                    if slot == REQUESTED_CHANGE_SLOT:
                        value = self.attribute_to_slot(None, value)
                    data_temp = value
                    valid_slot_values[slot] = data_temp

        # validation succeed, set the slots values to the extracted values
        return [SlotSet(slot, value) for slot, value in valid_slot_values.items()]

    def submit(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """Define what the form has to do
            after all required slots are filled"""
        # address = tracker.get_slot('ns')
        # if isinstance(address, list):
        #     address_str = list(set(address))[0]
        # else:
        #     address_str = address

        # date_time = tracker.get_slot('t')
        # if isinstance(date_time, list):
        #     date_time_str = list(set(date_time))[0]
        # else:
        #     date_time_str = date_time

        address = tracker.get_slot('weather_ns')
        time = tracker.get_slot('weather_t')
        if time.lower() not in self.t_db():
            dispatcher.utter_message("暂不支持{}的天气查询".format(time))
        else:
            # if isinstance(date_time_number, str):  # parse date_time failed
            #     return [SlotSet("matches", "暂不支持查询 {} 的天气".format([address_str, date_time_number]))]
            # else:
            weather_data = get_weather(address, time)

            # utter submit template
            # dispatcher.utter_template('utter_report_weather', tracker)
            # dispatcher.utter_message("您想查询什么时候的天气？")
            dispatcher.utter_message("{}".format(weather_data))

        return []


class ReportConstellationForm(FormAction):
    """A custom form action"""

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "report_constellation_form"

    # zyb-change:区分关键槽值与非关键槽值
    @staticmethod
    def required_slots(tracker):
        # type: () -> Dict[Text: Any]
        """A list of required slots that the form has to fill"""

        return {"constellation_constellation": "KEY", "constellation_fortune": "KEY", "constellation_t": "NO_KEY",
                REQUESTED_CHANGE_SLOT: "NO_KEY"}

    def slot_mappings(self):
        # type: () -> Dict[Text: Union[Dict, List[Dict]]]
        """A domain_words to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {"constellation_constellation": self.from_entity(entity="constellation",
                                                                intent=["intent_task_query_constellation",
                                                                        "intent_no_valid",
                                                                        "intent_task_constellation"]),
                "constellation_fortune": self.from_entity(entity="fortune",
                                                          intent=["intent_task_query_constellation",
                                                                  "intent_no_valid",
                                                                  "intent_task_fortune"]),
                "constellation_t": self.from_entity(entity="t",
                                                    intent=["intent_task_query_constellation",
                                                            "intent_no_valid",
                                                            "intent_task_time"]),
                REQUESTED_CHANGE_SLOT: self.from_entity(entity="attribute",
                                                        intent="intent_task_exchange_attribute")
                }

    @staticmethod
    def constellation_constellation_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["白羊座",
                "金牛座",
                "双子座",
                "巨蟹座",
                "狮子座",
                "处女座",
                "天秤座",
                "天蝎座",
                "射手座",
                "摩羯座",
                "水瓶座",
                "双鱼座",
                ]

    @staticmethod
    def constellation_fortune_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["综合指数",
                "爱情指数",
                "工作指数",
                "财富指数",
                "爱情运势",
                "工作运势",
                "学业运势",
                "财富运势",
                "健康运势",
                "运势",
                "提醒",
                "优势",
                "弱势",
                "贵人星座",
                "小人星座",
                "缘分星座",
                "幸运数字",
                "吉日",
                "吉时",
                "吉利方位",
                "幸运色",
                "简评",
                ]

    @staticmethod
    def constellation_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["今天",
                "明天",
                "本周",
                "本月",
                "本年"
                ]

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer"""
        try:
            int(string)
            return True
        except ValueError:
            return False

    @staticmethod
    def attribute_to_slot(sub_slot: Text, attribute: Text) -> Text:
        """"""
        attribute_to_slot = {"星座": "constellation_constellation", "运势": "constellation_fortune",
                             "时间": "constellation_t"}
        if attribute in attribute_to_slot.keys():
            return attribute_to_slot[attribute]
        else:
            return None

    def validate(self, dispatcher, tracker, domain, form_is_exist):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any], int) -> List[Dict]
        """Validate extracted requested slot
            else reject the execution of the form action
        """
        # extract other slots that were not requested
        # but set by corresponding entity
        # zyb-note:首先解析没有被请求的其他槽值
        slot_values = self.extract_other_slots(dispatcher, tracker, domain)
        valid_slot_values = {}
        # extract requested slot
        slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
        if slot_to_fill or form_is_exist:
            # zyb-note:然后解析被请求的其他槽值
            slot_values.update(self.extract_requested_slot(dispatcher,
                                                           tracker, domain))
            if not slot_values:
                # reject form action execution
                # if some slot was requested but nothing was extracted
                # it will allow other policies to predict another action
                raise ActionExecutionRejection(self.name(),
                                               "Failed to validate slot {0} "
                                               "with action {1}"
                                               "".format(slot_to_fill,
                                                         self.name()))

        # we'll check when validation failed in order
        # to add appropriate utterances
        for slot, value in slot_values.items():
            if slot == 'constellation_t' or slot == 'constellation_constellation' or \
                    slot == 'constellation_fortune' or slot == 'change_requested_slot':
                if isinstance(value, list):
                    if slot == REQUESTED_CHANGE_SLOT:
                        value = [self.attribute_to_slot(None, value_value)
                                 for value_value in value]
                    data_temp = list(set(value))[0]
                    if slot == "constellation_fortune":
                        valid_slot_values[slot] = "".join(data_temp)
                    else:
                        valid_slot_values[slot] = data_temp
                else:
                    if slot == REQUESTED_CHANGE_SLOT:
                        value = self.attribute_to_slot(None, value)
                    data_temp = value
                    valid_slot_values[slot] = data_temp

        # validation succeed, set the slots values to the extracted values
        return [SlotSet(slot, value) for slot, value in valid_slot_values.items()]

    def submit(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """Define what the form has to do
            after all required slots are filled"""

        constellation_time = tracker.get_slot('constellation_t')
        constellation_constellation = tracker.get_slot('constellation_constellation')
        constellation_fortune = tracker.get_slot('constellation_fortune')

        if constellation_time is not None and constellation_time not in self.constellation_db():
            dispatcher.utter_message("暂不支持{}的星座查询".format(constellation_time))
            return [SlotSet('constellation_t', None)]
        else:
            constellation_data = get_constellation(constellation_constellation, constellation_time,
                                                   constellation_fortune)
            # utter submit template
            dispatcher.utter_message("{}".format(constellation_data))
            return []


class RecItemForm(FormAction):
    """A custom form action"""
    weel_num = 4
    get_count = 0
    item_commodity = ""

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "rec_item_form"

    # zyb-change:区分关键槽值与非关键槽值
    @staticmethod
    def required_slots(tracker):
        # type: () -> List[Text]
        """A list of required slots that the form has to fill"""

        if tracker.slots["requested_sub_slot"] == "item_toy":
            return {"item_general_commodity": "NO_KEY", "item_toy": "KEY",
                    "item_sleeve": "NO_KEY", "item_trousers": "NO_KEY", "item_shoes": "NO_KEY",
                    "item_shoes_size": "NO_KEY", "item_clothes_size": "NO_KEY",
                    "item_height": "NO_KEY", "item_weight": "NO_KEY",
                    "item_sex": "KEY", "item_age": "KEY",
                    "item_brand": "KEY",
                    REQUESTED_CHANGE_SLOT: "NO_KEY"}
        elif tracker.slots["requested_sub_slot"] == "item_shoes":
            return {"item_general_commodity": "NO_KEY", "item_toy": "NO_KEY",
                    "item_sleeve": "NO_KEY", "item_trousers": "NO_KEY", "item_shoes": "KEY",
                    "item_shoes_size": "KEY", "item_clothes_size": "NO_KEY",
                    "item_height": "NO_KEY", "item_weight": "NO_KEY",
                    "item_sex": "KEY", "item_age": "NO_KEY",
                    "item_brand": "KEY",
                    REQUESTED_CHANGE_SLOT: "NO_KEY"}
        elif tracker.slots["requested_sub_slot"] == "item_sleeve":
            return {"item_general_commodity": "NO_KEY", "item_toy": "NO_KEY",
                    "item_sleeve": "KEY", "item_trousers": "NO_KEY", "item_shoes": "NO_KEY",
                    "item_shoes_size": "NO_KEY", "item_clothes_size": "KEY",
                    "item_height": "NO_KEY", "item_weight": "NO_KEY",
                    "item_sex": "KEY", "item_age": "NO_KEY",
                    "item_brand": "KEY",
                    REQUESTED_CHANGE_SLOT: "NO_KEY"}
        elif tracker.slots["requested_sub_slot"] == "item_trousers":
            return {"item_general_commodity": "NO_KEY", "item_toy": "NO_KEY",
                    "item_sleeve": "NO_KEY", "item_trousers": "KEY", "item_shoes": "NO_KEY",
                    "item_shoes_size": "NO_KEY", "item_clothes_size": "KEY",
                    "item_height": "NO_KEY", "item_weight": "NO_KEY",
                    "item_sex": "KEY", "item_age": "NO_KEY",
                    "item_brand": "KEY",
                    REQUESTED_CHANGE_SLOT: "NO_KEY"}
        else:
            return {"item_general_commodity": "KEY", "item_toy": "NO_KEY",
                    "item_sleeve": "NO_KEY", "item_trousers": "NO_KEY", "item_shoes": "NO_KEY",
                    "item_shoes_size": "NO_KEY", "item_clothes_size": "NO_KEY",
                    "item_height": "NO_KEY", "item_weight": "NO_KEY",
                    "item_sex": "NO_KEY", "item_age": "NO_KEY",
                    "item_brand": "NO_KEY",
                    REQUESTED_CHANGE_SLOT: "NO_KEY"}

    def slot_mappings(self):
        # type: () -> Dict[Text: Union[Dict, List[Dict]]]
        """A domain_words to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {"item_general_commodity": self.from_entity(entity="general_commodity",
                                                           intent=["intent_task_general_commodity",
                                                                   "intent_no_valid",
                                                                   "intent_task_buy_item"]
                                                           ),
                "item_toy": self.from_entity(entity="toy",
                                             intent=["intent_task_toy",
                                                     "intent_no_valid",
                                                     "intent_task_buy_item"]
                                             ),
                "item_sleeve": self.from_entity(entity="sleeve",
                                                intent=["intent_task_sleeve",
                                                        "intent_no_valid",
                                                        "intent_task_buy_item"]
                                                ),
                "item_trousers": self.from_entity(entity="trousers",
                                                  intent=["intent_task_trousers",
                                                          "intent_no_valid",
                                                          "intent_task_buy_item"]
                                                  ),
                "item_shoes": self.from_entity(entity="shoes",
                                               intent=["intent_task_shoes",
                                                       "intent_no_valid",
                                                       "intent_task_buy_item"]
                                               ),
                "item_shoes_size": [self.from_entity(entity="shoes_size",
                                                     intent=["intent_task_shoes_size",
                                                             "intent_no_valid",
                                                             "intent_task_buy_item"]
                                                     ),
                                    self.from_entity(entity="number",
                                                     intent=["intent_task_number",
                                                             "intent_task_buy_item"]
                                                     ),
                                    self.from_intent(intent="intent_task_whatever",
                                                     value="")],
                "item_clothes_size": [self.from_entity(entity="clothes_size",
                                                       intent=["intent_task_clothes_size",
                                                               "intent_no_valid",
                                                               "intent_task_buy_item"]
                                                       ),
                                      self.from_entity(entity="number",
                                                       intent=["intent_task_number",
                                                               "intent_task_buy_item"]
                                                       ),
                                      self.from_intent(intent="intent_task_whatever",
                                                       value="")],
                "item_sex": [self.from_entity(entity="sex",
                                              intent=["intent_task_sex",
                                                      "intent_no_valid",
                                                      "intent_task_buy_item"]
                                              ),
                             self.from_entity(entity="number",
                                              intent=["intent_task_number",
                                                      "intent_task_buy_item"]
                                              ),
                             self.from_intent(intent="intent_task_whatever",
                                              value="")],
                "item_age": [self.from_entity(entity="age",
                                              intent=["intent_task_age",
                                                      "intent_no_valid",
                                                      "intent_task_buy_item"]
                                              ),
                             self.from_entity(entity="number",
                                              intent=["intent_task_number",
                                                      "intent_task_buy_item"]
                                              ),
                             self.from_intent(intent="intent_task_whatever",
                                              value="")],
                "item_brand": [self.from_entity(entity="brand",
                                                intent=["intent_task_brand",
                                                        "intent_no_valid",
                                                        "intent_task_buy_item"]
                                                ),
                               self.from_entity(entity="number",
                                                intent=["intent_task_number",
                                                        "intent_task_buy_item"]
                                                ),
                               self.from_intent(intent="intent_task_whatever",
                                                value="")],
                REQUESTED_CHANGE_SLOT: [self.from_entity(entity="attribute",
                                                         intent="intent_task_exchange_attribute"),
                                        self.from_intent(intent="intent_task_exchange_item",
                                                         value="exchange_item_flag")
                                        ]}

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer"""
        try:
            int(string)
            return True
        except ValueError:
            return False

    @staticmethod
    def number_to_age(string: Text) -> Text:
        """"""
        number_list = [{"0", "零", "zero", "ZERO"}, {"1", "一", "one", "ONE"}, {"2", "二", "two", "TWO"},
                       {"3", "三", "three", "THREE"}, {"4", "四", "four", "FOUR"}, {"5", "五", "five", "FIVE"},
                       {"6", "六", "six", "SIX"}, {"7", "七", "seven", "SEVEN"}, {"8", "八", "eight", "EIGHT"},
                       {"9", "九", "nine", "NINE"}]
        age_list = ["", "婴儿", "2岁", "3岁", "4岁", "5岁", "6岁", "7岁", "10岁", "14岁以上"]

        for i, number in enumerate(number_list):
            if string in number:
                if i < len(age_list):
                    return age_list[i]
                else:
                    return age_list[0]  # TODO:后续需修改为失效
        return string

    @staticmethod
    def number_to_sex(string: Text) -> Text:
        """"""
        number_list = [{"0", "零", "zero", "ZERO"}, {"1", "一", "one", "ONE"}, {"2", "二", "two", "TWO"},
                       {"3", "三", "three", "THREE"}, {"4", "四", "four", "FOUR"}, {"5", "五", "five", "FIVE"},
                       {"6", "六", "six", "SIX"}, {"7", "七", "seven", "SEVEN"}, {"8", "八", "eight", "EIGHT"},
                       {"9", "九", "nine", "NINE"}]
        sex_list = ["", "男孩", "女孩"]

        for i, number in enumerate(number_list):
            if string in number:
                if i < len(sex_list):
                    return sex_list[i]
                else:
                    return sex_list[0]  # TODO:后续需修改为失效
        return string

    @staticmethod
    def number_to_shoes_size(string: Text) -> Text:
        """"""
        number_list = [{"0", "零", "zero", "ZERO"}, {"1", "一", "one", "ONE"}, {"2", "二", "two", "TWO"},
                       {"3", "三", "three", "THREE"}, {"4", "四", "four", "FOUR"}, {"5", "五", "five", "FIVE"},
                       {"6", "六", "six", "SIX"}, {"7", "七", "seven", "SEVEN"}, {"8", "八", "eight", "EIGHT"},
                       {"9", "九", "nine", "NINE"}]
        clothes_size_list = ["", "36", "37", "38", "39", "40", "41", "42", "43", "44"]

        for i, number in enumerate(number_list):
            if string in number:
                if i < len(clothes_size_list):
                    return clothes_size_list[i]
                else:
                    return clothes_size_list[0]  # TODO:后续需修改为失效
        return string

    @staticmethod
    def number_to_clothes_size(string: Text) -> Text:
        """"""
        number_list = [{"0", "零", "zero", "ZERO"}, {"1", "一", "one", "ONE"}, {"2", "二", "two", "TWO"},
                       {"3", "三", "three", "THREE"}, {"4", "四", "four", "FOUR"}, {"5", "五", "five", "FIVE"},
                       {"6", "六", "six", "SIX"}, {"7", "七", "seven", "SEVEN"}, {"8", "八", "eight", "EIGHT"},
                       {"9", "九", "nine", "NINE"}]
        clothes_size_list = ["", "S", "M", "L", "XL", "XXL", "3XL"]

        for i, number in enumerate(number_list):
            if string in number:
                if i < len(clothes_size_list):
                    return clothes_size_list[i]
                else:
                    return clothes_size_list[0]  # TODO:后续需修改为失效
        return string

    @staticmethod
    def number_to_brand(slot: Text, string: Text) -> Text:
        """"""
        number_list = [{"0", "零", "zero", "ZERO"}, {"1", "一", "one", "ONE"}, {"2", "二", "two", "TWO"},
                       {"3", "三", "three", "THREE"}, {"4", "四", "four", "FOUR"}, {"5", "五", "five", "FIVE"},
                       {"6", "六", "six", "SIX"}, {"7", "七", "seven", "SEVEN"}, {"8", "八", "eight", "EIGHT"},
                       {"9", "九", "nine", "NINE"}]
        item_clothes_shoes_list = ["", "鸿星尔克", "森马", "安踏", "耐克",
                                   "特步", "花花公子", "阿迪达斯", "李宁", "优衣库"]
        item_toy_list = ["", "乐高", "Disney", "育儿宝", "神通小子", "益米", "兔妈妈", "三宝", "万童乐"]

        if slot == "item_shoes" or slot == "item_sleeve" or slot == "item_trousers":
            for i, number in enumerate(number_list):
                if string in number:
                    if i < len(item_clothes_shoes_list):
                        return item_clothes_shoes_list[i]
                    else:
                        return item_clothes_shoes_list[0]  # TODO:后续需修改为失效
        elif slot == "item_toy":
            for i, number in enumerate(number_list):
                if string in number:
                    if i < len(item_toy_list):
                        return item_toy_list[i]
                    else:
                        return item_toy_list[0]  # TODO:后续需修改为失效
        if string in item_clothes_shoes_list or string in item_toy_list:
            return string
        else:
            return "no_valid_brand"

    @staticmethod
    def brand_select(slot: Text) -> Text:
        """"""
        item_clothes_shoes_list = ["", "鸿星尔克", "森马", "安踏", "耐克",
                                   "特步", "花花公子", "阿迪达斯", "李宁", "优衣库"]
        item_toy_list = ["", "乐高", "Disney", "育儿宝", "神通小子", "益米", "兔妈妈", "三宝", "万童乐"]
        brand_text = []
        if slot == "item_shoes" or slot == "item_sleeve" or slot == "item_trousers":
            for i, item_clothes_shoes in enumerate(item_clothes_shoes_list):
                if i == 0 or i >= len(item_clothes_shoes_list) - 1:
                    brand_text.append("0:随便看看")  # TODO:后续需修改为失效
                else:
                    brand_text.append("{}:{}".format(i, item_clothes_shoes))
        elif slot == "item_toy":
            for i, item_toy in enumerate(item_toy_list):
                if i == 0 or i >= len(item_toy_list) - 1:
                    brand_text.append("0:随便看看")  # TODO:后续需修改为失效
                else:
                    brand_text.append("{}:{}".format(i, item_toy))
        return " ".join(brand_text)

    @staticmethod
    def attribute_to_slot(sub_slot: Text, attribute: Text) -> Text:
        """"""
        attribute_to_slot = {"品牌": "item_brand", "性别": "item_sex",
                             "年龄": "item_age"}
        if attribute in attribute_to_slot.keys():
            return attribute_to_slot[attribute]
        elif attribute == "尺寸":
            if sub_slot == "item_trousers" or sub_slot == "item_sleeve":
                return "item_clothes_size"
            elif sub_slot == "item_shoes":
                return "item_shoes_size"
        else:
            return attribute

    def validate(self, dispatcher, tracker, domain, form_is_exist):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any], int) -> List[Dict]
        """Validate extracted requested slot
            else reject the execution of the form action
        """
        # extract other slots that were not requested
        # but set by corresponding entity
        # zyb-note:首先解析没有被请求的其他槽值（比如用户自动更改的槽，以及用户请示的槽）
        # 注意此处过滤掉了带有number的槽
        slot_values = self.extract_other_slots(dispatcher, tracker, domain)
        valid_slot_values = {}
        # TODO:主动换槽结束后最好机器人反馈给用户更换状态，这样比较友好。待添加
        # 下面这些是特殊的键值，只有在澄清的时候方可填槽，其它状态下不应被强制填槽
        # special_slots = ["item_shoes_size", "item_clothes_size", "item_age", "item_brand", "item_sex"]
        # for special_slot in special_slots:
        #     if special_slot in slot_values.keys():
        #         del slot_values[special_slot]

        # extract requested slot
        slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
        if slot_to_fill or form_is_exist:
            # zyb-note:解析被请求的槽值
            slot_values.update(self.extract_requested_slot(dispatcher,
                                                           tracker, domain))
            if not slot_values:
                # reject form action execution
                # if some slot was requested but nothing was extracted
                # it will allow other policies to predict another action
                raise ActionExecutionRejection(self.name(),
                                               "Failed to validate slot {0} "
                                               "with action {1}"
                                               "".format(slot_to_fill,
                                                         self.name()))
        # we'll check when validation failed in order
        # to add appropriate utterances
        # 此处用来进一步加工实体
        requested_sub_dict = {REQUESTED_SUB_SLOT: tracker.slots[REQUESTED_SUB_SLOT]}
        # item_general_commodity优先级放到最低，如果有别的商品被识别，则将其剔除
        if "item_general_commodity" in slot_values.keys():
            direct_slots = ["item_toy", "item_sleeve", "item_trousers", "item_shoes"]
            for direct_slot in direct_slots:
                if direct_slot in slot_values.keys():
                    del slot_values["item_general_commodity"]
                    break
        item_list = ["item_general_commodity", "item_toy", "item_sleeve", "item_trousers", "item_shoes"]
        attribute_list = ["item_shoes_size", "item_clothes_size", "item_height", "item_weight",
                          "item_sex", "item_age", "item_brand"]

        for slot, value in slot_values.items():
            if slot in item_list:
                # 更新必须填槽项
                requested_sub_dict[REQUESTED_SUB_SLOT] = slot
                # 连续两次商品品类请求不一致,则把之前的状态清除
                if slot != tracker.slots[REQUESTED_LAST_SUB_SLOT]:
                    for attribute in attribute_list:
                        if attribute not in slot_values.keys():
                            valid_slot_values[attribute] = None
                    break

        for slot, value in slot_values.items():

            if isinstance(value, list):
                if slot == "item_age":
                    value = [self.number_to_age(value_value) for value_value in value]
                elif slot == "item_sex":
                    value = [self.number_to_sex(value_value) for value_value in value]
                elif slot == "item_clothes_size":
                    value = [self.number_to_clothes_size(value_value) for value_value in value]
                elif slot == "item_shoes_size":
                    value = [self.number_to_shoes_size(value_value) for value_value in value]
                elif slot == "item_brand":
                    value = [self.number_to_brand(requested_sub_dict[REQUESTED_SUB_SLOT], value_value)
                             for value_value in value]
                    value = list(set(value))
                    if "no_valid_brand" in value:
                        value.remove("no_valid_brand")
                elif slot == REQUESTED_CHANGE_SLOT:
                    value = [self.attribute_to_slot(tracker.slots[REQUESTED_SUB_SLOT], value_value)
                             for value_value in value]
                if len(value) != 0:
                    data_temp = list(set(value))[0]
                    valid_slot_values[slot] = data_temp
            else:
                if slot == "item_age":
                    value = self.number_to_age(value)
                elif slot == "item_sex":
                    value = self.number_to_sex(value)
                elif slot == "item_clothes_size":
                    value = self.number_to_clothes_size(value)
                elif slot == "item_shoes_size":
                    value = self.number_to_shoes_size(value)
                elif slot == "item_brand":
                    value = self.number_to_brand(requested_sub_dict[REQUESTED_SUB_SLOT], value)
                elif slot == REQUESTED_CHANGE_SLOT:
                    value = self.attribute_to_slot(tracker.slots[REQUESTED_SUB_SLOT], value)
                if value != "no_valid_brand":
                    data_temp = value
                    valid_slot_values[slot] = data_temp

        if REQUESTED_SUB_SLOT in requested_sub_dict.keys():
            valid_slot_values[REQUESTED_SUB_SLOT] = requested_sub_dict[REQUESTED_SUB_SLOT]
            valid_slot_values[REQUESTED_LAST_SUB_SLOT] = valid_slot_values[REQUESTED_SUB_SLOT]
            valid_slot_values["var_brand_list"] = self.brand_select(requested_sub_dict[REQUESTED_SUB_SLOT])

        # validation succeed, set the slots values to the extracted values
        return [SlotSet(slot, value) for slot, value in valid_slot_values.items()]

    def submit(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """Define what the form has to do
            after all required slots are filled"""

        if tracker.slots[REQUESTED_SUB_SLOT] == "item_shoes":
            item_shoes = tracker.get_slot('item_shoes')
            item_shoes_size = tracker.get_slot('item_shoes_size')
            item_sex = tracker.get_slot('item_sex')
            item_brand = tracker.get_slot('item_brand')
            logger.debug("检索到的槽值为:" + item_brand + item_shoes_size + item_sex + item_shoes)
            item_shoes_size = item_shoes_size + "码" if item_shoes_size != "" else ""
            item_sex = item_sex[0] if item_sex != "" else ""
            get_list = get_taobao(item_brand + item_shoes_size + item_sex + item_shoes)
            RecItemForm.item_commodity = item_shoes
            # dispatcher.utter_message("shoes{}的尺寸是:{},性别是:{},品牌是:{}".format(
            #     item_shoes, item_shoes_size, item_sex, item_brand))

        if tracker.slots[REQUESTED_SUB_SLOT] == "item_toy":
            item_toy = tracker.get_slot('item_toy')
            item_age = tracker.get_slot('item_age')
            item_sex = tracker.get_slot('item_sex')
            item_brand = tracker.get_slot('item_brand')
            logger.debug("检索到的槽值为:" + item_age + item_brand + item_sex + item_toy)
            item_sex = item_sex[0] if item_sex != "" else ""
            get_list = get_taobao(item_age + item_brand + item_sex + item_toy)
            RecItemForm.item_commodity = item_toy

        if tracker.slots[REQUESTED_SUB_SLOT] == "item_trousers":
            item_trousers = tracker.get_slot('item_trousers')
            item_clothes_size = tracker.get_slot('item_clothes_size')
            item_sex = tracker.get_slot('item_sex')
            item_brand = tracker.get_slot('item_brand')
            logger.debug("检索到的槽值为:" + item_clothes_size + item_brand + item_sex + item_trousers)
            item_clothes_size = item_clothes_size + "码" if item_clothes_size != "" else ""
            item_sex = item_sex[0] if item_sex != "" else ""
            get_list = get_taobao(item_clothes_size + item_brand + item_sex + item_trousers)
            RecItemForm.item_commodity = item_trousers
            # dispatcher.utter_message("trousers{}的尺寸是:{},性别是:{},品牌是:{}".format(
            #     item_trousers, item_clothes_size, item_sex, item_brand))
            # return []
        if tracker.slots[REQUESTED_SUB_SLOT] == "item_sleeve":
            item_sleeve = tracker.get_slot('item_sleeve')
            item_clothes_size = tracker.get_slot('item_clothes_size')
            item_sex = tracker.get_slot('item_sex')
            item_brand = tracker.get_slot('item_brand')
            logger.debug("检索到的槽值为:" + item_clothes_size + item_brand + item_sex + item_sleeve)
            item_clothes_size = item_clothes_size + "码" if item_clothes_size != "" else ""
            item_sex = item_sex[0] if item_sex != "" else ""
            get_list = get_taobao(item_clothes_size + item_brand + item_sex + item_sleeve)
            RecItemForm.item_commodity = item_sleeve
            # dispatcher.utter_message("sleeve{}的尺寸是:{},性别是:{},品牌是:{}".format(
            #     item_sleeve, item_clothes_size, item_sex, item_brand))
            # return []
        if tracker.slots[REQUESTED_SUB_SLOT] == "item_general_commodity":
            item_general_commodity = tracker.get_slot('item_general_commodity')
            logger.debug("检索到的槽值为:" + item_general_commodity)
            get_list = get_taobao(item_general_commodity)
            RecItemForm.item_commodity = item_general_commodity
            # dispatcher.utter_message("您要买的commodity是{}".format(item_general_commodity))
            # return []

        if len(get_list) != 0:
            group_length = int(len(get_list) / RecItemForm.weel_num)
            if tracker.slots[REQUESTED_CHANGE_SLOT] == "exchange_item_flag":
                dispatcher.utter_message("好的,下面是重新为你精选的{}:<br/>{}<br/>您可以说“换一批”为您重新挑选".format(
                    RecItemForm.item_commodity,
                    "<br/>".join(get_list[RecItemForm.get_count * group_length:
                                          RecItemForm.get_count * group_length + group_length])
                )
                )
            else:
                dispatcher.utter_message("下面是为你精选的{}:<br/>{}<br/>您可以说“换一批”为您重新挑选".format(
                    RecItemForm.item_commodity,
                    "<br/>".join(get_list[RecItemForm.get_count * group_length:
                                          RecItemForm.get_count * group_length + group_length])
                )
                )

            RecItemForm.get_count += 1
            if RecItemForm.get_count >= RecItemForm.weel_num:
                RecItemForm.get_count = 0
        else:
            dispatcher.utter_message("抱歉搜索不到你想要的商品信息，请重新选择")
        # dispatcher.utter_message("toy{}的年龄是:{},品牌{}".format(item_toy, item_age, item_brand))

        if tracker.slots[REQUESTED_CHANGE_SLOT] == "exchange_item_flag":
            return [SlotSet(REQUESTED_CHANGE_SLOT, None)]
        else:
            return []


class ActionKgBot(Action):
    """A custom form action"""
    last_same_question_buffer = []
    answer_list = []
    get_count = 0

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "action_kg_bot"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get('text')
        if text not in ActionKgBot.last_same_question_buffer:
            ActionKgBot.answer_list = get_kg(text)
            ActionKgBot.last_same_question_buffer = [text]
            ActionKgBot.get_count = 0
            if ActionKgBot.answer_list:
                dispatcher.utter_message("{}".format(ActionKgBot.answer_list[0]["value"]))  # 澄清话术
            else:
                dispatcher.utter_template("utter_default", tracker,
                                          silent_fail=True)
        else:
            ActionKgBot.last_same_question_buffer.append(text)
            ActionKgBot.get_count += 1
            if ActionKgBot.get_count >= 4:
                dispatcher.utter_template("utter_refuse_repeat", tracker,
                                          silent_fail=True)
            else:
                if ActionKgBot.answer_list:
                    dispatcher.utter_message("{}".format(ActionKgBot.answer_list[0]["value"]))  # 澄清话术
                else:
                    dispatcher.utter_template("utter_default", tracker,
                                              silent_fail=True)

        return []


class ActionQABot(Action):
    """A custom form action"""
    last_same_question_buffer = []
    get_count: int = 0

    def name(self):
        # type: () -> Text
        return "action_qa_bot"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get('text')
        if text not in ActionQABot.last_same_question_buffer:
            ActionQABot.last_same_question_buffer = [text]
            ActionQABot.get_count = 0
            qa_intent = tracker.latest_message.get("intent")["name"]
            if qa_intent.find("intent_cmd") != -1 or \
                    qa_intent.find("intent_qa") != -1:
                dispatcher.utter_template("utter_" + qa_intent, tracker,
                                          silent_fail=True)  # 澄清话术
            else:
                dispatcher.utter_template("utter_default", tracker,
                                          silent_fail=True)  # 澄清话术
        else:
            ActionQABot.last_same_question_buffer.append(text)
            ActionQABot.get_count += 1
            if ActionQABot.get_count >= 4:
                dispatcher.utter_template("utter_refuse_repeat", tracker,
                                          silent_fail=True)
            else:
                qa_intent = tracker.latest_message.get("intent")["name"]
                if qa_intent.find("intent_cmd") != -1 or \
                        qa_intent.find("intent_qa") != -1:
                    dispatcher.utter_template("utter_" + qa_intent, tracker,
                                              silent_fail=True)  # 澄清话术
                else:
                    dispatcher.utter_template("utter_default", tracker,
                                              silent_fail=True)  # 澄清话术
        return []


class ActionSmalltalkBot(Action):
    """A custom form action"""
    last_same_question_buffer = []
    get_count = 0

    def name(self):
        # type: () -> Text
        return "action_smalltalk_bot"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text")
        if text not in ActionSmalltalkBot.last_same_question_buffer:
            ActionSmalltalkBot.last_same_question_buffer = [text]
            ActionSmalltalkBot.get_count = 0
            smalltalk_intent = tracker.latest_message.get("intent")["name"]
            if smalltalk_intent.find("agent") != -1 or \
                    smalltalk_intent.find("appraisal") != -1 or \
                    smalltalk_intent.find("confirmation") != -1 or \
                    smalltalk_intent.find("dialog") != -1 or \
                    smalltalk_intent.find("emotions") != -1 or \
                    smalltalk_intent.find("greetings") != -1 or \
                    smalltalk_intent.find("user") != -1:
                dispatcher.utter_template("utter_" + smalltalk_intent, tracker,
                                          silent_fail=True)  # 澄清话术
            else:
                dispatcher.utter_template("utter_default", tracker,
                                          silent_fail=True)  # 澄清话术
        else:
            ActionSmalltalkBot.last_same_question_buffer.append(text)
            ActionSmalltalkBot.get_count += 1
            if ActionSmalltalkBot.get_count >= 4:
                dispatcher.utter_template("utter_refuse_repeat", tracker,
                                          silent_fail=True)
            else:
                smalltalk_intent = tracker.latest_message.get("intent")["name"]
                if smalltalk_intent.find("agent") != -1 or \
                        smalltalk_intent.find("appraisal") != -1 or \
                        smalltalk_intent.find("confirmation") != -1 or \
                        smalltalk_intent.find("dialog") != -1 or \
                        smalltalk_intent.find("emotions") != -1 or \
                        smalltalk_intent.find("greetings") != -1 or \
                        smalltalk_intent.find("user") != -1:
                    dispatcher.utter_template("utter_" + smalltalk_intent, tracker,
                                              silent_fail=True)  # 澄清话术
                else:
                    dispatcher.utter_template("utter_default", tracker,
                                              silent_fail=True)  # 澄清话术
        return []


# class RecSizeForm(FormAction):
#     """A custom form action"""
#
#     def name(self):
#         # type: () -> Text
#         """Unique identifier of the form"""
#         return "rec_size_form"
#
#     # zyb-change:区分关键槽值与非关键槽值
#     @staticmethod
#     def required_slots(tracker):
#         # type: () -> List[Text]
#         """A list of required slots that the form has to fill"""
#
#         # return ["weather_ns", "weather_t"]
#         return {"item_height": "KEY", "item_weight": "KEY"}
#
#     def slot_mappings(self):
#         # type: () -> Dict[Text: Union[Dict, List[Dict]]]
#         """A domain_words to map required slots to
#             - an extracted entity
#             - intent: value pairs
#             - a whole message
#             or a list of them, where a first match will be picked"""
#
#         return {"item_height": self.from_entity(entity="height",
#                                                    not_intent=["other_chit",
#                                                                "intent_task_query_constellation",
#                                                                "intent_task_query_weather"]),
#                 "item_weight": self.from_entity(entity="weight",
#                                                not_intent=["other_chit",
#                                                            "intent_task_query_constellation",
#                                                            "intent_task_query_weather"])}
#
#     @staticmethod
#     def is_int(string: Text) -> bool:
#         """Check if a string is an integer"""
#         try:
#             int(string)
#             return True
#         except ValueError:
#             return False
#
#     def validate(self, dispatcher, tracker, domain, form_is_exist):
#         # type: (CollectingDispatcher, Tracker, Dict[Text, Any], int) -> List[Dict]
#         """Validate extracted requested slot
#             else reject the execution of the form action
#         """
#         # extract other slots that were not requested
#         # but set by corresponding entity
#         # zyb-note:首先解析没有被请求的其他槽值
#         slot_values = self.extract_other_slots(dispatcher, tracker, domain)
#
#         # extract requested slot
#         slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
#         if slot_to_fill or form_is_exist:
#             # zyb-note:然后解析被请求的其他槽值
#             slot_values.update(self.extract_requested_slot(dispatcher,
#                                                            tracker, domain))
#             if not slot_values:
#                 # reject form action execution
#                 # if some slot was requested but nothing was extracted
#                 # it will allow other policies to predict another action
#                 raise ActionExecutionRejection(self.name(),
#                                                "Failed to validate slot {0} "
#                                                "with action {1}"
#                                                "".format(slot_to_fill,
#                                                          self.name()))
#
#         # we'll check when validation failed in order
#         # to add appropriate utterances
#         for slot, value in slot_values.items():
#             if slot == 't' or slot == 'ns':
#                 if isinstance(value, list):
#                     data_temp = list(set(value))[0]
#                     slot_values[slot] = data_temp
#                 else:
#                     data_temp = value
#                     slot_values[slot] = data_temp
#
#         # validation succeed, set the slots values to the extracted values
#         return [SlotSet(slot, value) for slot, value in slot_values.items()]
#
#     def submit(self, dispatcher, tracker, domain):
#         # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
#         """Define what the form has to do
#             after all required slots are filled"""
#         # address = tracker.get_slot('ns')
#         # if isinstance(address, list):
#         #     address_str = list(set(address))[0]
#         # else:
#         #     address_str = address
#
#         # date_time = tracker.get_slot('t')
#         # if isinstance(date_time, list):
#         #     date_time_str = list(set(date_time))[0]
#         # else:
#         #     date_time_str = date_time
#
#         address_str = tracker.get_slot('ns')
#         date_time_str = tracker.get_slot('t')
#         date_time_number = text_date_to_number_date(date_time_str)
#
#         if date_time_str.lower() not in self.t_db():
#             dispatcher.utter_message("暂不支持{}的天气查询".format(date_time_str))
#         else:
#             # if isinstance(date_time_number, str):  # parse date_time failed
#             #     return [SlotSet("matches", "暂不支持查询 {} 的天气".format([address_str, date_time_number]))]
#             # else:
#             weather_data = get_text_weather_date(address_str, date_time_str, date_time_number)
#
#             # utter submit template
#             # dispatcher.utter_template('utter_report_weather', tracker)
#             # dispatcher.utter_message("您想查询什么时候的天气？")
#             dispatcher.utter_message("{}".format(weather_data))
#
#         return []


class ActionReportWeather(Action):
    """A custom form action"""
    RANDOMIZE = True

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "action_report_weather"

    def run(self, dispatcher, tracker, domain):
        address = tracker.get_slot("ns")
        date_time = tracker.get_slot('t')

        if date_time is None:
            dispatcher.utter_message("您想查询什么时候的天气？")  # 澄清话术
            return []

        if address is None:
            dispatcher.utter_message("您想查询哪个城市的天气？")  # 澄清话术
            return []


class ActionSearchConsume(Action):
    def name(self):
        return 'action_search_consume'

    def run(self, dispatcher, tracker, domain):
        item = tracker.get_slot("item")
        item = extract_item(item)
        if item is None:
            dispatcher.utter_message("您好，我现在只会查话费和流量")
            dispatcher.utter_message("你可以这样问我：“帮我查话费”")
            return [AllSlotsReset()]

        time = tracker.get_slot("time")
        if time is None:
            dispatcher.utter_message("您想查询哪个月的消费？")
            return []
        # query database here using item and time as key. but you may normalize time format first.
        dispatcher.utter_message("好，请稍等")
        if item == "流量":
            dispatcher.utter_message(
                "您好，您{}共使用{}二百八十兆，剩余三十兆。".format(time, item))
        else:
            dispatcher.utter_message("您好，您{}共消费二十八元。".format(time))
        return [AllSlotsReset()]


# 找商品
support_search = ["话费", "流量"]


class ActionSearchItem(Action):
    def name(self):
        return 'action_search_item'

    def run(self, dispatcher, tracker, domain):
        item = tracker.get_slot("item")
        item = extract_item(item)
        if item is None:
            dispatcher.utter_message("您好，我现在只会查话费和流量")
            dispatcher.utter_message("你可以这样问我：“帮我查话费”")
            return [AllSlotsReset()]

        time = tracker.get_slot("time")
        if time is None:
            dispatcher.utter_message("您想查询哪个月的消费？")
            return []
        # query database here using item and time as key. but you may normalize time format first.
        dispatcher.utter_message("好，请稍等")
        if item == "流量":
            dispatcher.utter_message(
                "您好，您{}共使用{}二百八十兆，剩余三十兆。".format(time, item))
        else:
            dispatcher.utter_message("您好，您{}共消费二十八元。".format(time))
        return [AllSlotsReset()]


# class ActionUnknowIntent(Action):
#     """Executes the fallback action and goes back to the previous state
#     of the dialogue"""
#
#     def name(self):
#         return 'action_unknown_intent'
#
#     def run(self, dispatcher, tracker, domain):
#         from rasa_core.events import UserUtteranceReverted
#         # text = tracker.latest_message.get('text')
#         # qa_message = get_qa(text)
#         # if qa_message != "未找到答案":
#         #     dispatcher.utter_message("{}".format(qa_message))
#         # else:
#         #     dispatcher.utter_template('utter_default', tracker, silent_fail=True)
#         # return []
#
#         text = tracker.latest_message.get('text')
#         # qa_message = get_qa(text)
#         qa_message = "未找到答案"
#         if qa_message != "未找到答案":
#             dispatcher.utter_message("{}".format(qa_message))
#         else:
#             message = get_qa(text)
#             if message[0]['confidence'] >= 0.8:
#                 dispatcher.utter_message("{}".format(message[0]['answer']))
#             else:
#                 dispatcher.utter_template('utter_default', tracker, silent_fail=True)
#         return []


class CaseForm(FormAction):
    """A custom form action"""

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""
        return "case_form"

    @staticmethod
    def required_slots(tracker):
        # type: () -> List[Text]
        """A list of required slots that the form has to fill"""
        return ["case", "place", "day"]

    def slot_mappings(self):
        return {"case": self.from_entity(entity="case", not_intent="unknown_intent"),
                "place": [self.from_entity(entity="place"),
                          self.from_text()],
                "day": [self.from_entity(entity="day"),
                        self.from_text()]
                }

    # # 无数据验证可省略
    # def validate(self,
    #              dispatcher: CollectingDispatcher,
    #              tracker: Tracker,
    #              domain: Dict[Text, Any]) -> List[Dict]:
    #     """Validate extracted requested slot
    #         else reject the execution of the form action
    #     """
    #     # extract other slots that were not requested
    #     # but set by corresponding entity
    #     slot_values = self.extract_other_slots(dispatcher, tracker, domain)
    #
    #     # extract requested slot
    #     slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
    #     if slot_to_fill:
    #         slot_values.update(self.extract_requested_slot(dispatcher,
    #                                                        tracker, domain))
    #         if not slot_values:
    #             # reject form action execution
    #             # if some slot was requested but nothing was extracted
    #             # it will allow other policies to predict another action
    #             raise ActionExecutionRejection(self.name(),
    #                                            "Failed to validate slot {0} "
    #                                            "with action {1}"
    #                                            "".format(slot_to_fill,
    #                                                      self.name()))
    #     return [SlotSet(slot, value) for slot, value in slot_values.items()]

    def submit(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """Define what the form has to do
            after all required slots are filled"""
        # utter submit template
        dispatcher.utter_template('utter_search_template', tracker)
        dispatcher.utter_message("{},在{}发生一起性质恶劣的{},引起全市人民的高度关注，以下是详细信息："
                                 .format(tracker.get_slot("day"), tracker.get_slot("place"), tracker.get_slot("case")))
        return [AllSlotsReset()]
