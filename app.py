from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import os

app = Flask(__name__)

# 配置
WECHAT_TOKEN = "wechat123456"
COZE_API_KEY = "pat_QBqyqt7si3wJWXKLjgG2U4RMSv2wnQgsuRiUQ222IS1pWlVZYxzUo22ry6WJFLIV"
COZE_BOT_ID = "7623699127591026742"
COZE_API_URL = "https://api.coze.cn/v1/chat"

# ========== 添加这个根路由（在第108行之前） ==========
@app.route('/')
def index():
    """首页健康检查"""
    return "微信机器人运行中", 200


@app.route('/wechat', methods=['GET'])
def verify():
    """微信服务器验证"""
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    echostr = request.args.get('echostr')

    params = sorted([WECHAT_TOKEN, timestamp, nonce])
    hash_str = hashlib.sha1("".join(params).encode()).hexdigest()

    if hash_str == signature:
        return echostr
    return '验证失败'


@app.route('/wechat', methods=['POST'])
def handle_message():
    """接收和处理微信消息"""
    xml_data = request.data
    root = ET.fromstring(xml_data)

    from_user = root.find('FromUserName').text
    msg_type = root.find('MsgType').text

    if msg_type == 'text':
        user_text = root.find('Content').text
        
        # 调用扣子API
        reply_text = call_coze_api(user_text, from_user)
        
        # 返回XML回复
        reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{root.find('ToUserName').text}]]></FromUserName>
<CreateTime>{int(__import__('time').time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""
        return reply_xml
    
    return "success"


def call_coze_api(query, user_id):
    """调用扣子API"""
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
            # 根据扣子API返回格式提取内容
            if 'content' in data:
                return data['content']
            elif 'messages' in data and len(data['messages']) > 0:
                return data['messages'][0].get('content', '抱歉，我无法回答')
            else:
                return "AI暂时无法响应"
        else:
            return f"AI服务错误: {response.status_code}"
    except Exception as e:
        print(f'扣子API调用失败: {e}')
        return '系统繁忙，请稍后重试'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
