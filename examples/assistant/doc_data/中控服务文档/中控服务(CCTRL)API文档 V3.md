## 中控服务(CCTRL):API文档 V3

### 功能描述:

#### 1. 对接业务后端，接入对话流的请求

#### 2. 基于bot id实现对话流的控制和转发

#### 3. 管理和维护bot id, sess id等资源属性


### API 接口

| api名称                | 请求方式 | url                                                     | comments         |
| :--------------------- | :------- | :------------------------------------------------------ | :--------------- |
| query                  | POST     | `http://bot-cctrl-service/api/v1/cctrl/query`           | 对话请求         |
| status                 | GET      | `http://bot-cctrl-service/api/v1/cctrl/status`          | 服务状态查询     |
| version                | GET      | `http://bot-cctrl-service/api/v1/cctrl/version`         | 版本查询         |


### API-query 

#### 1. 请求格式
JSON

#### 2. 请求参数
| 参数          | 类型   | 是否必选 | 描述                                                         |
| :------------ | :----- | :------- | :----------------------------------------------------------- |
| bot_id        | uint64 | 是       | 表示机器人id                                                     |
| sess_id       | string | 是       | 表示session id                                                   |
| query         | string | 是       | 表示请求的具体内容                                               |
| **time_zone** | string | 是       | 表示当前query的具体时区比如`Etc/GMT+8`，详情参加附录1  |
| **country_code** | string | 是       | 表示当前query的国家码<br>其格式与[https://countrycode.org](https://countrycode.org)中COUNTRY CODE字段一致|
| debug         | string | 否       | 表示是否返回调试信息<br>`on`：返回<br>`off`：不返回 不填时等同于`off` |

#### 3. 返回参数
| 参数          | 类型   | 是否必选 | 描述                                                         |
| ---------------- | ------ | ---------- | ------------------------------------------------------------ |
| err_code         | 是     | int        | 表示错误码<br>非零时表示有错误，并返回错误消息                             |
| err_msg          | 否     | string     | 表示提示性错误消息                                               |
| bot_type         | 是     | string     | 表示bot类型<br>取值范围：`FAQ_BOT`, `EAOG_BOT`, `KG_BOT`, `CHAT_BOT`         |
| bot_id           | 是     | uint64     | 表示机器人id<br>与对应请求时一致                                   |
| sess_id          | 是     | string     | 表示session id<br>与对应请求时一致                                 |
| **faq_type**     | 否     | string     | 表示faq类型<br>当bot_type=`FAQ_BOT`时：<br>faq_type=`keyword`时表示是核心词匹配;<br>faq_type=`synonym`时表示是核心词同义词匹配;<br>faq_type=`keyword_rule`时表示，核心词规则泛化;<br>    faq_type=`no_keyword`时表示没有用到核心词相关的<br>当bot_type=`EAOG_BOT`时，后续再定义<br>当bot_type=`KG_BOT`时，后续再定义<br>当bot_type=`CHAT_BOT`时，没有该字段 |
| result           | 否     | list[dict] | 表示返回结果<br>当bot_type=`FAQ_BOT`时，该list相当于一个任务栈，先后执行`instruction`或`answer`功能即可<br>err_code为非零时，没有此字段                    |
| **+instruction** | 否     | dict       | 表示动作指令输出<br>当bot_type=`EAOG_BOT`时，表示当前EAOG_BOT动作指令的输出，注意在每个dict里面，其与`answer`字段是二选一的关系<br>其他bot_type没有该字段 |
| **+answer**      | 否     | string     | 表示文本回复输出<br>当bot_type=`EAOG_BOT`时，表示当前EAOG_BOT文本回复指令的输出，注意在每个dict里面，其与`instruction`字段是二选一的关系|
| +question        | 否     | string     | 表示推荐的相似问题<br>当bot_type=`FAQ_BOT`时，并且最大置信度在0.2和0.8之间，那么FAQ会列出相似问题, 用于推荐给用户；<br>当bot_type=`EAOG_BOT`时,没有该字段；<br>当bot_type=`CHAT_BOT`时，没有该字段 |
| +confidence      | 否     | float      | 表示文本回复置信度<br>当bot_type=`FAQ_BOT`时，表示FAQ的置信度；<br>当bot_type=`AOG_BOT`时，没有该字段；<br>当bot_type=`CHAT_BOT`时，没有该字段 |
| intent       | 否     | string     | 表示意图<br>仅当debug字段为`on`时有效<br>当bot_type=`EAOG_BOT`时，表示当前用户query的意图<br>其他bot_type没有该字段 |
| params       | 否     | list[dict] | 表示槽位<br>仅当debug字段为`on`时有效<br>当bot_type=`EAOG_BOT`时，表示当前用户query的意图对应的槽位<br>其他bot_type没有该字段 |
| +param_name  | 否     | string     | 表示槽名                                                         |
| +origin      | 否     | string     | 表示槽的原始值                                                   |
| +value       | 否     | string     | 表示槽的标准值                                                   |
| score        | 否     | float      | 表示置信度<br>仅当debug字段为`on`时有效<br>当bot_type=`EAOG_BOT`时，表示当前用户query的意图置信度<br>当bot_type=FAQ_BOT时，表示当前用户query的Top-1匹配度<br>其他bot_type没有该字段 |
| dialogue_status        | 否     | string      | 表示对话流状态<br>仅当debug字段为`on`时有效<br>当bot_type=`EAOG_BOT`时，表示当前对话流的状态，有以下三种种取值：<br>`dialogue_flow_start`：处于当前对话流第一轮的回复（如果对话流只有一轮，应该标识为`dialogue_flow_end`）；<br>`dialogue_flow_end`：处于当前对话流最后一轮的回复；<br>`dialogue_flow_in`：处于当前对话流中间的回复（如果对话流只有一轮，应该标识为`dialogue_flow_end`）<br>其他bot_type没有该字段 |


#### 4. 示例

##### (1) EAOG_BOT请求-正确示例(返回文本回复)
请求示例:
```json
{
    "bot_id": 1234,
    "sess_id": "ssfddsfdf",
    "query": "I want to buy a train ticket",
    "time_zone": "Asia/Shanghai",
    "country_code": "86",
    "debug": "on"
}
```
返回示例:
```json
{
	"err_code": 0,
	"bot_id": 1234,
    "sess_id": "ssfddsfdf",
	"bot_type": "EAOG_BOT",
	"result": [
		{
			"answer": "要购买哪一天的火车票呢？"
		}
	]
}
```
##### (2) EAOG_BOT请求-正确示例(返回指令回复)
请求示例:
```json
{
    "bot_id": 1234,
    "sess_id": "ssfddsfdf",
    "query": "open bluetooth",
    "time_zone": "Asia/Shanghai",
    "country_code": "86",
    "debug": "on"
}
```
返回示例:
```json
{
	"err_code": 0,
	"bot_id": 1234,
    "sess_id": "ssfddsfdf",
	"bot_type": "EAOG_BOT",
	"result": [
		{
			"instruction": 
            {
                    "ins_name": "action_trun_on_settings",
                    "ins_params":
                    {
                      "device.name": "BLUETOOTH"
                    }      
            }
		}
	]
}
```

##### (3) FAQ_BOT请求-正确示例( type=`keyword_rule`时，或type=`no_keyword`时)
请求示例
```json
{
    "bot_id": 1234,
    "sess_id": "ssfddsfdf",
    "query": "老咳嗽咋回事",
    "time_zone": "Asia/Shanghai",
    "country_code": "86",
    "debug": "on"
}
```
返回示例:
```json
{
	"err_code": 0,
	"bot_id": 1234,
    "sess_id": "ssfddsfdf",
	"bot_type": "FAQ_BOT",
    "faq_type": "no_keyword",
	"result": [
        {
            "answer": "https://wechat.dxy.cn/japi/weixin/news/group/28018/d4e4e19ba5cacd0b74a6707ffc6d4e5a",
           "confidence": 0.8844898343086243,
           "question": "孩子发烧咳嗽怎么办？"
        }
    ]
}
```

##### (4) FAQ_BOT请求-正确示例( type=keyword时，或type=synonym时)
请求示例
```json
{
    "bot_id": 1234,
    "sess_id": "ssfddsfdf",
    "query": "老咳嗽咋回事",
    "time_zone": "Asia/Shanghai",
    "country_code": "86",
    "debug": "on"
}
```
返回示例:
```json
{
	"err_code": 0,
	"bot_id": 1234,
    "sess_id": "ssfddsfdf",
	"bot_type": "FAQ_BOT",
    "faq_type": "keyword",
	"result": [
		{
			"question": "信用卡还款怎么算利息",
			"answer": "一千元一天利息5角...",
			"confidence": 0.8500000238418579
		},
        {
        	"question": "银行卡异地能换卡吗",
        	"answer": "不能，目前银行卡...",
       		"confidence": 0.8489999771118164
       	}
    ]
}
```
##### (5) CHAT_BOT请求-正确示例( type=keyword时，或type=synonym时)
请求示例
```json
{
    "bot_id": 1234,
    "sess_id": "ssfddsfdf",
    "query": "我今天好开心啊",
    "time_zone": "Asia/Shanghai",
    "country_code": "86",
    "debug": "on"
}
```
返回示例:
```json
{
	"err_code": 0,
	"bot_id": 1234,
    "sess_id": "ssfddsfdf",
 	"bot_type": "CHAT_BOT",
    "faq_type": "keyword",
 	"result": [{"answer": "你开心我也开心"}]
}
```
##### (6) BOT请求-错误返回示例
```json
{
	"err_code": 1000,
	"err_msg": "this is error!"
}
```

### 附录1-timezone取值列表
| timezone时区名称                 | 
| :--------- |
| 'Etc/GMT+12'
| 'Etc/GMT+11'
| 'Etc/GMT+10'
| 'Etc/GMT+9'
| 'Etc/GMT+8'
| 'Etc/GMT+7'
| 'Etc/GMT+6'
| 'Etc/GMT+5'
| 'Etc/GMT+4'
| 'Etc/GMT+3'
| 'Etc/GMT+2'
| 'Etc/GMT+1'
| 'Etc/GMT-1'
| 'Etc/GMT-2'
| 'Etc/GMT-3'
| 'Etc/GMT-4'
| 'Etc/GMT-5'
| 'Etc/GMT-6'
| 'Etc/GMT-7'
| 'Etc/GMT-8'
| 'Etc/GMT-9'
| 'Etc/GMT-10'
| 'Etc/GMT-11'
| 'Etc/GMT-12'
| 'Etc/GMT-13'
| 'Etc/GMT-14'