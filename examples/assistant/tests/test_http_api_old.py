import sys
import os
from os import path
import urllib3
import unittest
import json
import time
from random import randint
import uuid
from multiprocessing import Pool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


# host = "http://192.168.28.72:8000"
# host = "http://127.0.0.1:8000"
# host = 'http://bot-cctrl-service.px-dialogue.dev.dm-ai.cn'
host = "http://bot-cctrl-service.ex-dialogue.test.dm-ai.cn/"

api_url = {
    "version": "/api/v1/cctrl/version",
    "status": "/api/v1/cctrl/status",
    "query": "/api/v1/cctrl/query",

}



class TestAPI(unittest.TestCase):

    def setUp(self):
        self.http = urllib3.PoolManager()

    # def test00_get_version(self):
    #     pool = Pool(processes=16)
    #     for i in range(16):
    #         print("start task: {}".format(i))
    #         pool.apply_async(self.__get_version,)
    #
    #     pool.close()
    #     pool.join()

    def test01_get_status(self):
        response = self.http.request('GET', host + api_url['status'],
                                     headers={'Content-Type': 'application/json'})
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(0, data['err_code'])

    def test02_get_version(self):
        response = self.http.request('GET', host + api_url['version'],
                                     headers={'Content-Type': 'application/json'})
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(0, data['err_code'])

    def test03_query(self, sess_id=789):
        """
        测试eaog/task bot
        """

        print("=============EAOG BOT===============")
        data = ['我想买一张去上海的火车票',
               '明天',
               '广州',
               '帮我订G1306次列车二等座一张',
               '预约一下去广州南站的出租车',
               '我叫周星星']

        idx = 0
        while idx < len(data):

            body = {
                    'request_id': str(uuid.uuid4()),
                    'bot_id': 23333,
                    'user_id': 4567,
                    'sess_id': sess_id,
                    'query': data[idx]}

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            print('Q: {}'.format(data[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('A:', json.loads(response.data.decode('utf-8')), (e-s))
            idx += 1

        print("=============Test EAOG BOT END===============")

    def test03_multi_bots(self):
        """
        测试eaogbot， 多sess的情况
        """

        print("=============Multiply Bots===============")
        data1 = ['我想买一张去上海的火车票',
                 '明天',
                 '广州',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去广州南站的出租车',
                 '我叫周星星']

        data2 = ['我想买一张去北京的火车票',
                 '后天',
                 '上海',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去上海火车站的出租车',
                 '我叫周发发']

        idx = 0
        while idx < len(data1):

            body1 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 23333,
                     'user_id': 456,
                     'sess_id': 789,
                     'query': data1[idx]}

            body2 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 66666,
                     'user_id': 777,
                     'sess_id': 888,
                     'query': data2[idx]}

            body1 = json.dumps(body1).encode('utf-8')
            body2 = json.dumps(body2).encode('utf-8')

            s = time.time()
            print('bot1 Q: {}'.format(data1[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body1,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot1 A:', (e-s), json.loads(response.data.decode('utf-8')))

            s = time.time()
            print('bot2 Q: {}'.format(data2[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body2,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot2 A:', (e - s), json.loads(response.data.decode('utf-8')))

            idx += 1

        print("=============Test Multiply Bots END===============")

    def test03_multi_sess(self):
        """
        测试eaogbot， 多sess的情况
        """

        print("=============Multiply Sessions===============")
        data1 = ['我想买一张去上海的火车票',
                 '明天',
                 '广州',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去广州南站的出租车',
                 '我叫周星星']

        data2 = ['我想买一张去北京的火车票',
                 '后天',
                 '上海',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去上海火车站的出租车',
                 '我叫周发发']

        idx = 0
        while idx < len(data1):

            body1 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 23333,
                     'user_id': 456,
                     'sess_id': 789,
                     'query': data1[idx]}

            body2 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 23333,
                     'user_id': 456,
                     'sess_id': 888,
                     'query': data2[idx]}

            body1 = json.dumps(body1).encode('utf-8')
            body2 = json.dumps(body2).encode('utf-8')

            s = time.time()
            print('bot1 Q: {}'.format(data1[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body1,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot1 A:', (e-s), json.loads(response.data.decode('utf-8')))

            s = time.time()
            print('bot2 Q: {}'.format(data2[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body2,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot2 A:', (e - s), json.loads(response.data.decode('utf-8')))

            idx += 1

        print("=============Test Multiply Sessions END===============")

    def test03_multi_bot_sess(self):
        """
        测试eaogbot， 多bot, 多sess的情况
        """

        print("=============Multiply Bots Sessions===============")
        data1 = ['我想买一张去上海的火车票',
                 '明天',
                 '广州',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去广州南站的出租车',
                 '我叫周星星']

        data2 = ['我想买一张去北京的火车票',
                 '后天',
                 '上海',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去南站的出租车',
                 '我叫周发发']

        data3 = ['我想买一张去成都的火车票',
                 '下星期一',
                 '西安',
                 '帮我订G1306次列车二等座一张',
                 '预约一下去火车站的出租车',
                 '我叫周杰棍']

        idx = 0
        while idx < len(data1):

            body1 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 23333,
                     'user_id': 456,
                     'sess_id': 789,
                     'query': data1[idx]}

            body2 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 66666,
                     'user_id': 777,
                     'sess_id': 888,
                     'query': data2[idx]}

            body3 = {
                     'request_id': str(uuid.uuid4()),
                     'bot_id': 66666,
                     'user_id': 777,
                     'sess_id': 999,
                     'query': data3[idx]}

            body1 = json.dumps(body1).encode('utf-8')
            body2 = json.dumps(body2).encode('utf-8')
            body3 = json.dumps(body3).encode('utf-8')

            s = time.time()
            print('bot1 Q: {}'.format(data1[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body1,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot1 A:', (e-s), json.loads(response.data.decode('utf-8')))

            s = time.time()
            print('bot2 Q: {}'.format(data2[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body2,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot2 A:', (e - s), json.loads(response.data.decode('utf-8')))

            s = time.time()
            print('bot3 Q: {}'.format(data3[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body3,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('bot3 A:', (e - s), json.loads(response.data.decode('utf-8')))

            idx += 1

        print("=============Test Multiply Bots Sessions END===============")

    def test04_query(self):
        """
        测试FAQbot
        """

        data = ['什么时候打卡', '年休假可以去度假吗？', '你喜欢红烧肉吗？红烧肉像不像你']

        print("=============FAQ BOT===============")

        for d in data:
            body = {
                    'request_id': str(uuid.uuid4()),
                    'bot_id': 82,
                    'user_id': '456',
                    'sess_id': '789',
                    'query': d}

            print('Q:', d)

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()

            print('A:', (e - s), json.loads(response.data.decode('utf-8')))
            print('\n\n')

        print("=============Test FAQ BOT END ===============")

    def test05_query(self):
        """
        测试chatbot/tulingbot
        """

        print("=============CHAT BOT===============")

        body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 1,
                'user_id': 456,
                'sess_id': 789,
                'query': '我发烧了'}

        body = json.dumps(body).encode('utf-8')

        s = time.time()

        response = self.http.request('POST', host + api_url['query'],
                                     body=body,
                                     headers={'Content-Type': 'application/json'})
        e = time.time()

        print((e - s), json.loads(response.data.decode('utf-8')))

        print("=============Test CHAT BOT END===============")

    def test05_multi_thread_query(self):
        """
        多线程测试
        """
        pool = Pool(processes=8)
        for i in range(8):
            sess_id = randint(1, 1000000)
            print("start {} task,  session: {}".format(i, sess_id))
            pool.apply_async(test_query, args=(sess_id,))

        pool.close()
        pool.join()

    def test06_memory_test(self):
        """
        测试内存占用
        """

        data = ['我想买一张去上海的火车票',
                '明天',
                '广州',
                '帮我订G1306次列车二等座一张',
                '预约一下去广州南站的出租车',
                '我叫周星星']

        idx = 1

        while idx:
            body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 23333,
                'user_id': 456,
                'sess_id': idx,
                'query': data[0]}

            body = json.dumps(body).encode('utf-8')
            try:
                response = http.request('POST', host + api_url['query'],
                                    body=body,
                                    headers={'Content-Type': 'application/json'})
            except Exception as e:
                print(e)
                break
            else:
                res = json.loads(response.data.decode('utf-8'))
                if res.get('err_code', -1) != 0:
                    print(res)
                    break

            print('create: {}'.format(idx))
            idx += 1

        print('total {} sess created'.format(idx))

    def test07_en_query1(self, sess_id=7819):
        """
        测试eaog/task bot
        """

        print("=============EAOG BOT===============")
        data = ['what time']

        idx = 0
        while idx < len(data):
            body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 6,
                'user_id': 4567,
                'sess_id': sess_id,
                'query': data[idx]}

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            print('Q: {}'.format(data[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('A:', json.loads(response.data.decode('utf-8')), (e - s))
            idx += 1

        print("=============Test EAOG BOT END===============")

    def test07_en_query2(self, sess_id=78191):
        """
        测试eaog/task bot
        """

        print("=============EAOG BOT===============")
        data = ['book seat',
                'yes',
                'Trevor Noah',
                'October 5',
                '5pm']

        idx = 0
        while idx < len(data):
            body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 6,
                'user_id': 4567,
                'sess_id': sess_id,
                'query': data[idx]}

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            print('Q: {}'.format(data[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            print('A:', json.loads(response.data.decode('utf-8')), (e - s))
            idx += 1

        print("=============Test EAOG BOT END===============")

    def test07_en_query3(self, sess_id=781):
        """
        测试eaog/task bot
        """

        print("=============EAOG BOT===============")
        data = ['cab reserve',
                'Xiangjiangguoji',
                'Guangdong South Station',
                ]

        ans = [ 'You may wait for a while, the cab is coming soon where is your destination?',
                'where to pick you up?',
                'cab reserved. Please wait at Guangdong South Station , and the cab will take you to Xiangjiangguoji '
                ]

        idx = 0
        sess_id = str(uuid.uuid4())
        while idx < len(data):
            body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 6,
                'user_id': 4567,
                'sess_id': sess_id,
                'query': data[idx]}

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            print('Q: {}'.format(data[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            a = json.loads(response.data.decode('utf-8'))
            print('A:', a, (e - s))
            if not a['result']:
                print('!!!! Error !!!!')
                break
            idx += 1

        print("=============Test EAOG BOT END===============")

    def test08_en_query1(self, sess_id=781):
        """
        测试eaog/task bot
        测试问候语
        """

        print("=============EAOG BOT===============")
        data = ['',
                'cab reserve',
                'hello',
                'Xiangjiangguoji',
                'Guangdong South Station',
                'hello',
                ]

        # data = ['',
        #         'cab reserve',
        #         ]

        ans = [ 'I am meeting words',
                'You may wait for a while, the cab is coming soon where is your destination?',
                'where to pick you up?',
                'cab reserved. Please wait at Guangdong South Station , and the cab will take you to Xiangjiangguoji '
                ]

        idx = 0
        sess_id = str(uuid.uuid4())
        while idx < len(data):
            body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 6,
                'user_id': 4567,
                'sess_id': sess_id,
                'query': data[idx]}

            body = json.dumps(body).encode('utf-8')

            s = time.time()
            print('Q: {}'.format(data[idx]))
            response = self.http.request('POST', host + api_url['query'],
                                         body=body,
                                         headers={'Content-Type': 'application/json'})
            e = time.time()
            a = json.loads(response.data.decode('utf-8'))
            print('A:', a, (e - s))
            if not a['result']:
                print('!!!! Error !!!!')
                break
            idx += 1

        print("=============Test EAOG BOT END===============")


http = urllib3.PoolManager()

def test_query(sess_id=789):
    """
    测试eaog/task bot
    """

    print("=============EAOG BOT===============")
    data = ['我想买一张去上海的火车票',
           '明天',
           '广州',
           '帮我订G1306次列车二等座一张',
           '预约一下去广州南站的出租车',
           '我叫周星星']

    idx = 0
    dialogue = []

    while idx < len(data):

        body = {
                'request_id': str(uuid.uuid4()),
                'bot_id': 23333,
                'user_id': 456,
                'sess_id': sess_id,
                'query': data[idx]}

        body = json.dumps(body).encode('utf-8')

        s = time.time()
        time.sleep(float(randint(0, 500))/1000)
        dialogue.append('[{}] Q: {}'.format(sess_id, data[idx]))
        response = http.request('POST', host + api_url['query'],
                                 body=body,
                                 headers={'Content-Type': 'application/json'})
        e = time.time()
        dialogue.append('[{}] A: {}'.format(sess_id, json.loads(response.data.decode('utf-8'))))
        idx += 1

    for d in dialogue:
        print(d)

    print("=============Test EAOG BOT END===============")


if __name__ == "__main__":
    pass
    # unittest.main()

    # suite = unittest.TestSuite()
    # suite.addTest(TestAPI("test04_query"))
    # suite.addTest(TestAPI("test03_query"))
    # suite.addTest(TestAPI("test03_multi_bots"))
    # suite.addTest(TestAPI("test03_multi_sess"))
    # suite.addTest(TestAPI("test03_multi_bot_sess"))
    # suite.addTest(TestAPI("test05_multi_thread_query"))
    # suite.addTest(TestAPI("test06_memory_test"))
    # suite.addTest(TestAPI("test07_en_query3"))
    # suite.addTest(TestAPI("test07_en_query2"))
    # suite.addTest(TestAPI("test08_en_query1"))

    # runner = unittest.TextTestRunner()
    # runner.run(suite)
