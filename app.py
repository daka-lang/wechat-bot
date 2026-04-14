from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time
import logging

app = Flask(__name__)

# 设置日志
logging.basicConfig(level=logging.INFO)

# ========== 配置信息 ==========
WECHAT_TOKEN = "wechat123456"

# 扣子配置
COZE_API_KEY = "pat_8nHPY6IBnTz67KSF48N1H18dTgeWso7z3bYyFPUxzSytsGCHrFNJFPnVlqsIavMf"
COZE_BOT_ID = "7623699127591026742"
COZE_API_URL = "https://api.coze.cn/v3/chat"

@app.route('/')
def index():
    return "微信机器人运行中", 200

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
                
                app.logger.info(f"收到用户消息: {user_text} from {from_user}")
                
                # 调用扣子AI
                reply_text = call_coze_api(user_text, from_user)
                
                app.logger.info(f"回复内容: {reply_text}")
                
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
            app.logger.error(f"处理消息出错: {e}")
            return "success"

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
        app.logger.info(f"调用扣子API: {COZE_API_URL}")
        response = requests.post(COZE_API_URL, json=payload, headers=headers, timeout=30)
        
        app.logger.info(f"扣子API状态码: {response.status_code}")
        app.logger.info(f"扣子API响应: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            # 尝试多种可能的返回格式
            if 'content' in data:
                return data['content']
            elif 'message' in data:
                return data['message']
            elif 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0].get('message', {}).get('content', '无法解析回复')
            elif 'output' in data:
                return data['output']
            else:
                return f"解析失败，原始返回: {response.text[:100]}"
        else:
            return f"API错误({response.status_code})"
            
    except Exception as e:
        app.logger.error(f"扣子API异常: {e}")
        return f"系统错误: {str(e)[:50]}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
