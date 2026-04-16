#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import hashlib
import xml.etree.ElementTree as ET
import time

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

# ========== 知识库（关键词 -> 回复）==========
KNOWLEDGE = {
    # 品牌信息
    "全称": "亲亲，咱们对外宣传使用'大咖素质训练营'，正式文件落款的全称是'海南郡唐美育科技有限公司'哦~",
    "运营": "您好，大咖素质训练营由海南郡唐美育科技有限公司运营，是海口市龙华区引进的科技龙头企业~",
    "成立": "您好，大咖素质训练营成立于2017年，至今已深耕素质教育领域多年~",
    "创始人": "亲亲，创始人是'璐瑶妈妈'，她深耕素质教育领域多年，帮助超10万家庭实现教育升级~",
    "璐瑶妈妈": "亲亲，璐瑶妈妈拥有多国跨文化生活经历，创立了树干学习法、城邦法等教育方法~",
    "使命": "亲亲，咱们的使命是'让每个孩子都享受高效学习的快乐，让每个员工都成为被感谢的人'~",
    "愿景": "您好，咱们的愿景是'成为中国家长最信任的在线教育平台'~",
    "官网": "亲亲，官方网址是 https://www.dkzsxt.com ~",
    "APP": "您好，官方APP叫'大咖素质训练营'，有阅读、表演、广播剧等多元化课程~",
    "法人": "您好，企业法人对外统一使用'贾茹'这一名称~",
    
    # 典范英语
    "典范英语": "亲亲，典范英语是牛津树的中国引进版，1-6级适合小学生，7-10级适合中学生~",
    "典范": "亲亲，典范英语每月14-17日和28-31日有活动~",
    "牛津树": "亲亲，典范英语就是牛津树的中国引进版，语言地道、趣味性强~",
    "典范几级": "亲亲，1-6级适合小学生，7-10级适合中学生~",
    "点读笔": "亲亲，典范英语仅支持弘书阁点读笔~",
    
    # 物流
    "发货": "亲亲，14点前付款当天可发货（周日除外），一般24小时内发货~",
    "新疆": "亲亲，非常抱歉，新疆地区目前暂不能发货~",
    "西藏": "亲亲，非常抱歉，西藏地区目前暂不能发货~",
    "物流": "亲亲，14点前付款当天发货，周日除外~",
    
    # 售后
    "退款": "亲亲，课程为数字化商品，暂不支持退款。如有质量问题可按售后流程处理~",
    "退货": "亲亲，课程为数字化商品，暂不支持无理由退货~",
    "售后": "亲亲，复读机有问题可寄回：深圳市龙岗区横岗街道新世界广场四期A栋二楼U谷空间B202室，张小姐，14774806187~",
    
    # 发票
    "发票": "亲亲，购买后3个月内可以申请开发票，需提供订单号和开票信息~",
    
    # 优惠券
    "优惠券": "亲亲，优惠券由平台发放，平台客服电话是4000862867~",
    
    # 公益
    "公益": "亲亲，咱们2020年向武汉慈善总会捐赠过，还成立了'璐瑶妈妈扶贫解困特别公益助学金'~",
    "捐赠": "亲亲，咱们参与过多次公益捐赠，包括抗疫、抗洪、抗震等~",
    
    # 媒体报道
    "报道": "亲亲，咱们获得过光明网、新华社、人民网、人民日报等主流媒体报道~",
    
    # 社群
    "班班": "亲亲，英语情境法手工游戏可以咨询21天英语班班或英语阅读群班班~",
}

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
                print(f"用户消息: {user_text}")
                
                reply_text = get_reply(user_text)
                
                print(f"回复: {reply_text[:50]}...")
                
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

def get_reply(user_text):
    """根据关键词匹配回复"""
    # 课程咨询类关键词（引导留电话）
    course_keywords = ["课程", "报名", "费用", "怎么学", "多少钱", "怎么买", "上课", "学习", "咨询", "介绍"]
    for kw in course_keywords:
        if kw in user_text:
            return f"关于{user_text}，内容比较丰富呢~为了更好地为您介绍，麻烦您留下联系电话，专属老师会与您详细沟通，为您推荐最合适的学习方案哦~"
    
    # 检查知识库中的关键词
    for keyword, reply in KNOWLEDGE.items():
        if keyword in user_text:
            return reply
    
    # 打招呼
    if any(word in user_text for word in ["你好", "您好", "嗨", "hi", "hello"]):
        return "您好~我是大咖素质训练营的客服助手，请问有什么可以帮您的吗？"
    
    # 默认回复
    return f"收到您的消息：{user_text}\n\n您好，我是大咖素质训练营的客服助手。请问您想咨询课程信息、典范英语还是其他问题呢？如需详细咨询，麻烦留下您的联系电话~"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
