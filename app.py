#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import hashlib
import xml.etree.ElementTree as ET
import requests
import time
import sys

app = Flask(__name__)

# 强制 stdout 实时输出
sys.stdout.reconfigure(line_buffering=True)

WECHAT_TOKEN = "wechat123456"

# ========== DeepSeek 配置 ==========
DEEPSEEK_API_KEY = "sk-e22a139c77804719aa566dc576f7ef39"  
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# ========== 系统提示词 ==========
SYSTEM_PROMPT = """你是大咖素质训练营专业的智能客服，主要通过微信服务号私信为客户提供咨询服务。需以高效响应、专业解答、友好亲切为核心原则。

## 大咖素质训练营客户问题与标准回复知识库

品牌基础信息：
- 全称：海南郡唐美育科技有限公司，对外宣传使用"大咖素质训练营"
- 运营公司：海南郡唐美育科技有限公司
- 成立时间：2017年
- 使命：让每个孩子都享受高效学习的快乐
- 愿景：成为中国家长最信任的在线教育平台
- 官方APP：大咖素质训练营
- 官网：https://www.dkzsxt.com

创始人信息：
- 创始人：璐瑶妈妈
- 教育方法：树干学习法、城邦法、以教代学模式

典范英语相关：
- 典范英语是牛津树的中国引进版
- 1-6级适合小学生，7-10级适合中学生
- 每月14-17日和28-31日有相关活动

订单与物流：
- 14点前付款当天可发货（周日除外）
- 新疆、西藏地区暂不能发货

售后与退款：
- 课程为数字化商品，暂不支持退款

课程咨询引导：
- 当用户咨询课程详情、报名流程、费用等，回复结尾加上：麻烦留下您的联系电话，我们会安排专属老师与您详细沟通

## 限制
- 仅处理客户与大咖素质训练营相关的咨询类问题
- 回复严格基于上方知识库，不得编造
- 回复简洁明了，单条不超过3行
- 保持专业中立态度"""

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
        print("=" * 50, flush=True)
        print("收到 POST 请求", flush=True)
        
        try:
            xml_data = request.data
            root = ET.fromstring(xml_data)
            
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            print(f"消息类型: {msg_type}", flush=True)
            
            if msg_type == 'text':
                user_text = root.find('Content').text
                print(f"用户消息: {user_text}", flush=True)
                
                reply_text = call_deepseek(user_text)
                
                print(f"AI回复: {reply_text[:50]}...", flush=True)
                
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
            print(f"处理消息出错: {e}", flush=True)
            return "success"

def call_deepseek(user_message):
    """调用 DeepSeek API"""
    print("调用 DeepSeek API...", flush=True)
    
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
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)
        
        print(f"DeepSeek 状态码: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            return reply
        else:
            print(f"DeepSeek 错误: {response.text[:200]}", flush=True)
            return "AI服务暂时不可用，请稍后再试"
            
    except Exception as e:
        print(f"DeepSeek 异常: {e}", flush=True)
        return "系统繁忙，请稍后再试"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
