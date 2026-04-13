from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time

app = Flask(__name__)

# ========== 配置信息 ==========
WECHAT_TOKEN = "wechat123456"

# 扣子配置（国内版 - 使用正确的 v3 接口）
COZE_API_KEY = "pat_8nHPY6IBnTz67KSF48N1H18dTgeWso7z3bYyFPUxzSytsGCHrFNJFPnVlqsIavMf"
COZE_BOT_ID = "7623699127591026742"
COZE_API_URL = "https://api.coze.cn/v3/chat"  # 正确的 API 地址

# ========== 首页 ==========
@app.route('/')
def index():
    return "微信机器人运行中", 200

# ========== 微信接口 ==========
@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    # GET请求：微信验证
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
    
    # POST请求：接收消息
    if request.method == 'POST':
        try:
            xml_data = request.data
            root = ET.fromstring(xml_data)
            
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            if msg_type == 'text':
                user_text = root.find('Content').text
                
                # 调用扣子AI
                reply_text = call_coze_api(user_text, from_user)
                
                reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""
                return reply_xml
            
            return "success"
            
        except Exception as e:
            print(f"错误: {e}")
            return "success"

# ========== 调用扣子API ==========
def call_coze_api(query, user_id):
    """调用扣子AI Bot - 使用 v3/chat 接口"""
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
        
        print(f"扣子API响应状态: {response.status_code}")
        print(f"扣子API响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            # v3 接口返回格式可能不同，尝试多种解析方式
            if 'content' in data:
                return data['content']
            elif 'message' in data:
                return data['message']
            elif 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0].get('message', {}).get('content', '抱歉，我无法回答')
            elif 'messages' in data and len(data['messages']) > 0:
                return data['messages'][0].get('content', '抱歉，我无法回答')
            else:
                return f"AI回复解析失败，请稍后重试"
        else:
            return f"AI服务错误: {response.status_code}"
            
    except Exception as e:
        print(f"扣子API调用失败: {e}")
        return "系统繁忙，请稍后重试"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
