#!/bin/bash
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname $0); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=/dialog_server/source/eliza_stack/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=/dialog_server/source/eliza_stack/eliza_pretraining_model/chinese_L-12_H-768_A-12
# 微调训练数据的存储路径
export NLU_DIR=${LOCAL_PATH}/data/nlu
# 微调训练模型的存储路径
export NLU_MODEL_FINETUNE_DIR=${LOCAL_PATH}/bert_finetune_models
# 定义端口配置文件
export NLU_IN_PORT=5555
export NLU_OUT_PORT=5556
# 恢复默认意图端口号
echo "注意此文件要用source finetune.sh运行，并且打开文件后设置:set fileformat=unix后方可执行"
echo "读取domain_data的数据进行预训练"
echo "首先初始化conda" && conda --v && conda init bash && conda deactivate && echo "初始化conda完毕"
echo "加载pybot虚拟环境" && conda activate pybot && python --version && echo "pybot虚拟环境加载完毕"

echo "开始微调训练-----------------------------------------------------------------------------------"
echo "关闭DOMAIN-bert-as-service"
ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
echo "微调训练DOMAIN-------------"
echo "domain-model-finetune所在目录${NLU_MODEL_FINETUNE_DIR}"
if [[ ! -d ${NLU_MODEL_FINETUNE_DIR} ]];then
    echo "创建文件夹"
    mkdir ${NLU_MODEL_FINETUNE_DIR}
else
    echo "文件夹已经存在，清空文件夹内容"
    rm -rf ${NLU_MODEL_FINETUNE_DIR}/*
fi
python ${BERT_FINETUNE_DIR}/run_classifier.py \
  --task_name rasajson \
  --do_train True \
  --do_eval True \
  --data_dir ${NLU_DIR} \
  --vocab_file ${BERT_BASE_DIR}/vocab.txt \
  --bert_config_file ${BERT_BASE_DIR}/bert_config.json \
  --init_checkpoint ${BERT_BASE_DIR}/bert_model.ckpt \
  --max_seq_length 64 \
  --train_batch_size 64 \
  --learning_rate 3e-5 \
  --num_train_epochs 3.0 \
  --output_dir ${NLU_MODEL_FINETUNE_DIR}
echo "微调训练DOMAIN完毕-------------"
conda deactivate