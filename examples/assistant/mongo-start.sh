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
# 定义MONGO数据库文件
export MONGO_CONF=/dialog_server/configfile/mongo.conf
# 定义MONGO-log文件
export NLU_MONGO_LOG_FILE=${LOCAL_PATH}/mongo.log
# 定义端口配置文件
export NLU_IN_PORT=5555
export NLU_OUT_PORT=5556

#echo "首先初始化conda" && conda --v && source activate && conda deactivate && echo "初始化conda完毕"
#echo "加载pybot虚拟环境" && conda activate pybot && python --version && echo "pybot虚拟环境加载完毕"

echo "首先启动mongodb数据库"
nohup mongod --config ${MONGO_CONF} --noauth > ${NLU_MONGO_LOG_FILE} 2> ${NLU_MONGO_LOG_FILE} &
sleep 20s
echo "创建admin数据库"
mongo test --eval "db.createUser({user:\"test\", pwd:\"laka\", roles:[{role:\"root\", db:\"admin\"}]})"
echo "创建admin管理员"
mongo admin --eval "db.createUser({user:\"admin\", pwd:\"laka\", roles:[\"root\"]})"
echo "授权admin管理员"
mongo admin --eval "db.auth(\"admin\",\"laka\")"
echo "mongo启动完毕"