import os

INITIAL_CASH = 10000.0
INITIAL_REPUTATION = 0
INITIAL_DAY = 0
GAME_DAYS = 31

FIXED_COST_RENT = 200
FIXED_COST_UTILITIES = 100
FIXED_COST_OTHER = 50
FIXED_COST_TOTAL = FIXED_COST_RENT + FIXED_COST_UTILITIES + FIXED_COST_OTHER

LOAN_DEFAULT_DAYS = 10
LOAN_DAILY_INTEREST_RATE = 0.005
LOAN_MAX_MULTIPLIER = 3

RAW_MATERIALS = [
    {"id": "RC", "name": "A4纸", "base_price": 20, "unit": "张"},
]

PRODUCTS = [
    {"id": "CP", "name": "帽子", "recipe": {"RC": 1}},
]

RETAILERS = [
    {"id": "RT1", "name": "精品店", "price_multiplier": 2.5, "description": "出价最高，品质要求严"},
    {"id": "RT2", "name": "标准店", "price_multiplier": 1.8, "description": "价格适中，普通渠道"},
    {"id": "RT3", "name": "批发商", "price_multiplier": 1.2, "description": "大量收购，价格较低"},
]

DEMAND_TRENDS = [
    "近期市场对{product}需求旺盛，价格看涨",
    "市场对{product}需求平稳，价格稳定",
    "市场对{product}供过于求，价格有所下滑",
]

WEEKLY_SCHEDULE = {
    1:  {"name": "周一", "action": "采购日",   "desc": "购买原材料 A4纸", "allowed": ["buy"]},
    2:  {"name": "周二", "action": "生产日",   "desc": "用A4纸制作帽子",  "allowed": ["produce"]},
    3:  {"name": "周三", "action": "销售日",   "desc": "出售帽子给老师",  "allowed": ["sell"]},
    4:  {"name": "周四", "action": "收款/贷款","desc": "结算货款/申请贷款","allowed": ["loan", "repay"]},
    5:  {"name": "周五", "action": "计划日",   "desc": "制定下周经营计划","allowed": ["plan"]},
    6:  {"name": "周六", "action": "消费日",   "desc": "诚信商店开放",   "allowed": ["shop"]},
    7:  {"name": "周日", "action": "休息日",   "desc": "停业休息",      "allowed": []},
}

HONESTY_SHOP = [
    {"id": "S01", "name": "可乐",     "price": 5,  "emoji": "🥤"},
    {"id": "S02", "name": "冰淇淋",   "price": 8,  "emoji": "🍦"},
    {"id": "S03", "name": "薯片",     "price": 3,  "emoji": "🥨"},
    {"id": "S04", "name": "棒棒糖",   "price": 2,  "emoji": "🍭"},
    {"id": "S05", "name": "矿泉水",   "price": 1,  "emoji": "💧"},
    {"id": "S06", "name": "巧克力",   "price": 6,  "emoji": "🍫"},
    {"id": "S07", "name": "饼干",     "price": 4,  "emoji": "🍪"},
]

PRODUCT_GRADES = {
    "A": {"label": "优秀", "multiplier": 1.5, "color": "#66bb6a"},
    "B": {"label": "良好", "multiplier": 1.2, "color": "#4fc3f7"},
    "C": {"label": "合格", "multiplier": 0.8, "color": "#ffb74d"},
    "D": {"label": "待改进", "multiplier": 0.5, "color": "#ef5350"},
}
DEFAULT_GRADE = "B"

SCENARIO_CARDS = [
    {"id": "C01", "name": "优秀工匠",   "type": "reward",  "amount": 10, "desc": "帽子做工精美，获得额外奖金"},
    {"id": "C02", "name": "创意之星",   "type": "reward",  "amount": 15, "desc": "设计创意独特，获得创新奖励"},
    {"id": "C03", "name": "团队协作",   "type": "reward",  "amount": 8,  "desc": "帮助同桌解决问题，获得互助奖"},
    {"id": "C04", "name": "全勤奖",     "type": "reward",  "amount": 12, "desc": "本周全勤参与，获得全勤奖励"},
    {"id": "C05", "name": "诚信模范",   "type": "reward",  "amount": 10, "desc": "自觉遵守规则，获得诚信奖励"},
    {"id": "C06", "name": "延迟交货",   "type": "penalty", "amount": -5, "desc": "未能按时完成生产，扣除押金"},
    {"id": "C07", "name": "材料浪费",   "type": "penalty", "amount": -8, "desc": "制作过程中浪费材料，扣除成本"},
    {"id": "C08", "name": "课堂违纪",   "type": "penalty", "amount": -10,"desc": "违反课堂纪律，罚款处理"},
    {"id": "C09", "name": "操作失误",   "type": "penalty", "amount": -6, "desc": "操作流程错误导致损失，扣款"},
    {"id": "C10", "name": "市场机遇",   "type": "reward",  "amount": 20, "desc": "突遇市场需求暴增，获得额外订单"},
]

SAVES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")


def get_day_schedule(day):
    if day < 1 or day > GAME_DAYS:
        return None
    weekday = ((day - 1) % 7) + 1
    return WEEKLY_SCHEDULE.get(weekday)


def get_weekday_name(day):
    s = get_day_schedule(day)
    return s["name"] if s else f"第{day}天"


def get_allowed_actions(day):
    s = get_day_schedule(day)
    return s["allowed"] if s else []


def get_material_base_price(material_id):
    for m in RAW_MATERIALS:
        if m["id"] == material_id:
            return m["base_price"]
    return None


def get_product_info(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def get_material_name(material_id):
    for m in RAW_MATERIALS:
        if m["id"] == material_id:
            return m["name"]
    return material_id


def get_product_name(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p["name"]
    return product_id


def get_retailer_info(retailer_id):
    for r in RETAILERS:
        if r["id"] == retailer_id:
            return r
    return None


def get_shop_item(item_id):
    for s in HONESTY_SHOP:
        if s["id"] == item_id:
            return s
    return None


def get_scenario_card(card_id):
    for c in SCENARIO_CARDS:
        if c["id"] == card_id:
            return c
    return None


def get_grade_info(grade):
    return PRODUCT_GRADES.get(grade, PRODUCT_GRADES[DEFAULT_GRADE])


def get_grade_price(base_price, grade):
    info = get_grade_info(grade)
    return round(base_price * info["multiplier"], 2)