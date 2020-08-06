#!/bin/bash -x
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname "$0"); pwd)
export BASE_PATH=$(cd $(dirname "${LOCAL_PATH}"); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
echo "脚本工程目录：${BASE_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=${BASE_PATH}/ds_kernel/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=${BASE_PATH}/ds_kernel/eliza_pretraining_model/chinese_L-12_H-768_A-12
# graph_tmp_dir
export GRAPH_TMP_DIR=${LOCAL_PATH}/graph_tmp
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
export MONGO_CONF=${LOCAL_PATH}/configs/database/mongo.conf
# 定义MONGO-log文件
export NLU_MONGO_LOG_FILE=${LOCAL_PATH}/log/mongo.log
# 定义端口配置文件
export NLU_IN_PORT=5555
export NLU_OUT_PORT=5556

#echo "首先初始化conda" && conda --v && source activate && conda deactivate && echo "初始化conda完毕"
echo "首先初始化conda" && conda --v && conda deactivate && echo "初始化conda完毕"
echo "加载alice虚拟环境" && conda activate dmai && python --version && echo "pybot虚拟环境加载完毕"

echo "首先启动mongodb数据库"
nohup mongod --config ${MONGO_CONF} --noauth > ${NLU_MONGO_LOG_FILE} 2> ${NLU_MONGO_LOG_FILE} &
sleep 2s
echo "创建admin数据库"
mongo test --eval "db.createUser({user:\"test\", pwd:\"eliza\", roles:[{role:\"root\", db:\"admin\"}]})"
echo "创建admin管理员"
mongo admin --eval "db.createUser({user:\"admin\", pwd:\"eliza\", roles:[\"root\"]})"
echo "授权admin管理员"
mongo admin --eval "db.auth(\"admin\",\"eliza\")"

echo "加载DOMAIN-BERT-AS-SERVICE"
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
echo "tmp所在目录${GRAPH_TMP_DIR}"
if [[ ! -d ${GRAPH_TMP_DIR} ]];then
    echo "创建文件夹"
    mkdir ${GRAPH_TMP_DIR}
else
    echo "文件夹已经存在，清空文件夹内容"
    rm -rf ${GRAPH_TMP_DIR}/*
fi

# 清除临时tmp文件
rm -rf ${LOCAL_PATH}/tmp*

echo "开启DOMAIN-bert-as-service"
#bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
#-graph_tmp_dir ${GRAPH_TMP_DIR} \
#-tuned_model_dir=${NLU_MODEL_FINETUNE_DIR} -ckpt_name=${ckpt_name} \
#-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
#不加载微调模型
bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
-graph_tmp_dir ${GRAPH_TMP_DIR} \
-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
sleep 20s
echo "已开启DOMAIN-bert-as-service"

echo "启动多轮对话服务"
echo "首先关闭action和endpoint服务"
lsof -t -i:5055 |awk '{print $1}'|xargs kill -9
lsof -t -i:5005 |awk '{print $1}'|xargs kill -9

# 定义endpoint接口配置文件
export NLU_ENDPOINTS_CONFIG_FILE=${LOCAL_PATH}/configs/endpoints/endpoints.yml
# 定义restful接口配置文件
export NLU_RESTFUL_CONFIG_FILE=${LOCAL_PATH}/configs/credentials/credentials_custom.yml
# 定义core-log文件
export NLU_CORE_LOG_FILE=${LOCAL_PATH}/log/core.log
# 定义action-log文件
export NLU_ACTION_LOG_FILE=${LOCAL_PATH}/log/action.log
# 定义dialog-log文件
export NLU_DIALOG_LOG_FILE=${LOCAL_PATH}/log/dialog.log

# 定义环境变量
export PYTHONPATH=${BASE_PATH}/eliza_stack:$PYTHONPATH
export PYTHONPATH=${BASE_PATH}/eliza_stack/eliza_rasa:$PYTHONPATH
echo "当前环境变量为：${PYTHONPATH}"
echo "增加域名"
echo "127.0.0.1 bert_server" >> /etc/hosts
echo "启动action服务"
#rasa run actions --actions actions.actions > ${NLU_ACTION_LOG_FILE} 2> ${NLU_ACTION_LOG_FILE}
nohup rasa run actions --actions actions.actions > ${NLU_ACTION_LOG_FILE} 2> ${NLU_ACTION_LOG_FILE} &
echo "启动dialog服务"
#rasa run --endpoints ${NLU_ENDPOINTS_CONFIG_FILE} --credentials ${NLU_RESTFUL_CONFIG_FILE} --enable-api -m ${NLU_MODEL_TRAIN_DIR}  --log-file ${NLU_CORE_LOG_FILE} > ${NLU_DIALOG_LOG_FILE} 2> ${NLU_DIALOG_LOG_FILE}
nohup rasa run --endpoints ${NLU_ENDPOINTS_CONFIG_FILE} --credentials ${NLU_RESTFUL_CONFIG_FILE} --enable-api -m ${NLU_MODEL_TRAIN_DIR}  --log-file ${NLU_CORE_LOG_FILE} > ${NLU_DIALOG_LOG_FILE} 2> ${NLU_DIALOG_LOG_FILE} &
echo "dialog启动完毕"