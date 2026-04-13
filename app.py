from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time
import os

app = Flask(__name__)

# ========== 配置信息 ==========
WECHAT_TOKEN = "wechat123456"

# 扣子配置（国内版）
COZE_API_KEY = "pat_8nHPY6IBnTz67KSF48N1H18dTgeWso7z3bYyFPUxzSytsGCHrFNJFPnVlqsIavMf"
COZE_BOT_ID = "7623699127591026742"
COZE_API_URL = "https://api.coze.com/v1/chat"  # 已改为 .com

# ========== 首页 ==========
@app.route('/')
def index():
    return "微信机器人运行中", 200

# ========== 微信接口（同时处理GET和POST）==========
@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    # GET请求：微信服务器验证
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 如果没有echostr，说明只是测试访问
        if not echostr:
            return "微信接口运行正常", 200
        
        # 验证签名
        params = sorted([WECHAT_TOKEN, timestamp, nonce])
        hash_str = hashlib.sha1("".join(params).encode()).hexdigest()
        
        if hash_str == signature:
            return echostr
        return "验证失败", 403
    
    # POST请求：接收用户消息
    if request.method == 'POST':
        try:
            # 获取XML数据
            xml_data = request.data
            root = ET.fromstring(xml_data)
            
            # 解析用户信息
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            # 只处理文本消息
            if msg_type == 'text':
                user_text = root.find('Content').text
                
                # 调用扣子AI
                reply_text = call_coze_api(user_text, from_user)
                
                # 构造回复XML
                reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""
                return reply_xml
            
            # 非文本消息，返回空
            return "success"
            
        except Exception as e:
            print(f"处理消息出错: {e}")
            return "success"

# ========== 调用扣子API ==========
def call_coze_api(query, user_id):
    """调用扣子AI Bot"""
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bot_id": COZE_BOT_ID,
        "user_id": user_id,
        "query": query,
        "stream": False
    }
    
    try:
        response = requests.post(COZE_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # 提取回复内容
            if 'content' in data:
                return data['content']
            elif 'messages' in data and len(data['messages']) > 0:
                return data['messages'][0].get('content', '抱歉，我无法回答这个问题')
            else:
                return "AI暂时无法响应"
        else:
            print(f"扣子API返回错误: {response.status_code}, {response.text}")
            return f"AI服务错误: {response.status_code}"
            
    except Exception as e:
        print(f"扣子API调用失败: {e}")
        return "系统繁忙，请稍后重试"

# ========== 启动服务 ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
