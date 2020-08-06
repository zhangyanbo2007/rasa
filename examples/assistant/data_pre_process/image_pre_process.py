import requests
import json
import re
import sys
import os
import jieba
import math
import time
from shutil import copyfile, copy
sys.path.append('/dialog_server/source/bot_application/api')
from baidu_ocr_api import recognize_img_words
from baidu_sex_detect_api import recognize_sex_detect


def generate_no_word_images():
    """
    :return:
    """
    for root, dirs, file_list in os.walk("./images".encode('utf-8'), topdown=False):
        for file in file_list:
            image_name = recognize_img_words(os.path.join(root, file))
            if image_name == "":
                copy(os.path.join(root, file), "./image_pre_process/no_word_images".encode('utf-8'))


def generate_filt_sex_images():
    """
    过滤黄图
    :return:
    """
    for root, dirs, file_list in os.walk("./images".encode('utf-8'), topdown=False):
        for file in file_list:
            result = recognize_sex_detect(os.path.join(root, file))
            #  正常图片
            if result == 255:
                copy(os.path.join(root, file), "./image_pre_process/no_sex_images".encode('utf-8'))
            #  非正常图片
            else:
                if not os.path.exists(os.path.join("./image_pre_process", str(result))):
                    os.mkdir(os.path.join("./image_pre_process", str(result)))
                copy(os.path.join(root, file), os.path.join("./image_pre_process", str(result)).encode('utf-8'))


if __name__ == "__main__":
    # generate_no_word_images()
    generate_filt_sex_images()
