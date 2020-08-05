import os
import os
os.environ['JAVA_HOME'] = '/usr/java/jdk-14.0.1'
# a = os.getenv()

import spacy
from spacy import displacy
from collections import Counter
# import en_core_web_sm
from pprint import pprint

# # chinese
# nlp = spacy.load("cn")
# # nlp = en_core_web_sm.load()
# doc = nlp('明天下午我们开个会吧')
# pprint([(X.text, X.label_) for X in doc.ents])
# doc = nlp('我将在2小时后去北京')
# pprint([(X.text, X.label_) for X in doc.ents])
# doc = nlp('我下午2点动身去北京')
# pprint([(X.text, X.label_) for X in doc.ents])
# pprint("dddd")

# english
nlp = spacy.load("en")
# nlp = en_core_web_sm.load()
doc = nlp('European authorities fined Google a record $5.1 billion on Every Wednesday for abusing its power in the mobile phone market and ordered the company to alter its practices')
pprint([(X.text, X.label_) for X in doc.ents])
doc = nlp('I will go to beijing in 2 hours')
pprint([(X.text, X.label_) for X in doc.ents])
doc = nlp('I leave for Beijing at 2 PM')
pprint([(X.text, X.label_) for X in doc.ents])
doc = nlp('See you in two hours')
pprint([(X.text, X.label_) for X in doc.ents])
doc = nlp('From 11:45am to 14:45pm')
pprint([(X.text, X.label_) for X in doc.ents])
pprint("dddd")

doc = nlp('Set your alarm for eight minutes')
pprint([(X.text, X.label_) for X in doc.ents])

doc = nlp("I'm leaving for Beijing in two hours")
pprint([(X.text, X.label_) for X in doc.ents])

doc = nlp("set timer for two hours")
pprint([(X.text, X.label_) for X in doc.ents])


doc = nlp("Let's have a meeting at 3:50 morning")
pprint([(X.text, X.label_) for X in doc.ents])

from duckling import *

# english
d = DucklingWrapper(language=Language.ENGLISH)


msg_input = "Play Billie Ellish's' latest album"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "Schedule  a lunch meeting Monday at noon"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "Let's have a meeting at 3:50 next week"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "We will meet on March 7th, 2020"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "We will meet on March 7th, 2020 at 2:00 PM"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "I'm leaving for Beijing in two hours today"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间# this context just only sparse time point
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "I'm leaving for Beijing in two hours today"
print("duckling:", msg_input, d.parse_duration(msg_input))  # this point compare to the last one
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "Set an alarm for an hour later"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间 # this context just only sparse time point
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "Set an alarm for an hour later"
print("duckling:", msg_input, d.parse_duration(msg_input))  # 解析时间 # this context just only sparse time point
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "I need it to be repeated every Monday"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "What will the weather be like in the next two days"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "See you in two hours"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "From 11:45am to 14:45pm"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "What will the weather be like in the next two days"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "Let's meet at 11:45am"
print("duckling:", msg_input, d.parse_time(msg_input))  # 解析时间
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "My timezone is pdt"
print("duckling:", msg_input, d.parse_timezone(msg_input))  # 解析时区
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])


msg_input = "set timer for 10 mins"
print("duckling:", msg_input, d.parse_duration(msg_input))   # 解析时间,this context just only sparse time duration
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "set timer for 20 seconds"
print("duckling:", msg_input, d.parse_duration(msg_input))   # 解析时间,this context just only sparse time duration
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

msg_input = "I ran for 2 hours today"
print("duckling:", msg_input, d.parse_duration(msg_input))   # 解析时间,this context just only sparse time duration
doc = nlp(msg_input)
print("spacy:", msg_input, [(X.text, X.label_) for X in doc.ents])

print(d.parse_cycle("coming week"))  # 解析周期，失效
print(d.parse_distance("A circle around the equator is 40075.02 kilometers"))  # 解析距离
print(d.parse_email("Shoot me an email at contact@frank-blechschmidt.com"))  # 解析邮箱
print(d.parse_leven_product("5 cups of sugar"))  # 解析产品
print(d.parse_leven_unit("two pounds of meat"))  # 解析单位
print(d.parse_money("You owe me 10 dollars"))  # 解析金钱
print(d.parse_number("I'm 25 years old"))  # 解析数值
print(d.parse_ordinal("I'm first, you're 2nd"))  # 解析序数
print(d.parse_ordinal("I'm first, you're the last one"))  # 解析序数
print(d.parse_phone_number("424-242-4242 is obviously a fake number"))  # 解析电话号码
print(d.parse_quantity("5 cups of sugar"))  # 解析总量
print(d.parse_temperature("Let's change the temperature from thirty two celsius to 65 degrees"))  # 解析温度
print(d.parse_unit("6 degrees outside"))  # 解析单位（失效）
print(d.parse_unit_of_duration("1 second"))  # 解析时长的单位（失效）
print(d.parse_url("http://frank-blechschmidt.com is under construction, but you can check my github github.com/FraBle"))  # 解析URL
print(d.parse_volume("1 gallon is 3785ml"))  # 解析体积

# chinese
d = DucklingWrapper(language=Language.CHINESE)
print(d.parse_duration("我今天跑了两个小时"))  # 解析时长
print(d.parse_number("我25岁了"))  # 解析数值
print(d.parse_ordinal("我是第一，你是第二"))  # 解析序数
print(d.parse_temperature("人体最适宜的温度是25摄氏度"))  # 解析温度
print(d.parse_time("我们十一点半见"))  # 解析时间
print(d.parse_timezone("中国统一用一个时区UTC"))  # 解析时区