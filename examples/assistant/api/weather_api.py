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
from requests import (
    ConnectionError,
    HTTPError,
    TooManyRedirects,
    Timeout
)

KEY = os.getenv('SENIVERSE_KEY', 'jmxnvpumy8txxz24')  # API key
UID = ""  # 用户ID, TODO: 当前并没有使用这个值,签名验证方式将使用到这个值

LOCATION = 'beijing'  # 所查询的位置，可以使用城市拼音、v3 ID、经纬度等
API = 'https://api.seniverse.com/v3/weather/daily.json'  # API URL，可替换为其他 URL
UNIT = 'c'  # 单位
LANGUAGE = 'zh-Hans'  # 查询结果的返回语言

weather_number = {"今天": 0, "明天": 1, "后天": 2}


def fetch_weather(location, start=0, days=15):
    result = requests.get(API, params={
        'key': KEY,
        'location': location,
        'language': LANGUAGE,
        'unit': UNIT,
        'start': start,
        'days': days
    }, timeout=2)
    return result.json()


def get_weather_by_number(location, day=1):
    result = fetch_weather(location)
    if 'status' not in result.keys():
        normal_result = {
            "location": result["results"][0]["location"],
            "result": result["results"][0]["daily"][day]
        }
    else:
        normal_result = {}
    return normal_result


def get_weather(address, time="明天"):
    try:
        result = get_weather_by_number(address, weather_number[time])
        if result == {}:
            text_message_tpl = """
                很抱歉查不到{} {} 的天气情况
            """
            text_message = text_message_tpl.format(
                address,
                time,
            )
        else:
            text_message_tpl = """
                {} {} ({}) 的天气情况为：白天：{}；夜晚：{}；气温：{}-{} °C
            """
            text_message = text_message_tpl.format(
                result['location']['name'],
                time,
                result['result']['date'],
                result['result']['text_day'],
                result['result']['text_night'],
                result['result']["high"],
                result['result']["low"],
            )
    except (ConnectionError, HTTPError, TooManyRedirects, Timeout) as e:
        text_message = "{}".format(e)

    return text_message

if __name__ == '__main__':
    default_location = "合肥"
    result = fetch_weather(default_location)
    print(json.dumps(result, ensure_ascii=False))

    default_location = "合肥"
    result = get_weather(default_location)
    print(json.dumps(result, ensure_ascii=False))
