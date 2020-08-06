#!/bin/bash
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname $0); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=/dialog_server/source/eliza_stack/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=/dialog_server/source/eliza_stack/eliza_pretraining_model/chinese_L-12_H-768_A-12
# graph_tmp_dir
export GRAPH_TMP_DIR=${LOCAL_PATH}/tmp
# 训练数据的存储路径
export NLU_DIR=${LOCAL_PATH}/data/nlu
export DATA_DIR=${LOCAL_PATH}/data
# 微调训练模型的存储路径
export NLU_MODEL_FINETUNE_DIR=${LOCAL_PATH}/bert_finetune_models
# 训练模型的存储路径
export NLU_MODEL_TRAIN_DIR=${LOCAL_PATH}/models
# 定义配置文件
export NLU_MODEL_TRAIN_CONFIG_FILE=${LOCAL_PATH}/config.yml
# 定义端口配置文件
export NLU_IN_PORT=5555
export NLU_OUT_PORT=5556
echo "首先初始化conda" && conda --v && conda init bash && conda deactivate && echo "初始化conda完毕"
echo "加载pybot虚拟环境" && conda activate pybot && python --version && echo "pybot虚拟环境加载完毕"
echo "正式训练---------------------------------------------------------------------------------------"
echo "正式训练NLU--------------"

echo "遍历模型文件，找到最新的模型"
max="0"
temp="0"
for meta_file in `ls ${NLU_MODEL_FINETUNE_DIR}/model.ckpt-*.meta` #注意此处这是两个反引号，表示运行系统命令
do
    temp=${meta_file##*model.ckpt-}
    temp=${temp%.meta*}
    if [[ "${temp}" > "${max}" ]];then
        max=${temp}
    fi
done
ckpt_name="model.ckpt-"${max}
echo ${ckpt_name}
echo "关闭DOMAIN-bert-as-service"
ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
echo "开启DOMAIN-bert-as-service"
# 加载微调模型
#bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
#-graph_tmp_dir ${GRAPH_TMP_DIR} \
#-tuned_model_dir=${NLU_MODEL_FINETUNE_DIR} -ckpt_name=${ckpt_name} \
#-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
#不加载微调模型
bert-serving-start -num_worker=4 -model_dir=${BERT_BASE_DIR} \
-graph_tmp_dir ${GRAPH_TMP_DIR} \
-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
sleep 20s
echo "已开启DOMAIN-bert-as-service"

rasa train nlu -u ${NLU_DIR} -c ${NLU_MODEL_TRAIN_CONFIG_FILE} --out ${NLU_MODEL_TRAIN_DIR}
echo "关闭DOMAIN-bert-as-service"
ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
echo "训练NLU完毕--------------"

echo "正式训练完毕--------------------------------------------------------------------------------------"
