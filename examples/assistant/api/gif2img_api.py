from PIL import Image
import os
import shutil
import time


def gif2img(image_path, new_image_path):
    """
    读取gif图片，然后生成对应的图像帧，注意此处为了兼容中文，用的是encode("UTF-8")
    :param image_path:
    :param new_image_path:注意这里是文件夹路径
    :return:
    """
    im = Image.open(image_path)
    fpath, fname_all = os.path.split(image_path)
    fname, fename = os.path.splitext(fname_all)
    # 创建存放每帧图片的文件夹
    if not os.path.exists(os.path.join(new_image_path, fname)):
        os.mkdir(os.path.join(new_image_path, fname))
    try:
        while True:
            start = time.time()
            # 保存当前帧图片
            current = im.tell()
            # im.save(os.path.join("./gif_images", pngDir, str(current) + '.png').encode("UTF-8"))
            im.save(os.path.join(new_image_path.decode(), 'temp.png'))
            shutil.move(os.path.join(new_image_path.decode(), 'temp.png').encode("UTF-8"),
                        os.path.join(new_image_path, fname, (str(current) + '.png').encode("UTF-8")))
            yield os.path.join(new_image_path, fname, (str(current) + '.png').encode("UTF-8"))
            # 获取下一帧图片
            im.seek(current + 1)
    except Exception as e:
        over = time.time()
        # print("总时间{}".format(over-start))
        # print("识别结束")


if __name__ == "__main__":
    gifFileName = '456.gif'
    for m in gif2img(gifFileName):
        print(m)
        time.sleep(2)

    # # 使用Image模块的open()方法打开gif动态图像时，默认是第一帧
    # im = Image.open(gifFileName.encode("UTF-8"))
    # pngDir = gifFileName[:-4]
    # # 创建存放每帧图片的文件夹
    # if not os.path.exists(os.path.join("./gif_images", pngDir)):
    #     os.mkdir(os.path.join("./gif_images", pngDir))
    # try:
    #     while True:
    #         # 保存当前帧图片
    #         current = im.tell()
    #         # im.save(os.path.join("./gif_images", pngDir, str(current) + '.png').encode("UTF-8"))
    #         im.save(os.path.join("./gif_images", pngDir, str(current) + '.png'))
    #         # 获取下一帧图片
    #         im.seek(current + 1)
    # except Exception as e:
    #     print("异常")
    # # for i, frame in enumerate(iter_frames(im)):
    # #     frame.save('圣诞节没人约我吗.png',**frame.info)
