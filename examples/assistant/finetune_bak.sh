#!/bin/bash
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname $0); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=/dialog_server/source/eliza_stack/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=/dialog_server/source/eliza_stack/eliza_pretraining_model/chinese_L-12_H-768_A-12
# 训练数据的存储路径
export DOMAIN_DIR=${LOCAL_PATH}/data/domain_data
export NLU_DIR=${LOCAL_PATH}/data/intent_data
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
# 恢复默认意图端口号
sed '1,$s/port: 4.../port: 4555/g' ${INTENT_MODEL_TRAIN_CONFIG_FILE} > tmp_config && mv tmp_config ${INTENT_MODEL_TRAIN_CONFIG_FILE}
sed '1,$s/port_out: 4.../port_out: 4556/g' ${INTENT_MODEL_TRAIN_CONFIG_FILE} > tmp_config && mv tmp_config ${INTENT_MODEL_TRAIN_CONFIG_FILE}
echo "注意此文件要用source finetune.sh运行，并且打开文件后设置:set fileformat=unix后方可执行"
echo "分别读取domain_data和nlu_data的数据进行预训练"
echo "首先初始化conda" && conda --v && conda init bash && conda deactivate && echo "初始化conda完毕"
echo "加载pybot虚拟环境" && conda activate pybot && python --version && echo "pybot虚拟环境加载完毕"

echo "开始微调训练-----------------------------------------------------------------------------------"
echo "微调训练DOMAIN-------------"
echo "domain-model-finetune所在目录${DOMAIN_MODEL_FINETUNE_DIR}"
if [[ ! -d ${DOMAIN_MODEL_FINETUNE_DIR} ]];then
    echo "创建文件夹"
    mkdir ${DOMAIN_MODEL_FINETUNE_DIR}
else
    echo "文件夹已经存在，清空文件夹内容"
    rm -rf ${DOMAIN_MODEL_FINETUNE_DIR}/*
fi
python ${BERT_FINETUNE_DIR}/run_classifier.py \
  --task_name rasajson \
  --do_train True \
  --do_eval True \
  --data_dir ${DOMAIN_DIR} \
  --vocab_file ${BERT_BASE_DIR}/vocab.txt \
  --bert_config_file ${BERT_BASE_DIR}/bert_config.json \
  --init_checkpoint ${BERT_BASE_DIR}/bert_model.ckpt \
  --max_seq_length 64 \
  --train_batch_size 64 \
  --learning_rate 3e-5 \
  --num_train_epochs 2.0 \
  --output_dir ${DOMAIN_MODEL_FINETUNE_DIR}
echo "微调训练DOMAIN完毕-------------"

echo "微调训练INTENT-------------"
echo "nlu-model所在目录:${INTENT_MODEL_FINETUNE_DIR}"
for file in `ls ${NLU_DIR}` #注意此处这是两个反引号，表示运行系统命令
do
    if [[ ! -d ${INTENT_MODEL_FINETUNE_DIR}/${file} ]]; then
          echo "创建${file}文件夹"
          mkdir ${INTENT_MODEL_FINETUNE_DIR}/${file}
    else
          echo "删除${file}文件夹的内容"
          rm -rf  ${INTENT_MODEL_FINETUNE_DIR}/${file}/*
    fi
    echo "微调训练${file}意图--------------------------"
    if [[ "`ls -A ${NLU_DIR}/${file}`" != "" ]]; then
          echo "意图数据${file}存在，开始微调训练"
          python ${BERT_FINETUNE_DIR}/run_classifier.py \
              --task_name rasajson \
              --do_train \
              --do_eval \
              --data_dir ${NLU_DIR}"/"${file} \
              --vocab_file ${BERT_BASE_DIR}/vocab.txt \
              --bert_config_file ${BERT_BASE_DIR}/bert_config.json \
              --init_checkpoint ${BERT_BASE_DIR}/bert_model.ckpt \
              --max_seq_length 64 \
              --train_batch_size 32 \
              --learning_rate 3e-5 \
              --num_train_epochs 2.0 \
              --output_dir ${INTENT_MODEL_FINETUNE_DIR}/${file}
    fi
    echo "微调训练${file}意图完毕--------------------------"
done

echo "微调训练INTENT完毕---------------"

echo "正式训练---------------------------------------------------------------------------------------"
echo "正式训练DOMAIN--------------"
echo "domain-model-train所在目录${DOMAIN_MODEL_TRAIN_DIR}"
if [[ ! -d ${DOMAIN_MODEL_TRAIN_DIR} ]];then
    echo "创建文件夹"
    mkdir ${DOMAIN_MODEL_TRAIN_DIR}
else
    echo "文件夹已经存在，清空文件夹内容"
    rm -rf ${DOMAIN_MODEL_TRAIN_DIR}/*
fi

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
sleep 20s
echo "已开启DOMAIN-bert-as-service"
python ${LOCAL_PATH}/bot.py \
    --segment train \
    --obj domain \
    --config_file ${DOMAIN_MODEL_TRAIN_CONFIG_FILE} \
    --data_dir ${DOMAIN_DIR} \
    --output_dir ${DOMAIN_MODEL_TRAIN_DIR}
echo "关闭DOMAIN-bert-as-service"
ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
echo "训练DOMAIN完毕--------------"

echo "训练INTENT--------------"
echo "nlu-model所在目录:${INTENT_MODEL_TRAIN_DIR}"
for file in `ls ${NLU_DIR}` #注意此处这是两个反引号，表示运行系统命令
do
    if [[ ! -d ${INTENT_MODEL_TRAIN_DIR}/${file} ]]; then
          echo "创建${file}文件夹"
          mkdir ${INTENT_MODEL_TRAIN_DIR}/${file}
    else
          echo "删除${file}文件夹的内容"
          rm -rf  ${INTENT_MODEL_TRAIN_DIR}/${file}/*
    fi
    echo "训练${file}意图------------------------"
    if [[ "`ls -A ${NLU_DIR}/${file}`" != "" ]]; then
          echo "意图数据${file}存在，开始正式训练"
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
          bert-serving-start -num_worker=4 -model_dir=${BERT_BASE_DIR} \
          -tuned_model_dir=${INTENT_MODEL_FINETUNE_DIR}/${file} -ckpt_name=${ckpt_name} \
          -port ${INTENT_IN_PORT} -port_out ${INTENT_OUT_PORT} &
          sleep 15s
          echo "已开启${file}-bert-as-service"
          python ${LOCAL_PATH}/bot.py \
          --segment train \
          --obj domain \
          --config_file ${INTENT_MODEL_TRAIN_CONFIG_FILE} \
          --data_dir ${NLU_DIR}/${file} \
          --output_dir ${INTENT_MODEL_TRAIN_DIR}/${file}
          echo "关闭${file}-bert-as-service"
          ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
          echo "训练${file}意图完毕------------------------"
          let NEW_INTENT_IN_PORT=INTENT_IN_PORT+2
          let NEW_INTENT_OUT_PORT=INTENT_OUT_PORT+2
          sed '1,$s/'`echo ${INTENT_IN_PORT}`'/'`echo ${NEW_INTENT_IN_PORT}`'/g' ${INTENT_MODEL_TRAIN_CONFIG_FILE} > tmp_config && mv tmp_config ${INTENT_MODEL_TRAIN_CONFIG_FILE}
          sed '1,$s/'`echo ${INTENT_OUT_PORT}`'/'`echo ${NEW_INTENT_OUT_PORT}`'/g' ${INTENT_MODEL_TRAIN_CONFIG_FILE} > tmp_config && mv tmp_config ${INTENT_MODEL_TRAIN_CONFIG_FILE}
          let INTENT_IN_PORT=NEW_INTENT_IN_PORT
          let INTENT_OUT_PORT=NEW_INTENT_OUT_PORT
          echo "下个输入端口是${INTENT_IN_PORT}；输出端口是${INTENT_OUT_PORT}"
    fi
done
echo "训练INTENT完毕--------------"
echo "正式训练完毕--------------------------------------------------------------------------------------"
conda deactivate