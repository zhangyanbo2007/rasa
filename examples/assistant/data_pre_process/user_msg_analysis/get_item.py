import requests
import json
import re
import sys
import os
import time
sys.path.append('/dialog_server/source/bot_application/api')
from taobao_api import get_item


def pull_data():
    page_size = "100"
    for material_id in all_list:
        data_list = []
        for page_no in range(int(page_size)):
            temp_list = get_item(material_id=material_id, page_size=page_size, page_no=str(page_no + 1))
            if temp_list:
                data_list.extend(temp_list)
            else:
                break
        item_id_list = []
        for data in data_list:
            item_id_list.append(data["item_id"])
        # 首先判断文件是否存在
        origin_data_list = []
        if os.path.exists(os.path.join("items_data", str(material_id) + "_items.json")):
            with open(os.path.join("items_data", str(material_id) + "_items.json"), "r", encoding="utf-8") as f:
                origin_data_list = json.load(f)
                for i in range(len(origin_data_list)-1, -1, -1):
                        if origin_data_list[i]["item_id"] in item_id_list:
                            origin_data_list.pop(i)
        # 判断文件是否
        with open(os.path.join("items_data", str(material_id) + "_items.json"), "w", encoding="utf-8") as f:
            json.dump(data_list+origin_data_list, f, ensure_ascii=False, indent=2, sort_keys=True)


def save_string():
    # 全体去重并保存所有标题
    items_dict = {}
    for material_id in all_list:
        if os.path.exists(os.path.join("items_data", str(material_id) + "_items.json")):
            with open(os.path.join("items_data", str(material_id) + "_items.json"), "r", encoding="utf-8") as f:
                origin_data_list = json.load(f)
                for origin_data in origin_data_list:
                    items_dict[origin_data["item_id"]] = origin_data["title"]
    print("标题保存长度为：{}".format(len(items_dict)))
    with open(os.path.join("items_data", "items_string.json"), "w", encoding="utf-8") as f:
        json.dump(items_dict, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    # 需求1：每隔一个小时爬下来给每个list去重，并存入到相应的文本里面（初步估计一次最大24400条数据）
    # 需求2：全部数据分析去重，整理商品标题列表->目标20万
    general_item_list = ["synthesis", "shoes", "mother", "woman_closes", "beautiful", "food", "home", "man_closes",
                         "sport", "digital", "underwear"]
    good_material_list = ["3756", "3762", "3760", "3767", "3763", "3761", "3758", "3764", "3766", "3759", "3765"]
    big_material_list = ["9660", "9648", "9650", "9658", "9653", "9649", "9655", "9654", "9651", "9656", "9652"]
    high_material_list = ["13366", "13370", "13374", "13367", "13371", "13375", "13368", "13372", "13376", "13369",
                          "13373"]
    brand_material_list = ["3786", "3796", "3789", "3788", "3794", "3791", "3792", "3790", "3795", "3793", "3787"]
    mother_material_list = ["4040", "4041", "4044", "4042", "4043", "4045"]
    other_material_list = ["4092", "4093", "4094"]
    all_list = good_material_list + big_material_list + high_material_list + \
               brand_material_list + mother_material_list + other_material_list
    pull_data()
    save_string()
    while True:
        # 每隔大概1小时多一点儿更新一次
        time.sleep(60*60+2*60)
        pull_data()
        save_string()
