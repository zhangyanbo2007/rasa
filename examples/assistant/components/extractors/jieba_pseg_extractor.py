from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import warnings

from builtins import str
from typing import Any
from typing import Dict
from typing import Optional
from typing import Text

from rasa.nlu import utils
from rasa.nlu.extractors import EntityExtractor
from rasa.nlu.model import Metadata
from rasa.nlu.training_data import Message, TrainingData
from rasa.nlu.utils import write_json_to_file
import itertools


class JiebaPsegExtractor(EntityExtractor):

    provides = ["entities"]

    # zyb-change: -> 换成n,t,ns,m,x,constellation,fortune命名实体
    # defaults = {
    #     "part_of_speech": ["n", "t", "ns", "m", "x"]  # nr：人名，ns：地名，nt：机构名
    # }
    defaults = {
        "part_of_speech": ["t", "ns", "m", "x"]  # nr：人名，ns：地名，nt：机构名
    }

    def __init__(self, component_config=None):
        # type: (Optional[Dict[Text, Text]]) -> None

        super(JiebaPsegExtractor, self).__init__(component_config)

        # zyb-delete: -> 删除jieba词典加载
        # if dictionary_path is not None:
        #     jieba.load_userdict(dictionary_path)

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None
        extracted = self.add_extractor_name(self.posseg_cut_examples(message))

        message.set("entities", extracted, add_to_output=True)

    def posseg_cut_examples(self, example):
        raw_entities = example.get("entities", [])
        example_posseg = self.posseg(example.text)

        for (item_posseg, start, end) in example_posseg:
            part_of_speech = JiebaPsegExtractor.defaults["part_of_speech"]
            for (word_posseg, flag_posseg) in item_posseg:
                if flag_posseg in part_of_speech:
                    # zyb-add: -> 将数字m强制替换成number
                    if flag_posseg == "m":
                        flag_posseg = "number"
                    elif flag_posseg == "x":
                        if word_posseg in self.item_number_db():
                            flag_posseg = "number"
                        else:
                            continue
                    elif flag_posseg == "n":
                        if word_posseg in self.constellation_constellation_db():
                            flag_posseg = "constellation"
                        elif word_posseg in self.constellation_fortune_db():
                            flag_posseg = "fortune"
                        elif word_posseg in self.item_brand_db():
                            flag_posseg = "brand"
                        elif word_posseg in self.item_age_db():
                            flag_posseg = "age"
                        elif word_posseg in self.item_sex_db():
                            flag_posseg = "sex"
                    # zyb-end
                    raw_entities.append({
                        'start': start,
                        'end': end,
                        'value': word_posseg,
                        'entity': flag_posseg,
                        'confidence': 1,  # 增加置信度实体
                    })
        return raw_entities

    # zyb-add:start -> 新增数字，星座，运势,年龄实体检测
    @staticmethod
    def item_number_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10"
                ]

    @staticmethod
    def item_age_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["1岁",
                "2岁",
                "2岁",
                "3岁",
                "4岁",
                "5岁",
                "6岁",
                "7岁",
                "8岁",
                "9岁",
                "10岁",
                "11岁",
                "12岁",
                "13岁",
                "14岁",
                "15岁",
                "1周岁",
                "2周岁",
                "2周岁",
                "3周岁",
                "4周岁",
                "5周岁",
                "6周岁",
                "7周岁",
                "8周岁",
                "9周岁",
                "10周岁",
                "11周岁",
                "12周岁",
                "13周岁",
                "14周岁",
                "15周岁",
                "1个月",
                "满月",
                "2个月",
                "3个月",
                "4个月",
                "5个月",
                "6个月",
                "7个月",
                "8个月",
                "9个月",
                "10个月",
                "11个月",
                "12个月",
                "大人",
                "成年人",
                "成人",
                "婴儿",
                "新生",
                "新生婴儿",
                "婴幼儿"
                ]

    @staticmethod
    def item_sex_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["男孩",
                "女孩",
                "大男孩",
                "小男孩",
                "男孩子",
                "男孩儿",
                "男性",
                "男",
                "男士",
                "男式",
                "男用",
                "男款",
                "女孩",
                "小女孩",
                "女孩子",
                "女孩儿",
                "女性",
                "女",
                "女士",
                "女式",
                "女用",
                "女款"
                ]

    @staticmethod
    def constellation_constellation_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["白羊座",
                "金牛座",
                "双子座",
                "巨蟹座",
                "狮子座",
                "处女座",
                "天秤座",
                "天蝎座",
                "射手座",
                "摩羯座",
                "水瓶座",
                "双鱼座",
                ]

    @staticmethod
    def constellation_fortune_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["综合指数",
                "爱情指数",
                "工作指数",
                "财富指数",
                "爱情运势",
                "工作运势",
                "学业运势",
                "财富运势",
                "健康运势",
                "运势",
                "提醒",
                "优势",
                "弱势",
                "贵人星座",
                "小人星座",
                "缘分星座",
                "幸运数字",
                "吉日",
                "吉时",
                "吉利方位",
                "幸运色",
                "简评",
                "爱情运",
                "桃花运",
                "财富运",
                "财运",
                "幸运数",
                "幸运字",
                "幸运颜色",
                "吉利颜色",
                "吉色",
                "吉利时间",
                "幸运日期",
                "幸运日",
                "速配星座",
                "配对星座",
                "简单评价",
                "简要评价"
                ]

    @staticmethod
    def item_brand_db():
        # type: () -> List[Text]
        """Database of supported constellation"""
        return ["惠氏",
                "美索佳儿",
                "美赞臣",
                "雅培",
                "诺优能",
                "雀巢母婴",
                "飞鹤",
                "金领冠",
                "爱他美",
                "君乐宝",
                "鸿星尔克",
                "回力",
                "安踏",
                "耐克",
                "特步",
                "花花公子",
                "阿迪达斯",
                "李宁",
                "优衣库",
                "森马",
                "北极绒",
                "唐狮",
                "美特斯邦威",
                "乐高",
                "Disney",
                "育儿宝",
                "神通小子",
                "益米",
                "兔妈妈",
                "三宝",
                "万童乐",
                "LEGO"
                ]
    # zyb-add:end

    @staticmethod
    def posseg(text):
        # type: (Text) -> List[Token]

        # zyb-add: -> 增加jieba导入
        import jieba
        import jieba.posseg as pseg

        result = []
        for (word, start, end) in jieba.tokenize(text):
            pseg_data = [(w, f) for (w, f) in pseg.cut(word)]
            result.append((pseg_data, start, end))

        return result

    @classmethod
    def load(cls,
             meta: Dict[Text, Any],
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[Component]
             **kwargs  # type:**Any
             ):

        return cls(meta)
