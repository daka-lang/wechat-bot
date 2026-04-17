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
    
    # 投诉
    "投诉": "很抱歉给您带来的不便，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    
    # 退费
    "退费": "很抱歉给您带来的不便，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    
    # APP下载（使用【】代替中文引号，避免转义）
    "APP下载": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "app下载": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "下载APP": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "下载app": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    
    # 课程找不到/无法登录
    "课程找不到": "请留下你的联系方式，我让后台同事帮你查阅。查询完成后，给您回复。",
    "无法登录": "请留下你的联系方式，我让后台同事帮你查阅。查询完成后，给您回复。",
    "登录不上": "请留下你的联系方式，我让后台同事帮你查阅。查询完成后，给您回复。",
    "找不到课程": "请留下你的联系方式，我让后台同事帮你查阅。查询完成后，给您回复。",
    
    # 收到/谢谢
    "谢谢": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    "感谢": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    "收到": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    
    # 天外飞仙
    "天外飞仙": "您是想了解怎么使用天外飞仙吗？这个可以跟您的班班沟通了解一下。",
    
    # 英语情境法手工游戏
    "英语情境法手工游戏": "亲亲，英语情境法手工游戏可以咨询21天英语班班或者英语阅读群班班。",
    "英语手工游戏": "亲亲，英语情境法手工游戏可以咨询21天英语班班或者英语阅读群班班。",
    "手工游戏": "亲亲，手工游戏可以咨询您的班班。或者留下您的联系方式，让班班和您联系",
    
    # 大语文手工游戏
    "大语文手工游戏": "您好，所有涉及大语文的手工游戏，都可以找领袖群班班沟通。",
    "语文手工游戏": "您好，所有涉及大语文的手工游戏，都可以找领袖群班班沟通。",
    "手工游戏": "亲亲，手工游戏可以咨询您的班班。或者留下您的联系方式，让班班和您联系",
    
    # 大语文课程
    "大语文课程": "您好，咱们的大语文课程内容丰富，涵盖阅读、写作、传统文化等模块，不同阶段适合不同年龄段的孩子。为了给您推荐适合的课程阶段，麻烦留下您的联系电话，后续有专属老师会根据孩子的年龄和学习基础，详细介绍课程内容和适合程度~",
    
    # 课程详情
    "课程详情": "您好，想了解课程详情，麻烦您先留下您的联系电话，后续有班班会与您联系~班班会根据您的需求，了解孩子的年龄、学习基础等信息后，为您详细介绍课程内容、上课方式、费用、优惠活动等详情，帮您选择合适的课程~",
    
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
    "退款": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "退货": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "售后": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    
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
    "班班": "亲亲，如果您想找到您的班班，可以留下您的电话，我让班班和您联系",
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
    # 课程咨询类关键词（引导留电话）- 注意不要与大语文课程等重复
    course_keywords = ["报名", "费用", "怎么学", "多少钱", "怎么买", "上课", "学习", "咨询", "介绍"]
    for kw in course_keywords:
        if kw in user_text:
            # 避免重复匹配已处理的关键词
            if "课程详情" in user_text or "大语文课程" in user_text:
                break
            return f"关于您的问题，内容比较丰富~为了更好地为您介绍，麻烦您留下联系电话，我会让班班与您详细沟通，为您推荐最合适的学习方案哦~"
    
    # 检查知识库中的关键词
    for keyword, reply in KNOWLEDGE.items():
        if keyword in user_text:
            return reply
    
    # 打招呼
    if any(word in user_text for word in ["你好", "您好", "嗨", "hi", "hello"]):
        return "您好~我是咖宝，请问有什么可以帮您的吗？"
    
    # 默认回复
    return f"收到您的消息：{user_text}\n\n您好，我是咖宝。请问您想咨询课程信息吗？如需详细咨询，麻烦留下您的联系电话~"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
