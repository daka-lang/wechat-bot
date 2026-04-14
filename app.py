from flask import Flask, request
import hashlib
import xml.etree.ElementTree as ET
import time

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

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
                
                # 固定回复内容（可以根据不同消息自定义）
                if "你好" in user_text or "您好" in user_text:
                    reply_text = "你好呀！我是大咖素质训练营的客服助手，有什么可以帮你的吗？"
                elif "谢谢" in user_text:
                    reply_text = "不客气！有问题随时问我哦~"
                elif "帮助" in user_text or "help" in user_text.lower():
                    reply_text = "你可以问我关于大咖素质训练营的任何问题，我会尽力帮你解答！"
                else:
                    reply_text = f"收到你的消息：{user_text}\n\n（AI智能回复正在开发中，即将上线，敬请期待！）"
                
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
