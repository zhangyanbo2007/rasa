#!/bin/bash
# 获取脚本所在目录
export LOCAL_PATH=$(cd $(dirname $0); pwd)
echo "脚本所在目录：${LOCAL_PATH}"
# 微调工程的存储路径
export BERT_FINETUNE_DIR=/home/zyb/myProject/eliza/source/eliza_stack/bert_finetune
# 微调工程原始模型的存储路径
export BERT_BASE_DIR=/home/zyb/myProject/eliza/source/eliza_stack/eliza_pretraining_model/chinese_L-12_H-768_A-12
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

#echo "首先启动mongodb数据库"
#nohup mongod --config ${MONGO_CONF} --noauth > ${NLU_MONGO_LOG_FILE} 2> ${NLU_MONGO_LOG_FILE} &
#sleep 20s
#echo "创建admin数据库"
#mongo result --eval "db.createUser({user:\"result\", pwd:\"laka\", roles:[{role:\"root\", db:\"admin\"}]})"
#echo "创建admin管理员"
#mongo admin --eval "db.createUser({user:\"admin\", pwd:\"laka\", roles:[\"root\"]})"
#echo "授权admin管理员"
#mongo admin --eval "db.auth(\"admin\",\"laka\")"

#echo "加载DOMAIN-BERT-AS-SERVICE"
#echo "遍历模型文件，找到最新的模型"
#max="0"
#temp="0"
#for meta_file in `ls ${NLU_MODEL_FINETUNE_DIR}/model.ckpt-*.meta` #注意此处这是两个反引号，表示运行系统命令
#do
#    temp=${meta_file##*model.ckpt-}
#    temp=${temp%.meta*}
#    if [[ "${temp}" > "${max}" ]];then
#        max=${temp}
#    fi
#done
#ckpt_name="model.ckpt-"${max}
#echo ${ckpt_name}
#echo "关闭DOMAIN-bert-as-service"
#ps -ef |grep bert-serving-start |awk '{print $2}'|xargs kill -9
#echo "tmp所在目录${GRAPH_TMP_DIR}"
#if [[ ! -d ${GRAPH_TMP_DIR} ]];then
#    echo "创建文件夹"
#    mkdir ${GRAPH_TMP_DIR}
#else
#    echo "文件夹已经存在，清空文件夹内容"
#    rm -rf ${GRAPH_TMP_DIR}/*
#fi
#echo "开启DOMAIN-bert-as-service"
#bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
#-graph_tmp_dir ${GRAPH_TMP_DIR} \
#-tuned_model_dir=${NLU_MODEL_FINETUNE_DIR} -ckpt_name=${ckpt_name} \
#-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
#不加载微调模型
#bert-serving-start -num_worker=$1 -model_dir=${BERT_BASE_DIR} \
#-graph_tmp_dir ${GRAPH_TMP_DIR} \
#-port ${NLU_IN_PORT} -port_out ${NLU_OUT_PORT} &
#sleep 20s
#echo "已开启DOMAIN-bert-as-service"

echo "启动多轮对话服务"
echo "首先关闭action和endpoint服务"
lsof -t -i:5055 |awk '{print $1}'|xargs kill -9
lsof -t -i:5005 |awk '{print $1}'|xargs kill -9

# 定义endpoint接口配置文件
export NLU_ENDPOINTS_CONFIG_FILE=${LOCAL_PATH}/configs/endpoints/endpoints.yml
# 定义restful接口配置文件
export NLU_RESTFUL_CONFIG_FILE=${LOCAL_PATH}/configs/credentials/credentials_custom.yml
# 定义core-log文件
export NLU_CORE_LOG_FILE=${LOCAL_PATH}/core.log
# 定义action-log文件
export NLU_ACTION_LOG_FILE=${LOCAL_PATH}/action.log
# 定义dialog-log文件
export NLU_DIALOG_LOG_FILE=${LOCAL_PATH}/dialog.log
#echo "然后延时等待BERT启动"
#sleep 20s
#echo "因为远程加载bert的缘故因此需要重新训练模型,注意要将config中bert对应的远程服务(docker-compose里面对应的bert_server)进行强制修改"
#echo "首先删除模型"
#rm -rf ${NLU_MODEL_TRAIN_DIR}/*
#sed '1,$s/ip: "localhost"/ip: "bert_server"/g' ${NLU_MODEL_TRAIN_CONFIG_FILE} > temp && mv temp ${NLU_MODEL_TRAIN_CONFIG_FILE}
#rasa train --domain ${NLU_MODEL_DOMAIN_CONFIG_FILE} --data ${DATA_DIR} --config ${NLU_MODEL_TRAIN_CONFIG_FILE} --out ${NLU_MODEL_TRAIN_DIR}
echo "启动action服务"
nohup rasa run actions --actions actions.actions > ${NLU_ACTION_LOG_FILE} 2> ${NLU_ACTION_LOG_FILE} &
echo "启动dialog服务"
nohup rasa run --endpoints ${NLU_ENDPOINTS_CONFIG_FILE} --credentials ${NLU_RESTFUL_CONFIG_FILE} --enable-api -m ${NLU_MODEL_TRAIN_DIR}  --log-file ${NLU_CORE_LOG_FILE} > ${NLU_DIALOG_LOG_FILE} 2> ${NLU_DIALOG_LOG_FILE} &
echo "dialog启动完毕"
