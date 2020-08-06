#!/bin/bash
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname $0); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=/dialog_server/source/eliza_stack/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=/dialog_server/source/eliza_stack/eliza_pretraining_model/chinese_L-12_H-768_A-12
# 训练数据的存储路径
export DOMAIN_DIR=${LOCAL_PATH}/kg_data/domain_data
export NLU_DIR=${LOCAL_PATH}/kg_data/intent_data
# 微调训练模型睤存储路径
export DOMAIN_MODEL_FINETUNE_DIR=${LOCAL_PATH}/models/domain/bert/bert_finetune_models
export INTENT_MODEL_FINETUNE_DIR=${LOCAL_PATH}/models/intent/bert/bert_finetune_models
# 训练模型的存储路径
export DOMAIN_MODEL_TRAIN_DIR=${LOCAL_PATH}/models/domain/bert/bert_train_models
export INTENT_MODEL_TRAIN_DIR=${LOCAL_PATH}/models/intent/bert/bert_train_models
# 定义配置文件
export DOMAIN_MODEL_TRAIN_CONFIG_FILE=${LOCAL_PATH}/configs/domain_embedding_config_bert_estimator.yml
export INTENT_MODEL_TRAIN_CONFIG_FILE=${LOCAL_PATH}/configs/nlu_embedding_config_bert_estimator.yml
# 定义端口配置文件
export DOMAIN_IN_PORT=5555
export DOMAIN_OUT_PORT=5556
export INTENT_IN_PORT=4555
export INTENT_OUT_PORT=4556
echo "首先初始化conda" && conda --v && conda init bash && conda deactivate && echo "初始化conda完毕"
echo "加载pybot虚拟环境" && conda activate pybot && python --version && echo "pybot虚拟环境加载完毕"
echo "加载DOMAIN-BERT-AS-SERVICE"
echo "遍历模型文件，找到最新的模型"
max="0"
temp="0"
for meta_file in `ls ${DOMAIN_MODEL_FINETUNE_DIR}/model.ckpt-*.meta` #注意此处这是两个反引号，表示运行系统命令
do
    temp=${meta_file##*model.ckpt-}
    temp=${temp%.meta*}
    if [[ "${temp}" > "${max}" ]];then
        max=${temp}
    fi
done
ckpt_name="model.ckpt-"${max}
echo ${ckpt_name}
echo "开启DOMAIN-bert-as-service"
bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
-tuned_model_dir=${DOMAIN_MODEL_FINETUNE_DIR} -ckpt_name=${ckpt_name} \
-port ${DOMAIN_IN_PORT} -port_out ${DOMAIN_OUT_PORT} &
echo "已开启DOMAIN-bert-as-service"
for file in `ls ${NLU_DIR}` #注意此处这是两个反引号，表示运行系统命令
do
    if [[ "`ls -A ${NLU_DIR}/${file}`" != "" ]]; then
          echo "意图数据${file}存在，可提供bert服务"
          echo "遍历模型文件，找到最新的模型"
          max="0"
          temp="0"
          for meta_file in `ls ${INTENT_MODEL_FINETUNE_DIR}/${file}/model.ckpt-*.meta` #注意此处这是两个反引号，表示运行系统命令
          do
              temp=${meta_file##*model.ckpt-}
              temp=${temp%.meta*}
              if [[ "${temp}" > "${max}" ]];then
                  max=${temp}
              fi
          done
          ckpt_name="model.ckpt-"${max}
          echo ${ckpt_name}
          echo "开启${file}-bert-as-service"
          bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
          -tuned_model_dir=${INTENT_MODEL_FINETUNE_DIR}/${file} -ckpt_name=${ckpt_name} \
          -port ${INTENT_IN_PORT} -port_out ${INTENT_OUT_PORT} &
          sleep 15s
          echo "已开启${file}-bert-as-service"
          let NEW_INTENT_IN_PORT=INTENT_IN_PORT+2
          let NEW_INTENT_OUT_PORT=INTENT_OUT_PORT+2
          let INTENT_IN_PORT=NEW_INTENT_IN_PORT
          let INTENT_OUT_PORT=NEW_INTENT_OUT_PORT
          echo "下个输入端口是${INTENT_IN_PORT}；输出端口是${INTENT_OUT_PORT}"
    fi
done
echo "启动多轮对话服务"
echo "启动action服务"
nohup python -m rasa_core_sdk.endpoint --actions actions &
echo "启动外部服务"
nohup python -m rasa_core.run --nlu models/intent/bert/bert_train_models/ergou_task/default/current \
--core models/dialogue --port 5002 --credentials credentials_custom.yml --endpoints endpoints.yml \
--log-file out.log &
echo "启动完毕"
