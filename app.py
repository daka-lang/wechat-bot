#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import hashlib
import xml.etree.ElementTree as ET
import time
import re
import json

app = Flask(__name__)

WECHAT_TOKEN = "wechat123456"

# ========== 防重复机制（升级版）==========
# 记录用户最后回复时间
user_last_reply_time = {}
# 记录用户消息历史（用于频次限制）
user_message_history = {}

# 冷却时间（秒）：用户发送消息后，在这个时间内不回复第二条
REPLY_COOLDOWN = 3
# 时间窗口（秒）
TIME_WINDOW = 10
# 时间窗口内最大回复次数
MAX_REPLIES_IN_WINDOW = 2

def can_reply(user_id, message):
    """判断是否可以回复（防重复+频次限制）"""
    current_time = time.time()
    
    # 1. 冷却时间检查：用户刚发过消息，不回复
    if user_id in user_last_reply_time:
        time_since_last = current_time - user_last_reply_time[user_id]
        if time_since_last < REPLY_COOLDOWN:
            print(f"⏱️ 用户 {user_id} 在冷却期内（{time_since_last:.1f}秒），不回复")
            return False
    
    # 2. 频次限制检查：时间窗口内回复次数过多
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    
    # 清理过期记录
    user_message_history[user_id] = [
        t for t in user_message_history[user_id] 
        if current_time - t < TIME_WINDOW
    ]
    
    # 检查回复次数
    if len(user_message_history[user_id]) >= MAX_REPLIES_IN_WINDOW:
        print(f"⚠️ 用户 {user_id} 在{TIME_WINDOW}秒内回复次数过多，不回复")
        return False
    
    # 3. 相似消息检查（可选：短时间内相同消息不回复）
    # 这里简化处理，主要依靠冷却时间和频次限制
    
    return True

def record_reply(user_id):
    """记录一次回复"""
    current_time = time.time()
    user_last_reply_time[user_id] = current_time
    
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    user_message_history[user_id].append(current_time)

# ========== 人工介入机制 ==========
human_mode_cache = {}
HUMAN_MODE_DURATION = 24 * 60 * 60

def is_human_mode(user_id):
    if user_id in human_mode_cache:
        data = human_mode_cache[user_id]
        if time.time() - data["time"] < HUMAN_MODE_DURATION:
            return True
        else:
            del human_mode_cache[user_id]
    return False

def set_human_mode(user_id):
    human_mode_cache[user_id] = {"status": "human", "time": time.time()}
    print(f"✅ 用户 {user_id} 已切换到人工接管模式")

def clear_human_mode(user_id):
    if user_id in human_mode_cache:
        del human_mode_cache[user_id]
        print(f"✅ 用户 {user_id} 已恢复机器人回复模式")

# ========== 人工介入关键词 ==========
HUMAN_TRIGGER_KEYWORDS = [
    "转人工", "人工客服", "人工服务", "找真人", "真人客服",
    "客服在吗", "有人在吗", "帮我转人工", "我要找真人"
]

def is_request_human(text):
    for keyword in HUMAN_TRIGGER_KEYWORDS:
        if keyword in text:
            return True
    return False

# ========== 特定触发关键词 ==========
SPECIAL_TRIGGER_KEYWORDS = {
    "了解课程": "你好，欢迎咨询！课程内容比较丰富，为了更好地为您介绍适合孩子的课程，麻烦留下您的联系电话，我们会让班班与您详细沟通~",
    "咨询课程": "你好，欢迎咨询！课程内容比较丰富，为了更好地为您介绍适合孩子的课程，麻烦留下您的联系电话，我们会让班班与您详细沟通~",
    "课程咨询": "你好，欢迎咨询！课程内容比较丰富，为了更好地为您介绍适合孩子的课程，麻烦留下您的联系电话，我们会让班班与您详细沟通~",
    "我想咨询": "你好，欢迎咨询！课程内容比较丰富，为了更好地为您介绍适合孩子的课程，麻烦留下您的联系电话，我们会让班班与您详细沟通~",
}

def is_special_trigger(text):
    for keyword, reply in SPECIAL_TRIGGER_KEYWORDS.items():
        if keyword == text or keyword in text:
            return True, reply
    return False, None

# ========== 知识库 ==========
KNOWLEDGE = {
    "全称": "亲亲，咱们对外宣传使用'大咖素质训练营'，正式文件落款的全称是'海南郡唐美育科技有限公司'哦~",
    "运营": "您好，大咖素质训练营由海南郡唐美育科技有限公司运营，是海口市龙华区引进的科技龙头企业~",
    "成立": "您好，大咖素质训练营成立于2017年，至今已深耕素质教育领域多年~",
    "创始人": "亲亲，创始人是'璐瑶妈妈'，她深耕素质教育领域多年，帮助超10万家庭实现教育升级~",
    "璐瑶妈妈": "亲亲，璐瑶妈妈拥有多国跨文化生活经历，创立了树干学习法、城邦法等教育方法~",
    "使命": "亲亲，咱们的使命是'让每个孩子都享受高效学习的快乐，让每个员工都成为被感谢的人'~",
    "愿景": "您好，咱们的愿景是'成为中国家长最信任的在线教育平台'~",
    "官网": "亲亲，官方网址是 https://www.dkzsxt.com ~",
    "APP": "您好，官方APP叫'大咖素质训练营'，有阅读、表演、广播剧等多元化课程~",
    "投诉": "很抱歉给您带来的不便，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "退费": "很抱歉给您带来的不便，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "APP下载": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "app下载": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "下载APP": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "下载app": "您可以前往应用商店搜索【大咖素质训练营APP】，各大商店均可下载。",
    "谢谢": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    "感谢": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    "收到": "感谢您对大咖素质训练营的支持，祝您生活愉快！",
    "天外飞仙": "您是想了解怎么使用天外飞仙吗？这个可以跟您的班班沟通了解一下。",
    "英语情境法手工游戏": "亲亲，英语情境法手工游戏可以咨询21天英语班班或者英语阅读群班班。",
    "英语手工游戏": "亲亲，英语情境法手工游戏可以咨询21天英语班班或者英语阅读群班班。",
    "大语文手工游戏": "您好，所有涉及大语文的手工游戏，都可以找领袖群班班沟通。",
    "语文手工游戏": "您好，所有涉及大语文的手工游戏，都可以找领袖群班班沟通。",
    "大语文课程": "您好，咱们的大语文课程内容丰富，涵盖阅读、写作、传统文化等模块，不同阶段适合不同年龄段的孩子。为了给您推荐适合的课程阶段，麻烦留下您的联系电话，后续有专属老师会根据孩子的年龄和学习基础，详细介绍课程内容和适合程度~",
    "课程详情": "您好，想了解课程详情，麻烦您先留下您的联系电话，后续有专属老师会与您联系~老师会根据您的需求，了解孩子的年龄、学习基础等信息后，为您详细介绍课程内容、上课方式、费用、优惠活动等详情，帮您选择合适的课程~",
    "典范英语": "亲亲，典范英语是牛津树的中国引进版，1-6级适合小学生，7-10级适合中学生~",
    "典范": "亲亲，典范英语每月14-17日和28-31日有活动~",
    "牛津树": "亲亲，典范英语就是牛津树的中国引进版，语言地道、趣味性强~",
    "典范几级": "亲亲，1-6级适合小学生，7-10级适合中学生~",
    "点读笔": "亲亲，典范英语仅支持弘书阁点读笔~",
    "发货": "亲亲，14点前付款当天可发货（周日除外），一般24小时内发货~",
    "新疆": "亲亲，非常抱歉，新疆地区目前暂不能发货~",
    "西藏": "亲亲，非常抱歉，西藏地区目前暂不能发货~",
    "物流": "亲亲，14点前付款当天发货，周日除外~",
    "退款": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "退货": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "售后": "亲亲，请您简述您遇到的问题，并留下您的联系方式，我们尽快与您取得联系。",
    "发票": "亲亲，购买后3个月内可以申请开发票，需提供订单号和开票信息~",
    "优惠券": "亲亲，优惠券由平台发放，平台客服电话是4000862867~",
    "公益": "亲亲，咱们2020年向武汉慈善总会捐赠过，还成立了'璐瑶妈妈扶贫解困特别公益助学金'~",
    "捐赠": "亲亲，咱们参与过多次公益捐赠，包括抗疫、抗洪、抗震等~",
    "报道": "亲亲，咱们获得过光明网、新华社、人民网、人民日报等主流媒体报道~",
    "班班": "亲亲，如果您想找到您的班班，可以留下您的电话，我让班班和您联系",
}

APP_ISSUE_KEYWORDS = ["无法打开", "打不开", "闪退", "卡顿", "加载不了", "页面空白", "APP打不开", "app打不开", "APP无法打开", "app无法打开", "课程打不开", "视频打不开", "内容加载失败"]
COURSE_PURCHASE_KEYWORDS = ["购课", "买课", "付费", "购买", "下单", "支付", "付款", "怎么买", "怎么购", "如何购买", "如何购课", "多少钱", "价格", "费用", "收费", "价位", "想买", "想购", "要买", "要购"]
MEMBER_ISSUE_KEYWORDS = ["会员到期", "会员过期", "会员失效", "无法听故事", "听不了故事", "故事听不了", "故事播放不了", "找不到课程", "课程不见了", "课程找不到了", "课程消失", "会员怎么续", "会员续费", "续会员"]

def is_phone_number(text):
    phone_pattern = r'1[3-9]\d{9}'
    match = re.search(phone_pattern, text)
    return match is not None, match.group() if match else None

def is_app_issue(text):
    for keyword in APP_ISSUE_KEYWORDS:
        if keyword in text:
            return True
    return False

def is_course_purchase(text):
    for keyword in COURSE_PURCHASE_KEYWORDS:
        if keyword in text:
            return True
    return False

def is_member_issue(text):
    for keyword in MEMBER_ISSUE_KEYWORDS:
        if keyword in text:
            return True
    return False

@app.route('/')
def index():
    return "微信机器人运行中", 200

@app.route('/admin/set_human_mode', methods=['POST'])
def api_set_human_mode():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return {"code": 1, "msg": "缺少 user_id"}, 400
        set_human_mode(user_id)
        return {"code": 0, "msg": f"✅ 用户 {user_id} 已切换到人工模式"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}, 500

@app.route('/admin/clear_human_mode', methods=['POST'])
def api_clear_human_mode():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return {"code": 1, "msg": "缺少 user_id"}, 400
        clear_human_mode(user_id)
        return {"code": 0, "msg": f"✅ 用户 {user_id} 已恢复机器人模式"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}, 500

@app.route('/admin/human_mode_list', methods=['GET'])
def api_human_mode_list():
    users = []
    for user_id, data in human_mode_cache.items():
        remaining = HUMAN_MODE_DURATION - (time.time() - data["time"])
        users.append({
            "user_id": user_id,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data["time"])),
            "remaining_hours": round(remaining / 3600, 1)
        })
    return {"code": 0, "data": users}

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
                print(f"用户消息 [{from_user}]: {user_text}")
                
                # 检查人工模式
                if is_human_mode(from_user):
                    print(f"🚫 用户 {from_user} 处于人工接管模式，机器人不回复")
                    return "success"
                
                # 检查转人工
                if is_request_human(user_text):
                    set_human_mode(from_user)
                    reply_text = "您好，您的留言已记录，我们会尽快安排人工客服与您联系，请耐心等待~"
                    print(f"🔄 用户请求转人工")
                    # 记录回复
                    record_reply(from_user)
                else:
                    # ========== 防重复检查（核心修改）==========
                    if not can_reply(from_user, user_text):
                        print(f"🚫 防重复机制触发，不回复")
                        return "success"
                    
                    is_trigger, trigger_reply = is_special_trigger(user_text)
                    if is_trigger:
                        reply_text = trigger_reply
                        print(f"🎯 识别到特定触发关键词")
                    else:
                        has_phone, phone_num = is_phone_number(user_text)
                        if has_phone:
                            reply_text = f"您好，电话【{phone_num}】已收到，我们会尽快与您取得联系。"
                        elif is_app_issue(user_text):
                            reply_text = "请您留下您的联系电话，我让后台同事帮您查询一下，尽快给您回复。"
                        elif is_course_purchase(user_text):
                            reply_text = "请问您想咨询课程信息吗？如需详细咨询，麻烦留下您的联系电话~"
                        elif is_member_issue(user_text):
                            reply_text = "请您留下您的联系电话，我让后台同事帮您查询一下，尽快给您回复。"
                        else:
                            reply_text = get_reply(user_text)
                    
                    # 记录本次回复
                    record_reply(from_user)
                
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
    # 明确咨询意图识别
    consult_keywords = ["咨询", "想了解", "想咨询", "想学习", "想报名", "有兴趣", "考虑一下", "了解一下", "我也想"]
    for kw in consult_keywords:
        if kw in user_text:
            return f"感谢您的关注！课程内容比较丰富，为了更好地为您介绍适合孩子的课程，麻烦留下您的联系电话，我们会让班班与您详细沟通~"
    
    # 课程相关关键词
    course_keywords = ["报名", "怎么学", "上课"]
    for kw in course_keywords:
        if kw in user_text:
            return f"关于您的问题，内容比较丰富~为了更好地为您介绍，麻烦您留下联系电话，我会让班班与您详细沟通，为您推荐最合适的学习方案哦~"
    
    # 知识库匹配
    for keyword, reply in KNOWLEDGE.items():
        if keyword in user_text:
            return reply
    
    # 打招呼
    if any(word in user_text for word in ["你好", "您好", "嗨", "hi", "hello"]):
        return "您好~我是咖宝，请问有什么可以帮您的吗？"
    
    # 默认回复
    return "我是咖宝，请问您想咨询课程信息吗？如需详细咨询，麻烦留下您的联系电话~"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
