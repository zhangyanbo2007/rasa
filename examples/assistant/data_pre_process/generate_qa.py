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


def generate_items_qa():
    """
    :return:
    """
    qa_list = ["question" + '\t' + "answer"]

    with open(os.path.join(os.path.dirname(__file__), "user_msg_analysis", "items_data", "items_string.json"), "r", encoding="UTF-8") as f:
        qa_dict = json.load(f)
        for (key, value) in qa_dict.items():
            data_str = str(value) + '\t' + str(key)
            qa_list.append(data_str)

    with open(os.path.join(os.path.dirname(__file__), "result/qa_data/qa_items_data/sample_docs"), "w", encoding="UTF-8") as fopen:
        fopen.write("\n".join(qa_list))


def generate_chit_qa():
    """
    :return:
    """
    chit_list = ["question" + '\t' + "answer\n"]
    with open(os.path.join(os.path.dirname(__file__), "other_chit/origin_qingyundata.csv"), "r", encoding="UTF-8") as f:
        for line in f:
            data_list = line.split("|")
            if len(data_list) == 2:  # 不等于2的舍弃
                data_str = "".join(data_list[0].strip().split()) + '\t' + "".join(data_list[1].strip().split()) + '\n'
                chit_list.append(data_str)

    with open(os.path.join(os.path.dirname(__file__), "result/qa_data/qa_chit_data/sample_docs"), "w", encoding="UTF-8") as fopen:
        fopen.write("".join(chit_list))


def generate_images_qa():
    """
    :return:
    """
    qa_list = ["question" + '\t' + "answer\n"]
    for root, dirs, file_list in os.walk("/dialog_server/database/images/images_source".encode('utf-8'), topdown=False):
        for file in file_list:
            answer = file.decode()
            # data_list = re.findall(r"\d*?-(.*?)(?:.gif|.jpg|.jpeg)", answer)
            data_list = re.findall(r"^(.*?)(?:.gif|.jpg|.jpeg)", answer)
            if len(data_list) == 1 and data_list[0] != "":
                question = data_list[0]
                data_str = question + '\t' + answer + '\n'
                qa_list.append(data_str)
    with open(os.path.join(os.path.dirname(__file__), "result/qa_data/qa_images_data/sample_docs"), "w", encoding="UTF-8") as fopen:
        fopen.write("".join(qa_list))


if __name__ == "__main__":
    # generate_items_qa()
    # generate_chit_qa()
    generate_images_qa()
