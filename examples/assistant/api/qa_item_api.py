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
from requests import (
    ConnectionError,
    HTTPError,
    TooManyRedirects,
    Timeout
)
logger = logging.getLogger(__name__)


def get_qa_item(msg):
    # key = ''   # 自己的图灵机器人key
    # api = 'http://www.tuling123.com/openapi/api?key={}&info={}'.format(key, msg)
    # return requests.get(api).json()
    key = ''   # 自己的图灵机器人key
    msg = re.sub(r"(?:<br/>|[^\w\u4e00-\u9fff,.，。？?!！]+)", "", msg)
    # zyb-note: -> 注意这里引用另外一个容器的服务
    api = 'http://nginx_qa_item_server:8999/anyq?question={}'.format(msg)
    # api = '192.168.46.36:8999/anyq?question={}'.format(msg)
    try:
        return requests.get(api).json()
    except Exception as e:
        logger.error(
            "Failed to parse text '{}'over http. "
            "Error: {}".format(msg, e))
        return []


if __name__ == '__main__':
    result = get_qa("提现")
    print(json.dumps(result, ensure_ascii=False))
