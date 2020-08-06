import os
import argparse
import json

parser = argparse.ArgumentParser(
    description='starts the bot')

parser.add_argument(
    'path',
    help="what the bot should do ?")
path = parser.parse_args().path
data_dict = {}

for root, dirs, files in os.walk(path, topdown=False):
    for file in files:
        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
            data_dict = json.load(f)
        for num, smalltalk_sub_dict in enumerate(data_dict["rasa_nlu_data"]["common_examples"]):
            ans_dict = {"type": "task", "intent": smalltalk_sub_dict["intent"],
                        "match_item": smalltalk_sub_dict["text"], "ans_list": {},
                        "entity": smalltalk_sub_dict["entities"], "confidence": 0}
            # 此处只在用anyq的时候才用到回复，现在没有用anyq故设置为空
            data_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"] = ans_dict
            data_dict["rasa_nlu_data"]["common_examples"][num]["answer_text"] = {}
        with open(os.path.join(root, file), "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
