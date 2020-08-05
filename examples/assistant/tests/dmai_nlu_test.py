import requests
import json

# 中文测试数据
nlu_trainer_submit_default_data = {
    "app_id": "1111",
    "job_id": "1111",
    "intent": {
        "intent_name": "自我介绍",
        "params": [
            {
                "param_name": "中文名",
                "entity_name": "@built-in_name",
                "entity_id": "@built-in_name"
            },
            {
                "param_name": "英文名",
                "entity_name": "@英文名",
                "entity_id": "1"
            },
            {
                "param_name": "星座",
                "entity_name": "@星座",
                "entity_id": "2"
            }
        ],
        "rules": [
            {
                "cfg_rule": "我(叫|名字是)${中文名}，我的英文名是${英文名}",
                "matching_mode": 3
            },
            {
                "cfg_rule": "我(叫|名字是)${中文名}，我的英文名是${英文名}，我是${星座}的",
                "matching_mode": 3
            }
        ]
    },
    "cus_ents": {
        "normal_entities": [
            {
                "entity_id": "1",
                "entity_name": "@星座",
                "entity_values": [
                    {
                        "item": "水瓶座",
                        "synonym": [
                            "水瓶"
                        ]
                    },
                    {
                        "item": "天蝎座",
                        "synonym": [
                            "天蝎"
                        ]
                    }
                ]
            }
        ],
        "regular_entities": [
            {
                "entity_id": "2",
                "entity_name": "@英文名",
                "re": "[A-Z][a-z]{2,8}"
            }
        ]
    }
}
nlu_trainer_status_default_data = {
    "app_id": "1111",
    "job_id": "2222"
}
nlu_chitchat_default_data = {
    "request_id": "cc4ee624-a4a8-11ea-8961-1831bfbde45a",
    "text": "hello"
}
nlu_model_parse_default_data = {
    "request_id": "cc4ee624-a4a8-11ea-8961-1831bfbde45a",
    "query": "我叫张三，我的英文名是Alice，我是白羊座的",
    "app_id": "1111",
    "job_ids": ["2222"],
    "cus_ents_id": ["1", "2"]
}
nlu_model_delete_entity_default_data = {
    "app_id": "1111",
    "job_ids": ["2222"]
}
nlu_model_delete_intent_default_data = {
    "app_id": "1111",
    "job_ids": ["2222"]
}


class NluService:
    # 这个其实可以用语法糖
    def __init__(self):
        pass
        self.nlu_train_zh_host = "http://nlu-online-trainer-zh.px-dialogue.dev.dm-ai.cn"
        self.nlu_train_en_host = "http://nlu-online-trainer-en.px-dialogue.dev.dm-ai.cn"
        self.nlu_parse_zh_host = "http://nlu-manager-zh-service.px-dialogue.dev.dm-ai.cn"
        self.nlu_parse_en_host = "http://nlu-manager-en-service.px-dialogue.dev.dm-ai.cn"
        self.nlu_universal_host = " http://universal-intent-recognition-service.px-dialogue.dev.dm-ai.cn"

    def nlu_trainer_submit(self, data=nlu_trainer_submit_default_data, mode="zh"):
        """
        nlu训练数据提交
        :param data:
        :param mode: en英文模型，cn中文模型
        :return:
        """
        if mode == "zh":
            url = self.nlu_train_zh_host + "/api/v1/nlu/trainer/submit/job"
        if mode == "en":
            url = self.nlu_train_en_host + "/api/v1/nlu/trainer/submit/job"
        # 通用代码
        param_header = {
            "Content-Type": "application/json"
        }
        contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
        return contents

    def nlu_trainer_status(self, data=nlu_trainer_status_default_data, mode="en"):
        """
        nlu训练状态查询
        :param mode: en英文模型，cn中文模型
        :param data: 输入的数据
        :return:
        """
        if mode == "zh":
            url = self.nlu_train_zh_host + "/api/v1/nlu/trainer/get/job"
        if mode == "en":
            url = self.nlu_train_en_host + "/api/v1/nlu/trainer/get/job"
        # 通用代码
        param_header = {
            "Content-Type": "application/json"
        }
        contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
        return contents

    def nlu_chitchat(self, data=nlu_chitchat_default_data, mode="en"):
        """
        nlu内置闲聊接口，目前只能支持中文
        :param data:
        :param mode: en英文模型，cn中文模型
        :return:
        """
        if mode == "zh":
            url = self.nlu_universal_host + "/api/v1/nlu/intent-recognition/intent"
            # 通用代码
            param_header = {
                "Content-Type": "application/json"
            }
            contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
            return contents
        else:
            print("暂不支持英文闲聊")
        pass

    def nlu_model_parse(self, data=nlu_model_parse_default_data, mode="en"):
        """
        nlu模型识别接口
        :param data:
        :param mode: en英文模型，cn中文模型
        :return:
        """
        if mode == "zh":
            url = self.nlu_parse_zh_host + "/api/v1/nlu/manager/parse"
        if mode == "en":
            url = self.nlu_parse_en_host + "/api/v1/nlu/manager/parse"
        # 通用代码
        param_header = {
            "Content-Type": "application/json"
        }
        contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
        return contents

    def nlu_model_delete_entity(self, data=nlu_model_delete_entity_default_data, mode="en"):
        """
        nlu删除实体命令
        :param data:
        :param mode: en英文模型，cn中文模型
        :return:
        """
        if mode == "zh":
            url = self.nlu_parse_zh_host + "/api/v1/nlu/manager/delete/entities"
        if mode == "en":
            url = self.nlu_parse_en_host + "/api/v1/nlu/manager/delete/entities"
        # 通用代码
        param_header = {
            "Content-Type": "application/json"
        }
        contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
        return contents

    def nlu_model_delete_intent(self, data=nlu_model_delete_intent_default_data, mode="en"):
        """
        nlu删除意图命令
        :param data:
        :param mode: en英文模型，cn中文模型
        :return:
        """
        if mode == "zh":
            url = self.nlu_parse_zh_host + "/api/v1/nlu/manager/delete/intents"
        if mode == "en":
            url = self.nlu_parse_en_host + "/api/v1/nlu/manager/delete/intents"
        # 通用代码
        param_header = {
            "Content-Type": "application/json"
        }
        contents = (requests.post(url=url, data=json.dumps(data), headers=param_header)).json()
        return contents


if __name__ == "__main__":
    nlu_service = NluService()

    # 中文测试
    result = nlu_service.nlu_trainer_submit(mode="zh")
    print(result)
    result = nlu_service.nlu_trainer_status(mode="zh")
    print(result)
    result = nlu_service.nlu_chitchat(mode="zh")
    print(result)
    result = nlu_service.nlu_model_parse(mode="zh")
    print(result)
    # result = nlu_service.nlu_model_delete_entity(mode="zh")
    # print(result)
    # result = nlu_service.nlu_model_delete_intent(mode="zh")
    # print(result)

    # # 英文测试数据代码
    # nlu_trainer_submit_default_data = {
    #     "app_id": "1111",
    #     "job_id": "2222",
    #     "intent": {
    #         "intent_name": "introduction",
    #         "params": [
    #             {
    #                 "param_name": "param_english_name",
    #                 "entity_name": "@english_name",
    #                 "entity_id": "1"
    #             },
    #             {
    #                 "param_name": "param_gpe",
    #                 "entity_name": "@built-in_gpe",
    #                 "entity_id": "2"
    #             },
    #             {
    #                 "param_name": "param_person",
    #                 "entity_name": "@person",
    #                 "entity_id": "3"
    #             }
    #         ],
    #         "rules": [
    #             {
    #                 "cfg_rule": "my name is ${param_english_name}，i come from ${param_gpe}",
    #                 "matching_mode": 3
    #             },
    #             {
    #                 "cfg_rule": "i'm ${param_english_name}，i'm from ${param_gpe}, i'm a ${param_person}",
    #                 "matching_mode": 3
    #             }
    #         ]
    #     },
    #     "cus_ents": {
    #         "normal_entities": [
    #             {
    #                 "entity_id": "3",
    #                 "entity_name": "@person",
    #                 "entity_values": [
    #                     {
    #                         "item": "boy",
    #                         "synonym": [
    #                             "man",
    #                             "guy"
    #                         ]
    #                     },
    #                     {
    #                         "item": "girl",
    #                         "synonym": [
    #                             "woman",
    #                             "lady"
    #                         ]
    #                     }
    #                 ]
    #             }
    #         ],
    #         "regular_entities": [
    #             {
    #                 "entity_id": "2",
    #                 "entity_name": "@english_name",
    #                 "re": "[A-Z][a-z]{2,8}"
    #             }
    #         ]
    #     }
    # }
    # nlu_trainer_status_default_data = {
    #     "app_id": "1111",
    #     "job_id": "2222"
    # }
    # nlu_chitchat_default_data = {
    #     "request_id": "cc4ee624-a4a8-11ea-8961-1831bfbde45a",
    #     "text": "hello"
    # }
    # nlu_model_parse_default_data = {
    #     "request_id": "cc4ee624-a4a8-11ea-8961-1831bfbde45a",
    #     "query": "我叫张三，我的英文名是Alice，我是白羊座的",
    #     "app_id": 1111,
    #     "job_ids": ["2222"],
    #     "cus_ents_id": ["1", "2"]
    # }
    # nlu_model_delete_entity_default_data = {
    #     "app_id": 1111,
    #     "job_ids": ["2222"]
    # }
    # nlu_model_delete_intent_default_data = {
    #     "app_id": "1111",
    #     "job_ids": ["2222"]
    # }
    # # 英文测试
    # result = nlu_service.nlu_trainer_submit(mode="en", data=nlu_trainer_submit_default_data)
    # print(result)
    # result = nlu_service.nlu_trainer_status(mode="en", data=nlu_trainer_status_default_data)
    # print(result)
    # result = nlu_service.nlu_chitchat(mode="en", data=nlu_chitchat_default_data)
    # print(result)
    # result = nlu_service.nlu_model_parse(mode="en", data=nlu_model_parse_default_data)
    # print(result)
    # result = nlu_service.nlu_model_delete_entity(mode="en", data=nlu_model_delete_entity_default_data)
    # print(result)
    # result = nlu_service.nlu_model_delete_intent(mode="en", data=nlu_model_delete_intent_default_data)
    # print(result)
