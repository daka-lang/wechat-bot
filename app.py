from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import requests
import time

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

# ========== 扣子配置 ==========
COZE_API_KEY = "pat_你新生成的令牌"  # 替换成你的
COZE_BOT_ID = "7623699127591026742"

# 扣子 API 地址
COZE_CHAT_URL = "https://api.coze.cn/v3/chat"
COZE_RETRIEVE_URL = "https://api.coze.cn/v3/chat/retrieve"  # 修改为正确的地址

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
                
                print(f"收到消息: {user_text}")
                
                reply_text = call_coze(user_text)
                
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

def call_coze(user_message):
    """调用扣子 API"""
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 第一步：发起对话
    chat_payload = {
        "bot_id": COZE_BOT_ID,
        "user_id": "wechat_user",
        "query": user_message,
        "stream": False
    }
    
    try:
        # 发起对话
        response = requests.post(COZE_CHAT_URL, json=chat_payload, headers=headers, timeout=30)
        result = response.json()
        print(f"发起对话响应: {result}")
        
        if result.get('code') != 0:
            return f"AI服务错误: {result.get('msg', '未知错误')}"
        
        chat_id = result.get('data', {}).get('id')
        conversation_id = result.get('data', {}).get('conversation_id')
        
        if not chat_id or not conversation_id:
            return "对话初始化失败"
        
        # 第二步：轮询获取回复（最多10次，每次等待1秒）
        for i in range(10):
            time.sleep(1)
            
            retrieve_payload = {
                "chat_id": chat_id,
                "conversation_id": conversation_id
            }
            retrieve_response = requests.post(
                COZE_RETRIEVE_URL, 
                json=retrieve_payload, 
                headers=headers, 
                timeout=10
            )
            retrieve_result = retrieve_response.json()
            print(f"第{i+1}次查询: {retrieve_result}")
            
            if retrieve_result.get('code') == 0:
                data = retrieve_result.get('data', {})
                # 尝试多种可能的回复字段
                if 'content' in data:
                    return data['content']
                elif 'messages' in data:
                    for msg in data['messages']:
                        if msg.get('role') == 'assistant':
                            return msg.get('content', '')
                elif 'answer' in data:
                    return data['answer']
            
            # 检查状态
            status = retrieve_result.get('data', {}).get('status')
            if status == 'failed':
                return "AI处理失败"
        
        return "AI响应超时，请稍后再试"
        
    except Exception as e:
        print(f"扣子调用异常: {e}")
        return f"系统错误: {str(e)[:50]}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
