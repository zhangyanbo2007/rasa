import requests
import json
import re
import hashlib
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist
import shutil
import matplotlib.pyplot as plt
import os
SSE = []

import random
import jieba
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import gensim
from gensim.models import Word2Vec
from sklearn.preprocessing import scale
import multiprocessing

import xlsxwriter

# TODO:后续用HNLP, FNLP里面的聚类再试下

# 定义分词函数preprocess_text
# 参数content_lines即为上面转换的list
# 参数sentences是定义的空list，用来储存分词后的数据
def load_log_data():
    with open(os.path.join(os.path.dirname(__file__), "data_201903.log"), 'r') as f:
        data_dict = {}
        lastPage = None

        for n, line in enumerate(f.readlines()):
            m = line.split()
            # pattern = re.compile(r'^(?!room).*$') #排除指定字符串，这个方法我一定要掌握
            # pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(\b(?!chatroom).*\b)") #zyb注释：这是一个很好的正则实例，排除包含群聊的条目
            # pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(.(?=chatroom)*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)") #zyb注释：这是一个很好的正则实例，排除包含群聊的条目
            pattern = re.compile(r"notify:(\s+)&{(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)(.*?)(\s+)") #zyb注释：这是一个很好的正则实例,末尾不能正则匹配待研究
            pattern_data = pattern.findall(line)
            if len(pattern_data) > 0: #存在有效数据
                msg_id = pattern_data[0][5]
                msg_type = pattern_data[0][7]
                msg_value = pattern_data[0][9]
                if msg_type == "1" and re.findall(r"【.*", msg_value) == [] and re.findall(r"\d{18}", msg_value) == [] and \
                        re.findall(r"￥.*￥", msg_value) == [] and re.findall(r"€.*€", msg_value) == [] and \
                        re.findall(r"可以开始聊天+?", msg_value) == [] and re.findall(r"http+?", msg_value) == []: #代表有效文本,且不是淘宝文本
                    #总的文本分布数据表格
                    if msg_id not in data_dict:
                        data_dict[msg_id] = {msg_value: 1}
                    else:
                        if msg_value not in data_dict[msg_id]:
                            data_dict[msg_id][msg_value] = 1
                        else:
                            data_dict[msg_id][msg_value] += 1
                    #局部的文本分布数据表格
            #     if '< title >' in line and '< / title >' in line:
            #         if lastPage:
            #             dataset.append(lastPage)
            #         lastPage = line
            #     else:
            #         lastPage += line
            # if lastPage:
            #     dataset.append(lastPage)
            # f.close()
        data_list = []
        data_statistics_dict = {}
        for msg_id in data_dict.keys(): #用户ID
            for msg_value in data_dict[msg_id].keys(): #消息数据
                if msg_value not in data_list:
                    data_list.append(msg_value)
                    data_statistics_dict[msg_value] = {"0": data_dict[msg_id][msg_value], "1": 1} #按总数记
                else:
                    data_statistics_dict[msg_value]["0"] += data_dict[msg_id][msg_value] #按总数记
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

        random.shuffle(data_list) #将数据打散
        for sentence in data_list:
            try:
                segs = jieba.lcut(sentence)
                segs = [v for v in segs if not str(v).isdigit()]  # 去数字
                segs = list(filter(lambda x: x.strip(), segs))  # 去左右空格
                segs = list(filter(lambda x: len(x) > 1, segs))  # 长度为1的字符
                segs = list(filter(lambda x: x not in stopwords, segs))  # 去掉停用词
                target_sentence = " ".join(segs)
                data_statistics_dict[sentence]["2"] = target_sentence  # 增加分词内容
                if target_sentence != "":
                        # and target_sentence != "查询" and target_sentence != "佣金" and target_sentence != "提现" \
                        # and target_sentence != "丢单" and target_sentence != "任务" and target_sentence != "代理": #分词后空的数据清掉
                    sentences.append(target_sentence) #保存分词后的数据
                    origin_sentences.append(sentence) #保存分词前的数据，为什么要保存，因为存在分词前句子不一样，但是分词后一样的情况
            except Exception:
                print(sentence)
                continue
        # random.shuffle(sentences)  # 打散语句

        # 存储
        with open(os.path.join(os.path.dirname(__file__), "pre_aaa.json"), 'w') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(os.path.join(os.path.dirname(__file__), "pre_statistics_aaa.json"), 'w') as f:
            json.dump(data_statistics_dict, f, ensure_ascii=False, indent=2, sort_keys=True)

    return data_statistics_dict, origin_sentences, sentences

def transform(sentences):
    # 将文本中的词语转换为词频矩阵 矩阵元素a[i][j] 表示j词在i类文本下的词频
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5)
    # 统计每个词语的tf-idf权值
    transformer = TfidfTransformer()
    # 第一个fit_transform是计算tf-idf 第二个fit_transform是将文本转为词频矩阵
    tfidf = transformer.fit_transform(vectorizer.fit_transform(sentences))
    # 获取词袋模型中的所有词语
    word = vectorizer.get_feature_names()
    # 将tf-idf矩阵抽取出来，元素w[i][j]表示j词在i类文本中的tf-idf权重
    weight = tfidf.toarray()
    # 查看特征大小
    print('Features length: ' + str(len(word)))
    return weight

def plot_cluster(clf,result,newData,numClass):
    plt.figure(2)
    Lab = [[] for i in range(numClass)]
    index = 0
    for labi in result:
        Lab[labi].append(index)
        index += 1
    color = ['oy', 'ob', 'og', 'cs', 'ms', 'bs', 'ks', 'ys', 'yv', 'mv', 'bv', 'kv', 'gv', 'y^', 'm^', 'b^', 'k^',
             'g^'] * 4
    for i in range(numClass):
        x1 = []
        y1 = []
        for ind1 in newData[Lab[i]]:
            # print ind1
            try:
                if ind1[0] < 0.04 and ind1[1] < 0.05:
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
    plt.savefig("kmeans.png")
    plt.show()


# !/usr/bin/env python
# -*-coding: utf-8-*-
import xlsxwriter

# 生成excel文件
def generate_excel(rec_data):
    workbook = xlsxwriter.Workbook(os.path.join(os.path.dirname(__file__), "rec_data.xlsx"))
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
        for i, sentence in enumerate(sentences["data"]):
            # 使用write_string方法，指定数据格式写入数据
            worksheet.write_string(sentences_id, i+1, sentence)
    workbook.close()

if __name__ == "__main__":
    stopwords = pd.read_csv(os.path.join(os.path.dirname(__file__), "stop_words.txt"), index_col=False, quoting=3,
                            sep="\t", names=['stop_words'], encoding="GBK")
    stopwords = stopwords['stop_words'].values

    data_statistics_dict, origin_sentences, sentences = load_log_data()
    weight = transform(sentences)
    #先确定K值
    # for num_clusters in range(25, 100):
    #     clf = KMeans(n_clusters=num_clusters, max_iter=10000, tol=1e-6, init='k-means++')
    #     pca = PCA(n_components=50)  # 降维后再训练
    #     TnewData = pca.fit_transform(weight)  # 降维后再Kmeans训练
    #     # TnewData = weight
    #     s = clf.fit(TnewData)
    #     SSE.append(clf.inertia_)
    #     # SSE.append(sum(np.min(cdist(images_features, km_cluster.cluster_centers_, 'euclidean'), axis=1)) / images_features.shape[0])
    # X = range(25, 100)
    # # SSE = range(1, 9)
    # plt.xlabel('k')
    # plt.ylabel('SSE')
    # plt.plot(X, SSE, 'o-')
    #
    # plt.savefig("k_picture.png")
    # plt.show()

    numClass = 52
    clf = KMeans(n_clusters=numClass, max_iter=10000, init="k-means++", tol=1e-6)  #这里也可以选择随机初始化init="random"
    pca = PCA(n_components=50)  # 降维后再训练
    TnewData = pca.fit_transform(weight)  # 降维后再Kmeans训练
    # TnewData = weight
    s = clf.fit(TnewData)
    result = list(clf.predict(TnewData))
    #result = list(s.labels_) #结果同上
    #方式1：直接PCA,将数据降维进行可视化显示
    pca = PCA(n_components=2)  # 输出两维
    newData = pca.fit_transform(weight)  # 载入N维

    #方式2：先PCA后TSNE,将数据降维进行可视化显示
    # from sklearn.manifold import TSNE
    # newData = PCA(n_components=4).fit_transform(weight)  # 载入N维
    # newData = TSNE(2).fit_transform(newData) #二维用于可视化

    keep_out = {}
    for i in range(numClass):
        keep_out[i] = {"norm": {"norm_value": {}, "norm_probability": {}}, "data": {}}
    for i, sentence in enumerate(sentences):
        keep_out[int(result[i])]["data"][origin_sentences[i]] = {"0": data_statistics_dict[origin_sentences[i]]["0"], "1": data_statistics_dict[origin_sentences[i]]["1"]}

    sum_0 = []
    sum_1 = []
    max_i = []
    max_value = []
    for i, keep_out_value in enumerate(keep_out):
        sum_0.append(0)
        sum_1.append(0)
        max_i.append(0)
        max_value.append(0)
        for sim_sentence in keep_out[keep_out_value]["data"]:
            sum_0[i] += keep_out[keep_out_value]["data"][sim_sentence]["0"]
            sum_1[i] += keep_out[keep_out_value]["data"][sim_sentence]["1"]
            if max_i[i] < keep_out[keep_out_value]["data"][sim_sentence]["1"]: #暂时按个体的最大值计数
                max_i[i] = keep_out[keep_out_value]["data"][sim_sentence]["1"]
                max_value[i] = sim_sentence

        keep_out[keep_out_value]["norm"]["norm_value"] = max_value[i]
        keep_out[keep_out_value]["norm"]["norm_probability"] = {"0": sum_0[i], "1": sum_1[i]}

    view_temp = sorted(keep_out.items(), key=lambda d: d[1]["norm"]["norm_probability"]["1"], reverse=True) #暂时按个体的最大值计数
    view_out = [sort_sentence for _, sort_sentence in view_temp]
    generate_excel(view_out)
    # 装载数据显示
    # plot_cluster(clf, result, newData, numClass)
    # pass