#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by C.L.Wang
# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function

from annoy import AnnoyIndex

#PYTHON2请求方式
# import urllib, urllib2, base64
# reload(sys)
# sys.setdefaultencoding('utf8')

#PYTHON3请求方式
import urllib.request, urllib.parse, base64
import requests


def search_img(text):
    """
    根据文字检索图片，这块为了可控后续换成本地模式，已废弃
    :param text:
    :return:
    """
    # url = 'https://www.doutula.com/api/search?keyword=%s&mime=%s&page=%s'
    url = 'https://www.doutula.com/api/search'
    # headers = {'Content-Type': 'application/json;charset=UTF-8'}
    data = {}
    img_list = list()
    for j in range(50):  # 50页
        data['keyword'] = text
        data['mime'] = 0
        data['page'] = j+1
        #通用代码
        contents = (requests.post(url=url, data=data)).json()
        if contents["status"] == 1:  # zyb说明有数据
            for content in contents["kg_data"]["list"]:
                img_list.append(content)
                if len(img_list) >= 5:
                    return img_list
        if contents["kg_data"]["more"] != 1:  # 没有数据了
            return img_list
    return img_list


if __name__ == '__main__':
    search_img("金馆长")
    print("finish")