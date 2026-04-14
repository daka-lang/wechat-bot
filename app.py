from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

# ========== DeepSeek 配置 ==========
DEEPSEEK_API_KEY = "sk-a8393c12ec6445989eb1bcf0fb1f0229" 
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 系统提示词（定义AI的角色）
SYSTEM_PROMPT = """你是大咖素质训练营的客服助手，请友好、热情地回答用户的问题。
训练营主要提供素质教育和能力提升相关课程。
回答要简洁、有帮助，保持礼貌和专业的语气。"""

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
                
                print(f"收到用户消息: {user_text}")
                
                # 调用 DeepSeek AI
                reply_text = call_deepseek(user_text)
                
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
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10)
        
        print(f"DeepSeek 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            return reply
        else:
            print(f"DeepSeek 错误: {response.text}")
            return "AI服务暂时不可用，请稍后再试"
            
    except Exception as e:
        print(f"DeepSeek 调用失败: {e}")
        return "系统繁忙，请稍后再试"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
