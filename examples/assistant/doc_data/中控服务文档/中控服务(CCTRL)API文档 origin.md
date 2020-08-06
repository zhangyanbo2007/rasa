## 中控服务(CCTRL):API文档 V2

### 功能描述:

#### 1. 对接业务后端，接入对话流的请求

#### 2. 基于bot id实现对话流的控制和转发

#### 3. 管理和维护bot id, sess id等资源属性



### API 接口

| api名称                | 请求方式 | url                                                     | comments         |
| :--------------------- | :------- | :------------------------------------------------------ | :--------------- |
| information_state_sync | POST     | `http://bot-cctrl-service/api/v1/cctrl/info_state_sync` | 同步会话对话状态 |
| query                  | POST     | `http://bot-cctrl-service/api/v1/cctrl/query`           | 对话请求         |
| status                 | GET      | `http://bot-cctrl-service/api/v1/cctrl/status`          | 服务状态查询     |
| version                | GET      | `http://bot-cctrl-service/api/v1/cctrl/version`         | 版本查询         |



### Query 请求

#### 1. 请求格式

JSON

#### 2. 请求参数

| 参数          | 类型   | 是否必选 | 描述                                                         |
| :------------ | :----- | :------- | :----------------------------------------------------------- |
| request_id    | string | 是       | 表示该请求的唯一表示符                                       |
| bot_id        | uint64 | 是       | 机器人id                                                     |
| debug         | string | 否       | 是否返回调试信息，"on"：返回, "off"：不返回。 不填时等同于"off" |
| query         | string | 是       | 请求的具体内容                                               |
| sess_id       | string | 是       | session id                                                   |
| **time_zone** | string | 否       | 如果存在，表示当前query的具体时区，比如”Asia/Shanghai“       |
| user_id       | uint64 | 是       | 用户id                                                       |

#### 3. 返回参数

| bot_type         | 是     | string     | bot类型: "FAQ_BOT", "EAOG_BOT", "KG_BOT", "CHAT_BOT"         |
| ---------------- | ------ | ---------- | ------------------------------------------------------------ |
| sess_id          | 是     | string     | session id, 与对应请求时一致                                 |
| **+instruction** | 否     | dict       | 当bot_type=EAOG_BOT时，表示当前EAOG_BOT动作指令的输出其他bot_type没有该字段 |
| ***faq_type\***  | 否     | string     | 当bot_type=FAQ_BOT时, type=keyword时表示是核心词匹配，type=synonym时表示是核心词同义词匹配,type=keyword_rule时表示，核心词规则泛化， type=no_keyword时表示没有用到核心词相关的 。当bot_type=EAOG_BOT时，没有该字段。当bot_type=KG_BOT时，后续再定义。当bot_type=CHAT_BOT时，没有该字段。 |
| +question        | 否     | string     | 当bot_type=FAQ_BOT时，并且最大置信度在0.2和0.8之间，那么FAQ会列出相似问题, 用于推荐给用户。当bot_type=EAOG_BOT时,没有该字段。当bot_type=CHAT_BOT时，没有该字段。 |
| +confidence      | 否     | float      | 当bot_type=FAQ_BOT时，表示FAQ的置信度当bot_type=AOG_BOT时，没有该字段。当bot_type=CHAT_BOT时，没有该字段。 |
| err_msg          | 否     | string     | 提示性错误消息                                               |
| bot_id           | 是     | uint64     | 机器人id, 与对应请求时一致                                   |
| **+param_name**  | 否     | string     | 槽名                                                         |
| **+origin**      | 否     | string     | 槽的原始值                                                   |
| **+value**       | 否     | string     | 槽的标准值                                                   |
| user_id          | 是     | uint64     | 用户id, 与对应请求时一致                                     |
| request_id       | **是** | string     | 表示该请求的唯一表示符, 与对应请求时一致                     |
| **intent**       | 否     | string     | 调试信息：debug模式时返回该字段内容当bot_type=EAOG_BOT时，表示当前用户query的意图其他bot_type没有该字段 |
| **params**       | 否     | list[dict] | 调试信息：debug模式时返回该字段内容当bot_type=EAOG_BOT时，表示当前用户query的意图对应的槽位其他bot_type没有该字段 |
| **score**        | 否     | float      | 调试信息：debug模式时返回该字段内容当bot_type=EAOG_BOT时，表示当前用户query的意图置信度其他bot_type没有该字段 |
| result           | 否     | list[json] | 返回结果(err_code为非零时，没有此字段)                       |
| +answer          | 是     | string     | 问题答案当bot_type=EAOG_BOT时，表示当前EAOG_BOT回复指令的输出 |
| err_code         | 是     | int        | 非零时表示有错误，并返回错误消息                             |

#### 4. 返回示例

##### (1) 正确返回

```json
Taskbot(Eaog)返回时的结果：
{
	'bot_id': 23333,
	'bot_type': 'EAOG_BOT',
	'result': [
		{
			'answer': '要购买哪一天的火车票呢？'
		}
	],
	'sess_id': 789,
	'user_id': 456,
	'err_code': 0,
	'request_id': '123'
}
 
 
FAQbot返回时的结果( type=keyword_rule时，或type=no_keyword时):
{
	'bot_id': 1,
	'bot_type': 'FAQ_BOT',
	'result': [
        {
            'answer': 'https://wechat.dxy.cn/japi/weixin/news/group/28018/d4e4e19ba5cacd0b74a6707ffc6d4e5a',
           'confidence': 0.8844898343086243,
           'question': '孩子发烧咳嗽怎么办？'
        }
    ],
 	'type': 'no_keyword',
 	'sess_id': 789,
 	'user_id': 456,
 	'err_code': 0,
 	'request_id': '123'
}
 
 
FAQbot返回时的结果( type=keyword时，或type=synonym时):
{
	'bot_id': 1,
	'bot_type': 'FAQ_BOT',
	'result': [
		{
			'question': '信用卡还款怎么算利息',
			'answer': '一千元一天利息5角...',
			'confidence': 0.8500000238418579,
		},
        {
        	'question': '银行卡异地能换卡吗',
        	'answer': '不能，目前银行卡...',
       		'confidence': 0.8489999771118164,
       	},
    ],
    'type': 'keyword',
    'sess_id': 789,
    'user_id': 456,
    'err_code': 0,
    'request_id': '123'
}
 
 
Chatbot返回时的结果:
{
    'bot_id': 1,
 	'bot_type': 'CHAT_BOT',
 	'result': [{'answer': '发烧了我们就应该吃药然后好好休息。'}],
	'sess_id': 789,
	'user_id': 456,
	'err_code': 0,
	'request_id': '123'
}
```

##### (2) 错误返回

```json
{
	"err_msg": "this is error!", 
	"err_code": 1000
}
```



### Information State Sync请求

#### 1. 请求格式

JSON

#### 2. 请求参数

| 参数       | 类型   | 是否必选 | 描述                   |
| :--------- | :----- | :------- | :--------------------- |
| request_id | string | 是       | 表示该请求的唯一表示符 |
| bot_id     | uint64 | 是       | 机器人id               |
| sess_id    | string | 是       | session id             |
| info_state | dict   | 是       | 对话信息状态字典       |

#### 3. 返回参数

| request_id | **是** | string | 表示该请求的唯一表示符, 与对应请求时一致 |
| ---------- | ------ | ------ | ---------------------------------------- |
| bot_id     | 是     | uint64 | 机器人id, 与对应请求时一致               |
| sess_id    | 是     | string | session id, 与对应请求时一致             |
| rsp        | 是     | string | 服务返回信息                             |
| err_code   | 是     | int    | 非零时表示有错误，并返回错误消息         |
| err_msg    | 否     | string | 提示性错误消息                           |

#### 4. 返回示例

##### (1) 正确返回

```json
{
	'bot_id': 23333,
	'sess_id': '789',
	'rsp': 'sync success',
	'err_code': 0,
	'request_id': '123'
}
```

##### (2) 错误返回

```json
{
	"err_msg": "this is error!",
	"err_code": 1000
}
```