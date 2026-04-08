from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time
import json
from threading import Thread
import os

app = Flask(__name__)

# ========== 配置信息（已填好） ==========
WECHAT_TOKEN = 'wechat123456'
WECHAT_APPID = 'wxb0fdfd3539c92288'
WECHAT_SECRET = 'b27f6fde11739364be714dcca4becafd'
COZE_API_KEY = 'pat_8nHPY6IBnTz67KSF48N1H18dTgeWso7z3bYyFPUxzSytsGCHrFNJFPnVlqsIavMf'
COZE_BOT_ID = '7623699127591026742'
# ===========================================

# 获取access_token（带缓存）
access_token_cache = {'token': '', 'expires_at': 0}

def get_access_token():
    """获取微信access_token"""
    now = time.time()
    if access_token_cache['token'] and now < access_token_cache['expires_at']:
        return access_token_cache['token']
    
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_SECRET}'
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if 'access_token' in data:
            access_token_cache['token'] = data['access_token']
            access_token_cache['expires_at'] = now + 7000
            return data['access_token']
        else:
            print(f'获取access_token失败: {data}')
    except Exception as e:
        print(f'获取access_token异常: {e}')
    return None

def send_wechat_message(openid, content):
    """发送客服消息"""
    access_token = get_access_token()
    if not access_token:
        print('无法获取access_token')
        return
    
    url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}'
    data = {
        'touser': openid,
        'msgtype': 'text',
        'text': {'content': content}
    }
    try:
        requests.post(url, json=data, timeout=5)
        print(f'已发送消息给{openid}: {content[:50]}')
    except Exception as e:
        print(f'发送消息失败: {e}')

def call_coze(user_id, query):
    """调用扣子API"""
    headers = {
        'Authorization': f'Bearer {COZE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = 'https://api.coze.cn/v3/chat'
    payload = {
        'bot_id': COZE_BOT_ID,
        'user_id': user_id,
        'stream': False,
        'additional_messages': [
            {
                'role': 'user',
                'content': query,
                'content_type': 'text'
            }
        ]
    }
    
    print(f'调用扣子API，用户：{user_id}，问题：{query}')
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f'扣子API响应状态码：{response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'扣子返回：{result}')
            
            if 'messages' in result and len(result['messages']) > 0:
                ai_reply = result['messages'][0].get('content', '抱歉，我没有理解')
            elif 'content' in result:
                ai_reply = result['content']
            else:
                ai_reply = '暂时无法回答，请稍后再试'
            
            send_wechat_message(user_id, ai_reply)
        else:
            send_wechat_message(user_id, f'AI服务异常，请稍后再试')
    except requests.exceptions.Timeout:
        send_wechat_message(user_id, 'AI思考时间较长，请稍后再试')
    except Exception as e:
        print(f'扣子API调用失败: {e}')
        send_wechat_message(user_id, '系统繁忙，请稍后重试')

@app.route('/wechat', methods=['GET'])
def verify():
    """微信服务器验证"""
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    echostr = request.args.get('echostr')
    
    params = sorted([WECHAT_TOKEN, timestamp, nonce])
    hash_str = hashlib.sha1(''.join(params).encode()).hexdigest()
    
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
        
        reply = f'''<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{WECHAT_APPID}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[🤖 收到，正在思考...]]></Content>
</xml>'''
        
        Thread(target=call_coze, args=(from_user, user_text)).start()
        return reply
    
    return 'success'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)