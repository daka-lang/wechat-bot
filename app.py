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

# ========== 智谱清言配置 ==========
ZHIPU_API_KEY = "c937dde0c0454b288646b3cdcbda6fda.yJPDxhrLCHuVDGhz"
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 系统提示词（简化版）
SYSTEM_PROMPT = """你是大咖素质训练营的智能客服。知识库：
- 大咖素质训练营，成立于2017年，创始人璐瑶妈妈
- 典范英语是牛津树中国引进版，1-6级小学生，7-10级中学生
- 14点前付款当天发货（周日除外），新疆西藏不发货
- 课程为数字化商品，不支持退款
- 咨询课程请引导用户留下联系方式

回复简洁友好，单条不超过3行。"""

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
        print("收到 POST 请求")
        
        try:
            xml_data = request.data
            root = ET.fromstring(xml_data)
            
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            if msg_type == 'text':
                user_text = root.find('Content').text
                print(f"用户消息: {user_text}")
                
                reply_text = call_zhipu(user_text)
                
                print(f"AI回复: {reply_text[:100]}")
                
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
            print(f"错误: {e}")
            return "success"

def call_zhipu(user_message):
    """调用智谱清言 API"""
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4-flash",  # 免费模型
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(ZHIPU_API_URL, json=payload, headers=headers, timeout=15)
        
        print(f"智谱状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            return reply
        else:
            print(f"智谱错误: {response.text[:200]}")
            return "AI服务暂时不可用，请稍后再试"
            
    except Exception as e:
        print(f"智谱异常: {e}")
        return "系统繁忙，请稍后再试"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
