from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import glob
import logging
import os
import shutil
import typing
from typing import Any, Dict, List, Optional, Text

from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.tokenizers import Token, Tokenizer
from rasa.nlu.training_data import Message, TrainingData

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from rasa.nlu.model import Metadata

# zyb-change: -> 增加停用词表,IDF词表
JIEBA_CUSTOM_DICTIONARY_PATH = "tokenizer_jieba"
JIEBA_CUSTOM_STOPWORD_PATH = "stopword_jieba"
JIEBA_CUSTOM_IDF_PATH = "idf_jieba"


class JiebaTokenizer(Tokenizer, Component):

    provides = ["tokens"]

    language_list = ["zh"]

    # zyb-change: -> 增加停用词表
    defaults = {
        "dictionary_path": None,  # default don't load custom dictionary
        "stopword_path": None,  # default don't load custom stopword
        "idf_path": None  # default don't load custom stopword
    }
    stopwords = []
    # zyb-end

    def __init__(self, component_config: Dict[Text, Any] = None) -> None:
        """Construct a new intent classifier using the MITIE framework."""

        super(JiebaTokenizer, self).__init__(component_config)

        # path to dictionary file or None
        self.dictionary_path = self.component_config.get('dictionary_path')
        # zyb-change: -> 增加停用词表
        self.stopword_path = self.component_config.get('stopword_path')
        # zyb-change: -> 增加IDF词表
        self.idf_path = self.component_config.get('idf_path')

        # zyb-change: -> 增加停用词表,IDF词表
        if self.dictionary_path is not None:
            self.load_custom_dictionary(self.dictionary_path)
        if self.stopword_path is not None:
            self.load_custom_stopword(self.stopword_path)
        if self.idf_path is not None:
            self.load_custom_idf(self.idf_path)
        # zyb-end

        # zyb-change: -> 这个地方暂不加载
        # # load dictionary
        # if self.dictionary_path is not None:
        #     self.load_custom_dictionary(self.dictionary_path)


    @classmethod
    def required_packages(cls) -> List[Text]:
        return ["jieba"]

    # zyb-change: -> 增加建议词典
    @staticmethod
    def load_suggest_userdict(f):
        '''
        Load personalized dict to improve detect rate.

        Parameter:
            - f : A plain text file contains words and their ocurrences.
                  Can be a file-like object, or the path of the dictionary file,
                  whose encoding must be utf-8.

        Structure of dict file:
        word1 freq1 word_type1
        word2 freq2 word_type2
        ...
        Word type may be ignored
        '''
        import jieba
        import re
        re_userdict = re.compile('^(.+?)( [0-9]+)?( [a-z]+)?$', re.U)
        re_split_userdict = re.compile('^(.+?)( .+?)$', re.U)

        if isinstance(f, (str,)):
            f_name = f
            f = open(f, 'rb')
        else:
            try:
                f_name = f.name
            except AttributeError:
                f_name = repr(f)
        for lineno, ln in enumerate(f, 1):
            line = ln.strip()
            if not isinstance(line, str):
                try:
                    line = line.decode('utf-8').lstrip('\ufeff')
                except UnicodeDecodeError:
                    raise ValueError('dictionary file %s must be utf-8' % f_name)
            if not line:
                continue
            # match won't be None because there's at least one character
            word, freq, tag = re_userdict.match(line).groups()

            if freq is not None:
                freq = freq.strip()
            if tag is not None:
                tag = tag.strip()

            # 增加建议词典
            if word is not None and word.strip().find(" ") == -1:
                # 仅当有词频要求时才增加词典，待测试
                if freq is not None or tag is not None:
                    jieba.add_word(word, freq, tag)
                jieba.suggest_freq(word.strip(), tune=True)

            result = re_split_userdict.match(line)
            if result is not None:
                word1, word2 = result.groups()
                jieba.suggest_freq((word1.strip(), word2.strip()), tune=True)
    # zyb-end

    @staticmethod
    def load_custom_dictionary(path: Text) -> None:
        """Load all the custom dictionaries stored in the path.

        More information about the dictionaries file format can
        be found in the documentation of jieba.
        https://github.com/fxsjy/jieba#load-dictionary
        """
        jieba_userdicts = glob.glob("{}/*".format(path))
        for jieba_userdict in jieba_userdicts:
            logger.info("Loading Jieba User Dictionary at {}".format(jieba_userdict))

            # zyb-change: -> 注释掉加载词典，加载建议词典
            # jieba.load_userdict(jieba_userdict)

            # zyb-change: -> 加载用户建议词典
            JiebaTokenizer.load_suggest_userdict(jieba_userdict)

    # zyb-change: -> 增加停用词表
    @staticmethod
    def load_custom_stopword(path):
        # type: (Text) -> None
        """Load all the custom stopword stored in the path.

        More information about the dictionaries file format can
        be found in the documentation of jieba.
        https://github.com/fxsjy/jieba#load-dictionary
        """
        from jieba import analyse
        jieba_stopwords = glob.glob("{}/*".format(path))
        for jieba_stopword in jieba_stopwords:
            logger.info("Loading Jieba User Stopwords at "
                        "{}".format(jieba_stopword))
            # zyb-note: -> 注意这个地方尽在关键词提取中使用停用词,分词并不使用
            analyse.set_stop_words(jieba_stopword)
            # for word in open(jieba_stopword, 'r', encoding='UTF-8'):
            #     JiebaTokenizer.stopwords.append(word.strip())

    # zyb-change: -> 增加idf词表
    @staticmethod
    def load_custom_idf(path):
        # type: (Text) -> None
        """Load idf
        """
        from jieba import analyse
        jieba_idfs = glob.glob("{}/*".format(path))
        for jieba_idf in jieba_idfs:
            logger.info("Loading Jieba User Idf at "
                        "{}".format(jieba_idf))
            analyse.set_idf_path(jieba_idf)

    def train(
        self, training_data: TrainingData, config: RasaNLUModelConfig, **kwargs: Any
    ) -> None:

        for example in training_data.training_examples:
            example.set("tokens", self.tokenize(example.text))

    def process(self, message: Message, **kwargs: Any) -> None:
        message.set("tokens", self.tokenize(message.text))

    @staticmethod
    def tokenize(text: Text) -> List[Token]:
        import jieba

        # zyb-change: -> 增加停用词表
        tokenized = jieba.tokenize(text)
        tokens = [Token(word, start) for (word, start, end) in tokenized if word not in JiebaTokenizer.stopwords]
        # zyb-end

        return tokens

    @classmethod
    def load(
        cls,
        meta: Dict[Text, Any],
        model_dir: Optional[Text] = None,
        model_metadata: Optional["Metadata"] = None,
        cached_component: Optional[Component] = None,
        **kwargs: Any
    ) -> "JiebaTokenizer":

        relative_dictionary_path = meta.get("dictionary_path")

        # zyb-change: -> 增加停用词表
        relative_stopword_path = meta.get("stopword_path")
        # zyb-change: -> 增加IDF表
        relative_idf_path = meta.get("idf_path")

        # get real path of dictionary path, if any
        if relative_dictionary_path is not None:
            dictionary_path = os.path.join(model_dir, relative_dictionary_path)

            meta["dictionary_path"] = dictionary_path

        # zyb-change: -> 增加停用词表
        if relative_stopword_path is not None:
            stopword_path = os.path.join(model_dir, relative_stopword_path)

            meta["stopword_path"] = stopword_path
        # zyb-change: -> 增加IDF词表
        if relative_idf_path is not None:
            idf_path = os.path.join(model_dir, relative_idf_path)

            meta["idf_path"] = idf_path

        return cls(meta)

    @staticmethod
    def copy_files_dir_to_dir(input_dir, output_dir):
        # make sure target path exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        target_file_list = glob.glob("{}/*".format(input_dir))
        for target_file in target_file_list:
            shutil.copy2(target_file, output_dir)

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        """Persist this model into the passed directory."""

        model_dictionary_path = None

        # zyb-change: -> 增加停用词表
        model_stopword_path = None
        # zyb-change: -> 增加idf词表
        model_idf_path = None

        # copy custom dictionaries to model dir, if any
        if self.dictionary_path is not None:
            target_dictionary_path = os.path.join(model_dir, JIEBA_CUSTOM_DICTIONARY_PATH)
            self.copy_files_dir_to_dir(self.dictionary_path,
                                       target_dictionary_path)

            # set dictionary_path of model metadata to relative path
            model_dictionary_path = JIEBA_CUSTOM_DICTIONARY_PATH

        # zyb-change: -> 增加停用词表
        # copy custom dictionaries to model dir, if any
        if self.stopword_path is not None:
            target_stopword_path = os.path.join(model_dir, JIEBA_CUSTOM_STOPWORD_PATH)
            self.copy_files_dir_to_dir(self.stopword_path,
                                       target_stopword_path)

            # set stopword_path of model metadata to relative path
            model_stopword_path = JIEBA_CUSTOM_STOPWORD_PATH

        # zyb-change: -> 增加IDF词表
        # copy custom dictionaries to model dir, if any
        if self.idf_path is not None:
            target_idf_path = os.path.join(model_dir, JIEBA_CUSTOM_IDF_PATH)
            self.copy_files_dir_to_dir(self.idf_path,
                                       target_idf_path)

            # set stopword_path of model metadata to relative path
            model_idf_path = JIEBA_CUSTOM_IDF_PATH

        return {"dictionary_path": model_dictionary_path, "stopword_path": model_stopword_path,
                "idf_path": model_idf_path}
