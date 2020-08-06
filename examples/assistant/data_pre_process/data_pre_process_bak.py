#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：Zhang Yanbo time:2019/5/15

import os
import re
import json
import sys
import xlrd
import xlsxwriter
from xlutils.copy import copy
import pandas as pd
from pandas import DataFrame
import numpy as np
import jieba
import jieba.posseg
import math
import random
sys.path.append('/dialog_server/source/bot_application/api')
import logging
from qa_api import get_qa

# import re
#
# s = 'dneog1893^&&341den'
# r1 = "[a-zA-Z0-9\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、：；;《》“”~@#￥%……&*（）]+"
# kg_data = re.sub(r1, '', s)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
pattern = re.compile(r'(?:<br/>|[^\w\u4e00-\u9fff,.，。？?!！]+)')


def process_constellation():
    """
    处理星座数据
    :return:
    """
    constellation_faq_dict = {"rasa_nlu_data": {}}
    constellation_faq_dict["rasa_nlu_data"]["common_examples"] = []
    constellation_faq_dict["rasa_nlu_data"]["entity_synonyms"] = []
    constellation_faq_dict["rasa_nlu_data"]["regex_features"] = []
    temp_dict = []
    count = 0
    with open(os.path.dirname(__file__) + "/constellation_faq/origin_constellation_faq.txt", "r") as f:
        for line_num, line in enumerate(f):
            ask_sentence = re.findall(r"^[0-9]+、(.*)$", line)
            if len(ask_sentence) != 0:
                ask_valid_sentence = pattern.sub("", ask_sentence[0])
                # 赋值给上一个
                if count >= 1:
                    constellation_faq_dict["rasa_nlu_data"]["common_examples"][count - 1]["answer_text"].append("".join(
                        temp_dict).strip())
                    temp_dict = []
                constellation_faq_sub_dict = {"entities": [], "intent": "intent_constellation_faq_bot",
                                              "answer_text": [], "text": ask_valid_sentence}
                constellation_faq_dict["rasa_nlu_data"]["common_examples"].append(constellation_faq_sub_dict)
                count += 1
            else:
                temp_dict.append(line.strip())

        # 赋值给最后一个
        constellation_faq_dict["rasa_nlu_data"]["common_examples"][count - 1]["answer_text"].append("".join(
            temp_dict).strip())

    # 去除问答中无效的数据对
    # TODO:暂时只去除空字符串，后续待改进
    datas = []
    for data in constellation_faq_dict["rasa_nlu_data"]["common_examples"]:
        data["answer_text"] = list(set(data["answer_text"]))
        if data["text"] == "":
            datas.append(data)
        elif "" in data["answer_text"]:
            if len(data["answer_text"]) != 1:
                data["answer_text"].remove("")
            else:
                datas.append(data)
    for data in datas:
        constellation_faq_dict["rasa_nlu_data"]["common_examples"].remove(data)

    # 按最新格式生成数据
    for num, data in enumerate(constellation_faq_dict["rasa_nlu_data"]["common_examples"]):
        ans_dict = {"type": "other_chit", "intent": "intent_constellation_faq_bot",
                    "match_item": constellation_faq_dict["rasa_nlu_data"]["common_examples"][num]["text"],
                    "ans_list": constellation_faq_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"],
                    "entity": "", "confidence": 0}
        constellation_faq_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"] = ans_dict

    with open(os.path.dirname(__file__) + "/result/nlu_data/constellation_faq/constellation_faq.json", "w") as f:
        json.dump(constellation_faq_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def delete_stopword(msg):
    """
    去停用词
    :param msg:
    :return:
    """
    return re.sub(r"", "",msg)


def process_boast():
    """
    处理夸夸数据:总计18278条数据
    :return:
    """
    boast_dict = {"rasa_nlu_data": {}}
    boast_dict["rasa_nlu_data"]["common_examples"] = []
    boast_dict["rasa_nlu_data"]["entity_synonyms"] = []
    boast_dict["rasa_nlu_data"]["regex_features"] = []
    temp_dict = []
    count = 0
    last_data = ""
    with open(os.path.dirname(__file__) + "/boast/origin_douban_kuakua_qa.txt", "r") as f:
        for line_num, line in enumerate(f):
            ask_sentence = re.findall(r"^Q:	(.*)$", line)
            ans_sentence = re.findall(r"^A:	(.*)$", line)
            if len(ask_sentence) != 0:
                ask_valid_sentence = pattern.sub("", ask_sentence[0])
                # 赋值给上一个
                if last_data != ask_valid_sentence:
                    if count >= 1:
                        boast_dict["rasa_nlu_data"]["common_examples"][count - 1]["answer_text"].extend(
                            temp_dict[0:10])  # 仅保留最多10组备选
                        temp_dict = []

                    boast_sub_dict = {"entities": [], "intent": "intent_boast_bot", "answer_text": [],
                                      "text": ask_valid_sentence}
                    boast_dict["rasa_nlu_data"]["common_examples"].append(boast_sub_dict)
                    count += 1
                last_data = ask_valid_sentence
            elif len(ans_sentence) != 0:
                data = ans_sentence[0].strip()

                # 判断最后一个字是否是夸字，没有的话补上
                if len(data) > 0:
                    if data[-1] != "夸":
                        data = data + " 夸"
                else:
                    pass
                temp_dict.append(data)

        # 赋值给最后一个
        boast_dict["rasa_nlu_data"]["common_examples"][count - 1]["answer_text"].extend(temp_dict[0:10])

    # 去除问答中无效的数据对
    # TODO:暂时只去除空字符串，后续待改进
    datas = []
    for data in boast_dict["rasa_nlu_data"]["common_examples"]:
        data["answer_text"] = list(set(data["answer_text"]))
        if data["text"] == "" or (data["text"].find("表扬") == -1 and data["text"].find("鼓励") == -1 and
                                  data["text"].find("夸") == -1 and data["text"].find("安慰") == -1):
            datas.append(data)
        elif "" in data["answer_text"]:
            if len(data["answer_text"]) != 1:
                data["answer_text"].remove("")
            else:
                datas.append(data)
    for data in datas:
        boast_dict["rasa_nlu_data"]["common_examples"].remove(data)

    # 按最新格式生成数据
    for num, data in enumerate(boast_dict["rasa_nlu_data"]["common_examples"]):
        ans_dict = {"type": "other_chit", "intent": "intent_boast_bot",
                    "match_item": boast_dict["rasa_nlu_data"]["common_examples"][num]["text"],
                    "ans_list": boast_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"],
                    "entity": "", "confidence": 0}
        boast_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"] = ans_dict

    with open(os.path.dirname(__file__) +
              "/result/nlu_data/boast/boast.json", "w", encoding="UTF-8") as f:
        json.dump(boast_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def process_smalltalk():
    """
    处理smalltalk数据,总共1475条数据
    :return:
    """
    smalltalk_dict = {"rasa_nlu_data": {}}
    smalltalk_dict["rasa_nlu_data"]["common_examples"] = []
    smalltalk_dict["rasa_nlu_data"]["entity_synonyms"] = []
    smalltalk_dict["rasa_nlu_data"]["regex_features"] = []
    count = 0
    last_data = ""

    # 下面是写excel
    knowledge_base_data = pd.read_excel("knowledge_base.xlsx", sheet_name="CHIT_DATABASES")
    # workbook = xlrd.open_workbook('knowledge_base.xlsx')
    # knowledge_base_data = workbook.sheet_by_name("CHIT_DATABASES")
    # knowledge_base_data_new = copy(knowledge_base_data).get_sheet(0)
    last_intent = ""
    chit_index = 0
    row_data = ["" for i in range(4)]
    for root, dirs, files in os.walk("ergou_chit", topdown=False):
        for file in files:
            if file[-3:] == ".md":
                with open(os.path.join(root, file), "r") as f:
                    for line_num, line in enumerate(f):
                        ask_sentence = re.findall(r"^- (.*)$", line)
                        intent_line = re.findall(r"^## intent:(.*)$", line)
                        if len(ask_sentence) != 0:
                            # 赋值给上一个
                            ask_valid_sentence = pattern.sub("", ask_sentence[0])

                            # 装载闲聊回答数据
                            ans_list = []
                            with open(os.path.dirname(__file__) + "/ergou_chit/ergou_domain.yml", "r",
                                      encoding="UTF-8") as f1:
                                ans_lines = f1.readlines()
                                for ans_line_n, ans_line in enumerate(ans_lines):
                                    if ans_line_n >= 228:
                                        if ans_line.find(intent) != -1:
                                            number = ans_line_n + 1
                                            while ans_lines[number].find("utter") == -1:
                                                data = re.findall(r"- \"(.*)\"", ans_lines[number])
                                                number += 1
                                                if len(data):
                                                    ans_list.append(data[0])
                                            break

                            if intent != last_intent:
                                if chit_index != 0:
                                    knowledge_base_data.loc[chit_index-1] = row_data
                                    row_data = ["" for i in range(4)]
                                chit_index += 1
                                row_data[0] = chit_index-1
                                row_data[1] = "CHIT:" + intent
                                row_data[3] = "|" + "\n|".join(ans_list)
                                sub_chit_index = 0
                            row_data[2] = row_data[2] + "\n|" + ask_valid_sentence
                            sub_chit_index += 1
                            last_intent = intent
                            ans_dict = {"type": "chit", "intent": "", "match_item": ask_valid_sentence,
                                        "ans_list": ans_list, "entity": "", "confidence": 0}
                            smalltalk_sub_dict = {"entities": [], "intent": intent, "answer_text": ans_dict,
                                                  "text": ask_valid_sentence}
                            smalltalk_dict["rasa_nlu_data"]["common_examples"].append(smalltalk_sub_dict)

                        elif len(intent_line) != 0:
                            intent = intent_line[0].strip()
        # 保存最后一组数据
        knowledge_base_data.loc[chit_index - 1] = row_data
        knowledge_base_data.to_excel('chit_knowledge_base.xlsx', sheet_name="CHIT_DATABASES", index=False)

    with open(os.path.dirname(__file__) + "/result/nlu_data/ergou_chit/ergou_chit.json", "w", encoding="UTF-8") as f:
        json.dump(smalltalk_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def pre_process_knowledge_base():
    """
    规整知识库excel格式
    :return:
    """
    chit_knowledge_base_data = pd.read_excel("chit_knowledge_base.xlsx", sheet_name="CHIT_DATABASES")
    row_data = ["" for i in range(4)]
    sheet_list = ['CMD_DATABASES', 'Q_DATABASES']
    # 遍历3个表
    for sheet in sheet_list:
        data = pd.read_excel('knowledge_base.xlsx', sheet_name=sheet, index_col=0)
        # 遍历表里面的每条数据
        for line_num, line in enumerate(data.values):

            valid_sentence = line[2:]
            valid_sentence = [data for data in valid_sentence if str(data).strip() != "nan" and str(data).strip() != ""]
            row_data[0] = line_num
            row_data[1] = line[0]
            row_data[2] = "|" + "\n|".join(valid_sentence)
            row_data[3] = ""
            chit_knowledge_base_data.loc[line_num] = row_data
        if sheet == "CMD_DATABASES":
            chit_knowledge_base_data.to_excel('cmd_knowledge_base.xlsx', sheet_name="CMD_DATABASES", index=False)
        elif sheet == "Q_DATABASES":
            chit_knowledge_base_data.to_excel('qa_knowledge_base.xlsx', sheet_name="Q_DATABASES", index=False)


def process_chit():
    """
    处理chit数据,剔除重复的无效闲聊数据badlist，总共1475条数据
    :return:
    """
    chit_dict = {"rasa_nlu_data": {}}
    chit_dict["rasa_nlu_data"]["common_examples"] = []
    chit_dict["rasa_nlu_data"]["entity_synonyms"] = []
    chit_dict["rasa_nlu_data"]["regex_features"] = []
    temp_dict = []
    count = 0
    bad_chitchat_list = []
    with open(os.path.dirname(__file__) + "/other_chit/bad_chitchat.txt", "r") as f:
        for line_num, line in enumerate(f):
            data = re.findall(r"^(.*)->.*$", line)[0]
            if data not in bad_chitchat_list:
                bad_chitchat_list.append(data)

    with open(os.path.dirname(__file__) + "/other_chit/rough_sample_docs", "r") as f:
        for line_num, line in enumerate(f):
            ask_sentence = re.findall(r"^(.*)\t.*$", line)
            ans_sentence = re.findall(r"^.*\t(.*)$", line)
            if len(ask_sentence) != 0 and len(ans_sentence) != 0:
                ask_valid_sentence = pattern.sub("", ask_sentence[0])
                if ask_valid_sentence not in bad_other_chit_list and \
                        ask_valid_sentence != "question" and ans_sentence[0].strip() != "answer" and \
                        ask_valid_sentence != "":
                    chit_sub_dict = {"entities": [], "intent": "intent_other_chit_bot",
                                     "answer_text": [ans_sentence[0].strip()], "text": ask_valid_sentence}
                    chit_dict["rasa_nlu_data"]["common_examples"].append(chit_sub_dict)

    with open(os.path.dirname(__file__) + "/other_chit/other_chit.json", "w", encoding="UTF-8") as f:
        json.dump(chit_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def process_knowledge_base():
    """
    处理来自知识库里的二购数据以及系统自建的数据,并生成有效数据
    1生成nlu使用的json文件
    2生成关键词表
    3生成用户词表
    4生成domain文件的意图列表和默认回复列表
    5生成story
    6生成相似度模型用的QA数据对
    :return:
    """
    sheet_list = ['CMD_DATABASES', 'Q_DATABASES', 'CHIT_DATABASES']
    cmd_list = []
    intent_list = []
    ans_dict_list = []
    # 遍历3个表
    for sheet in sheet_list:
        data = pd.read_excel('knowledge_base.xlsx', sheet_name=sheet, index_col=0)

        knowledge_base_dict = {"rasa_nlu_data": {}}
        knowledge_base_dict["rasa_nlu_data"]["common_examples"] = []
        knowledge_base_dict["rasa_nlu_data"]["entity_synonyms"] = []
        knowledge_base_dict["rasa_nlu_data"]["regex_features"] = []
        intent = ""
        # 遍历表里面的每条数据
        for line_num, line in enumerate(data.values):
            ask_list = []
            valid_sentence = line[1].split("|")
            valid_sentence = [data.strip() for data in valid_sentence if str(data).strip() != "nan"
                              and str(data).strip() != ""]

            if line[0].find("CMD:") != -1:
                intent = "intent_cmd_" + str(line_num) + "_bot"
                ask_list = line[0][4:].split("|")
                ask_list = [data.strip() for data in ask_list]
                cmd_list.append(" ".join(ask_list))
                ask_list.extend(valid_sentence)
                data_type = "test_cmd"
            elif line[0].find("Q:") != -1:
                intent = "intent_qa_" + str(line_num) + "_bot"
                ask_list.append(line[0][2:])
                ask_list.extend(valid_sentence)
                data_type = "question"
            elif line[0].find("CHIT:") != -1:
                # 注意这个地方与之前不同，因为希望闲聊意图可控，所以给其用名称表示
                intent = line[0][5:]
                ask_list = valid_sentence
                data_type = "chit"

            if str(line[2]).strip() == "nan" or str(data).strip() == "":  # 空数据
                ans_list = []
            else:
                ans_list = line[2].split("|")
                ans_list = [data.strip() for data in ans_list if str(data).strip() != "nan" and str(data).strip() != ""]

            for ask_sentence in ask_list:
                ans_dict = {"type": data_type, "intent": intent, "match_item": ask_sentence, "ans_list": ans_list,
                            "entity": "", "confidence": 0}
                knowledge_base_sub_dict = {"entities": [], "intent": intent,
                                           "answer_text": ans_dict, "text": ask_sentence}
                knowledge_base_dict["rasa_nlu_data"]["common_examples"].append(knowledge_base_sub_dict)

            intent_list.append(intent)
            # 注意这里只保存一个匹配项，因为后面的domain里面不需要做区分
            ans_dict["match_item"] = intent
            ans_dict_list.append(ans_dict)

        # 1生成NLU-JSON数据
        if sheet == "CMD_DATABASES":
            with open(os.path.dirname(__file__) + "/result/nlu_data/ergou_qa/ergou_cmd.json", "w", encoding="UTF-8") as f:
                json.dump(knowledge_base_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        elif sheet == "Q_DATABASES":
            with open(os.path.dirname(__file__) + "/result/nlu_data/ergou_qa/ergou_qa.json", "w", encoding="UTF-8") as f:
                json.dump(knowledge_base_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        elif sheet == "CHIT_DATABASES":
            with open(os.path.dirname(__file__) + "/result/nlu_data/ergou_chit/ergou_chit.json", "w", encoding="UTF-8") as f:
                json.dump(knowledge_base_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 加载系统数据库（boast+constellation_faq+ergou_kgqa+ergou_task+other_chit,目前只加载task）
    file_list = [
                 "/data_pre_process/result/nlu_data/ergou_task/rasa_dataset_training.json",
                 "/data_pre_process/result/nlu_data/boast/boast.json",
                 "/data_pre_process/result/nlu_data/constellation_faq/constellation_faq.json",
                 "/data_pre_process/result/nlu_data/ergou_kgqa/rasa_dataset_training.json",
                 "/data_pre_process/result/nlu_data/other_chit/other_chit.json",
                 ]
    for file in file_list:
        with open(os.path.dirname(os.path.dirname(__file__)) + file, "r") as f:
            data_dict = json.load(f)
            for smalltalk_sub_dict in data_dict["rasa_nlu_data"]["common_examples"]:
                if smalltalk_sub_dict["intent"] not in intent_list:
                    intent_list.append(smalltalk_sub_dict["intent"])
                # if smalltalk_sub_dict["answer_text"] not in ans_dict_list:
                #     ans_dict_list.append(smalltalk_sub_dict["answer_text"])

    # 2生成关键词词表
    domain_words_list = []
    last_domain_words_list = []
    last_valid_domain_words_list = []
    last_split_domain_words_list = []
    data = pd.read_excel('knowledge_base.xlsx', sheet_name="DOMAIN_WORDS")
    for line_num, line in enumerate(data.values):
        domain_words_list.append(line[0].strip())
    with open(os.path.dirname(__file__) + "/result/domain_words/domain_words.txt", "r", encoding="UTF-8") as f:
        for last_domain_word in f:
            # 代表是有效词，否则是分词机制
            if len(last_domain_word.split()) == 3:
                last_valid_domain_words_list.append(last_domain_word)
                last_domain_words_list.append(last_domain_word.split()[0])
            elif len(last_domain_word.split()) == 2:
                last_split_domain_words_list.append(last_domain_word)
    for domain_word in domain_words_list:
        if "".join(last_domain_words_list).find(domain_word) == -1:
            jieba.add_word(domain_word)
            word_seg = [seg for word, seg in jieba.posseg.cut(domain_word)]
            if len(word_seg) == 1:
                last_valid_domain_words_list.append(domain_word + " " + "400" + " " + word_seg[0] + "\n")
            else:
                last_valid_domain_words_list.append(domain_word + " " + "400" + " " + "n" + "\n")

    last_valid_domain_words_list.extend(last_split_domain_words_list)
    with open(os.path.dirname(__file__) + "/result/domain_words/domain_words.txt", "w", encoding="UTF-8") as f:
        f.write("".join(last_valid_domain_words_list))

    # 3生成命令词词表
    with open(os.path.dirname(__file__) + "/result/cmd_words/cmd_words.txt", "w", encoding="UTF-8") as f:
        f.write("\n".join(cmd_list))

    # 4生成Domain文件的意图intents+回复列表templates+执行单元actions
    ergou_domain_list = ["intents:"]
    for intent in intent_list:
        ergou_domain_list.append("  - " + intent)
    ergou_domain_list.append("")
    ergou_domain_list.append("templates:")
    # zyb-todo: ->这个地方到底是填写返回值还是返回json后面好好理下，现在是不是很完美
    for num, ans_dict in enumerate(ans_dict_list):
        ergou_domain_list.append("  utter_" + intent_list[num] + ":")

        # 一种情况：返回值
        # if len(ans_dict["ans_list"]) != 0:
        #     for answer in ans_dict["ans_list"]:
        #         ergou_domain_list.append("    - \"" + str(answer) + "\"")
        # else:
        #     ergou_domain_list.append("    - \"" + "默认回答为空，待添加" + "\"")
        # 二种情况：返回列表
        ergou_domain_list.append("    - \"" + str(ans_dict) + "\"")
    ergou_domain_list.append("")
    ergou_domain_list.append("actions:")
    for num, ans_dict in enumerate(ans_dict_list):
        ergou_domain_list.append("  - utter_" + intent_list[num])

    with open(os.path.dirname(__file__) + "/result/dialogue_data_config/dialogue_data_config.yml", "w", encoding="UTF-8") as f:
        f.write("\n".join(ergou_domain_list))

    # 5生成story
    ergou_story_list = []
    for num, ans_dict in enumerate(ans_dict_list):
        ergou_story_list.append("## " + intent_list[num])
        ergou_story_list.append("* " + intent_list[num])
        ergou_story_list.append("    - " + "utter_" + intent_list[num])
        ergou_story_list.append("")

    with open(os.path.dirname(__file__) + "/result/dialogue_data/dialogue_data.md", "w", encoding="UTF-8") as f:
        f.write("\n".join(ergou_story_list))

    # 6生成QA数据对
    generate_qa()


def generate_rough_chit():
    """
    处理原始闲聊数据
    :return:
    """
    chit_list = ["question" + '\t' + "answer\n"]
    with open(os.path.dirname(__file__) + "/other_chit/origin_qingyundata.csv", "r") as f:
        for line in f:
            data_list = line.split("|")
            if len(data_list) == 2:  # 不等于2的舍弃
                data_str = "".join(data_list[0].strip().split()) + '\t' + "".join(data_list[1].strip().split()) + '\n'
                chit_list.append(data_str)

    with open(os.path.dirname(__file__) + "/other_chit/rough_sample_docs", "w", encoding="UTF-8") as fopen:
        fopen.write("".join(chit_list))


def generate_qa():
    """
    生成QA查询数据，主要是other_chit+constellation_faq+boast
    这里生成可控的QA语料，可控的QA语料包括constellation_faq，boast,ergou_qa,ergou_kgqa,ergou_chit,task不包括other_chit
    目前先使用ergou_qa,ergou_chit,task三个语料库构建
    注意这里的json将会   完整的问答语句，回答不应为空，这里是最后一波操作。
    这里还要构建2份表格，一个喂给FAQ做问句检索，一个是根据索引检索查回答。
    :return:
    """
    qa_list = ["question" + '\t' + "answer\n"]

    file_list = ["/result/nlu_data/ergou_qa/ergou_qa.json",
                 "/result/nlu_data/ergou_qa/ergou_cmd.json",
                 "/result/nlu_data/ergou_chit/ergou_chit.json",
                 "/result/nlu_data/ergou_task/rasa_dataset_training.json"
                 ]
    index = 0
    for file in file_list:
        # other_chit加载，闲聊一对一全部加载
        # boast加载,夸夸一对多，这个暂时全部加载进去，后续再处理。
        #  constellation加载，星座一对一全部加载
        with open(os.path.dirname(__file__) + file, "r") as f:
            qa_dict = json.load(f)
            for qa_valid_dicts in qa_dict["rasa_nlu_data"]["common_examples"]:
                data_str = qa_valid_dicts["text"] + '\t' + str(qa_valid_dicts["answer_text"]) + '\n'
                qa_list.append(data_str)

    with open(os.path.dirname(__file__) + "/result/qq_data/sample_docs", "w", encoding="UTF-8") as fopen:
        fopen.write("".join(qa_list))


def generate_norough_chit():
    """
    生成QA查询数据，主要是other_chit+constellation_faq+boast
    :return:
    """
    qa_list = ["question" + '\t' + "answer\n"]

    # other_chit加载，闲聊一对一全部加载
    with open(os.path.dirname(__file__) + "/other_chit/other_chit.json", "r") as f:
        qa_dict = json.load(f)
        for qa_valid_dicts in qa_dict["rasa_nlu_data"]["common_examples"]:
            for qa_valid_dict in qa_valid_dicts["answer_text"]:
                data_str = qa_valid_dicts["text"] + '\t' + qa_valid_dict + '\n'
                qa_list.append(data_str)

    with open(os.path.dirname(__file__) + "/other_chit/rough1_sample_docs", "w", encoding="UTF-8") as fopen:
        fopen.write("".join(qa_list))


def filt_chit():
    """
    闲聊数据最杂，过滤掉闲聊数据中有关有效主题的数据
    :return:
    """
    bad_data_list = []
    # smalltalk_cn加载
    file_list = ["/constellation_faq/constellation_faq.json",
                 "/ergou_chit/ergou_chit.json",
                 "/ergou_kgqa/rasa_dataset_training.json",
                 "/ergou_task/rasa_dataset_training.json",
                 "/boast/boast.json"
                 ]
    for file in file_list:
        with open(os.path.dirname(__file__) + file, "r") as f:
            qa_dict = json.load(f)
            for qa_valid_dict in qa_dict["rasa_nlu_data"]["common_examples"]:
                try:
                    result = get_qa(qa_valid_dict["text"])
                    if len(result) > 0:
                        for data in result:
                            bad_data_list.append(data["question"] + "->" + qa_valid_dict["text"])
                except:
                    print("出错")
        logger.info("{}加载完毕".format(file))

    with open(os.path.dirname(__file__) + "/other_chit/bad_other_chit.txt", "w") as f:
        f.write("\n".join(bad_data_list))


def cut_chit():
    """
    # 闲聊数据剪切
    # other_chit加载，闲聊一对一全部加载
    :return:
    """
    with open(os.path.dirname(__file__) + "/other_chit/other_chit.json", "r") as f:
        qa_dict = json.load(f)
        qa_dict["rasa_nlu_data"]["common_examples"] = qa_dict["rasa_nlu_data"]["common_examples"][0:50000]
    with open(os.path.dirname(__file__) + "/other_chit/cut_other_chit.json", "w") as f1:
        json.dump(qa_dict, f1, ensure_ascii=False, indent=2, sort_keys=True)


def extract_features_to_rasa_devide(file_path, ratio=0.8, min_class_num=20):
    """
    对文件夹的意图数据进行分割，默认2-8分,生成nlu_data_new,nlu_data_test,nlu_data_train里面的数据
    :param min_class_num: 每个类别最小个数
    :param ratio: 分割比例
    :param file_path: 待分割文件
    :return:
    """
    with open(file_path, 'r', encoding="utf-8") as f:
        rasa_intent_dict = json.load(f)

    # 存储每个子类的个数
    rasa_by_sub_intent_dict = {}
    for num, rasa_sub_intent_dict in enumerate(rasa_intent_dict["rasa_nlu_data"]["common_examples"]):
        if rasa_sub_intent_dict['intent'] in rasa_by_sub_intent_dict.keys():
            rasa_by_sub_intent_dict[rasa_sub_intent_dict['intent']].append(rasa_sub_intent_dict)
        else:
            rasa_by_sub_intent_dict[rasa_sub_intent_dict['intent']] = [rasa_sub_intent_dict]

    #  按领域分类数据集
    # 注意这个地方要用深copy
    from copy import deepcopy
    rasa_new_intent_dict = deepcopy(rasa_intent_dict)
    rasa_new_by_sub_intent_dict = deepcopy(rasa_by_sub_intent_dict)
    for intent, rasa_by_sub_intent_list in rasa_by_sub_intent_dict.items():
        length = len(rasa_by_sub_intent_list)
        if length < min_class_num:  # 如果类别数量过少，这里进行过采样操作
            for _ in range(math.ceil(min_class_num/length)-1):
                rasa_new_by_sub_intent_dict[intent].extend(rasa_by_sub_intent_dict[intent])

            for num, rasa_sub_intent_dict in enumerate(rasa_intent_dict["rasa_nlu_data"]["common_examples"]):
                if rasa_sub_intent_dict['intent'] == intent:  # 先删除所有这个分类
                    rasa_new_intent_dict["rasa_nlu_data"]["common_examples"].remove(rasa_sub_intent_dict)
            rasa_new_intent_dict["rasa_nlu_data"]["common_examples"].extend(rasa_new_by_sub_intent_dict[intent])  # 然后再一次性添加

    # 训练集和数据集分割
    for intent, rasa_sub_intent_list in rasa_new_by_sub_intent_dict.items():
        random.shuffle(rasa_new_by_sub_intent_dict[intent])
    rasa_train_intent_dict = deepcopy(rasa_new_intent_dict)
    rasa_train_intent_dict["rasa_nlu_data"]["common_examples"].clear()
    rasa_test_intent_dict = deepcopy(rasa_train_intent_dict)
    for intent, rasa_new_by_sub_intent_list in rasa_new_by_sub_intent_dict.items():
        length = int(len(rasa_new_by_sub_intent_list)*ratio)
        rasa_train_intent_dict["rasa_nlu_data"]["common_examples"].extend(rasa_new_by_sub_intent_list[:length])
        rasa_test_intent_dict["rasa_nlu_data"]["common_examples"].extend(rasa_new_by_sub_intent_list[length:])

    # 对所有领域进行存储
    (_, file_name) = os.path.split(os.path.dirname(file_path))
    # new_file_name = "new_" + file_name
    new_file_path = file_path.replace("nlu_data", "nlu_data_new")
    test_file_path = file_path.replace("nlu_data", "nlu_data_test")
    train_file_path = file_path.replace("nlu_data", "nlu_data_train")
    with open(new_file_path, "w", encoding="UTF-8") as f:
        json.dump(rasa_new_intent_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    if file_name == "ergou_task":  # 考虑后面还要再次使用这组数据做子意图，故单独把它分出来
        with open(os.path.join(os.path.dirname(test_file_path), "rasa_dataset_testing.json"), "w", encoding="UTF-8") as f:
            json.dump(rasa_test_intent_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(os.path.join(os.path.dirname(train_file_path), "rasa_dataset_training.json"), "w", encoding="UTF-8") as f:
            json.dump(rasa_train_intent_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        with open(test_file_path, "w", encoding="UTF-8") as f:
            json.dump(rasa_test_intent_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(train_file_path, "w", encoding="UTF-8") as f:
            json.dump(rasa_train_intent_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def generate_domains_data():
    """
    根据子领域数据生成领域数据
    先对子领域进行分割，然后将分割的train和test分别假如到相应的领域
    :return:
    """
    """
    生成rasa支持的数据格式
    :param file_path:
    :return:
    """

    # 分割数据
    for root, dir_list, file_list in os.walk("result/nlu_data"):
        if len(file_list) != 0:
            for file in file_list:
                extract_features_to_rasa_devide(os.path.join(root, file), 0.8)

    # 存储domain训练集
    rasa_domain_dict = {"rasa_nlu_data": {}}
    rasa_domain_dict["rasa_nlu_data"]["common_examples"] = []
    rasa_domain_dict["rasa_nlu_data"]["entity_synonyms"] = []
    rasa_domain_dict["rasa_nlu_data"]["regex_features"] = []
    for root, dir_list, file_list in os.walk("result/nlu_data_train"):
        if len(file_list) != 0:
            for file in file_list:
                with open(os.path.join(root, file), 'r', encoding="utf-8") as f:
                    data_dict = json.load(f)
                for num, rasa_sub_domain_dict in enumerate(data_dict["rasa_nlu_data"]["common_examples"]):
                    (_, rasa_sub_domain_dict['intent']) = os.path.split(root)  # 此处后面需调试
                    rasa_domain_dict["rasa_nlu_data"]["common_examples"].append(rasa_sub_domain_dict)
    random.shuffle(rasa_domain_dict["rasa_nlu_data"]["common_examples"])
    with open("./result/domain_data/rasa_dataset_training.json", "w", encoding="UTF-8") as f:
        json.dump(rasa_domain_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 存储domain测试集
    rasa_domain_dict = {"rasa_nlu_data": {}}
    rasa_domain_dict["rasa_nlu_data"]["common_examples"] = []
    rasa_domain_dict["rasa_nlu_data"]["entity_synonyms"] = []
    rasa_domain_dict["rasa_nlu_data"]["regex_features"] = []
    for root, dir_list, file_list in os.walk("result/nlu_data_test"):
        if len(file_list) != 0:
            for file in file_list:
                with open(os.path.join(root, file), 'r', encoding="utf-8") as f:
                    data_dict = json.load(f)
                for num, rasa_sub_domain_dict in enumerate(data_dict["rasa_nlu_data"]["common_examples"]):
                    (_, rasa_sub_domain_dict['intent']) = os.path.split(root)  # 此处后面需调试
                    rasa_domain_dict["rasa_nlu_data"]["common_examples"].append(rasa_sub_domain_dict)
    random.shuffle(rasa_domain_dict["rasa_nlu_data"]["common_examples"])
    with open("./result/domain_data/rasa_dataset_testing.json", "w", encoding="UTF-8") as f:
        json.dump(rasa_domain_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def generate_typical_data(path):
    """
    生成广告数据或者商品标题数据
    :param path:
    :param intent: ad或者item
    :return:
    """
    (_, name) = os.path.split(path)  # 取文件名全名
    (newpath, _) = os.path.splitext(path)  # 取路径名
    (_, newpath) = os.path.split(newpath)  # 取文件名的前缀
    intent = newpath  # 将前缀设置成意图
    rasa_dict = {"rasa_nlu_data": {}}
    rasa_dict["rasa_nlu_data"]["common_examples"] = []
    rasa_dict["rasa_nlu_data"]["entity_synonyms"] = []
    rasa_dict["rasa_nlu_data"]["regex_features"] = []
    with open(path, "r", encoding="UTF-8") as f:
        datas_dict = json.load(f)
    for data_values in datas_dict.values():
        for key in data_values.keys():
            rasa_sub_dict = {"entities": [], "intent": intent, "answer_text": {}, "text": key}
            rasa_dict["rasa_nlu_data"]["common_examples"].append(rasa_sub_dict)
    with open(os.path.join("./result/nlu_data", newpath, name), "w", encoding="UTF-8") as f:
        json.dump(rasa_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    # generate_typical_data("./user_msg_analysis/pre_process_online_log/ad_data.json")
    # generate_typical_data("./user_msg_analysis/pre_process_online_log/item_data.json")
    # 生成domain数据
    generate_domains_data()
    # chit优先处理，先把服务器跑起来
    # generate_rough_chit()

    # constellation boast smalltalk 分别生成
    # process_constellation()
    # process_boast()
    # pre_process_knowledge_base()
    # process_smalltalk()
    # process_knowledge_base()
    # 先过滤掉根据我们以上自己的数据重复的chit，注意过滤的时候要把anyQ的阈值调小，把列表调大，这样可以尽可能的过滤掉
    # 大多数重复的，我的是设置是example/conf/rank.conf里面的top_result设置为20，阈值设置为0.7
    # filt_chit()
    # 然后再由rough_sample_docs生成other_chit.json
    # process_chit()
    # chit数据过大，先裁剪使用
    # cut_chit()
    # 将生成的文件用作服务器可起到反复提纯的作用，注意更改名字
    # generate_norough_chit()

    # 最终生成qa的语料(constellation boast chit)
    # generate_qa()
