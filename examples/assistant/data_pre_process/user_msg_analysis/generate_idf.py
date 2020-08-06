import requests
import json
import re
import sys
import os
import jieba
import math
import time
sys.path.append('/dialog_server/source/bot_application/api')
from taobao_api import get_item


def generate_all_dict():
    total = 0
    all_dict = {}
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "result", "stop_words", "stopwords.txt"), "r", encoding="GBK") as f:
        stopwords = [line.strip() for line in f.readlines()]
    # 获取每个目录下所有的文件
    with open(os.path.join("items_data", "items_string.json"), "r", encoding="utf-8") as f:
        items_string_dict = json.load(f)
        for key in items_string_dict.keys():
            content = items_string_dict[key]
            content = content.replace("\r\n", "")  # 删除换行和多余的空格
            content = content.replace(" ", "")
            content_seg = jieba.cut(content.strip())  # 为文件内容分词
            outstr = []
            for word in content_seg:
                if word not in stopwords:
                    if word != '\t' and word != '\n':
                        outstr.append(word)
            for word in outstr:
                if ' ' in outstr:
                    outstr.remove(' ')
            temp_dict = {}
            total += 1
            for word in outstr:
                # print(word)
                temp_dict[word] = 1
                # print(temp_dict)
            for key in temp_dict:
                num = all_dict.get(key, 0)
                all_dict[key] = num + 1

    # idf_dict字典就是生成的IDF语料库
    idf_dict = {}
    for key in all_dict:
        # print(all_dict[key])
        w = key
        p = '%.10f' % (math.log10(total / (all_dict[key] + 1)))
        if u'\u4e00' < w <= u'\u9fa5':
            idf_dict[w] = p
    print('IDF字典构造结束')
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "result", "idf_words", "idf.txt"), 'w', encoding='utf-8') as fw:
        for num, k in enumerate(idf_dict):
            if k != '\n':
                print(k)
                if num != len(idf_dict)-1:
                    fw.write(k + ' ' + idf_dict[k] + '\n')
                else:
                    fw.write(k + ' ' + idf_dict[k])
        print('IDF字典生成完毕,总字数:{}'.format(num))


if __name__ == "__main__":
    generate_all_dict()

