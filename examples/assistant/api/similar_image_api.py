#!/usr/bin/env python
"""
Weather kg_data is provided by https://www.seniverse.com/,
below code are modified from https://github.com/seniverse/seniverse-api-demos

NOTE: user need provide shell environment `SENIVERSE_KEY` and `SENIVERSE_UID`\
 to using this API
"""
import logging
import os
import json
import time
import sys

import h5py
import numpy as np

from annoy import AnnoyIndex
from keras import optimizers
from keras.layers import Dense, BatchNormalization, Activation, Dropout
from keras.losses import cosine_proximity
from keras.preprocessing import image
from keras.models import Model
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input

logger = logging.getLogger()
logger.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(message)s")    # output format
sh = logging.StreamHandler(stream=sys.stdout)    # output to standard output
sh.setFormatter(format)
logger.addHandler(sh)

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def generate_path(folder):
    file_names = [fold for fold in os.listdir(folder.encode("UTF-8"))]
    paths_list = []
    for cl in file_names:
        path = os.path.abspath(os.path.join(folder.encode("UTF-8"), cl))
        if os.path.getsize(path) != 0:
            paths_list.append(path)
        else:
            os.remove(path)
    return paths_list


def load_headless_pretrained_model():
    """
    Loads the pretrained version of VGG with the last layer cut off
    :return: pre-trained headless VGG16 Keras Model
    """
    print("Loading headless pretrained model...")#zyb这个后面会从keras下载
    pretrained_vgg16 = VGG16(weights='imagenet', include_top=True)
    model = Model(inputs=pretrained_vgg16.input,
                  outputs=pretrained_vgg16.get_layer('fc2').output)
    return model


def save_features_index(index_folder, model_folder, n_trees=1000, dims=4096):
    """
    Takes in an array of image paths, and a trained model.
    Returns the activations of the last layer for each image
    :param image_paths: array of image paths
    :param model: pre-trained model
    :return: array of last-layer activations, and mapping from array_index to file_path
    """
    paths = generate_path(index_folder)
    file_mapping = {i: f.decode() for i, f in enumerate(paths)}  # 注意这个包含中文字符串str
    with open(os.path.join(model_folder, 'index.json'), 'w', encoding="utf-8") as index_file:
        json.dump(file_mapping, index_file, ensure_ascii=False, indent=2, sort_keys=True)  # 注意此处是utf-8存储，因此中文打开是字节
    print("filepath saved")

    print("加载VGG16模型")
    model = load_headless_pretrained_model()
    print("Generating features...")
    start = time.time()
    # images = np.zeros(shape=(len(paths), 224, 224, 3), dtype=np.uint8)
    # images = []#先不初始化

    images_features = []
    feature_index = AnnoyIndex(dims, metric='angular')
    # We load all our dataset in memory because it is relatively small
    for i, f in enumerate(paths):
        try:
            img = image.load_img(f, target_size=(224, 224))  # 注意这个地方要编码utf-8
        except Exception as e:
            pass
        # img = image.load_img(f, target_size=(224, 224))  # 注意这个地方要编码utf-8
        x_raw = image.img_to_array(img)
        x_expand = np.expand_dims(x_raw, axis=0)
        # images[i, :, :, :] = x_expand

        # logger.info("%s images loaded" % len(images))
        # inputs = preprocess_input(images)
        inputs = preprocess_input(x_expand)
        # logger.info("Images preprocessed")
        images_feature = model.predict(inputs)
        images_features.append(images_feature[0])
        # logger.warn("Inference done, %s Generation time" % (end - start))
        feature_index.add_item(i, images_feature[0])

    print("Saving feature index...")
    np.save(os.path.join(model_folder, 'feat.npy'), images_features)  # 先保存图像原始特征信息

    print("Saving feature AnnoyIndex...")
    feature_index.build(n_trees)
    feature_index.save(os.path.join(model_folder, "feat.ann"))
    end = time.time()
    print("Inference done, %s Generation time" % (end - start))


def generate_features(image_paths, model):
    """
    Takes in an array of image paths, and a trained model.
    Returns the activations of the last layer for each image
    :param image_paths: array of image paths
    :param model: pre-trained model
    :return: array of last-layer activations, and mapping from array_index to file_path
    """
    # print("Generating features...")
    # start = time.time()
    images = np.zeros(shape=(len(image_paths), 224, 224, 3))
    file_mapping = {i: f for i, f in enumerate(image_paths)}#注意这个包含中文字符串str

    # We load all our dataset in memory because it is relatively small
    for i, f in enumerate(image_paths):
        img = image.load_img(f.encode("utf-8"), target_size=(224, 224))  # 注意这个地方要编码utf-8
        x_raw = image.img_to_array(img)
        x_expand = np.expand_dims(x_raw, axis=0)
        images[i, :, :, :] = x_expand

    logger.info("%s images loaded" % len(images))
    inputs = preprocess_input(images)
    logger.info("Images preprocessed")
    images_features = model.predict(inputs)
    # end = time.time()
    # logger.info("Inference done, %s Generation time" % (end - start))
    return images_features, file_mapping


def get_vec(input_image, loaded_model):
    image_paths = [input_image]
    search_vec, _ = generate_features(image_paths, loaded_model)
    return search_vec[0]


def search_index_by_value(vector, image_index, file_index, top_n=10):
    """
    Search an Annoy index by value, return n nearest items
    :param vector: the index of our item in our array of features
    :param image_index: an Annoy tree of indexed features
    :param file_index: mapping from indices to paths/names
    :param top_n: how many items to return
    :return: an array of [index, item, distance] of size top_n
    """
    distances = image_index.get_nns_by_vector(vector, top_n, include_distances=True)
    return [[a, file_index[a], distances[1][i]] for i, a in enumerate(distances[0])]


def load_features_index(model_path, dims=4096):
    """
    Loads features and file_item mapping from disk
    :param features_filename: path to load features from
    :param mapping_filename: path to load mapping from
    :return: feature array and file_item mapping to disk

    """
    # print("Loading features...")
    feature_index = AnnoyIndex(dims, metric='angular')
    feature_index.load(os.path.join(model_path, "feat.ann"))

    with open(os.path.join(model_path, "index.json"), encoding="UTF-8") as f:
        index_str = json.load(f)  # json加载自动转化为字符串
        file_index = {int(k): str(v) for k, v in index_str.items()}
    return feature_index, file_index


def similar_image_init(model):
    """
    模型初始化
    :param model:
    :return:
    """
    print("加载VGG16模型")
    loaded_model = load_headless_pretrained_model()
    image_index, file_index = load_features_index(model)
    return loaded_model, image_index, file_index


def similar_image(input_image, loaded_model, image_index, file_index, top_n=5):
    """
    相似图接口
    :param input_image:支持任意图片输入，但貌似目前不支持中文
    :param loaded_model:
    :param image_index:
    :param file_index:
    :param top_n:
    :return: 返回最相似的图片列表(注意目前不支持gif动图回复s)
    """
    if not os.path.exists(input_image):
        return []
    start = time.time()
    search_vec = get_vec(input_image, loaded_model)
    results = search_index_by_value(search_vec, image_index, file_index, top_n)
    # for result in results:
    #     kg_data = [str(kg_data) for kg_data in result]
    #     print(" ".join(kg_data) + "\n")
    end = time.time()
    logger.info("Inference done, %s Generation time" % (end - start))
    return results


if __name__ == '__main__':
    # save_features_index("/dialog_server/database/images/images_clear_text", "/dialog_server/source/eliza_stack/fight_images_models")
    loaded_model, image_index, file_index = similar_image_init("/dialog_server/source/eliza_stack/fight_images_models")
    results = similar_image("fightimage/0-dog.gif", loaded_model, image_index, file_index)
    for result in results:
        data = [str(data) for data in result]
        print(" ".join(data) + "\n")
    sys.stdout.write("> ")
    sys.stdout.flush()
    input_data = sys.stdin.readline().strip()
    while input_data:
        results = similar_image(input_data, loaded_model, image_index, file_index)
        for result in results:
            data = [str(data) for data in result]
            print(" ".join(data) + "\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
        input_data = sys.stdin.readline().strip()

