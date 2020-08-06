#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from flask import Flask
import urllib
import hashlib
import urllib.parse
import urllib.request
from flask import request
from typing import Dict, Text, Any, List, Union
import json
import logging
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer, HashingVectorizer
import jieba
import numpy as np
import os
import re
import pandas as pd

app = Flask(__name__)

app_key = "25548908"
appSecret = "9352bffeb03e7b012d96ca8e0d72f65f"
adzone_id = "106035300166"

logger = logging.getLogger(__name__)


def ksort(d):
    return [(k, d[k]) for k in sorted(d.keys())]


def md5(s, raw_output=False):
    """Calculates the md5 hash of a given string"""
    res = hashlib.md5(s.encode())
    if raw_output:
        return res.digest()
    return res.hexdigest()


def createSign(paramArr):
    sign = appSecret
    paramArr = ksort(paramArr)
    paramArr = dict(paramArr)
    # print(paramArr)
    for k, v in paramArr.items():
        if k != "" and v != "":
            sign += k + v
    sign += appSecret
    # print(sign)
    sign = md5(sign).upper()
    return sign


def createStrParam(paramArr):
    strParam = ""
    for k, v in paramArr.items():
        if k != "" and v != "":
            strParam += k + "=" + urllib.parse.quote_plus(v) + "&"
    return strParam


# 如需固定API 可在下方数组内加入. 如"method"=> "taobao.tbk.privilege.get"
paramArr = {"app_key": app_key, "v": "2.0", "sign_method": "md5", "format": "json", "adzone_id": adzone_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "method": "taobao.tbk.dg.material.optional"}
# print(paramArr)
# 如需固定API 可在下方数组内加入. 如"method"=> "taobao.tbk.privilege.get"
optimus_paramArr = {"app_key": app_key, "v": "2.0", "sign_method": "md5", "format": "json", "adzone_id": adzone_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "method": "taobao.tbk.dg.optimus.material"}


# print(paramArr)

@app.route("/")
def hello_world():
    abc = "For Example:gxapi?session=6101e11da8f3e7596331c7d929076e7960e337657ec204a82248874&" \
          "item_id=552365633968&adzone_id=67754887&site_id=17832334"
    abc += "<br>" + "Get session:https://oauth.taobao.com/authorize?response_type=token&" \
                    "client_id=23421352&state=mrtk&view=web"

    return abc


@app.route("/get_taobao_web", methods={"GET", "POST"})
def get_taobao_web():
    global paramArr
    paramArr = {**paramArr, **request.args.to_dict()}
    sign = createSign(paramArr)
    strParam = createStrParam(paramArr)
    strParam += "sign=" + sign
    url = "http://gw.api.taobao.com/router/rest?" + strParam
    # print(url)
    res = urllib.request.urlopen(url).read().decode("utf-8")
    return res


def get_taobao(msg: Text, page_size="20") -> Text:
    """
    获取淘宝数据，默认20条
    :param msg:
    :param page_size:
    :return:
    """
    global paramArr
    paramArr = {**paramArr, "q": msg, "page_size": page_size}
    sign = createSign(paramArr)
    strParam = createStrParam(paramArr)
    strParam += "sign=" + sign
    url = "http://gw.api.taobao.com/router/rest?" + strParam
    # print(url)
    try:
        str = urllib.request.urlopen(url).read().decode("utf-8")
    except Exception as e:
        logger.info("error:{}".format(e))
        return []

    res = json.loads(str)
    if "error_response" in res.keys():
        return []
    else:
        return ["title:{}&&item_url:{}&&reserve_price:{}".format(map_data["title"], map_data["item_url"],
                                                                 map_data["reserve_price"]) for map_data in
                res["tbk_dg_material_optional_response"]["result_list"]["map_data"]]


def jaccard_similarity(s1, s2):
    """
    求s1与s2的相似度
    :param s1:
    :param s2:
    :return:
    """

    def token_add_space(s):
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "data/stop_words/stop_words.txt"), encoding="utf-8") as f:
            stopwords = f.readlines()
            stopwords = [stopword.strip() for stopword in stopwords]
        segs = jieba.lcut(s)
        segs = list(filter(lambda x: x.strip(), segs))  # 去左右空格
        segs = list(filter(lambda x: x not in stopwords, segs))  # 去停用词
        return ' '.join(segs)

    # 将字中间加入空格
    s1, s2 = token_add_space(s1), token_add_space(s2)
    # 转化为计数矩阵
    cv = CountVectorizer(token_pattern=r"(?u)\b\w+\b")
    corpus = [s1, s2]
    vectors = cv.fit_transform(corpus).toarray()
    # 求交集
    numerator = np.sum(np.min(vectors, axis=0))
    # 求并集
    denominator = np.sum(np.max(vectors, axis=0))
    # 计算杰卡德系数
    return 1.0 * numerator / denominator


def judge_item(s1):
    """
    通过jaccard相似度匹配判断是否是商品标题
    实测大于0.1即可确认
    实测最大耗时0.25S
    :param s1:
    :return:
    """
    result = get_taobao(s1, "1")
    if result:
        s2 = re.findall(r"title:(.*)&&item_url", result[0])[0]
        # s1 = '你在干嘛呢'
        # s2 = '你在干什么呢'
        # print("匹配概率为：{}".format(jaccard_similarity(s1, s2)))
        return jaccard_similarity(s1, s2)
    else:
        # print("不匹配")
        return 0


def get_item(material_id, page_size="20", page_no="1") -> Text:
    """
    获取淘宝数据，默认20条
    :param msg:
    :param page_size:
    :return:
    """
    global optimus_paramArr
    optimus_paramArr = {**optimus_paramArr, "material_id": material_id, "page_size": page_size, "page_no": page_no}
    sign = createSign(optimus_paramArr)
    strParam = createStrParam(optimus_paramArr)
    strParam += "sign=" + sign
    url = "http://gw.api.taobao.com/router/rest?" + strParam
    # print(url)
    try:
        str = urllib.request.urlopen(url).read().decode("utf-8")
    except Exception as e:
        logger.info("error:{}".format(e))
        return []

    res = json.loads(str)
    if "error_response" in res.keys():
        return []
    else:
        return res["tbk_dg_optimus_material_response"]["result_list"]["map_data"]


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True)
    return_data = get_taobao("曼龙宝宝爬行垫加厚无味xpe婴儿泡沫客厅游戏", "1")
    for i in range(0, 1):
        start_time = time.time()
        judge_item("谧斯T恤")
        end_time = time.time()
        print("test{}:耗时{}s".format(i, end_time-start_time))
