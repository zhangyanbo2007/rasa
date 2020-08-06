#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：Zhang Yanbo time:2019/5/15

import requests
import json
import re
import hashlib
import numpy as np
from scipy.spatial.distance import cdist
import shutil
import os
import random
import jieba
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer, HashingVectorizer
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, MiniBatchKMeans
import gensim
from gensim.models import Word2Vec
from sklearn.preprocessing import scale
import multiprocessing
import xlsxwriter
from pypinyin import pinyin, lazy_pinyin, Style
# # TEST
# pinyin('中心')
# pinyin("提现。", errors="ignore",  style=Style.NORMAL) == pinyin("提钱。", errors="ignore",  style=Style.NORMAL)
SSE = []

# TODO:后续用HNLP, FNLP里面的聚类再试下

# 定义分词函数preprocess_text
# 参数content_lines即为上面转换的list
# 参数sentences是定义的空list，用来储存分词后的数据


def process_origin_data():
    """
    原始数据预处理
    :return:
    """
    # 以下仅处理一次
    with open(os.path.join(os.path.dirname(__file__), "online_log/origin_data_201905.log"), 'r') as f:
        data_list = []
        for n, line in enumerate(f.readlines()):
            pattern = re.compile(r"^.*backendTextMessage wxid.*$")  # zyb注释：这是一个很好的正则实例,末尾不能正则匹配待研究
            pattern_data = pattern.findall(line)
            if len(pattern_data) > 0:  # 存在有效数据
                data_list.append(pattern_data[0])
    with open(os.path.join(os.path.dirname(__file__), "online_log/data_201905.log"), 'w') as f:
        f.write("\n".join(data_list))


def extraction_valid_data():
    """
    数据预处理-提取有效数据
    数据挖掘3级模式：
    1首先基于关键词来查找用户咨询的有效问句(排除纯关键词后，可再次做个聚类分析，也可人工直接筛选)
    2其次按高频信息查找用户咨询的无效问句（比较简单的方式，但容易发现假数据）
    3最后按聚类信息查找用户咨询的有效问句(聚类完成后要能人工挖掘用户的新的问法)
    此外前期由于用户数量少，尽量人工排查那些虽然低频但是有效的用户问句，另外可根据用户的问法做文本扩充
    注意由于关键词涉及命令，其本身比较高频，容易输入错误，基于关键词的错别字纠错至关重要，可通过拼音进行纠错
    另外最好是基于词的关键词纠错，基于字的关键词纠错代价较高，如果是字出错，或者是打字输入错误，直接在相似
    语句或者相应的命令列表添加即可，不可走拼音纠错流程。
    现发现的错别字列表:
    提、现,体现,提前,提现申请,提线->提现
    拥金->佣金
    帮肋,幫助,帮主,帮住->帮助
    人物->任务
    反现->返现
    二狗优惠圈->优惠券
    怎么反->怎么返
    :return:
    """
    cmd_keyword_list = [
        ["提现", "提款", "领奖", "返现", "返利", "套现", "提钱", "提前"],
        ["红包"],
        ["绑定"],
        ["海报", "分享", "代理", "分销", "下级", "推广", "推荐", "拉新", "拉人", "邀请"],
        ["帮助", "介绍", "说明", "功能", "教程", "视频", "帮忙", "帮肋"],
        ["个人信息", "个人中心", "查询", "余额", "佣金", "查看"],
        ["任务"],
        ["优惠券", "优惠", "领卷", "领券"],
        ["丢单"],  # 询问命令
        ["赚钱"],  # 无效命令
        ["人工", "客服"],  # 无效命令
        ["签到"],  # 无效命令
        ["下载"],  # 无效命令
        ["结算"],  # 无效命令
        ["确认收货"],  # 无效命令
        ["订单", "订单号", "详细订单"],  # 无效命令
        ["二狗", "狗", "2狗", "买狗"],  # 关联词
    ]

    for root, dir, files in os.walk("online_log", topdown=False):
        for file in files:
            if file[0:4] == "kg_data":
                with open(os.path.join(root, file), 'r', encoding="utf-8") as f:
                    data_dict = {}
                    ad_data_dict = {}
                    item_data_dict = {}
                    lastPage = None

                    for n, line in enumerate(f.readlines()):
                        m = line.split()
                        #  排除指定字符串，这个方法我一定要掌握
                        # pattern = re.compile(r'^(?!room).*$')
                        #  zyb注释：这是一个很好的正则实例，排除包含群聊的条目
                        # pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(\b(?!chatroom).*\b)")
                        # #zyb注释：这是一个很好的正则实例，排除包含群聊的条目
                        # pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(.(?=chatroom)*?)
                        # (\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)")

                        # zyb注释：这是一个很好的正则实例,末尾不能正则匹配待研究
                        pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)"
                                             r"(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)"
                                             r"(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)")

                        pattern_data = pattern.findall(line)
                        if len(pattern_data) > 0:  # 存在有效数据
                            msg_id = pattern_data[0][5]
                            msg_type = pattern_data[0][7]
                            msg_value = pattern_data[0][9]
                            if msg_type == "1" and \
                                    re.findall(r"【.*", msg_value) == [] and re.findall(r"\d{18}", msg_value) == [] and \
                                    re.findall(r"￥.*￥", msg_value) == [] and re.findall(r"€.*€", msg_value) == [] and \
                                    re.findall(r"可以开始聊天+?", msg_value) == [] and \
                                    re.findall(r"http+?", msg_value) == []:  # 代表有效文本,且不是淘宝文本

                                # 剔除广告
                                if (re.findall(r".*(?:为你推荐|请问您需要了解吗|办卡套现|本店专业|亲，|谢谢|亲爱的，|不闲聊|在家创业|"
                                               r"为您推荐|你好|包邮|早安|不好意思|点击|新老客户|免费|打扰了|上午好|"
                                               r"下午好|您好|亲们|在吗|一键转发|在抖音|朋友圈|"
                                               r"复制此条|复制这条).*", msg_value) != [] and len(msg_value) >= 20) \
                                        or re.findall(r".*(?:朋友圈.*点个赞|转发.*朋友圈|朋友圈第一条|第一条朋友圈|"
                                                      r"你好，欢迎关注|您好，欢迎关注|在抖音|旺季来了|私信我|感谢关注).*", msg_value) != []:

                                    if msg_id not in ad_data_dict:
                                        ad_data_dict[msg_id] = {msg_value: 1}
                                    else:
                                        if msg_value not in ad_data_dict[msg_id]:
                                            ad_data_dict[msg_id][msg_value] = 1
                                        else:
                                            ad_data_dict[msg_id][msg_value] += 1

                                # 存储商品链接信息（TODO:闲聊部分数据在里面暂时没法剔除，后续可采用分类模型非商品信息）
                                elif len(msg_value) >= 20:
                                    if msg_id not in item_data_dict:
                                        item_data_dict[msg_id] = {msg_value: 1}
                                    else:
                                        if msg_value not in item_data_dict[msg_id]:
                                            item_data_dict[msg_id][msg_value] = 1
                                        else:
                                            item_data_dict[msg_id][msg_value] += 1

                                # 存储用户有效咨询
                                else:
                                    # 总的文本分布数据表格
                                    if msg_id not in data_dict:
                                        data_dict[msg_id] = {msg_value: 1}
                                    else:
                                        if msg_value not in data_dict[msg_id]:
                                            data_dict[msg_id][msg_value] = 1
                                        else:
                                            data_dict[msg_id][msg_value] += 1

    # 存储用户有效咨询
    with open(os.path.join(os.path.dirname(__file__), "pre_process_online_log/all_valid_data.json"), 'w', encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 存储广告数据
    with open(os.path.join(os.path.dirname(__file__), "pre_process_online_log/ad_data.json"), 'w', encoding="utf-8") as f:
        json.dump(ad_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 存储商品链接信息
    with open(os.path.join(os.path.dirname(__file__), "pre_process_online_log/item_data.json"), 'w', encoding="utf-8") as f:
        json.dump(item_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 模糊匹配：命令筛选
    by_keyword_cmd_data_dict = {}
    by_user_cmd_data_dict = {}
    for msg_id in data_dict.keys():  # 按微信ID查找语句
        for msg_value in data_dict[msg_id].keys():  # 按微信ID查找语句
            for cmd_keyword_sub_list in cmd_keyword_list:  # 按关键词主题提取
                for cmd_keyword in cmd_keyword_sub_list:
                    if msg_value.find(cmd_keyword) != -1 \
                            or (pinyin(msg_value, errors="ignore",  style=Style.NORMAL)
                                == pinyin(cmd_keyword, errors="ignore", style=Style.NORMAL)):  # 模糊匹配上
                        by_user_cmd_data_dict.setdefault(msg_id, {})  # 添加键值，注意添加类型
                        by_user_cmd_data_dict[msg_id].setdefault(msg_value, int)  # 添加子键值，注意添加类型
                        by_user_cmd_data_dict[msg_id][msg_value] = data_dict[msg_id][msg_value]  # 检索到的放到dict

                        # 添加关键词键值，注意添加类型,注意这个地方省了频率，后续还是要加上分析，频率很重要的一个指标
                        by_keyword_cmd_data_dict.setdefault(cmd_keyword_sub_list[0], [])
                        if msg_value not in by_keyword_cmd_data_dict[cmd_keyword_sub_list[0]]:
                            by_keyword_cmd_data_dict[cmd_keyword_sub_list[0]].append(msg_value)
                        break

                # 这个地方处理的不是很好，不知道有没有更好的方式
                if msg_value.find(cmd_keyword) != -1 \
                    or (pinyin(msg_value, errors="ignore", style=Style.NORMAL)
                        == pinyin(cmd_keyword, errors="ignore", style=Style.NORMAL)):  # 模糊匹配上
                    break

    # 从原始数据中去除与关键词相关的数据
    for msg_id in by_user_cmd_data_dict.keys():
        for msg_value in by_user_cmd_data_dict[msg_id].keys():
            for cmd_keyword_sub_list in cmd_keyword_list:  # 按关键词主题提取
                for cmd_keyword in cmd_keyword_sub_list:
                    if msg_value.find(cmd_keyword) != -1 \
                       or (pinyin(msg_value, errors="ignore", style=Style.NORMAL)
                           == pinyin(cmd_keyword, errors="ignore", style=Style.NORMAL)):  # 模糊匹配上
                        del data_dict[msg_id][msg_value]
                        break

                # 这个地方处理的不是很好，不知道有没有更好的方式
                if msg_value.find(cmd_keyword) != -1 \
                   or (pinyin(msg_value, errors="ignore", style=Style.NORMAL)
                       == pinyin(cmd_keyword, errors="ignore", style=Style.NORMAL)):  # 模糊匹配上
                    break
    # 按用户存储其他数据
    with open(os.path.join(os.path.dirname(__file__),
                           "pre_process_online_log/by_user_other_valid_data.json"), 'w', encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 按用户存储模糊+精准命令命令数据
    with open(os.path.join(os.path.dirname(__file__),
                           "pre_process_online_log/by_user_keyword_valid_data.json"), 'w', encoding="utf-8") as f:
        json.dump(by_user_cmd_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 按命令存储模糊+精准命令数据
    with open(os.path.join(os.path.dirname(__file__),
                           "pre_process_online_log/by_keyword_valid_data.json"), 'w', encoding="utf-8") as f:
        json.dump(by_keyword_cmd_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 从关键词相关数据中去除关键词数据(这里省略了错别字的噻选，不多就人工筛吧)
    for cmd_keyword_sub_list in cmd_keyword_list:  # 按关键词主题提取
        for cmd_keyword in cmd_keyword_sub_list:
            if cmd_keyword in by_keyword_cmd_data_dict[cmd_keyword_sub_list[0]]:
                by_keyword_cmd_data_dict[cmd_keyword_sub_list[0]].remove(cmd_keyword)

    # 按命令存储模糊命令数据
    with open(os.path.join(os.path.dirname(__file__),
                           "pre_process_online_log/by_keyword_ext_valid_data.json"), 'w', encoding="utf-8") as f:
        json.dump(by_keyword_cmd_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    # 将命令存储模糊命令数据生成excel文件
    workbook = xlsxwriter.Workbook(os.path.join(os.path.dirname(__file__),
                                                "pre_process_online_log/by_keyword_ext_valid_data.xlsx"))
    worksheet = workbook.add_worksheet()
    # 设定格式，等号左边格式名称自定义，字典中格式为指定选项
    # bold：加粗，num_format:数字格式
    bold_format = workbook.add_format({'bold': True})
    money_format = workbook.add_format({'num_format': '$#,##0'})
    date_format = workbook.add_format({'num_format': 'mmmm d yyyy'})

    # 将二行二列设置宽度为15(从0开始)
    worksheet.set_column(0, 100, 20)

    # 用符号标记位置，例如：A列1行
    for sentences_id, sentences in enumerate(by_keyword_cmd_data_dict):
        worksheet.write('A'+str(sentences_id+1), sentences, bold_format)  # 写行头
        # 写相似值
        for i, sentence in enumerate(by_keyword_cmd_data_dict[sentences]):
            # 使用write_string方法，指定数据格式写入数据
            worksheet.write_string(sentences_id, i+1, sentence)
    workbook.close()


def load_log_data():
    """
    加载数据
    :return:
    """
    data_list = []
    data_statistics_dict = {}
    stopwords = pd.read_csv(os.path.join(os.path.dirname(__file__), "domain_words/stop_words.txt"),
                            index_col=False, quoting=3,
                            sep="\t", names=['stop_words'], encoding="GBK")
    stopwords = stopwords['stop_words'].values
    with open(os.path.join(os.path.dirname(__file__),
                           "pre_process_online_log/by_user_other_valid_data.json"), 'r') as f:
        by_user_other_valid_data = json.load(f)
        for msg_id in by_user_other_valid_data.keys():  # 用户ID
            for msg_value in by_user_other_valid_data[msg_id].keys():  # 消息数据
                if msg_value not in data_list:
                    data_list.append(msg_value)
                    data_statistics_dict[msg_value] = {"0": by_user_other_valid_data[msg_id][msg_value], "1": 1}  # 按总数记
                else:
                    data_statistics_dict[msg_value]["0"] += by_user_other_valid_data[msg_id][msg_value]  # 按总数记
                    data_statistics_dict[msg_value]["1"] += 1  # 一个用户记一次

        # 求频率
        sum_0 = 0
        sum_1 = 0
        for msg_value in data_statistics_dict:
            sum_0 += data_statistics_dict[msg_value]["0"]
            sum_1 += data_statistics_dict[msg_value]["1"]
        for msg_value in data_statistics_dict:
            data_statistics_dict[msg_value]["0"] = data_statistics_dict[msg_value]["0"]/sum_0
            data_statistics_dict[msg_value]["1"] = data_statistics_dict[msg_value]["1"]/sum_1

        # 分词
        sentences = []
        origin_sentences = []

        random.shuffle(data_list)  # 将数据打散
        for sentence in data_list:
            try:
                segs = jieba.lcut(sentence)
                # segs = [v for v in segs if not str(v).isdigit()]  # 去数字
                segs = list(filter(lambda x: x.strip(), segs))  # 去左右空格
                # segs = list(filter(lambda x: len(x) > 1, segs))  # 长度为1的字符
                segs = list(filter(lambda x: x not in stopwords, segs))  # 去掉停用词
                target_sentence = " ".join(segs)
                data_statistics_dict[sentence]["2"] = target_sentence  # 增加分词内容
                if target_sentence != "":
                        # and target_sentence != "查询" and target_sentence != "佣金" and
                        # target_sentence != "提现" \
                        # and target_sentence != "丢单" and target_sentence != "任务" and
                        # target_sentence != "代理": #分词后空的数据清掉
                    sentences.append(target_sentence)  # 保存分词后的数据
                    origin_sentences.append(sentence)  # 保存分词前的数据，为什么要保存，因为存在分词前句子不一样，但是分词后一样的情况
            except Exception:
                print(sentence)
                continue
        # random.shuffle(sentences)  # 打散语句

        with open(os.path.join(os.path.dirname(__file__), "pre_process_online_log/pre_statistics.json"), 'w') as f:
            json.dump(data_statistics_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

        return data_statistics_dict, origin_sentences, sentences


def transform(sentences):
    """
    完成TFIDF词向量表征处理
    :param sentences:
    :return:
    """
    # 测试DEMO
    # sentences = ["你好", "你好 啊", "你 是 谁", "你 来自 哪里", "你好 吗", "我 想 吃饭", "我 想 睡觉"]

    # 两种方式
    # 第一种直接TFIDF
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5, token_pattern=r"(?u)\b\w+\b")
    tfidf = vectorizer.fit_transform(sentences)
    word = vectorizer.get_feature_names()
    # print(word)
    # print(vectorizer.vocabulary_)
    # print(tfidf.toarray())

    # 第二种先CountVectorizer转换为词频矩阵，
    # 后TfidfTransformer统计CountVectorizer中每个词语的tf-idf权值
    # new_vectorizer = CountVectorizer(max_df=0.5, token_pattern=r"(?u)\b\w+\b")
    # count = new_vectorizer.fit_transform(sentences)
    # word = new_vectorizer.get_feature_names()
    # print(word)
    # print(new_vectorizer.vocabulary_)
    # print(count.toarray())
    #
    # transformer = TfidfTransformer()
    # tfidf = transformer.fit_transform(count)
    # print(tfidf.toarray())

    # 将tf-idf矩阵抽取出来，元素w[i][j]表示j词在i类文本中的tf-idf权重
    weight = tfidf.toarray()
    # 查看特征词的长度
    print('Features length: ' + str(len(word)))
    return weight


def cluster_k_adjust(weight):
    """
    K参数调试:先确定K值
    :param weight:
    :return:
    """
    for num_clusters in range(100, 200):
        clf = KMeans(n_clusters=num_clusters, max_iter=10000, tol=1e-6, init='k-means++')
        pca = PCA(n_components=50)  # 降维后再训练
        TnewData = pca.fit_transform(weight)  # 降维后再Kmeans训练
        # TnewData = weight
        s = clf.fit(TnewData)
        SSE.append(clf.inertia_)
        # SSE.append(sum(np.min(cdist(images_features, km_cluster.cluster_centers_, 'euclidean'), axis=1))
        #            / images_features.shape[0])
    x = range(100, 200)
    # SSE = range(1, 9)
    plt.xlabel('k')
    plt.ylabel('SSE')
    plt.plot(x, SSE, 'o-')

    plt.savefig(os.path.join(os.path.dirname(__file__), "result/k_picture.png"))
    plt.show()


def plot_cluster(clf, result, new_data, num_class):
    plt.figure(2)
    Lab = [[] for i in range(num_class)]
    index = 0
    for labi in result:
        Lab[labi].append(index)
        index += 1
    color = ['ob', 'om', 'og', 'oy', 'or', 'ok', 'oc', 'ow',
             'vb', 'vm', 'vg', 'vy', 'vr', 'vk', 'vc', 'vw',
             'ob', 'om', 'og', 'oy', 'or', 'ok', 'oc', 'ow',
             '^b', '^m', '^g', '^y', '^r', '^k', '^c', '^w',
             'sb', 'sm', 'sg', 'sy', 'sr', 'sk', 'sc', 'sw',
             'pb', 'pm', 'pg', 'py', 'pr', 'pk', 'pc', 'pw'
             ]*10
    for i in range(num_class):
        x1 = []
        y1 = []
        for ind1 in new_data[Lab[i]]:
            # print ind1
            try:
                # if -0.05 < ind1[0] < 0 and -0.05 < ind1[1] < 0:
                y1.append(ind1[1])
                x1.append(ind1[0])
            except:
                pass
            plt.plot(x1, y1, color[i])

    # #绘制初始中心点
    # x1 = []
    # y1 = []
    # for ind1 in clf.cluster_centers_:
    #     try:
    #         y1.append(ind1[1])
    #         x1.append(ind1[0])
    #     except:
    #         pass
    # plt.plot(x1, y1, "rv") #绘制中心
    plt.savefig(os.path.join(os.path.dirname(__file__), "result/kmeans.png"))
    plt.show()


def cluster_process(weight, num_class):
    """
    聚类处理
    :param weight:
    :return:
    """
    # Kmeans聚类
    clf = KMeans(n_clusters=num_class, max_iter=10000, init="k-means++", tol=1e-6)  # 这里也可以选择随机初始化init="random"
    pca = PCA(n_components=50)  # 降维后再训练
    tnew_data = pca.fit_transform(weight)  # 降维后再Kmeans训练
    # TnewData = weight
    s = clf.fit(tnew_data)
    result = list(clf.predict(tnew_data))
    # result = list(s.labels_) #结果同上
    # 方式1：直接PCA,将数据降维进行可视化显示
    pca = PCA(n_components=2)  # 输出两维
    new_data = pca.fit_transform(weight)  # 载入N维

    # 方式2：先PCA后TSNE,将数据降维进行可视化显示
    # from sklearn.manifold import TSNE
    # newData = PCA(n_components=4).fit_transform(weight)  # 载入N维
    # newData = TSNE(2).fit_transform(newData) #二维用于可视化

    plot_cluster(clf, result, new_data, num_class)
    return result

# 生成excel文件
def save_excel(rec_data):
    """
    将数据保存到excel
    :param rec_data:
    :return:
    """
    workbook = xlsxwriter.Workbook(os.path.join(os.path.dirname(__file__), "result/rec_data.xlsx"))
    worksheet = workbook.add_worksheet()
    # 设定格式，等号左边格式名称自定义，字典中格式为指定选项
    # bold：加粗，num_format:数字格式
    bold_format = workbook.add_format({'bold': True})
    money_format = workbook.add_format({'num_format': '$#,##0'})
    date_format = workbook.add_format({'num_format': 'mmmm d yyyy'})

    # 将二行二列设置宽度为15(从0开始)
    worksheet.set_column(0, 100, 20)

    # 用符号标记位置，例如：A列1行
    for sentences_id, sentences in enumerate(rec_data):
        worksheet.write('A'+str(sentences_id+1), sentences["norm"]["norm_value"], bold_format) #写行头
        #写相似值
        for i, sentence in enumerate(sentences["kg_data"]):
            # 使用write_string方法，指定数据格式写入数据
            worksheet.write_string(sentences_id, i+1, sentence)
    workbook.close()


def cluster_generate_data(sentences, result, num_class):
    """
    将聚类的数据进行存储
    :param sentences:
    :param result:
    :param num_class:
    :return:
    """
    keep_out = {}
    for i in range(num_class):
        keep_out[i] = {"norm": {"norm_value": {}, "norm_probability": {}}, "kg_data": {}}
    for i, sentence in enumerate(sentences):
        keep_out[int(result[i])]["kg_data"][origin_sentences[i]] = {"0": data_statistics_dict[origin_sentences[i]]["0"],
                                                                 "1": data_statistics_dict[origin_sentences[i]]["1"]}

    sum_0 = []
    sum_1 = []
    max_i = []
    max_value = []
    for i, keep_out_value in enumerate(keep_out):
        sum_0.append(0)
        sum_1.append(0)
        max_i.append(0)
        max_value.append(0)
        for sim_sentence in keep_out[keep_out_value]["kg_data"]:
            sum_0[i] += keep_out[keep_out_value]["kg_data"][sim_sentence]["0"]
            sum_1[i] += keep_out[keep_out_value]["kg_data"][sim_sentence]["1"]
            if max_i[i] < keep_out[keep_out_value]["kg_data"][sim_sentence]["1"]:  #暂时按个体的最大值计数
                max_i[i] = keep_out[keep_out_value]["kg_data"][sim_sentence]["1"]
                max_value[i] = sim_sentence

        keep_out[keep_out_value]["norm"]["norm_value"] = max_value[i]
        keep_out[keep_out_value]["norm"]["norm_probability"] = {"0": sum_0[i], "1": sum_1[i]}

    view_temp = sorted(keep_out.items(), key=lambda d: d[1]["norm"]["norm_probability"]["1"], reverse=True)  #暂时按个体的最大值计数
    view_out = [sort_sentence for _, sort_sentence in view_temp]
    save_excel(view_out)


if __name__ == "__main__":
    # process_origin_data()
    extraction_valid_data()

    # data_statistics_dict, origin_sentences, sentences = load_log_data()
    # weight = transform(sentences)
    # # cluster_k_adjust(weight)
    # result = cluster_process(weight, 200)
    # cluster_generate_data(sentences, result, 200)
