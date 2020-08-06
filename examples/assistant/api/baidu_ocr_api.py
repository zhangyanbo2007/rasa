#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by C.L.Wang
# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function

import shutil, os
import json
import time
import re
#通用请求方式
import sys
import requests
from datetime import datetime
from datetime import timedelta

#PYTHON2请求方式
# import urllib, urllib2, base64
# reload(sys)
# sys.setdefaultencoding('utf8')

#PYTHON3请求方式
import urllib.request, urllib.parse, base64

app_key = '15213870'
api_key = "yevqBGRaOvsRLKUVpY30GyWa"
secret_key = 'hZFX56yP7RsIgttXkGeocf2oBSLuVAOA'

global access_token
global update_access_token_flag
global last_time
global now_time
update_access_token_flag = 1
now_time = datetime.now().date()
last_time = now_time
access_token = '24.97a0feee99f0b548b33462e4bf721dc3.2592000.1569674979.282335-15213870'#zyb这个每个月要定时更新


def get_access_token(api_key, secret_key):
    api_key_url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s'
    host = (api_key_url % (api_key, secret_key))
    headers = {
        'Content-Type': 'application/json;charset=UTF-8'
    }

    #通用方式
    content = requests.get(url=host, headers=headers).json()
    return content['access_token']

    # python2方式
    # request = urllib2.Request(host)
    # request.add_header('Content-Type', 'application/json; charset=UTF-8')
    # response = urllib2.urlopen(request)
    # content = json.loads(response.read())
    # print(content['access_token'])
    # return content['access_token']

    # python3方式
    # req = urllib.request.Request(host)
    # req.add_header('Content-Type', 'application/json; charset=UTF-8')
    # response = urllib.request.urlopen(req)
    # res = response.read()
    # content = json.loads(res)
    # return content['access_token']


def recognize_img_words(input_img):
    global now_time
    global last_time
    global update_access_token_flag
    global access_token
    now_time = datetime.now().date()
    if now_time - last_time > timedelta(days=15):  #  每隔15天更新一次
        update_access_token_flag = 1
    if update_access_token_flag == 1:
        access_token = get_access_token(api_key=api_key, secret_key=secret_key)
        with open("/dialog_server/source/bot_application/api/config/baidu_ocr_access.txt", "w") as f:
            f.write(access_token)
        last_time = datetime.now().date()
        update_access_token_flag = 0
    # url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=' + access_token
    url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
    data = {}
    data['access_token'] = access_token
    # 二进制方式打开图文件
    f = open(input_img, 'rb')
    image_data = f.read()
    f.close()
    img = base64.b64encode(image_data)
    data['image'] = img

    # 参数image：图像base64编码
    #通用代码
    # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    # content = (requests.post(url=url, headers=headers, data=data)).json()

    # python2代码
    # params = urllib.urlencode(data)
    # request = urllib2.Request(url, params)
    # request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    # try:
    #     response = urllib2.urlopen(request)
    #     content = json.loads(response.read())
    # except urllib2.HTTPError, e:
    #     print e.getcode()
    #     return

    #python3代码
    params = urllib.parse.urlencode(data).encode('utf-8')
    request = urllib.request.Request(url, params)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    response = urllib.request.urlopen(request)
    content = json.loads(response.read())


    # 识别出的图片数据
    #python3模式提取
    # if content['error_code'] == 216201
    str = ''
    if 'words_result' in content:
        words_result = content['words_result']
        words_list = list()
        for words in words_result:
            sub_str = re.sub("[^\u4e00-\u9fa5^ ^ ^,^，^.^。^?^？^！^!^a-z^A-Z^0-9]", "", words['words'])
            words_list.append(sub_str)

        if len(words_list) > 0:
            str = ','.join(words_list)
            if len(str) > 80:  # zyb后续这个地方要优化
                str = str[0:80]
        return str
    else:
        return "error"


if __name__ == '__main__':
    local_img = '111.jpg'
    access_token = get_access_token(api_key=api_key, secret_key=secret_key)
    print(access_token)

    # text = recognize_img_words(local_img)
    # print("识别到的文本是{}".format(text))
