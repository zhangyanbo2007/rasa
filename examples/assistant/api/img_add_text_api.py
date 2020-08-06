#!/opt/conda/envs/pybot/bin/python
# coding=utf-8
from PIL import Image
import numpy as np
import time
from collections import Counter
import cv2
import os
import json
from PIL import ImageFont, ImageDraw, Image

EDGE_LENGTH = 5
FONT_MIN_SIZE = 10
FONT_MAX_SIZE = 150
FONT_DEBUG_COLOR = (255, 0, 0)
FONT_BLACK_COLOR = (0, 0, 0)
FONT_WHITE_COLOR = (255, 255, 255)
FONT_LIGHT_BLACK_COLOR = (0, 0, 0)
FONT_LIGHT_WHITE_COLOR = (255, 255, 255)
# FONT_LIGHT_BLACK_COLOR = (88, 87, 86)
# FONT_LIGHT_WHITE_COLOR = (245, 245, 245)
RATIO = 5  # 设置缩放比例
ZOOM_SIZE = 40  # 设置目标缩放尺寸
FONTPATH = "/dialog_server/source/bot_application/api/config/simsun.ttc"  # 先固定简体字（后续可扩充至别的汉字类型）
BW_THRESHOLD = 128
time_dict = {}
font_flag = 0


class MaxRectangle(object):
    # 求内接矩阵的解决方案
    def maximalRectangle(self, matrix):
        """
        :type matrix: List[List[str]]
        :rtype: int
        """
        # if not any(matrix):
        if matrix == [] or len(matrix) == 0:
            return 0
        M, N = len(matrix), len(matrix[0])
        height = [0] * N
        max_res = 0
        column_start = 0
        column_end = 0
        row_start = 0
        row_end = 0
        for row_num, row in enumerate(matrix):
            for i in range(N):
                if not row[i]:
                    height[i] = 0  # 遇到0就清零
                else:
                    height[i] += 1  # 连续就加1
            (index_start, index_end, valid_h, res) = self.maxRectangleArea(height)
            if res > max_res:
                max_res = res
                column_start = index_start
                column_end = index_end
                row_end = row_num
                row_start = row_num - valid_h + 1
        return row_start, row_end, column_start, column_end, max_res

    def maxRectangleArea(self, height):
        if not height:
            return 0
        res = 0
        index_start = 0
        index_end = 0
        valid_h = 0
        stack = list()
        temp_height = height + [0]
        for i in range(len(temp_height)):
            h_cur = temp_height[i]
            while stack and h_cur < temp_height[stack[-1]]:  # 如果当前索引的高度小于栈顶元素的高度，出栈
                h = temp_height[stack[-1]]  # 获取栈顶元素的高度
                stack.pop()
                w = i if not stack else i - stack[-1] - 1  # 如果栈顶元素为空，则宽度为当前索引，如果栈顶元素不为空，则宽度等于
                if w*h > res:
                    res = w*h
                    valid_h = h
                    index_start = i-w
                    index_end = i-1  # 右边界
            stack.append(i)
        return index_start, index_end, valid_h, res


class ImgAddText(object):
    global time_dict
    global EDGE_LENGTH
    global FONT_MIN_SIZE
    global FONT_MAX_SIZE
    global FONT_DEBUG_COLOR
    global FONT_BLACK_COLOR
    global FONT_WHITE_COLOR
    global RATIO  # 设置缩放比例
    global ZOOM_SIZE  # 设置目标缩放尺寸
    global FONTPATH  # 先固定简体字（后续可扩充至别的汉字类型）
    global BW_THRESHOLD
    global time_dict
    global font_flag
    def img_bw_detect(self, image, new_bw_path=None, resize_width=48, resize_height=48):
        """
        黑白二值化图像，并返回图像结果,注意这个地方的image是二进制路径
        :param img:
        :return:
        """
        # 自定义灰度界限，小于这个值为黑色，大于这个值为白色，尽可能阈值点接近白色，也就是白色苛刻一些
        table = []
        for i in range(256):
            if i < BW_THRESHOLD:  # 黑色
                table.append(0)
            else:
                table.append(1)  # 白色
        img = Image.open(image)
        width, height = img.size
        new_img = img.resize((resize_width, resize_height))  # 注意方向，这里是宽高
        Img = new_img.convert('L')  # 先转化为灰度图像模式
        photo = Img.point(table, '1')
        # 测试用，完毕后要关闭
        if new_bw_path:
            _, fullflname = os.path.split(image)
            new_bw_name = "bw_".encode("UTF-8") + fullflname
            photo.save(os.path.join(new_bw_path.decode(), "temp.jpg")) #  测试用 缩放之后，黑白二值化后的图像，调试接口，正常状态下关闭
            os.rename(os.path.join(new_bw_path.decode(), "temp.jpg").encode("UTF-8"), os.path.join(new_bw_path, new_bw_name))
        data = np.matrix(photo.getdata(), dtype=np.bool)
        matrix = np.reshape(data, (resize_height, resize_width))  # 注意方向，这里是行列
        bin_data = np.bincount(matrix.flat)
        if len(bin_data) == 2 and bin_data[0] > bin_data[1]:
            matrix = np.logical_not(matrix)  # 黑白反转
            black_or_white = "black"  # 黑色区域是1
        else:
            black_or_white = "white"  # 白色区域是1
        return black_or_white, matrix

    def img_add_text(self, img_text, image, new_image, debug_mode=0):
        """
        提取图像空白区，添加文字，生成新图像,注意为了兼容中文，这里的图片输入为ENCODE("utf-8")
        :param image:
        :param img_text:
        :param new_image:
        :return:
        """
        t_start = time.time()
        maximalRectangleSolution = MaxRectangle()
        # 测试
        # matrix = [
        #           [0, 1, 0, 1, 0, 1],
        #           [0, 1, 1, 1, 1, 0],
        #           [1, 1, 1, 1, 1, 0],
        #           [1, 0, 0, 1, 0, 1]
        # ]
        # height = [2, 1, 5, 6, 2, 3]
        # height = [5, 5, 5, 5, 5, 5]
        # res = maximalRectangleSolution.maxRectangleArea(height)
        img = Image.open(image)
        width, height = img.size
        # print("图片宽高是{},{}".format(width, height))  # 测试用，完了之后要关闭
        # set_width = 64 # 设置成固定大小方式
        # set_height = 64 # 设置成固定大小方式
        # 原则上缩放到32*32这样的比例
        ratio = (width*height/(ZOOM_SIZE ** 2)) ** 0.5
        resize_width = int(width/ratio)
        resize_height = int(height/ratio)
        if debug_mode == 1:  # 这个路径暂时是固定的
            new_bw_path = "/dialog_server/database/images/images_add_text_debug/images_bw".encode("UTF-8")
        else:
            new_bw_path = None
        black_or_white, matrix = self.img_bw_detect(image, new_bw_path, resize_width, resize_height)  # 比例控制方式
        if black_or_white == "black":
            font_color = FONT_WHITE_COLOR
            font_flag = 0
        elif black_or_white == "white":
            font_color = FONT_BLACK_COLOR
            font_flag = 1
        # matrix, ratio_width, ratio_height = self.img_bw_detect(image, set_width, set_height)  # 设置成固定大小方式
        matrix_list = matrix.tolist()  # 矩阵转化为list,其实可以不用转换，这块后续可以优化
        t_pre = time.time()  # 计算时间
        room_row_start, room_row_end, room_column_start, room_column_end, max_res = maximalRectangleSolution.maximalRectangle(matrix_list)  # 求内接矩形
        # 注意这个地方换算，起始位置顶对其，末端位置尾对齐，这样才能保证完全映射,注意宽高别除错了
        row_start = int(room_row_start*height/resize_height)
        row_end = int((room_row_end+1)*height/resize_height-1)
        column_start = int(room_column_start*width/resize_width)
        column_end = int((room_column_end+1)*width/resize_width-1)
        t_detect = time.time()  # 计算时间
        # print(row_start, row_end, column_start, column_end, max_res)

        # (如何根据空白区域大小填充合适的问题的问题？)
        # 1 空白区的宽大于高则输出横向字体，宽小于高则输出竖向字体
        # 2 字体有长度限制，然后有大小限制，优先一行，一行容纳不了，缩小文字到两行，依次类推
        # 3 如果最小的字体都满足不了用户的文本长度，则随机在图片上添加文字（固定文本然）
        # bk_img = cv2.imdecode(np.fromfile(image, dtype=np.uint8), 0)
        bk_img = cv2.imread(image.decode())
        if bk_img is None:
            if debug_mode == 1:  # 这个路径暂时是固定的
                s = image.decode()
                with open("/dialog_server/database/images/images_add_text_debug/images_add_text_debug.txt", "a+", encoding="UTF-8") as f:
                    f.write(s + "\n")
            return
        img_pil = Image.fromarray(bk_img)
        draw = ImageDraw.Draw(img_pil)

        # 设置需要显示的字体
        # 注意空白要留边，目前留8个像素的边
        if column_end > EDGE_LENGTH and row_end > EDGE_LENGTH:
            if (column_end - column_start + 1) > (2*EDGE_LENGTH+FONT_MIN_SIZE) and \
                    (row_end - row_start + 1) > (2*EDGE_LENGTH+FONT_MIN_SIZE):
                useful_column_start = column_start + EDGE_LENGTH
                useful_column_end = column_end - EDGE_LENGTH
                useful_row_start = row_start + EDGE_LENGTH
                useful_row_end = row_end - EDGE_LENGTH
            else:
                useful_column_start = column_start
                useful_column_end = column_end
                useful_row_start = row_start
                useful_row_end = row_end
            useful_width = useful_column_end - useful_column_start + 1
            useful_height = useful_row_end - useful_row_start + 1

            if useful_width >= useful_height:
                font_type = "horizontal"  # 横向字体
            else:
                font_type = "vertical"  # 竖向字体,竖向字体判断简单些，仅判断单竖行字体
        else:
            font_type = "default"

        if font_type == "horizontal":  # 横向字体
            text_char_num = len(img_text.encode("gbk"))  # 此处为了求字体所占字符个数
            font_max_size = (useful_width * useful_height / (text_char_num / 2)) ** 0.5  # 求字体大小
            #  假如行有row_num,那么可能存在row_num*font_size*font_size的空间浪费
            #  而row_num = int(font_width / useful_width) + (0 if font_width % useful_width == 0 else 1)  # 分成行数
            # 判断(row_num+text_char_num)*font_size*font_size小于useful_width * useful_height即可
            if int(font_max_size) >= FONT_MAX_SIZE:  # 先将一级
                font_max_size = FONT_MAX_SIZE
            if int(font_max_size) >= useful_height:  #  首先先降一截
                font_size = useful_height*4/5
            else:
                font_size = font_max_size
            if int(font_size) > FONT_MIN_SIZE:
                for font_size_index in range(int(font_size), FONT_MIN_SIZE-1, -1):
                    row_num = int(text_char_num*font_size_index / (2*useful_width)) + \
                                 (0 if text_char_num*font_size_index % (2*useful_width) == 0 else 1)  # 注意这里是拿宽度除以高度，分成列数
                    if row_num*font_size_index > useful_height:  # 越界则继续放小字体
                        continue
                    row_char_length = int(useful_width / (font_size_index/2))  # 每行允许的最大字符数(全部为英文时长度最大)
                    img_text_temp = img_text
                    for row_index in range(row_num):
                        # 依次遍历求需求面积
                        char_num = 0  # 字符个数
                        for word_index, img_word in enumerate(img_text_temp):
                            char_num = char_num + len(img_word.encode("gbk"))
                            if char_num >= row_char_length:
                                if char_num > row_char_length:  # 这种情况下每行回退一次再推出
                                    word_index = word_index - 1
                                break
                        img_text_temp = img_text_temp[word_index + 1:]
                    if len(img_text_temp) == 0:  # 正常应该遍历完，如果没有遍历完说明这个尺寸不合适
                        break
                font_size = font_size_index
            if font_size <= FONT_MIN_SIZE:  # 字体太小了，那么字体默认走32大小，有效空间按整个图片的空间计算,起始位置也按开头计算
                font_type = "default"
            else:
                font_size = int(font_size)
        elif font_type == "vertical":
            text_char_num = len(img_text)  # 竖排文字每个字符占一格，因此直接按长度给出，这里的字符与横排不同，1个汉字，1个字母均是一格字符
            font_max_size = (useful_width * useful_height / text_char_num) ** 0.5  # 如果按一字排开，此时的字体最大，求最大字体，这个只是我的直觉，待分析
            # TODO:这个地方还有待改善，假如列有column_num,那么可能存在column_num*font_size*font_size的空间浪费
            # 而column_num = int(font_width / useful_height) + (0 if font_width % useful_height == 0 else 1)  # 注意这里是拿宽度除以高度，分成列数
            # 判断(column_num+text_char_num)*font_size*font_size小于useful_width * useful_height即可
            if int(font_max_size) >= FONT_MAX_SIZE:  # 先将一级
                font_max_size = FONT_MAX_SIZE
            if int(font_max_size) >= useful_width:  # 首先先降一截
                font_size = useful_width*4/5
            else:
                font_size = font_max_size
            if int(font_size) > FONT_MIN_SIZE:
                for font_size_index in range(int(font_size), FONT_MIN_SIZE-1, -1):
                    column_num = int(text_char_num*font_size_index / useful_height) + \
                                 (0 if text_char_num*font_size_index % useful_height == 0 else 1)  # 注意这里是拿宽度除以高度，分成列数
                    if column_num*font_size_index > useful_width:  # 越界则继续放小字体
                        continue
                    column_char_length = int(useful_height / font_size_index)  # 每列允许的最大字符数
                    img_text_temp = img_text
                    for column_index in range(column_num):
                        # 依次遍历求需求面积
                        char_num = 0  # 字符个数
                        for word_index, img_word in enumerate(img_text_temp):
                            char_num = char_num + len(img_word)
                            if char_num >= column_char_length:
                                if char_num > column_char_length:  # 这种情况下每行回退一次再推出
                                    word_index = word_index - 1
                                break
                        img_text_temp = img_text_temp[word_index + 1:]
                    if len(img_text_temp) == 0:  # 正常应该遍历完，如果没有遍历完说明这个尺寸不合适
                        break
                font_size = font_size_index
            if font_size <= FONT_MIN_SIZE:  # 字体太小了，那么字体默认走32大小，有效空间按整个图片的空间计算,起始位置也按开头计算
                font_type = "default"
            else:
                font_size = int(font_size)

        if font_type == "default":
            text_char_num = len(img_text.encode("gbk"))  # 此处为了求字体所占字符个数
            useful_column_start = EDGE_LENGTH
            useful_row_start = EDGE_LENGTH
            useful_width = width - (EDGE_LENGTH * 2)
            useful_height = height - (EDGE_LENGTH * 2)
            useful_column_end = useful_column_start + useful_width - 1
            useful_row_end = useful_row_start + useful_height - 1
            font_size = (useful_width * useful_height / (text_char_num / 2)) ** 0.5  # 求字体大小
            if int(font_size) >= FONT_MAX_SIZE:  # 先将一级
                font_size = FONT_MAX_SIZE
            if int(font_size) >= useful_height:  # 首先先降一截
                font_size = useful_height*4/5
            if int(font_size) > FONT_MIN_SIZE:
                for font_size_index in range(int(font_size), FONT_MIN_SIZE-1, -1):
                    row_num = int(text_char_num * font_size_index / (2 * useful_width)) + \
                              (0 if text_char_num * font_size_index % (2 * useful_width) == 0 else 1)  # 注意这里是拿宽度除以高度，分成列数
                    if row_num*font_size_index > useful_height:  # 越界则继续放小字体
                        continue
                    row_char_length = int(useful_width / (font_size_index/2))  # 每行允许的最大字符数(全部为英文时长度最大)
                    img_text_temp = img_text
                    for row_index in range(row_num):
                        # 依次遍历求需求面积
                        char_num = 0  # 字符个数
                        for word_index, img_word in enumerate(img_text_temp):
                            char_num = char_num + len(img_word.encode("gbk"))
                            if char_num >= row_char_length:
                                if char_num > row_char_length:  # 这种情况下每行回退一次再推出
                                    word_index = word_index - 1
                                break
                        img_text_temp = img_text_temp[word_index + 1:]
                    if len(img_text_temp) == 0:  # 正常应该遍历完，如果没有遍历完说明这个尺寸不合适
                        break
                font_size = font_size_index
            if font_size <= FONT_MIN_SIZE:  # 字体太小了，那么字体默认走32大小，有效空间按整个图片的空间计算,起始位置也按开头计算
                font_type = "default"
            else:
                font_size = int(font_size)
            if font_flag == 0:
                font_color = FONT_LIGHT_WHITE_COLOR
            elif font_flag == 1:
                font_color = FONT_LIGHT_BLACK_COLOR
        if font_type == "horizontal" or font_type == "default":  # 竖向字体,竖向字体判断简单些，仅判断单竖行字体
            font = ImageFont.truetype(FONTPATH, font_size)
            font_width, font_height = font.getsize(img_text)

            row_num = int(font_width / useful_width) + (0 if font_width % useful_width == 0 else 1)  # 分成行数
            row_char_length = int(useful_width / (font_size/2))  # 每行允许的最大字符数
            point_x = useful_column_start
            point_y = useful_row_start

            # # 边缘画框，调试用
            # draw.polygon([(useful_column_start, useful_row_start), (useful_column_end, useful_row_start),
            #               (useful_column_end, useful_row_end), (useful_column_start, useful_row_end)], fill=FONT_DEBUG_COLOR)
            # draw.rectangle((useful_column_start, useful_row_start, useful_column_end, useful_row_end), outline=FONT_DEBUG_COLOR)

            for row in range(row_num):  # 逐行显示文本 原则：如果单行文本则居中显示，如果多行文本则顶格显示
                if row_num == 1:  # 居中显示文本
                    point_x = int(point_x + (useful_width - font_width)/2)
                    point_y = int(point_y + (useful_height - font_height) / 2)
                    valid_img_text = img_text
                    draw.text((point_x, point_y), valid_img_text, font=font, fill=font_color)
                else:
                    char_num = 0  # 字符个数
                    for word_index, img_word in enumerate(img_text):
                        char_num = char_num + len(img_word.encode("gbk"))
                        if char_num >= row_char_length:
                            if char_num > row_char_length:  # 这种情况下每行回退一次再推出
                                word_index = word_index - 1
                            break
                    valid_img_text = img_text[:word_index + 1]
                    img_text = img_text[word_index + 1:]
                    draw.text((point_x, point_y), valid_img_text, font=font, fill=font_color)
                    point_y = point_y + font_size  # 文本起始位置Y
        elif font_type == "vertical":  # 竖向字体,竖向字体判断简单些，仅判断单竖行字体
            font = ImageFont.truetype(FONTPATH, font_size)
            font_width, font_height = font.getsize(img_text)

            column_num = int(font_width / useful_height) + (0 if font_width % useful_height == 0 else 1)  # 注意这里是拿宽度除以高度，分成列数
            column_char_length = int(useful_height / font_size)  # 每列允许的最大字符数
            point_x = useful_column_start
            point_y = useful_row_start

            # # 边缘画框，调试用
            # draw.polygon([(useful_column_start, useful_row_start), (useful_column_end, useful_row_start),
            #               (useful_column_end, useful_row_end), (useful_column_start, useful_row_end)], fill=FONT_DEBUG_COLOR)
            # draw.rectangle((useful_column_start, useful_row_start, useful_column_end, useful_row_end), outline=FONT_DEBUG_COLOR)

            for column in range(column_num):  # 逐列显示文本 原则：如果单列文本则居中显示，如果多列文本则顶格显示
                if column_num == 1:  # 居中显示文本
                    point_x = int(point_x + (useful_width - font_size)/2)
                    point_y = int(point_y + (useful_height - font_size*text_char_num) / 2)
                    valid_img_text = img_text
                    down = 0
                    for k, s2 in enumerate(valid_img_text):
                        draw.text((point_x, point_y + down), s2, font_color, font=font)
                        down = down + font_size
                else:
                    char_num = 0  # 字符个数
                    for word_index, img_word in enumerate(img_text):
                        char_num = char_num + len(img_word)
                        if char_num >= column_char_length:
                            if char_num > column_char_length:  # 这种情况下每行回退一次再推出
                                word_index = word_index - 1
                            break
                    valid_img_text = img_text[:word_index + 1]
                    img_text = img_text[word_index + 1:]
                    down = 0
                    for k, s2 in enumerate(valid_img_text):
                        draw.text((point_x, point_y + down), s2, font_color, font=font)
                        down = down + font_size
                    point_x = point_x + font_size  # 文本起始位置Y

        bk_img = np.array(img_pil)
        cv2.imwrite(new_image.decode(), bk_img)
        t_end = time.time()  # 计算时间
        # print("图片预处理时间{},识别矩形时间{}".format(t_pre - t_start, t_detect - t_pre))
        # print("总的处理时间{},文字处理时间{}".format(t_end - t_start, t_end - t_detect))
        time_dict[str(t_end - t_start)] = [new_image.decode(),
                                           "预处理时间" + str(t_pre - t_start),
                                           "识别矩形时间" + str(t_detect - t_pre),
                                           "文字处理时间" + str(t_end - t_detect)]
        if debug_mode == 1:  # 这个路径暂时是固定的
            with open("/dialog_server/database/images/images_add_text_debug/images_add_text_time.json", "w", encoding="UTF-8") as f:
                json.dump(time_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        # # 字体测试
        # font = ImageFont.truetype(FONTPATH, 32)  # 经测试，字号实际上就是汉字字体的宽度和高度，其中宽度是衡量标准
        # img_text = "eewwedee"
        # for font_size in range(10, 100, 2):
        #     font = ImageFont.truetype(FONTPATH, font_size)
        #     font_width, font_height = font.getsize(img_text)
        #     print("字号{}对应的宽是{},高是{}".format(font_size, font_width, font_height))
        # cv2.imshow("add_text", bk_img)
        # cv2.waitKey()


if __name__ == '__main__':
    img_text = "他呀，说来他跟小布丁还有一腿呢"
    img_add_text = ImgAddText()

    image = "images/123.jpg"
    new_image = "images/result.jpg"

    img_add_text.img_add_text(img_text, image.encode("UTF-8"), new_image.encode("UTF-8"), debug_mode=1)  # 测试用
    # img_add_text.img_add_text(img_text, image1.encode("UTF-8"), new_image1.encode("UTF-8"), 1)  # 测试用
    # img_add_text.img_add_text(img_text, image2.encode("UTF-8"), new_image2.encode("UTF-8"), 1)  # 测试用
    # img_add_text.img_add_text(img_text, image3.encode("UTF-8"), new_image3.encode("UTF-8"), 1)  # 测试用

    # for root, dir_list, file_list in os.walk("/dialog_server/database/images/images_templete".encode("UTF-8")):
    #     for num, file in enumerate(file_list):
    #         file_path = os.path.join(root, file)
    #         newfile_path = os.path.join("/dialog_server/database/images/images_templete_add_text".encode("UTF-8"),
    #                                     ("new_" + file.decode()).encode("UTF-8"))
    #         try:
    #             if num == 1:
    #                 print("ss")
    #             img_add_text.img_add_text(img_text, file_path, newfile_path,
    #                                       "/dialog_server/database/images/images_templete_bw_test".encode("UTF-8"))
    #         except Exception as e:  # 这就让我懵逼了
    #             pass
