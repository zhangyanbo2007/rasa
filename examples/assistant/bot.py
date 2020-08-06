#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：Zhang Yanbo time:2019-06-14 11:14:20

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
import logging
import warnings
# from policy.mobile_policy import MobilePolicy
# from policy.attention_policy import AttentionPolicy
from rasa_core import utils
from rasa_core.agent import Agent
from rasa_core.policies.memoization import MemoizationPolicy
from rasa_core.policies.fallback import FallbackPolicy
from rasa_core.policies.form_policy import FormPolicy
from rasa_core.policies.embedding_policy import EmbeddingPolicy
from rasa_core import config

logger = logging.getLogger(__name__)


def train_dialogue(config_file="kg_data/dialogue_data_config/dialogue_data_config.yml",
                   data_dir="kg_data/dialogue_data/dialogue_data.md",
                   output_dir="models/dialogue"):

    agent = Agent(config_file, policies=config.load("policy/default_policy_config.yml"))
    training_data = agent.load_data(data_dir)
    agent.train(training_data)
    agent.persist(output_dir)
    return agent


def train_domain(config_file, data_dir, output_dir):
    from rasa_nlu_zyb.training_data import load_data
    from rasa_nlu_zyb import config
    from rasa_nlu_zyb.model import Trainer

    training_data = load_data(data_dir)
    trainer = Trainer(config.load(config_file))
    trainer.train(training_data)
    model_directory = trainer.persist(output_dir, fixed_model_name="current")

    return model_directory


def train_intent(config_file, data_dir, output_dir):
    from rasa_nlu_zyb.training_data import load_data
    from rasa_nlu_zyb import config
    from rasa_nlu_zyb.model import Trainer

    training_data = load_data(data_dir)
    trainer = Trainer(config.load(config_file))
    trainer.train(training_data)
    model_directory = trainer.persist(output_dir, fixed_model_name="current")

    return model_directory


if __name__ == '__main__':
    utils.configure_colored_logging(loglevel="INFO")

    parser = argparse.ArgumentParser(
            description='starts the bot')
    parser.add_argument(
        '--segment',
        choices=["fine-tune", "train", "predict", "evaluate"],
        type=str,
        help="训练，预测，评估")
    parser.add_argument(
        '--obj',
        choices=["domain", "intent", "dialogue"],
        type=str,
        help="训练，预测，评估")
    parser.add_argument(
        '--data_dir',
        type=str,
        help="输入文件")
    parser.add_argument(
        '--output_dir',
        type=str,
        help="输出文件")
    parser.add_argument(
        '--config_file',
        type=str,
        help="文件配置")
    cmdline_args = parser.parse_args()
    obj = cmdline_args.obj
    segment = cmdline_args.segment
    data_dir = cmdline_args.data_dir
    output_dir = cmdline_args.output_dir
    config_file = cmdline_args.config_file
    if segment == "train":
        if obj == "domain":
            # os.system('source bert-serving-start.sh')
            train_domain(config_file, data_dir, output_dir)
        elif obj == "intent":
            train_intent(config_file, data_dir, output_dir)
        elif obj == "dialogue":
            # os.system('source bert-serving-start.sh')
            train_dialogue(config_file, data_dir, output_dir)
