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
import re
import logging
from urllib import parse
from requests import (
    ConnectionError,
    HTTPError,
    TooManyRedirects,
    Timeout
)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_kg(msg):
    # key = ''   # 自己的图灵机器人key
    # api = 'http://www.tuling123.com/openapi/api?key={}&info={}'.format(key, msg)
    # return requests.get(api).json()
    key = ''   # 自己的图灵机器人key
    msg = re.sub(r"(?:<br/>|[^\w\u4e00-\u9fff,.，。？?!！]+)", "", msg)
    datas = {"question": msg}
    # 字典转参数
    param = parse.urlencode(datas)
    api = 'http://192.168.46.36:8000/search?{}'.format(param)
    try:
        return [requests.get(api).json()]
    except Exception as e:
        logger.error(
            "Failed to parse text '{}'over http. "
            "Error: {}".format(msg, e))
        return []


if __name__ == '__main__':
    result = get_kg("姚明的儿子是谁")
    # print(json.dumps(result, ensure_ascii=False))
    # logger.debug(json.dumps(result, ensure_ascii=False))