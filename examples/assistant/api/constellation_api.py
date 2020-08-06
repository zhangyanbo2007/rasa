#!/usr/bin/env python
"""
Weather data is provided by https://www.seniverse.com/,
below code are modified from https://github.com/seniverse/seniverse-api-demos

NOTE: user need provide shell environment `SENIVERSE_KEY` and `SENIVERSE_UID`\
 to using this API
"""
import os

import requests
import json

import logging

logger = logging.getLogger(__name__)
URL = 'http://route.showapi.com/872-1'  # API URL，可替换为其他 URL

SHOWAPI_APPID = "76103"
SHOWAPI_SIGN = "3240ad862be64c7489b0040f5b54a23e"
constellation_dict = {
    "白羊座": "baiyang",
    "金牛座": "jinniu",
    "双子座": "shuangzi",
    "巨蟹座": "juxie",
    "狮子座": "shizi",
    "处女座": "chunv",
    "天秤座": "tiancheng",
    "天蝎座": "tianxie",
    "射手座": "sheshou",
    "摩羯座": "mojie",
    "水瓶座": "shuiping",
    "双鱼座": "shuangyu",
}


#调用星座API
def fetch_constellation(constellation):
    if constellation in constellation_dict.keys():
        data = dict(showapi_appid=SHOWAPI_APPID, showapi_sign=SHOWAPI_SIGN, star=constellation_dict[constellation], needTomorrow="1", needWeek="1",
                    needMonth="1", needYear="1")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        result = requests.post(url=URL, data=data, headers=headers)
        msg = json.loads(result.text)
        return msg["showapi_res_body"]
    else:
        return None


#解析星座内容
def get_constellation(constellation, time="今天", value="运势"):
    data = fetch_constellation(constellation)
    return_list = []
    constellation_time = {"今天": "day", "明天": "tomorrow", "本周": "week", "本月": "month", "本年": "year"}
    constellation_index = {"综合指数": "summary_star", "爱情指数": "love_star", "财富指数": "money_star", "工作指数": "work_star"}
    constellation_fortune = {"爱情运势": "love_txt", "财富运势": "money_txt", "工作运势": "work_txt", "学业运势": "work_txt"}
    constellation_day = {"吉时": "lucky_time", "吉利方位": "lucky_direction", "幸运数字": "lucky_num",
                         "贵人星座": "grxz", "幸运色": "lucky_color", "提醒": "day_notice"}
    constellation_week = {"吉时": "lucky_time", "吉利方位": "lucky_direction", "幸运数字": "lucky_num", "健康运势": "health_txt",
                          "贵人星座": "grxz", "小人星座": "xrxz", "幸运色": "lucky_color", "吉日": "lucky_day", "提醒": "week_notice"}
    constellation_month = {"吉时": "lucky_time", "吉利方位": "lucky_direction", "幸运数字": "lucky_num",
                           "贵人星座": "grxz", "小人星座": "xrxz", "缘分星座": "yfxz", "幸运色": "lucky_color", "优势": "month_advantage", "弱势": "month_weakness"}
    constellation_year = {"健康运势": "health_txt", "简评": "oneword"}

    #默认为今天的星座
    if time not in constellation_time.keys():
        time = "今天"

    if data is not None:
        if time in constellation_time.keys():
            if value.find("指数") >= 0:
                for index in constellation_index.keys():
                    if value.find(index) >= 0:
                        msg = "您{}的{}如下：{}".format(time, index, data[constellation_time[time]][constellation_index[index]])
                        return_list.append(msg)

            if value.find("运势") >= 0:
                forture_flag = 0
                for fortune in constellation_fortune.keys():
                    if value.find(fortune) >= 0:
                        msg = "您{}的{}如下：{}".format(time, fortune, data[constellation_time[time]][constellation_fortune[fortune]])
                        return_list.append(msg)
                        forture_flag = 1
                if forture_flag == 0 and value.find("健康运势") < 0:
                    msg = "您{}的运势如下：{}".format(time, data[constellation_time[time]]["general_txt"])
                    return_list.append(msg)

            if time.find("今天") >= 0 or time.find("明天") >= 0:
                for index in constellation_day.keys():
                    if value.find(index) >= 0:
                        msg = "您{}的{}如下：{}".format(time, index,
                                                   data[constellation_time[time]][constellation_day[index]])
                        return_list.append(msg)

            if time.find("本周") >= 0:
                for index in constellation_week.keys():
                    if value.find(index) >= 0:
                        msg = "您{}的{}如下：{}".format(time, index,
                                                   data[constellation_time[time]][constellation_week[index]])
                        return_list.append(msg)

            if time.find("本月") >= 0:
                for index in constellation_month.keys():
                    if value.find(index) >= 0:
                        msg = "您{}的{}如下：{}".format(time, index,
                                                   data[constellation_time[time]][constellation_month[index]])
                        return_list.append(msg)

            if time.find("本年") >= 0:
                for index in constellation_year.keys():
                    if value.find(index) >= 0:
                        msg = "您{}的{}如下：{}".format(time, index,
                                                   data[constellation_time[time]][constellation_year[index]])
                        return_list.append(msg)

        if len(return_list) == 0:
            msg = "很抱歉查不到您{}的{}".format(time, value)
            # print(msg)
            # logger.info(msg)
            return msg
        else:
            msg = "\n".join(return_list)
            # print(msg)
            # logger.info(msg)
            return msg
    else:
        msg = "很抱歉查不到{}的信息".format(constellation)
        # print(msg)
        # logger.info(msg)
        return msg


if __name__ == '__main__':
    get_constellation("摩羯座", "本周", "爱情运势")
    get_constellation("摩羯座", "本年", "财富运势")
    get_constellation("摩羯座", None, "幸运色")
    get_constellation("摩羯座", None, "幸运数字")
