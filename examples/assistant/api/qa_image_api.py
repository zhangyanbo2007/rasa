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


def get_qa_image(msg):
    # key = ''   # 自己的图灵机器人key
    # api = 'http://www.tuling123.com/openapi/api?key={}&info={}'.format(key, msg)
    # return requests.get(api).json()
    key = ''   # 自己的图灵机器人key
    msg = re.sub(r"(?:<br/>|[^\w\u4e00-\u9fff,.，。？?!！]+)", "", msg)
    # zyb-note: -> 注意这里引用另外一个容器的服务
    api = 'http://qa_image_server1:8999/anyq?question={}'.format(msg)
    # api = '192.168.46.36:8999/anyq?question={}'.format(msg)
    try:
        return requests.get(api).json()
    except Exception as e:
        logger.error(
            "Failed to parse text '{}'over http. "
            "Error: {}".format(msg, e))
        return []


def search_img(text):
    """
    通过QA的索引列表查询本地图片，这个地方是临时的本地处理方式，后续要做成一个服务，因为文件实在太大了。
    这个地方我还是决定放在本地
    :param text:
    :return:
    """
    img_path = "/dialog_server/database/images/images_source"  # 注意这个地方的图片是固定的路径
    img_list = get_qa_image(text)
    if len(img_list):
        for num in range(len(img_list)-1, -1, -1):
            img_name = re.findall(r"\d*?-(.*?)$", img_list[num]["answer"])[0]  # 临时加的，后续这个地方要改成下面的格式
            # img_name =  img["answer"]
            path = os.path.join(img_path, img_name)
            if os.path.exists(path.encode("utf-8")):  # 如果存在添加进去，如果不存在则应该剔除
                img_list[num]["answer"] = path
            else:
                img_list.pop(num)
    return img_list


if __name__ == '__main__':
    # result = get_qa_image("我要把欺负我的人都变成傻蛋")
    result = search_img("我决定把欺压我的家伙全部给变做傻子")
    print(json.dumps(result, ensure_ascii=False))
