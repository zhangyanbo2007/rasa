import pandas as pd
import re
import os
import json
import numpy as np
from matplotlib import pyplot as plt
import copy


def nlu_data_to_rasa():
    """
    将数据转化为rasa格式
    :return:
    """
    # 读语料
    nlu_data = pd.read_excel("./origin_data/英语模板_v5(4208)-20200723.xlsx",
                             sheet_name="语料")
    nlu_data_dict = {
        "rasa_nlu_data": {
            "common_examples": [],
            "entity_synonyms": [],
            "regex_features": []
        }
    }
    for num in range(len(nlu_data)):
        line = nlu_data.iloc[num].tolist()
        line_dict = {}
        line_dict["intent"] = "_".join(line[:2])

        line_origin_text = line[2]
        # line_origin_text = line[2] + line[2]
        # line_origin_text = "dfsdf ds fs adfdf"

        try:
            # 槽值提取
            line_slot_list = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", line_origin_text)
            # 先删除左边方括号
            line_text = re.sub(r"\[(?=[^\]]*\]\()", "", line_origin_text)
            # 再删除右边槽值+方括号
            line_text = re.sub(r"\]\([^\)]*\)", "", line_text)
        except Exception as e:
            print(num)
        line_dict["text"] = line_text.strip()
        line_dict["entities"] = []
        start = 0
        for value, entity in line_slot_list:
            entity_dict = {}
            # 这个地方做个去重，有可能有重名的情况，不过几率几乎为0
            entity_dict["start"] = line_text.find(value, start)
            entity_dict["end"] = entity_dict["start"] + len(value)
            entity_dict["value"] = value
            entity_dict["entity"] = entity
            start = entity_dict["end"]
            line_dict["entities"].append(entity_dict)
        nlu_data_dict["rasa_nlu_data"]["common_examples"].append(line_dict)
        pass
    # 统计结果
    intent_list = list(set([example["intent"] for example in nlu_data_dict["rasa_nlu_data"]["common_examples"]]))
    domain_list = list(set([intent[:intent.find("_")] for intent in intent_list]))
    print("总条目数：{}".format(len(nlu_data_dict["rasa_nlu_data"]["common_examples"])))
    print("总意图数：{}".format(len(intent_list)))
    print("分别是:{}".format(intent_list))
    print("总领域数：{}".format(len(domain_list)))
    print("分别是:{}".format(domain_list))

    # 统计每种意图的条目数
    intent_count = {}
    for example in nlu_data_dict["rasa_nlu_data"]["common_examples"]:
        intent_name = example["intent"]
        intent_count[intent_name] = intent_count.get(intent_name, 0) + 1
    domain_count = {}
    for key in intent_count.keys():
        domain_name = key[:key.find("_")]
        domain_count[domain_name] = domain_count.get(domain_name, 0) + 1
    intent_count_item = list(intent_count.items())

    intent_count_key = [value[0] for value in intent_count_item]
    intent_count_value = [value[1] for value in intent_count_item]

    argmax_example_num = np.argmax(intent_count_value)
    argmin_example_num = np.argmin(intent_count_value)

    # 去除最大值和最小值后的平均书
    new_intent_count_value = copy.deepcopy(intent_count_value)
    del new_intent_count_value[argmax_example_num]
    del new_intent_count_value[argmin_example_num]
    average_example_num = round(np.mean(new_intent_count_value))

    std_example_num = np.std(new_intent_count_value, ddof=1)
    min_example_intent = intent_count_item[argmin_example_num][0]
    min_example_num = intent_count_item[argmin_example_num][1]

    max_example_intent = intent_count_item[argmax_example_num][0]
    max_example_num = intent_count_item[argmax_example_num][1]

    # 小于某个数的样本有哪些
    threshold = 10
    bad_intent_count_item = [item for item in intent_count_item if item[1] <= threshold]
    print("小于{}样本个数的意图有{}个，分别是：{}".format(threshold, len(bad_intent_count_item), bad_intent_count_item))

    print("样本的最小数是:{},对应的意图类别是{}".format(min_example_num, min_example_intent))
    print("样本的最大数是:{},对应的意图类别是{}".format(max_example_num, max_example_intent))
    print("去除最大最小后样本的平均数是:{}".format(average_example_num))
    print("去除最大最小后样本的标准差是:{}".format(std_example_num))

    plt.title("意图数量分布图")
    plt.xlabel("x axis caption")
    plt.ylabel("y axis caption")
    intent_count_item.sort(key=lambda x: x[1], reverse=True)
    keys_list = list(dict(intent_count_item).keys())
    values_list = list(dict(intent_count_item).values())
    print("排序后{}".format(keys_list))
    plt.bar(range(len(keys_list)), values_list, color='g', align='center')
    plt.show()
    plt.savefig("./test_result/intent_count.png")
    with open("../../../../assistant/data/nlu/train.json", "w", encoding="utf-8") as f:
        json.dump(nlu_data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


def nlu_data_to_dmai():
    """
    将数据转化为dmai格式
    注意dmai格式的语料是规则化的语料，不是完整的句子，并且其实体存在于意图项内。
    TODO: 这里为调试方便跟原生态的语料略有不同,这个留意下
    :return:
    """
    nlu_data = pd.read_excel("./origin_data/英语模板_v5(4208)-20200723.xlsx",
                             sheet_name="语料")
    dmai_data = {"cus_ents": {"normal_entities": []}}
    entity_id = {}
    entity_id_num = 0
    for num in range(len(nlu_data)):

        line = nlu_data.iloc[num].tolist()
        line_dict = {"domain_intent": "_".join(line[:2]), "intent": line[1]}

        line_origin_text = line[2].strip()
        # line_origin_text = line[2] + line[2]
        # line_origin_text = "dfsdf ds fs adfdf"

        try:
            # 槽值提取
            line_slot_list = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", line_origin_text)
            # 先删除左边方括号及其内容
            line_text = re.sub(r"\[[^]]*\](?=\([^\)]*\))", "", line_origin_text)
            # 循环遍历替换字串
            for line_slot in line_slot_list:
                slot = line_slot[1]
                origin_slot = "\(" + slot + "\)"
                new_slot = "${" + slot + "}"
                line_text = re.sub(origin_slot, new_slot, line_text)
        except Exception as e:
            print(num)

        line_dict["text"] = line_text

        # 这个地方保证意图项里面有值
        if line_dict["domain_intent"] not in dmai_data.keys():
            dmai_data[line_dict["domain_intent"]] = {"intent_name": line_dict["intent"], "params": [], "rules": []}

        # 以下for循环有2个作用，一个是加到全局实体列表中，另外一个作为意图项添加的意图列表里
        if len(line_slot_list):
            for entity_value, entity_name in line_slot_list:
                # 将槽值对加入到实体列表中
                new_slot_flag = 1
                new_value_flag = 1
                new_entity_name = "@" + entity_name
                for normal_entity_dict in dmai_data["cus_ents"]["normal_entities"]:
                    if new_entity_name in normal_entity_dict.values():
                        # 状态1
                        for entity_value_dict in normal_entity_dict["entity_values"]:
                            if entity_value == entity_value_dict["item"]:
                                new_value_flag = 0
                                break
                        if new_value_flag:
                            new_entity_value = {"item": entity_value, "synonym": []}
                            normal_entity_dict["entity_values"].append(new_entity_value)
                        new_slot_flag = 0
                        break
                if new_slot_flag:
                    # 状态2
                    entity_id_num += 1
                    entity_id[new_entity_name] = entity_id_num
                    new_normal_entity_dict = {
                        "entity_id": str(entity_id_num),
                        "entity_name": new_entity_name,
                        "entity_values": [
                            {
                                "item": entity_value,
                                "synonym": [
                                ]
                            }
                        ]
                    }
                    dmai_data["cus_ents"]["normal_entities"].append(new_normal_entity_dict)
                try:
                    param = {
                        "param_name": entity_name,
                        "entity_name": new_entity_name,
                        "entity_id": str(entity_id[new_entity_name])
                    }
                    rule = {
                        "cfg_rule": line_dict["text"],
                        "matching_mode": 3
                    }
                except Exception as e:
                    print(e)
                if param not in dmai_data[line_dict["domain_intent"]]["params"]:
                    dmai_data[line_dict["domain_intent"]]["params"].append(param)
                if rule not in dmai_data[line_dict["domain_intent"]]["rules"]:
                    dmai_data[line_dict["domain_intent"]]["rules"].append(rule)
        else:
            rule = {
                "cfg_rule": line_dict["text"],
                "matching_mode": 3
            }
            if rule not in dmai_data[line_dict["domain_intent"]]["rules"]:
                dmai_data[line_dict["domain_intent"]]["rules"].append(rule)
    with open("dmai_data/train.json", "w", encoding="utf-8") as f:
        json.dump(dmai_data, f, ensure_ascii=False, indent=2, sort_keys=True)


def nlu_data_to_fewshot():
    pass


if __name__ == "__main__":
    nlu_data_to_rasa()
    nlu_data_to_dmai()
    # nlu_data_to_fewshot()
