#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


def process(message):
    """
    用户消息处理函数
    :param message:
    :return:
    """
    # 广告判断
    if (re.findall(r".*(?:为你推荐|请问您需要了解吗|办卡套现|本店专业|亲，|谢谢|亲爱的，|不闲聊|在家创业|"
                   r"为您推荐|你好|包邮|早安|不好意思|点击|新老客户|免费|打扰了|上午好|"
                   r"下午好|您好|亲们|在吗|一键转发|在抖音|朋友圈|"
                   r"复制此条|复制这条).*", message) != [] and len(message) >= 20) \
            or re.findall(r".*(?:朋友圈.*点个赞|转发.*朋友圈|朋友圈第一条|第一条朋友圈|"
                          r"你好，欢迎关注|您好，欢迎关注|在抖音|旺季来了|私信我|感谢关注).*", message) != []:
        pass
    # FAQ判断
    # elif FAQ:
    #     pass
    # 商品标题判断
    elif len(message) >= 20:
        pass
    # 任务判断
    # elif TASK:
    #     pass
