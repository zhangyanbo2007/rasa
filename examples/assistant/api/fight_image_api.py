import re
import time
import random
import os
# from response import get_response_sim
from urllib import request
import itchat
import sys
from shutil import copyfile, rmtree
import emoji

sys.path.append('/dialog_server/source/bot_application/api')
from baidu_ocr_api import recognize_img_words
from qa_chit_api import get_qa_chit
from qa_image_api import get_qa_image, search_img
from gif2img_api import gif2img
from similar_image_api import similar_image_init, similar_image
from img_add_text_api import ImgAddText

global loaded_model
global image_index
global file_index
global similar_image_init_flag
global img_add_text

similar_image_init_flag = 0


def fight_image_init():
    """
    在调用斗图函数之前必须先初始化
    :return:
    """
    global loaded_model
    global image_index
    global file_index
    global similar_image_init_flag
    global img_add_text
    # 首先初始化
    if similar_image_init_flag == 0:
        similar_image_init_flag = 1
        loaded_model, image_index, file_index = similar_image_init("/dialog_server/source/eliza_stack/fight_images_models")
        img_add_text = ImgAddText()


def fight_image(fight_mode, image_or_text, image_path, text, new_image_name_path):
    """
    # TODO:图片模仿式如果没有正确返回值是直接跳出，并不会走别的模式，这个后续待优化
    # TODO:图片输入输出表征不明确
    :param fight_mode: 斗图模式，有文字模仿式和文字对话式以及图片模仿式以及图片内涵式分别对应0,1,2,3四种模式
    文字模仿式:方法-主要是通过检索文字，寻找图片表达不同的回复；效果-这种效果就是重复别人说话的意思。
    文字对话式:方法-主要是通过检索文字，回答文字的内容，寻找最近似的文本回复，如果不存在则通过创建文本的方式生成；效果-这种效果有对话的意思。
    图片模仿式：方法-主要是通过检索图片，回答相关图片内容，寻找最近似的图片回复；效果-这种效果与文字模仿式有相似之处。
    图片内涵式：这种旨在识别图片的内涵信息(图标信息，隐喻信息等)，然后配置相应的内涵回复。(待收集整理添加)
    :param image_or_text: "image" or "text",分别表示文字输入还是图片输入
    :param image_path:图片输入的完整路径，支持png格式和gif格式
    :param text:2个含义：image_or_text="text"表示文字输入，image_or_text="image"表示图片的OCR文字信息(None表示需要OCR，字符串表示不需要OCR)
    :param new_image_name_path:生成图片的文件名完整路径，注意不带后缀，如：222.jpg文件对应的这个路径是/ddd/222
    :return:dict["status"]=="failure"表示失败，"success"表示成功，dict["data"] == {"image":二进制文件流}
    """
    global loaded_model
    global image_index
    global file_index
    global similar_image_init_flag
    global img_add_text

    return_dict = {"error_msg": [], "error_code": 0, "data": {}}
    img_list = []

    if similar_image_init_flag != 1:
        return_dict["error_code"] = 1
        return_dict["error_msg"].append("原始错误:斗图API未初始化")
        # print(return_dict["error_msg"])
        return return_dict
    if image_or_text == "image":
        if os.path.getsize(image_path) == 0:
            img_list = []
            return_dict["error_code"] = 2
            return_dict["data"] = {"fight_mode": fight_mode}
            return_dict["error_msg"].append("图像模式-图像为空错误：图像文件大小为空，无法识别")
            # print(return_dict["error_msg"])
            return return_dict

        local_file, suffix = os.path.splitext(image_path)
        if text is None and fight_mode != 2:  # 表示没有传入已经提取过得OCR信息，且不是图片模仿式，那么就要首先提取OCR
            if suffix != ".gif":
                rec_text = recognize_img_words(image_path)  # zyb解析出来的文字
                print("OCR解析的文本是:{}".format(rec_text))
                # 删除png文件
                if os.path.isfile(image_path):
                    pass
                    #  如果为空则判断为无字图片，这个地方先不删除
                    # if rec_text != "":
                    #     os.remove(os.path.join("./images", msg['FileName']))
            elif suffix == ".gif":
                last_text = ""
                rec_flag = 0
                gif_path = "gif_temp_dir"  # 在程序当前目录创建临时文件夹
                if not os.path.exists(gif_path):
                    os.mkdir(gif_path)
                for num, img in enumerate(gif2img(image_path.encode("UTF-8"), gif_path.encode("UTF-8"))):
                    rec_text = recognize_img_words(img.decode())
                    #  至少识别前后两次一样，才算识别正确
                    if rec_text == last_text and rec_text != "" and rec_text != "error":
                        rec_flag = 1
                        break
                    last_text = rec_text
                    # 限制gif不超过10张，太多导致检测太慢
                    if num >= 9:
                        rec_flag = 0
                        break
                # 注意有可能gif只有一张图片，所以对num == 0做了个判定
                if rec_flag == 1 or num == 0:
                    print("OCR解析的文本是:{}".format(rec_text))
                else:
                    rec_text = ""
                rmtree(gif_path, True)    # 删除临时文件夹

            if rec_text == "" or rec_text == "error":
                rec_text == ""
            return_dict["data"]["ocr_text"] = rec_text  # 被识别出来就保存OCR信息
        else:
            rec_text = text
            return_dict["data"]["ocr_text"] = rec_text  # 继承之前已经识别出来的OCR信息
        # 如果解析过后，非图片模仿式模式文字为""
        if fight_mode != 2 and rec_text == "":
            img_list = []
            return_dict["error_code"] = 3
            return_dict["data"] = {"fight_mode": fight_mode, "ocr_text": ""}  # 保存OCR信息
            return_dict["error_msg"].append("图像模式-非图像模仿式-OCR错误：OCR解析失败")
            # print(return_dict["error_msg"])
            return return_dict
    elif image_or_text == "text":
        # 过滤掉@对象,这种模式下没有图片模仿模式
        match_list = re.findall(r"^(.*?)@.*\s(.*)$", text)  # 过滤掉文字前面最后一个空格
        if len(match_list) > 0:
            (left_value, right_value) = match_list[0]
            rec_text = left_value.strip() + right_value.strip()
        else:
            rec_text = text
    if fight_mode == 0:  # 模仿式接招
        if rec_text != "":
            img_list = search_img(rec_text)
        else:
            img_list = []
        print("模仿式接招解析的相似图片是:\n{}".format(
            "\n".join([img_data["question"] + "|" + str(img_data["confidence"]) for img_data in img_list])))
        temp_img_list = [temp_img for temp_img in img_list if temp_img["confidence"] >= 0.5]  # 模仿式的效果最好，所以适当放宽一些0.65
        img_list = temp_img_list
        if len(img_list) != 0:
            pass
        else:
            img_list = []
            return_dict["error_code"] = 4
            return_dict["data"]["fight_mode"] = fight_mode
            return_dict["error_msg"].append("文字模仿式错误：找不到相似图片")
            # print(return_dict["error_msg"])
            # 注意这里先不返回，等后续观察是否有表情符号
    elif fight_mode == 1:  # 对话式接招
        if rec_text != "":
            qa_list = get_qa_chit(rec_text)
        else:
            qa_list = []
        print("对话式接招解析的对应文本是:\n{}".format(
            "\n".join([qa_data["question"] + "|" + qa_data["answer"] + "|" + str(qa_data["confidence"])
                       for qa_data in qa_list])))
        temp_qa_list = [temp_qa for temp_qa in qa_list if temp_qa["confidence"] >= 0.5]  # 对话式模型要严格一些last:0.75
        qa_list = temp_qa_list
        if len(qa_list) != 0:  # 说明存在有效对话文本
            img_list = search_img(qa_list[0]["answer"])
            print("对话式接招-解析的对应文本的相似图片是:\n{}".format(
                "\n".join([img_data["question"] + "|" + str(img_data["confidence"]) for img_data in img_list])))
            temp_img_list = [temp_img for temp_img in img_list if temp_img["confidence"] >= 0.5]  # 对话式生成的文本图片检索要更严格一些0.8
            img_list = temp_img_list
            if len(img_list) != 0:
                pass
            else:
                # 如果是文字，则根据文字首先挑出来相似相似图片，再根据相似图片选择一个回复。
                flag = 0
                if image_or_text == "text":
                    img_list = search_img(rec_text)
                    print("对话式接招-输入文字解析的相似图片是:\n{}".format(
                        "\n".join([img_data["answer"] + "|" + str(img_data["confidence"]) for img_data in img_list])))
                    temp_img_list = [temp_img for temp_img in img_list if temp_img["confidence"] >= 0.5]  #  这个适当放宽些，因为只是为了找到相似图片写字0.6
                    img_list = temp_img_list
                    if len(img_list) != 0:
                        image_path = img_list[0]["answer"]
                    else:
                        img_list = []
                        return_dict["data"] = {"fight_mode": fight_mode}
                        return_dict["error_code"] = 5
                        return_dict["error_msg"].append("文本对话式错误：找不到输入文字相关的图片，因此无法根据相关图片生成回复")
                        # print(return_dict["error_msg"])
                        flag = 1  # 跳出进行一步
                if flag == 0:
                    _, suffix = os.path.splitext(image_path)
                    image_similary_path = os.path.join(os.path.dirname(new_image_name_path), "image_similary" + suffix)
                    copyfile(image_path.encode("UTF-8"), image_similary_path.encode("UTF-8"))  # 注意这个地方是临时文件
                    return_list = similar_image(image_similary_path, loaded_model, image_index, file_index)
                    # 寻找与原图最相似的图片，注意这个地方的置信度做了一个转换
                    img_list = []
                    for return_data in return_list:
                        img_list.append({"answer": return_data[1], "confidence": 1 - return_data[2]})
                    print("对话式接招-回复的模板图片是:\n{}".format(
                        "\n".join([img_data["answer"] + "|" + str(img_data["confidence"]) for img_data in img_list])))
                    img_list = [temp_img for temp_img in img_list if 0.2 <= temp_img["confidence"] <= 0.8]  #  这个适当放宽些，因为只是为了找到相似图片写字0.8
                    if len(img_list) != 0:
                        if len(img_list) == 1:
                            send_path = img_list[random.randint(0, len(img_list) - 1)]["answer"]
                        else:
                            send_path = img_list[random.randint(0, 1)]["answer"]
                        # 在空白处添加"就说像不像文字"
                        # TODO 注意目前只能回复静态jpg图
                        _, suffix = os.path.splitext(send_path)  # 注意此处添加文字不支持gif
                        new_image_path = new_image_name_path + suffix
                        img_add_text.img_add_text(qa_list[0]["answer"],
                                                  send_path.encode("UTF-8"),
                                                  new_image_path.encode("UTF-8"),
                                                  debug_mode=1)
                        # 注意这里转换为二进制返回
                        if os.path.exists(new_image_path):  # 添加文字只返回唯一一个数据
                            with open(new_image_path, 'rb') as f:
                                image_data = f.read()
                            return_dict["error_code"] = 0
                            return_dict["data"] = {"fight_mode": fight_mode, "image_data": image_data, "new_image_path": new_image_path}  # 注意这里回复的是表情
                            return return_dict
                        else:
                            img_list = []
                            return_dict["data"] = {"fight_mode": fight_mode}  # 注意这里回复的是表情文字
                            return_dict["error_code"] = 6
                            return_dict["error_msg"].append("文本对话式错误:对话添加文字失败")
                            # print(return_dict["error_msg"])
                    else:
                        img_list = []
                        return_dict["data"] = {"fight_mode": fight_mode}
                        return_dict["error_code"] = 7
                        return_dict["error_msg"].append("文本对话式错误:找不到与输入相关的模仿图片可以添加文字")
                        # print(return_dict["error_msg"])
        else:
            img_list = []
            return_dict["error_code"] = 8
            return_dict["data"]["fight_mode"] = fight_mode
            return_dict["error_msg"].append("文本对话式错误:文字对话式没有对话结果")
            # print(return_dict["error_msg"])
    elif fight_mode == 2:
        if image_or_text == 'image':
            _, suffix = os.path.splitext(image_path)
            temp_image_path = new_image_name_path + suffix   # 跟复制体后缀保持一致
            copyfile(image_path.encode("UTF-8"), temp_image_path.encode("UTF-8"))  # 注意这个地方是临时文件
            return_list = similar_image(temp_image_path, loaded_model, image_index, file_index)
            # 寻找最相似的图片，注意这个地方的置信度做了一个转换
            for return_data in return_list:
                img_list.append({"answer": return_data[1], "confidence": 1 - return_data[2]})
            print("图片模仿式解析的相似图片是:\n{}".format(
                "\n".join([img_data["answer"] + "|" + str(img_data["confidence"]) for img_data in img_list])))
            img_list = [temp_img for temp_img in img_list if 0.3 <= temp_img["confidence"] <= 0.8]  # 这个概率待调整0.4-0.8
            if len(img_list) != 0:
                if len(img_list) == 1:
                    send_path = img_list[random.randint(0, len(img_list) - 1)]["answer"]
                else:
                    send_path = img_list[random.randint(0, 1)]["answer"]
                # 在空白处添加"就说像不像文字"
                send_list = ["就说像不像!", "看我像不像!哈哈!"]
                # TODO 注意目前只能回复静态jpg图
                _, suffix = os.path.splitext(send_path)
                new_image_path = new_image_name_path + suffix
                img_add_text.img_add_text(send_list[random.randint(0, len(send_list) - 1)],
                                          send_path.encode("UTF-8"),
                                          new_image_path.encode("UTF-8"),
                                          debug_mode=0)
                # 注意这里转换为二进制返回
                if os.path.exists(new_image_path):
                    with open(new_image_path, 'rb') as f:
                        image_data = f.read()
                    return_dict["error_code"] = 0
                    return_dict["data"] = {"fight_mode": fight_mode, "image_data": image_data, "new_image_path": new_image_path}  # 注意这里回复的是表情
                    return return_dict
                else:
                    return_dict["data"] = {"fight_mode": fight_mode}  # 注意这里回复的是表情文字
                    return_dict["error_code"] = 9
                    return_dict["error_msg"].append("图像模仿式错误：图片模仿式添加文字失败")
                    # print(return_dict["error_msg"])
                    return return_dict
            else:
                return_dict["data"] = {"fight_mode": fight_mode}
                return_dict["error_code"] = 10
                return_dict["error_msg"].append("图像模仿式错误:抱歉，找不到模仿图片")
                # print(return_dict["error_msg"])
                return return_dict
        else:
            return_dict["data"] = {"fight_mode": fight_mode}
            return_dict["error_code"] = 11
            return_dict["error_msg"].append("图像模仿式错误:图片模仿式下没有文字模式")
            # print(return_dict["error_msg"])
            return return_dict

    img_len = len(img_list)
    if img_len > 0:  # 存在有效数据则返回
        # 以下目的是只保留前两个
        if len(img_list) == 1:
            send_path = img_list[random.randint(0, len(img_list) - 1)]["answer"]
        else:
            send_path = img_list[random.randint(0, 1)]["answer"]
        _, suffix = os.path.splitext(send_path)
        new_image_path = new_image_name_path + suffix
        copyfile(send_path.encode("UTF-8"), new_image_path.encode("UTF-8"))
        # 注意这里转换为二进制返回
        with open(new_image_path, 'rb') as f:
            image_data = f.read()
        return_dict["error_code"] = 0
        return_dict["data"] = {"fight_mode": fight_mode, "image_data": image_data, "new_image_path": new_image_path}  # 注意这里回复的是表情
        return return_dict
    else:
        # 文本模式下，如果不存在有效数据，则进一步判定是否是表情文字
        # 如果带有表情，则double表情回应(注意微信的表情是[微笑]这种格式)
        if image_or_text == 'text':
            emoji_pattern = re.compile(u'\[[\u4e00-\u9fa5]*?\]|[\U00010000-\U0010ffff]')
            emoji_list = emoji_pattern.findall(rec_text)
            if len(emoji_list) > 0:
                return_text = "".join(emoji_list) + "".join(emoji_list)
                # itchat.send("@%s：[呲牙]" % msg_from, msg['FromUserName'])
                # itchat.send("%s" % return_text, msg['FromUserName'])
                # print("表情式接招:\n{}\n".format(return_text))
                return_dict["data"] = {"fight_mode": 4, "image_data": return_text}  # 注意这里回复的是表情文字
                return_dict["error_code"] = 0
                return_dict["error_msg"].append("表情式接招")
                return return_dict
        return return_dict


if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "images", "0-dog.gif")
    new_image_name_path = os.path.join(os.path.dirname(__file__), "images", "new_image")
    return_dict = fight_image(fight_mode=0, image_or_text="text", image_path=None, text="放马过来",
                              new_image_name_path=new_image_name_path)
    return_dict = fight_image(fight_mode=1, image_or_text="text", image_path=None, text="放马过来",
                              new_image_name_path=new_image_name_path)
    # 这种组合不存在
    return_dict = fight_image(fight_mode=2, image_or_text="text", image_path=None, text="放马过来",
                              new_image_name_path=new_image_name_path)
    return_dict = fight_image(fight_mode=0, image_or_text="image", image_path=image_path, text=None,
                              new_image_name_path=new_image_name_path)
    return_dict = fight_image(fight_mode=1, image_or_text="image", image_path=image_path, text=None,
                              new_image_name_path=new_image_name_path)
    return_dict = fight_image(fight_mode=2, image_or_text="image", image_path=image_path, text=None,
                              new_image_name_path=new_image_name_path)
