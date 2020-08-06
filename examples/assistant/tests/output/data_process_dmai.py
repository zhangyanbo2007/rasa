import pandas as pd
import re
import os
import json
import numpy as np
from matplotlib import pyplot as plt
import copy


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
    with open("./dmai_data/train.json", "w", encoding="utf-8") as f:
        json.dump(dmai_data, f, ensure_ascii=False, indent=2, sort_keys=True)


def nlu_data_to_fewshot():
    pass


if __name__ == "__main__":
    nlu_data_to_dmai()
    # nlu_data_to_fewshot()
