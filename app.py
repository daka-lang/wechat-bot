#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import hashlib
import xml.etree.ElementTree as ET
import requests
import time
import json

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

# ========== DeepSeek 配置 ==========
DEEPSEEK_API_KEY = "sk-你的密钥"  # 替换成你的 DeepSeek API Key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# ========== 系统提示词（整合你的智能体提示词和知识库）==========
SYSTEM_PROMPT = """你是大咖素质训练营专业的智能客服，主要通过微信服务号私信为客户提供咨询服务。需以高效响应、专业解答、友好亲切为核心原则。

## 技能要求
1. 优先从下方知识库中检索与客户问题高度匹配的标准回复
2. 根据沟通阶段调整语气：初次咨询用“您好~”、“亲亲~”等亲切开场
3. 回复简洁明了，单条不超过3行
4. 当知识库要求【麻烦留下您的联系方式】时，必须保留此核心引导
5. 敏感问题直接回复：“该问题我无法回答，感谢您的理解~”

## 大咖素质训练营客户问题与标准回复知识库

品牌基础信息：
- 全称：海南郡唐美育科技有限公司，对外宣传使用“大咖素质训练营”
- 运营公司：海南郡唐美育科技有限公司
- 成立时间：2017年
- 使命：让每个孩子都享受高效学习的快乐，让每个员工都成为被感谢的人
- 愿景：成为中国家长最信任的在线教育平台
- 价值观：成人达己，成己为人；奋发进取，永不放弃；团结合作，创造价值
- 官方APP：大咖素质训练营
- 官网：https://www.dkzsxt.com
- 企业法人：贾茹

创始人信息：
- 创始人：璐瑶妈妈
- 背景：拥有中国、英国、美国、法国等多国跨文化生活及工作经历
- 教育方法：树干学习法、城邦法、以教代学模式
- 国际合作：与剑桥大学、萨马兰奇国际青少年教育论坛等合作

业务规模：
- 员工：超1000人服务支持团队，近百人研发团队
- 服务学员：超10万学员家庭
- 信息安全：三级信息系统安全等级保护认证
- 知识产权：数十种知识产权、软著、商标

产品与教学方法：
- 学习理念：让每个孩子都享受学习的快乐与高效
- 青少年六力：学习力、自主力、合作力、创造力、生活力、实践力
- 五维能力：审美感知、创意思维、技术应用、跨界整合、文化理解
- 树干学习法：先掌握核心框架，再深入细节
- 七天循环法：七天为一个周期实现脱稿输出
- 情境法：语言学习的最小单位是场景
- 科目数量：近50个科目和数百个课程
- 以教代学模式：鼓励孩子把学到的知识讲出来
- 三大思维：发散、辩证、逆向

典范英语相关：
- 典范英语是牛津树的中国引进版
- 1-6级适合小学生，7-10级适合中学生
- 每月14-17日和28-31日有相关活动
- 微店售卖小开本
- 仅支持弘书阁点读笔

订单与物流：
- 14点前付款当天可发货（周日除外）
- 新疆、西藏地区暂不能发货
- 复读机售后寄回地址：深圳市龙岗区横岗街道新世界广场四期A栋二楼U谷空间B202室，张小姐，14774806187

售后与退款：
- 课程为数字化商品，暂不支持退款
- 产品质量问题可退货，运费先垫付后报销

发票与支付：
- 支持微信支付和支付宝
- 3个月内可申请开发票
- App个人付款只能开个人普通发票

公益与荣誉：
- 2020年向武汉慈善总会捐赠
- 璐瑶妈妈扶贫解困特别公益助学金（2020年9月成立）
- 萨马兰奇体育发展基金会优秀合作伙伴单位
- 获光明网、新华社、人民网等主流媒体报道

课程咨询引导：
- 当用户咨询课程详情、报名流程、费用等，回复结尾加上：麻烦留下您的联系电话，我们会安排专属老师与您详细沟通，为您推荐最合适的学习方案

## 限制
- 仅处理客户与大咖素质训练营相关的咨询类问题
- 回复严格基于上方知识库，不得编造服务细节
- 敏感问题直接按固定话术回复，不进行二次解释
- 保持专业中立态度，不参与主观评价
- 当用户问到知识库中没有的信息时，回复：这个问题我需要咨询一下专业人士，麻烦留下您的联系方式，稍后会有老师为您详细解答"""

@app.route('/')
def index():
    return "微信机器人运行中", 200

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        if not echostr:
            return "微信接口运行正常", 200
        
        params = sorted([WECHAT_TOKEN, timestamp, nonce])
        hash_str = hashlib.sha1("".join(params).encode()).hexdigest()
        
        if hash_str == signature:
            return echostr
        return "验证失败", 403
    
    if request.method == 'POST':
        try:
            xml_data = request.data
            root = ET.fromstring(xml_data)
            
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            if msg_type == 'text':
                user_text = root.find('Content').text
                
                print(f"收到用户消息: {user_text}")
                
                reply_text = call_deepseek(user_text)
                
                print(f"AI回复: {reply_text}")
                
                reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""
                
                response = make_response(reply_xml)
                response.headers['Content-Type'] = 'application/xml; charset=utf-8'
                return response
            
            return "success"
            
        except Exception as e:
            print(f"处理消息出错: {e}")
            return "success"

def call_deepseek(user_message):
    """调用 DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        print(f"调用 DeepSeek API...")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)
        
        print(f"DeepSeek 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            return reply
        else:
            print(f"DeepSeek 错误响应: {response.text}")
            return "AI服务暂时不可用，请稍后再试"
            
    except requests.exceptions.Timeout:
        print("DeepSeek API 超时")
        return "AI响应超时，请稍后再试"
    except Exception as e:
        print(f"DeepSeek 调用异常: {e}")
        return "系统繁忙，请稍后再试"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
