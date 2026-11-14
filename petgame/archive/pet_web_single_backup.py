from datetime import date, datetime, timedelta
import colorsys
import html as _html
import os
import random
import re

import streamlit as st

# ===================== 宠物与玩法常量 =====================
PET_SPECIES = ["猫", "狗", "机器人", "小羊", "小鸡", "豹子", "兔子",
               "仓鼠", "狐狸", "企鹅", "青蛙", "小熊",
               "机械蜂", "小鹿", "小龙", "史莱姆", "布丁",
               "机械鼠", "机甲兔", "小鸭", "熊猫", "小狼", "小马",
               "独角兽", "麒麟", "豆豆", "蘑菇仔", "甜甜圈", "饭团",
               "机甲龟", "机械狮", "小刺猬", "小猪", "小松鼠",
               "凤凰", "貔貅", "方块仔", "炸弹仔", "小笼包", "冰淇淋"]
PET_LABEL = {
    "猫": "猫咪",
    "狗": "狗狗",
    "机器人": "机器人",
    "小羊": "小羊",
    "小鸡": "小鸡",
    "豹子": "豹子",
    "兔子": "兔子",
    "仓鼠": "仓鼠",
    "狐狸": "狐狸",
    "企鹅": "企鹅",
    "青蛙": "青蛙",
    "小熊": "小熊",
    "机械蜂": "机械蜂",
    "小鹿": "小鹿",
    "小龙": "小龙",
    "史莱姆": "史莱姆",
    "布丁": "布丁",
    "机械鼠": "机械鼠",
    "机甲兔": "机甲兔",
    "小鸭": "小鸭",
    "熊猫": "熊猫",
    "小狼": "小狼",
    "小马": "小马",
    "独角兽": "独角兽",
    "麒麟": "麒麟",
    "豆豆": "豆豆",
    "蘑菇仔": "蘑菇仔",
    "甜甜圈": "甜甜圈",
    "饭团": "饭团",
    "机甲龟": "机甲龟",
    "机械狮": "机械狮",
    "小刺猬": "小刺猬",
    "小猪": "小猪",
    "小松鼠": "小松鼠",
    "凤凰": "凤凰",
    "貔貅": "貔貅",
    "方块仔": "方块仔",
    "炸弹仔": "炸弹仔",
    "小笼包": "小笼包",
    "冰淇淋": "冰淇淋",
}
# 图鉴分类：五类，每个物种只归一类，图鉴页按这个顺序分栏展示
PET_CATEGORIES = [
    {"key": "mech", "name": "机械类", "desc": "齿轮与电流做的伙伴",
     "pets": ["机器人", "机械蜂", "机械鼠", "机甲兔", "机甲龟", "机械狮"]},
    {"key": "cute", "name": "萌宠类", "desc": "毛茸茸、软呼呼",
     "pets": ["猫", "狗", "小羊", "小鸡", "兔子", "仓鼠", "小熊", "豹子", "企鹅", "小鹿",
              "小鸭", "熊猫", "小狼", "小马", "小刺猬", "小猪", "小松鼠"]},
    {"key": "myth", "name": "神话类", "desc": "传说里走出来的生灵",
     "pets": ["狐狸", "小龙", "独角兽", "麒麟", "凤凰", "貔貅"]},
    {"key": "game", "name": "游戏类", "desc": "从游戏机里跳出来的",
     "pets": ["青蛙", "史莱姆", "豆豆", "蘑菇仔", "方块仔", "炸弹仔"]},
    {"key": "food", "name": "美食类", "desc": "看着就想咬一口",
     "pets": ["布丁", "甜甜圈", "饭团", "小笼包", "冰淇淋"]},
]
PET_CATEGORY_OF = {sp: c["name"] for c in PET_CATEGORIES for sp in c["pets"]}
# 旧存档里宠物名字后面可能还带着表情符号，用这张表反推宠物种类
EMOJI_SPECIES = {
    "🐱": "猫", "🐈": "猫",
    "🐕": "狗", "🐶": "狗",
    "🤖": "机器人",
    "🐏": "小羊", "🐑": "小羊",
    "🐥": "小鸡", "🐤": "小鸡",
    "🐆": "豹子",
    "🐰": "兔子", "🐇": "兔子",
    "🐹": "仓鼠",
    "🦊": "狐狸",
    "🐧": "企鹅",
    "🐸": "青蛙",
    "🐻": "小熊",
    "🐝": "机械蜂",
    "🦌": "小鹿",
    "🐉": "小龙", "🐲": "小龙",
    "🟢": "史莱姆",
    "🍮": "布丁",
    "🐭": "机械鼠",
    "🦆": "小鸭",
    "🐼": "熊猫",
    "🐺": "小狼",
    "🐴": "小马",
    "🦄": "独角兽",
    "🍄": "蘑菇仔",
    "🍩": "甜甜圈",
    "🍙": "饭团",
    "🐢": "机甲龟",
    "🦁": "机械狮",
    "🦔": "小刺猬",
    "🐷": "小猪",
    "🐿": "小松鼠",
    "💣": "炸弹仔",
    "🥟": "小笼包",
    "🍦": "冰淇淋",
}

start_pet = PET_SPECIES

random_event_list = [
    {"name": "捡到积分", "type": "gain_df",
        "msg": "出门散步，在路边捡到了一些积分！", "val": random.randint(15, 40)},
    {"name": "捡到药品", "type": "gain_item", "msg": "草丛里发现了一瓶药品！", "item": "药品"},
    {"name": "捡到急救针", "type": "gain_item", "msg": "运气不错，捡到一支急救针！", "item": "急救针"},
    {"name": "捡到全能营养膏", "type": "gain_item",
        "msg": "发现一支未拆封的全能营养膏！", "item": "全能营养膏"},
    {"name": "宠物突然生病", "type": "lose_health",
        "msg": "宠物突然不舒服，健康下降！", "val": random.randint(15, 30)},
    {"name": "偶遇好心人", "type": "gain_df",
        "msg": "好心人送给你一些积分！", "val": random.randint(20, 50)},
    {"name": "宠物开心蹦跶", "type": "gain_hn",
        "msg": "宠物看到蝴蝶，开心值上升！", "val": random.randint(10, 25)},
    {"name": "宠物饿了", "type": "lose_ha",
        "msg": "宠物肚子饿了，饱腹下降！", "val": random.randint(10, 20)},
    {"name": "下雨弄脏了", "type": "lose_cl",
        "msg": "下雨踩泥坑，清洁值下降！", "val": random.randint(10, 25)},
    {"name": "无事发生", "type": "none", "msg": "平平淡淡的一天，没有特殊事情。"}
]
event_weights = [4, 3, 2, 3, 2, 4, 4, 2, 2, 3]

explore_event_pool = [
    {"type": "gain_df", "msg": "路上捡到一袋积分！",
        "val_range": (20, 60), "rare": False},
    {"type": "gain_item", "msg": "找到一个物资包！", "item_list": [
        "面包", "葡萄", "零食", "药品"], "rare": False},
    {"type": "gain_rare_item", "msg": "发现隐藏宝箱！",
        "item_list": ["高级营养液", "幸运徽章", "宠物强化剂"], "rare": True},
    {"type": "gain_hn", "msg": "宠物在外玩得超开心！开心值上涨",
        "val_range": (15, 35), "rare": False},
    {"type": "lose_health", "msg": "探索路上被荆棘划伤，宠物健康下降",
        "val_range": (10, 25), "rare": False},
    {"type": "lose_cl", "msg": "泥潭里打滚，宠物变得脏兮兮",
        "val_range": (15, 30), "rare": False},
    {"type": "none", "msg": "安安静静逛了一圈，没遇到特别的事", "rare": False},
]
explore_config = {
    "1": {"name": "短途探索", "cost": 10, "rare_rate": 0.08, "bad_rate": 0.20},
    "2": {"name": "中途探索", "cost": 25, "rare_rate": 0.18, "bad_rate": 0.30},
    "3": {"name": "长途探索", "cost": 50, "rare_rate": 0.32, "bad_rate": 0.42},
}
EXPLORE_BASE_COOLDOWN = timedelta(minutes=30)
# 随机事件节流：固定两小时一次，改这个数字即可调整间隔
RAND_EVENT_INTERVAL = timedelta(hours=2)

daily_task_list = [
    {"id": 1, "name": "陪宠物玩耍", "desc": "和宠物玩耍一次", "action": "play", "reward": 10},
    {"id": 2, "name": "给宠物洗澡", "desc": "给宠物洗一次澡", "action": "bath", "reward": 10},
    {"id": 3, "name": "投喂食物", "desc": "给宠物投喂任意食物", "action": "feed", "reward": 10},
    {"id": 4, "name": "逛一次商店", "desc": "进入商店（不需要购买）", "action": "shop", "reward": 10},
    {"id": 5, "name": "买一张彩票", "desc": "进入彩票店购买任意彩票",
        "action": "lottery", "reward": 10}
]

# 周任务：进度按“总量 - 本周起点”计算，每周一自动重置
WEEK_TASK_LIST = [
    {"id": "w1", "name": "勤奋铲屎官", "desc": "本周累计投喂 10 次",
     "metric": "feed", "target": 10, "reward": 30},
    {"id": "w2", "name": "彩票爱好者", "desc": "本周累计购买彩票 3 次",
     "metric": "lottery", "target": 3, "reward": 30},
    {"id": "w3", "name": "资深探险家", "desc": "本周累计探索 5 次",
     "metric": "explore", "target": 5, "reward": 40},
]

RENAME_COST = 20


def mood_tag(pet):
    """心情标签：开心值联动称号、衰减速度和随机事件倾向。"""
    hn = float(pet.get("hn", 150))
    if hn >= 130:
        return {"key": "great", "label": "超开心", "decay": 0.85, "luck": "good"}
    if hn < 30:
        return {"key": "low", "label": "有点郁闷", "decay": 1.15, "luck": "bad"}
    return {"key": "normal", "label": "心情平稳", "decay": 1.0, "luck": "none"}


SEASON_DAYS = 3
SEASON_EPOCH = date(2026, 1, 1)
SEASON_ORDER = ["春", "夏", "秋", "冬"]
SEASON_INFO = {
    "春": {
        "name": "春季", "deco": "樱花", "shop": "春日花束",
        "ha": 1.0, "cl": 1.0, "hn": 0.95,
        "note": "气候温和，心情不易低落",
        "color": "#8FBF7A",
    },
    "夏": {
        "name": "夏季", "deco": "蝉鸣", "shop": "冰镇西瓜",
        "ha": 0.9, "cl": 1.5, "hn": 1.05,
        "note": "天热出汗多，清洁掉得快",
        "color": "#7FC7E8",
    },
    "秋": {
        "name": "秋季", "deco": "落叶", "shop": "丰收南瓜派",
        "ha": 0.8, "cl": 1.0, "hn": 1.0,
        "note": "天气凉爽，胃口更好，饱腹掉得慢",
        "color": "#E8A83B",
    },
    "冬": {
        "name": "冬季", "deco": "雪", "shop": "姜茶",
        "ha": 1.5, "cl": 1.05, "hn": 1.1,
        "note": "天气寒冷，热量消耗快，饱腹掉得快",
        "color": "#C6D8E8",
    },
}
SEASON_EVENTS = {
    "春": [
        {"name": "春风拂面", "type": "gain_hn", "val": 20,
         "msg": "春风拂面，宠物开心得原地转圈！"},
        {"name": "采到野花", "type": "gain_item", "item": "春日花束",
         "msg": "路边摘到一束野花，顺手收进仓库！"},
    ],
    "夏": [
        {"name": "冰镇西瓜", "type": "gain_item", "item": "冰镇西瓜",
         "msg": "买到半个冰镇西瓜，宠物吃得满脸汁水！"},
        {"name": "酷暑难耐", "type": "lose_cl", "val": 25,
         "msg": "天太热了，宠物出了一身汗，清洁值下降！"},
    ],
    "秋": [
        {"name": "丰收季", "type": "gain_item", "item": "丰收南瓜派",
         "msg": "秋收季节，邻居送来一份南瓜派！"},
        {"name": "秋高气爽", "type": "gain_hn", "val": 25,
         "msg": "秋高气爽，宠物在草地上打了个滚！"},
    ],
    "冬": [
        {"name": "寒风刺骨", "type": "lose_ha", "val": 20,
         "msg": "寒风刺骨，宠物饿得更快了，饱腹值下降！"},
        {"name": "围炉取暖", "type": "gain_hn", "val": 25,
         "msg": "在暖炉边烤火，宠物舒服地打起呼噜！"},
    ],
}


def season_of(day=None):
    """按日期算出当前季节，以及这一季还剩几天。"""
    d = day or date.today()
    idx = ((d - SEASON_EPOCH).days // SEASON_DAYS) % 4
    key = SEASON_ORDER[idx]
    info = dict(SEASON_INFO[key])
    info["key"] = key
    passed = ((d - SEASON_EPOCH).days % SEASON_DAYS) + 1
    info["day_in_season"] = passed
    info["left_days"] = SEASON_DAYS - passed + 1
    next_idx = (idx + 1) % 4
    info["next"] = SEASON_ORDER[next_idx]
    return info


achievement_list = [
    {"aid": 1, "title": "初次相伴", "desc": "解锁你的第一只宠物", "cond": "first_pet"},
    {"aid": 2, "title": "勤劳铲屎官", "desc": "累计完成10次每日任务", "cond": "task10"},
    {"aid": 3, "title": "幸运之星", "desc": "彩票中一次大奖", "cond": "lottery_win"},
    {"aid": 4, "title": "喂养达人", "desc": "累计投喂20次", "cond": "feed20"},
    {"aid": 5, "title": "成长伙伴", "desc": "宠物升到5级", "cond": "lv5"},
    {"aid": 6, "title": "初探秘境", "desc": "累计完成10次探索", "cond": "explore10"},
    {"aid": 7, "title": "寻踪不倦", "desc": "累计完成100次探索", "cond": "explore100"},
    {"aid": 8, "title": "秘境欧皇", "desc": "探索时拿到稀有宝箱奖励", "cond": "explore_rare_once"},
    {"aid": 9, "title": "星辉觉醒", "desc": "将一只宠物转化为星辉形态", "cond": "star_awake"},
    {"aid": 10, "title": "群星同行", "desc": "拥有3只星辉宠物", "cond": "star_3pet"},
    {"aid": 11, "title": "星途无尽", "desc": "使用星辉宠物完成50次探索", "cond": "star_explore50"},
    {"aid": 12, "title": "星能掌控者", "desc": "累计释放星辉技能50次", "cond": "star_skill50"},
    {"aid": 13, "title": "图鉴初成", "desc": "点亮 7 格图鉴", "cond": "dex7"},
    {"aid": 14, "title": "五行归一", "desc": "任意宠物进化到 5 阶", "cond": "evo5"},
]

shop_things = ["面包", "电池", "鲜鱼", "护发素", "玩具", "葡萄", "肥皂",
               "零食", "药品", "急救针", "全能营养膏", "高级营养液", "幸运徽章",
               "宠物强化剂", "除臭喷雾", "小零食礼包", "经验果",
               "星尘", "星尘结晶", "星光皮肤券"]
shop_desc = {
    "面包": "增加 10 点饱腹值",
    "电池": "增加机器人的饱腹值，给其他宠物会倒扣",
    "鲜鱼": "给猫吃会额外增加 5 点饱腹值",
    "护发素": "增加 15 点宠物开心值",
    "玩具": "增加 20 点宠物开心值",
    "葡萄": "增加 30 点饱食度",
    "肥皂": "洗澡时使用，本次洗澡额外 +40 清洁值",
    "零食": "增加 25 点开心值",
    "药品": "恢复 40 点健康值",
    "急救针": "紧急施救，直接把健康拉到 50（救急专用）",
    "全能营养膏": "饱腹 +25，开心 +25，健康 +25",
    "高级营养液": "饱腹 +40，开心 +40，健康 +40",
    "幸运徽章": "携带后，全局随机事件好事概率小幅提升（被动）",
    "宠物强化剂": "蕴含星辉之力的神秘药剂，宠物等级达到 10 级，消耗本品，将宠物转化为【星辉状态】，解锁大量额外增益。",
    "除臭喷雾": "清洁 +45，且不会占用洗澡冷却（不产生经验）",
    "小零食礼包": "打开随机获得 2 份零食类道具，开心值靠零食慢慢补",
    "经验果": "直接增加 35 点经验，不占饱腹、不触发投喂任务",
    "春日花束": "春季限定 · 开心 +30，花瓣带一点青草香",
    "冰镇西瓜": "夏季限定 · 饱腹 +25、清洁 +10，解暑又解饿",
    "丰收南瓜派": "秋季限定 · 饱腹 +30、健康 +10，秋收的味道",
    "姜茶": "冬季限定 · 健康 +20、开心 +10，寒冬里最暖的一杯",
    "星尘": "星辉升级材料。星辉 1~10 级每升一级都要消耗，探索稀有宝箱也会掉。",
    "星尘结晶": "进化的钥匙。宠物 25 级后可用来选择进化方向与五行元素，之后每阶也各需数枚。",
    "星光皮肤券": "给宠物换上星辉皮肤（纯外观，不加任何属性）。再次使用可切回普通外观。",
}
price_dict = {
    "面包": 10, "电池": 15, "鲜鱼": 12, "护发素": 20, "玩具": 25, "葡萄": 18, "肥皂": 22, "零食": 15,
    "药品": 30, "急救针": 40, "全能营养膏": 45, "高级营养液": 60, "幸运徽章": 80, "宠物强化剂": 120,
    "除臭喷雾": 26, "小零食礼包": 34, "经验果": 45,
    "星尘": 40, "星尘结晶": 150, "星光皮肤券": 100,
    "春日花束": 28, "冰镇西瓜": 26, "丰收南瓜派": 28, "姜茶": 30
}

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u2600-\u26FF]"
)


def strip_emoji(text):
    """去掉名字里的表情符号，只留下文字。"""
    return _EMOJI_RE.sub("", str(text)).strip()


def infer_species(name):
    """根据名字（可能带旧表情符号）推断宠物种类。"""
    raw = str(name)
    for emo, sp in EMOJI_SPECIES.items():
        if emo in raw:
            return sp
    base = strip_emoji(raw)
    for sp in PET_SPECIES:
        if sp in base:
            return sp
    return "猫"


def normalize_pet(pet):
    """补全旧存档字段，并把名字里的表情符号清理掉。"""
    raw_name = str(pet.get("name", ""))
    sp = pet.get("species")
    if sp not in PET_SPECIES:
        sp = infer_species(raw_name)
    clean = strip_emoji(raw_name)
    pet["species"] = sp
    pet["name"] = clean or sp
    pet.setdefault("is_star", False)
    # 星辉等级：觉醒即有 1 级，未觉醒为 0；进化方向与元素默认空
    if pet.get("is_star"):
        pet["star_lv"] = max(1, min(10, int(pet.get("star_lv", 1) or 1)))
    else:
        pet["star_lv"] = 0
    pet["evo_branch"] = pet.get("evo_branch") or ""
    if pet["evo_branch"] not in EVO_BRANCHES:
        pet["evo_branch"] = ""
    pet["evo_lv"] = max(0, min(EVO_MAX_LV, int(pet.get("evo_lv", 0) or 0)))
    pet["element"] = pet.get("element") or ""
    if pet["element"] not in ELEMENTS:
        pet["element"] = ""
    # 皮肤（纯外观）：normal / star 为旧值，主题皮肤存主题名（糖果/夜行/森野）
    skin = pet.get("skin")
    if skin not in ("normal", "star") and skin not in SKIN_THEMES:
        pet["skin"] = "normal"
    return pet


def species_of(pet):
    sp = pet.get("species")
    if sp in PET_SPECIES:
        return sp
    return infer_species(pet.get("name", ""))


# ===================== 星辉等级 · 进化方向 · 五行元素 =====================
STAR_MAX_LV = 10          # 未进化时星辉等级上限
EVO_MAX_LV = 5            # 三个进化方向各 5 级
STAR_DUST = "星尘"
STAR_CRYSTAL = "星尘结晶"

# 五行元素：优点固定，缺点也固定，选一个就得接受它的代价
ELEMENTS = {
    "金": {"name": "金", "tag": "锐意", "pro": "经验 +12%", "con": "开心衰减 +12%",
           "exp": 1.12, "df": 1.0, "cl": 1.0, "ha": 1.0, "hn": 1.12,
           "heal": 1.0, "hloss": 1.0},
    "木": {"name": "木", "tag": "生机", "pro": "健康回复 +25%", "con": "清洁衰减 +15%",
           "exp": 1.0, "df": 1.0, "cl": 1.15, "ha": 1.0, "hn": 1.0,
           "heal": 1.25, "hloss": 1.0},
    "水": {"name": "水", "tag": "凉润", "pro": "清洁衰减 -25%", "con": "饱腹衰减 +12%",
           "exp": 1.0, "df": 1.0, "cl": 0.75, "ha": 1.12, "hn": 1.0,
           "heal": 1.0, "hloss": 1.0},
    "火": {"name": "火", "tag": "炽烈", "pro": "开心衰减 -20%", "con": "健康流失 +10%",
           "exp": 1.0, "df": 1.0, "cl": 1.0, "ha": 1.0, "hn": 0.80,
           "heal": 1.0, "hloss": 1.10},
    "土": {"name": "土", "tag": "厚实", "pro": "饱腹衰减 -20%", "con": "开心衰减 +15%",
           "exp": 1.0, "df": 1.0, "cl": 1.0, "ha": 0.80, "hn": 1.15,
           "heal": 1.0, "hloss": 1.0},
}
ELEMENT_ORDER = ["金", "木", "水", "火", "土"]

# 三个进化方向：主增益随阶数递增，副作用固定不放大
EVO_BRANCHES = {
    "战意": {"name": "战意", "tag": "狂野", "desc": "越战越勇，成长与收获都快，代价是耗得也快",
             "pro": "经验 +4%/阶、积分收益 +5%/阶", "con": "三项衰减 ×1.15",
             "color": "#C05262"},
    "守护": {"name": "守护", "tag": "坚韧", "desc": "稳扎稳打，状态几乎不掉，代价是成长慢些",
             "pro": "衰减 -5%/阶、健康回复 +10%/阶", "con": "经验 -10%",
             "color": "#4C8A63"},
    "灵能": {"name": "灵能", "tag": "星感", "desc": "与星象共鸣，探索与事件更走运，代价是更费体力",
             "pro": "稀有率 +1.6%/阶、好事权重 +1/阶", "con": "饱腹衰减 ×1.25",
             "color": "#6A5ACD"},
}
EVO_ORDER = ["战意", "守护", "灵能"]
ELEM_RESET_COST = 30                  # 重塑元素的手续费
SKIN_PRICE = 100                      # 皮肤售价（积分）
# 主题皮肤：纯外观，改配色 + 专属光效；购买时自动绑定当前宠物的物种
SKIN_THEMES = {
    "糖果": {"hue": 315, "sat": 1.25, "glow": "#FF7AB6",
             "bg": ("#FFF3FA", "#FFDCEB"), "desc": "糖果配色，粉紫渐变，甜到发光",
             "room": {"wall": "#FFF0F8", "wall2": "#FFD9EA", "skirt": "#F0A2C4",
                      "floor": "#E8C8D8", "floor2": "#D6A8BF",
                      "sky": "#FFE4F2", "cloud": "#FFFFFF",
                      "rug1": "#FFCFE2", "rug2": "#FFEBF4", "rug3": "#EFA6C6",
                      "wood": "#9C6A55", "wood2": "#B98069", "frame": "#7E4A55",
                      "deco": "#FF7AB6", "night": False}},
    "夜行": {"hue": 205, "sat": 0.95, "glow": "#4AA8E0",
             "bg": ("#EAF2FB", "#CFE2F5"), "desc": "夜色冷蓝，像披了件夜行斗篷",
             "room": {"wall": "#1E2B48", "wall2": "#27365A", "skirt": "#3B4F7E",
                      "floor": "#182338", "floor2": "#223050",
                      "sky": "#0E1B33", "cloud": "#4A6CA4",
                      "rug1": "#40598C", "rug2": "#5B7CB4", "rug3": "#2E4468",
                      "wood": "#5A4432", "wood2": "#71563E", "frame": "#3A2A1E",
                      "deco": "#7CC6F2", "night": True}},
    "森野": {"hue": 85, "sat": 1.05, "glow": "#7CC94E",
             "bg": ("#F1FBE8", "#D8F2C6"), "desc": "草木青绿，带一身林间气息",
             "room": {"wall": "#EFF7E0", "wall2": "#DCEEC4", "skirt": "#9CC47A",
                      "floor": "#C6D8A2", "floor2": "#B2C78C",
                      "sky": "#D8F3E4", "cloud": "#FFFFFF",
                      "rug1": "#C4DF9E", "rug2": "#E0F1C6", "rug3": "#A6CB80",
                      "wood": "#7C5A34", "wood2": "#966E42", "frame": "#4E3A24",
                      "deco": "#7CC94E", "night": False}},
}
SKIN_ORDER = ["糖果", "夜行", "森野"]
# 彩票概率（固定，不再随宠物种类浮动）
LOT_BIG_P = 5                         # 大奖 5%
LOT_MID_P = 30                        # 高级奖 30%
LOT_NONE_P = 65                       # 不中奖 65%
EVO_LV_GATE = {1: 25, 2: 30, 3: 35, 4: 40, 5: 45}   # 每一阶的宠物等级门槛
EVO_LV_COST = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}        # 每一阶消耗的星尘结晶


def star_up_cost(slv):
    """星辉从 slv 升到 slv+1 需要 (星尘个数, 积分)。"""
    s = max(1, int(slv))
    return s, 15 * s


def pet_bonus(pet):
    """把星辉等级、进化方向、五行元素合成一套乘算增益。

    未觉醒时全部为 1（没有任何加成）；觉醒后逐级给，不再“有星辉就拥有全部”。
    """
    b = {"exp": 1.0, "df": 1.0, "cl": 1.0, "ha": 1.0, "hn": 1.0,
         "heal": 1.0, "hloss": 1.0, "rare": 0.0, "luck": 0,
         "star_lv": 0, "branch": "", "element": "", "evo_lv": 0, "guard": 1.0}
    if not pet.get("is_star", False):
        return b
    slv = max(1, min(STAR_MAX_LV, int(pet.get("star_lv", 1) or 1)))
    b["star_lv"] = slv
    st = 1 - 0.04 * slv              # 1 级 ×0.96 → 10 级 ×0.60
    b["cl"] *= st
    b["ha"] *= st
    b["hn"] *= st
    b["guard"] = st
    b["exp"] *= 1 + 0.03 * slv       # 1 级 ×1.03 → 10 级 ×1.30
    b["heal"] *= 1 + 0.10 * slv      # 满级 2.0 倍（对应原来的 0.24 回复）
    el = ELEMENTS.get(pet.get("element") or "")
    if el:
        b["element"] = el["name"]
        for k in ("exp", "df", "cl", "ha", "hn", "heal", "hloss"):
            b[k] *= el[k]
    br = pet.get("evo_branch") or ""
    ev = int(pet.get("evo_lv", 0) or 0)
    if br in EVO_BRANCHES and ev > 0:
        b["branch"] = br
        b["evo_lv"] = ev
        if br == "战意":
            b["exp"] *= 1 + 0.04 * ev
            b["df"] *= 1 + 0.05 * ev
            b["cl"] *= 1.15
            b["ha"] *= 1.15
            b["hn"] *= 1.15
        elif br == "守护":
            d = 1 - 0.05 * ev
            b["cl"] *= d
            b["ha"] *= d
            b["hn"] *= d
            b["heal"] *= 1 + 0.10 * ev
            b["exp"] *= 0.90
        else:
            b["rare"] += 0.016 * ev
            b["luck"] += ev
            b["ha"] *= 1.25
    return b


def bonus_summary(pet):
    """面板上的一行增益说明：让玩家一眼看到自己的优点与代价。"""
    if not pet.get("is_star", False):
        return "尚未觉醒星辉（10 级后使用宠物强化剂）"
    b = pet_bonus(pet)
    parts = [f"星辉 Lv.{b['star_lv']}"]
    if b["element"]:
        parts.append(f"{b['element']}元素")
    if b["branch"]:
        parts.append(f"{b['branch']} {b['evo_lv']}/5")
    d = (b["ha"] - 1) * 100
    bits = [f"经验 {(b['exp'] - 1) * 100:+.0f}%",
            (f"衰减 {'快' if d > 0 else '慢'}{abs(d):.0f}%" if abs(d) > 0.5 else "衰减 持平")]
    if b["df"] > 1.001:
        bits.append(f"积分 {(b['df'] - 1) * 100:+.0f}%")
    if b["rare"] > 0:
        bits.append(f"稀有 +{b['rare'] * 100:.0f}%")
    if b["heal"] > 1.001:
        bits.append(f"回血 {(b['heal'] - 1) * 100:+.0f}%")
    return " · ".join(parts) + "　|　" + " · ".join(bits)


# ===================== 图鉴 =====================
DEX_SKIN_KEYS = [f"{sp}|{k}" for sp in PET_SPECIES for k in ("normal", "star")]
DEX_SEASON_ITEMS = ["春日花束", "冰镇西瓜", "丰收南瓜派", "姜茶"]
DEX_SEASON_KEYS = [f"item|{i}" for i in DEX_SEASON_ITEMS]
DEX_ALL_KEYS = DEX_SKIN_KEYS + DEX_SEASON_KEYS
DEX_TOTAL = len(DEX_ALL_KEYS)
DEX_GROUPS = [
    {"gid": f"pair_{sp}", "name": f"{sp} · 双皮肤", "reward": 30,
     "keys": [f"{sp}|normal", f"{sp}|star"]}
    for sp in PET_SPECIES
] + [
    {"gid": "all_species", "name": "集齐全物种双皮肤", "reward": 100, "keys": DEX_SKIN_KEYS},
    {"gid": "all_season", "name": "集齐四季限定", "reward": 80, "keys": DEX_SEASON_KEYS},
    {"gid": "all_dex", "name": "图鉴满册", "reward": 200, "keys": DEX_ALL_KEYS},
]


def dex_label(key):
    if key.startswith("item|"):
        return key.split("|", 1)[1]
    sp, skin = key.split("|")
    return f"{sp} · {'星辉' if skin == 'star' else '普通'}"


def dex_add(gs, keys, out_msgs):
    """点亮图鉴格子，每格立刻 +5 积分，返回新点亮数量。"""
    dex = gs.setdefault("dex", [])
    new = [k for k in keys if k not in dex]
    for k in new:
        dex.append(k)
    if new:
        gain = 5 * len(new)
        gs["df"] += gain
        names = "、".join(dex_label(k) for k in new)
        out_msgs.append(f"图鉴点亮 {len(new)} 格：{names}（积分 +{gain}）")
        add_log(f"图鉴点亮 {names}", gs["game_log"])
    return len(new)


def dex_ready_groups(gs):
    dex = set(gs.get("dex", []))
    done = set(gs.get("dex_claimed", []))
    return [g for g in DEX_GROUPS
            if g["gid"] not in done and all(k in dex for k in g["keys"])]


def dex_claim(gs, gid, out_msgs):
    g = next(x for x in DEX_GROUPS if x["gid"] == gid)
    gs.setdefault("dex_claimed", []).append(gid)
    gs["df"] += g["reward"]
    out_msgs.append(f"图鉴奖励：{g['name']}　+{g['reward']} 积分")
    add_log(f"领取图鉴奖励 {g['name']} +{g['reward']}", gs["game_log"])


# ---------- 线性图标库 ----------
_ICON_BODY = {
    "heart": '<path d="M12 20.3C7.2 17.2 3.8 14.1 3.8 10.6 3.8 7.7 6 5.4 8.7 5.4c1.8 0 3 1 3.3 2.1.3-1.1 1.5-2.1 3.3-2.1 2.7 0 4.9 2.3 4.9 5.2 0 3.5-3.4 6.6-8.2 9.7z"/>',
    "happy": '<circle cx="12" cy="12" r="8.6"/><path d="M9 10.2h.01M15 10.2h.01M8.6 14.2c.9 1.3 2 2 3.4 2s2.5-.7 3.4-2"/>',
    "food": '<path d="M4 11h16a8 8 0 0 1-16 0z"/><path d="M7.5 8c0-1.6 1-2 1-3.6M12 7c0-1.6 1-2 1-3.6M16.5 8c0-1.6 1-2 1-3.6"/>',
    "clean": '<path d="M12 3.4s5.6 6.2 5.6 9.8a5.6 5.6 0 0 1-11.2 0z"/><path d="M9.4 13.2a2.6 2.6 0 0 0 2.6 2.6"/>',
    "coin": '<circle cx="12" cy="12" r="8.6"/><path d="M9.2 8l2.8 3.8L14.8 8M12 11.8V17M9.6 13.6h4.8"/>',
    "paw": '<circle cx="6.6" cy="10.4" r="2.1"/><circle cx="11.2" cy="7.9" r="2.1"/><circle cx="16.2" cy="9.6" r="2.1"/><path d="M12 19.4c-2.9 0-5-1.8-5-4 0-1.9 2.2-3.3 5-3.3s5 1.4 5 3.3c0 2.2-2.1 4-5 4z"/>',
    "dice": '<rect x="4" y="4" width="16" height="16" rx="4"/><circle cx="9" cy="9" r=".9"/><circle cx="15" cy="9" r=".9"/><circle cx="12" cy="12" r=".9"/><circle cx="9" cy="15" r=".9"/><circle cx="15" cy="15" r=".9"/>',
    "save": '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4"/><path d="M8 15h8"/>',
    "task": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M9 11h6M9 15h4"/>',
    "map": '<path d="M9 4 3 6.2v13.4L9 17.4l6 2.2 6-2.2V4l-6 2.2z"/><path d="M9 4v13.4M15 6.2v13.4"/>',
    "bell": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l1.6 2H4.4z"/><path d="M10 20.2a2.2 2.2 0 0 0 4 0"/>',
    "trophy": '<path d="M8 4h8v4.2a4 4 0 0 1-8 0z"/><path d="M8 5.4H5.2v1.2A3.4 3.4 0 0 0 8.6 10M16 5.4h2.8v1.2A3.4 3.4 0 0 1 15.4 10"/><path d="M12 12.4V16M9.4 20h5.2M10.2 16h3.6v4h-3.6z"/>',
    "log": '<path d="M6 3h11a2 2 0 0 1 2 2v16H8a2 2 0 0 1-2-2z"/><path d="M9 7h7M9 11h7M9 15h5"/><path d="M6 3v18"/>',
    "gear": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.6v2.6M12 18.8v2.6M2.6 12h2.6M18.8 12h2.6M5.4 5.4l1.9 1.9M16.7 16.7l1.9 1.9M18.6 5.4l-1.9 1.9M7.3 16.7l-1.9 1.9"/>',
    "shop": '<path d="M4 9.2h16l-1.2-4.4H5.2z"/><path d="M5 9.2V19h14V9.2"/><path d="M9.2 19v-5h5.6v5"/>',
    "ticket": '<path d="M4 7.5h16v3.2a2 2 0 0 0 0 3.8v2.9H4v-2.9a2 2 0 0 0 0-3.8z"/><path d="M12 7.5v9.9" stroke-dasharray="2 3"/>',
    "hospital": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8.2v7.6M8.2 12h7.6"/>',
    "skill": '<path d="M5.5 18.5 14 10"/><path d="M13.5 3.8l1.5 3.4 3.4 1.5-3.4 1.5-1.5 3.4-1.5-3.4L8.6 8.7l3.4-1.5z"/><path d="M4.5 5.5l.8 1.8 1.8.8-1.8.8-.8 1.8-.8-1.8L1.9 8.1l1.8-.8z"/>',
    "info": '<circle cx="12" cy="12" r="8.6"/><path d="M12 11.2v4.6M12 8.2h.01"/>',
    "check": '<path d="M4.5 12.6l4.7 4.7L20 6.6"/>',
    "clock": '<circle cx="12" cy="12" r="8.6"/><path d="M12 7.2v5.2l3.4 2"/>',
    "box": '<path d="M3.4 8.4 12 4l8.6 4.4L12 12.8z"/><path d="M3.4 8.4v7.4L12 20l8.6-4.2V8.4"/><path d="M12 12.8V20"/>',
    "star": '<path d="M12 2.8l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17l-5.6 2.9 1.1-6.2L3 9.4l6.2-.9z"/>',
    "gem": '<path d="M7 3h10l3 5-8 13L4 8z"/><path d="M4 8h16M9 3l-2 5 5 13 5-13-2-5"/>',
    # 道具图标
    "bread": '<path d="M4 13c0-3.8 3.2-6.5 8-6.5s8 2.7 8 6.5v4.2c0 1.3-1 2.3-2.3 2.3H6.3C5 19.5 4 18.5 4 17.2z"/><path d="M8.5 9.5c-.4 1-.4 2 .1 3M12 8.8c-.4 1.2-.4 2.4.1 3.6M15.5 9.5c-.4 1-.4 2 .1 3"/>',
    "battery": '<rect x="8.2" y="7" width="7.6" height="13" rx="2"/><path d="M10.4 4.2h3.2V7"/><path d="M10.2 12.4h3.6M12 10.6v3.6"/>',
    "fish": '<path d="M3.4 12c2.9-4 6.5-6 10.6-6 3 0 4.6 2.4 4.6 6s-1.6 6-4.6 6c-4.1 0-7.7-2-10.6-6z"/><path d="M18.2 9.4 21.6 7v10l-3.4-2.4"/><circle cx="7.6" cy="11" r=".8"/>',
    "conditioner": '<path d="M9 8h6v12H9z"/><path d="M10 8V5.4h4V8"/><path d="M12 5.4V3h3"/>',
    "toy": '<circle cx="12" cy="12" r="8.6"/><path d="M4 9.4c4.5 1.2 11.5 1.2 16 0M6.2 16.4c3.4-2.2 8.2-2.2 11.6 0"/><path d="M12 3.4v17.2"/>',
    "grapes": '<circle cx="9" cy="9.2" r="2.7"/><circle cx="15" cy="9.2" r="2.7"/><circle cx="12" cy="13" r="2.7"/><circle cx="8.4" cy="14.6" r="2.7"/><circle cx="15.6" cy="14.6" r="2.7"/><circle cx="12" cy="18.2" r="2.7"/><path d="M12 6.5V4"/>',
    "soap": '<rect x="4.4" y="9.6" width="15.2" height="9" rx="3.6"/><path d="M8 9.6c0-2 1.4-3.4 4-3.4"/><circle cx="8.8" cy="7" r="1.1"/><circle cx="11.4" cy="4.9" r=".8"/>',
    "snack": '<path d="M7 4h10l1 16H6z"/><path d="M7 8.2h10"/><path d="M9.6 12.4h4.8"/>',
    "medicine": '<rect x="8.6" y="2.8" width="6.8" height="18.4" rx="3.4"/><path d="M8.6 12h6.8"/>',
    "syringe": '<path d="M17 3l4 4"/><path d="M15.2 5.2l3.6 3.6"/><path d="M16.8 7.2 8 16l-1.4 4.4L11 19l8.8-8.8"/><path d="M5.6 18.4 3.2 20.8"/>',
    "paste": '<path d="M8 4h8v12.4L12 20l-4-3.6z"/><path d="M8 8.4h8"/>',
    "nutrition": '<path d="M10 3.2h4v3.2l2 2.8V20h-8V9.2l2-2.8z"/><path d="M8 13.6h8"/><path d="M12 10.8l1 2.1 2.1.3-1.5 1.5.3 2.1-1.9-1.1-1.9 1.1.3-2.1L9 13.2l2.1-.3z"/>',
    "badge": '<circle cx="12" cy="9.4" r="5.6"/><path d="M9 14.2 7.4 21l4.6-2.4L16.6 21 15 14.2"/><path d="M12 6.8l1 2.2 2.2.3-1.6 1.6.4 2.2-2-1.2-2 1.2.4-2.2-1.6-1.6 2.2-.3z"/>',
    "enhancer": '<path d="M9 3h6M10.4 3v3.8L7.2 14a4.6 4.6 0 0 0 4.1 6.6h1.4A4.6 4.6 0 0 0 16.8 14l-3.2-7.2V3"/><path d="M8.4 14.6h7.2"/>',
    "spray": '<rect x="8" y="8.4" width="8" height="12" rx="2.2"/><path d="M9.6 8.4V5.6h4.8v2.8"/><path d="M14.8 4.4h3.4M15.6 3l2.4-1.2M16.4 5.6l2.2 1.2"/><path d="M10 12.6h4"/>',
    "gift": '<rect x="4.2" y="10" width="15.6" height="9.6" rx="2"/><path d="M3.2 6.6h17.6v3.4H3.2z"/><path d="M12 6.6v13M12 6.6c-2.4 0-4.4-1-4.4-2.6S9 2.2 12 6.6zM12 6.6c2.4 0 4.4-1 4.4-2.6S15 2.2 12 6.6z"/>',
    "fruit": '<path d="M12 7.2c2.8-1.4 6.6.4 6.6 4.6 0 4.2-2.9 8.4-4.9 8.4-1 0-1.7-.6-2.6-.6s-1.7.6-2.6.6C6.6 20.2 3.9 16 3.9 11.8c0-4.2 3.9-6 6.6-4.6"/><path d="M12 7.2V3.8M12 4.4c1.4-1.2 3.2-1.4 4-1-.4 1.6-1.8 2.4-3.6 2.2"/>',
    "flower": '<circle cx="12" cy="7.4" r="2.6"/><circle cx="7.6" cy="10.6" r="2.6"/><circle cx="16.4" cy="10.6" r="2.6"/><circle cx="9.2" cy="15.6" r="2.6"/><circle cx="14.8" cy="15.6" r="2.6"/><circle cx="12" cy="11.8" r="2"/>',
    "melon": '<path d="M3.4 9.2h17.2c0 6.4-3.8 11.4-8.6 11.4S3.4 15.6 3.4 9.2z"/><path d="M3.4 9.2h17.2"/><circle cx="9.4" cy="14" r="1"/><circle cx="14" cy="12.4" r="1"/><circle cx="12.6" cy="16.6" r="1"/>',
    "pumpkin": '<ellipse cx="12" cy="14" rx="7.6" ry="6"/><path d="M12 8v12M8.2 8.4v11M15.8 8.4v11"/><path d="M12 8c-.6-2 .4-3.6 2-4.2"/>',
    "tea": '<path d="M5.6 9h11v6.4a4.4 4.4 0 0 1-4.4 4.4H10a4.4 4.4 0 0 1-4.4-4.4z"/><path d="M16.6 10.4h1.8a2.6 2.6 0 0 1 0 5.2h-1.8"/><path d="M8.6 5.6c-.6-1 .2-1.8.6-2.4M12 5.6c-.6-1 .2-1.8.6-2.4"/>',
    "paint": '<path d="M4 4h16v6.4H4z"/><path d="M8.4 10.4v3.2h7.2v3.2"/><path d="M13.8 16.8h1.2a2 2 0 0 1 0 4H13a2 2 0 0 1-2-2V16.8"/>',
    "element": '<path d="M12 3.2l3.6 6.8 7 .8-5.2 4.8 1.4 6.9L12 18.4 5.2 21.5 6.6 14.6 1.4 9.8l7-.8z"/>',
}

_ITEM_ICON = {
    "面包": "bread",
    "电池": "battery",
    "鲜鱼": "fish",
    "护发素": "conditioner",
    "玩具": "toy",
    "葡萄": "grapes",
    "肥皂": "soap",
    "零食": "snack",
    "药品": "medicine",
    "急救针": "syringe",
    "全能营养膏": "paste",
    "高级营养液": "nutrition",
    "幸运徽章": "badge",
    "宠物强化剂": "enhancer",
    "除臭喷雾": "spray",
    "小零食礼包": "gift",
    "经验果": "fruit",
    "春日花束": "flower",
    "冰镇西瓜": "melon",
    "丰收南瓜派": "pumpkin",
    "姜茶": "tea",
    "星尘": "star",
    "星尘结晶": "gem",
    "星光皮肤券": "paint",
}


def icon(name, size=18, color="currentColor", stroke=1.8):
    body = _ICON_BODY.get(name, _ICON_BODY["info"])
    return (
        f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
        f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{body}</svg>'
    )



PX = 8
GRID = 30


def _r(x, y, w, h, c, o=None):
    """按像素格绘制一个矩形。"""
    op = "" if o is None else f' opacity="{o}"'
    return (f'<rect x="{int(round(x * PX))}" y="{int(round(y * PX))}" '
            f'width="{int(round(w * PX))}" height="{int(round(h * PX))}" '
            f'fill="{c}"{op}/>')


def _mx(x, w):
    """左右镜像用的 x 坐标（画布宽 30 格）。"""
    return GRID - x - w


def _blob(cx, cy, rx, ry, c, o=None):
    """像素风椭圆：按行切成一格高的方块，保证边缘是台阶。"""
    out = []
    ry_i = max(1, int(round(ry)))
    for gy in range(-ry_i, ry_i + 1):
        k = 1 - (gy / (ry_i + 0.45)) ** 2
        if k <= 0:
            continue
        w = int(round(rx * (k ** 0.5)))
        if w <= 0:
            continue
        out.append(_r(cx - w, cy + gy, w * 2, 1, c, o))
    return "".join(out)


def _outline(cx, cy, rx, ry, pal):
    """外描边：先画一层更大的深色块，再叠主体色，得到像素黑边。"""
    return (_blob(cx, cy, rx + 1, ry + 1, pal["out"])
            + _blob(cx, cy, rx, ry, pal["base"]))


def _eyes(lx, rx, y, mood, pal, star):
    out = []
    for cx in (lx, rx):
        if star:
            c = pal["eye"]
            out.append(_r(cx + 1, y, 1, 1, c))
            out.append(_r(cx, y + 1, 1, 1, c))
            out.append(_r(cx + 2, y + 1, 1, 1, c))
            out.append(_r(cx + 1, y + 2, 1, 1, c))
            out.append(_r(cx + 1, y + 1, 1, 1, "#FFF7D6"))
        elif mood == "sick":
            c = pal["eye"]
            out.append(_r(cx, y, 1, 1, c))
            out.append(_r(cx + 1, y + 1, 1, 1, c))
            out.append(_r(cx + 1, y, 1, 1, c))
            out.append(_r(cx, y + 1, 1, 1, c))
        else:
            if pal.get("eyebg"):
                out.append(_r(cx, y, 2, 2, pal["eyebg"]))
                out.append(_r(cx, y, 1, 1, pal["eye"]))
                out.append(_r(cx + 1, y + 1, 1, 1, pal["eye"]))
            else:
                out.append(_r(cx, y, 2, 2, pal["eye"]))
                out.append(_r(cx, y, 1, 1, "#FFFFFF"))
    if mood == "sad" and not star:
        out.append(_r(lx, y - 2, 2, 1, pal["eye"]))
        out.append(_r(rx, y - 2, 2, 1, pal["eye"]))
    return "".join(out)


def _mouth(cx, y, mood, pal):
    c = pal.get("mouth", pal["eye"])
    if mood == "sad":
        return _r(cx - 1, y + 1, 1, 1, c) + _r(cx, y, 1, 1, c) + _r(cx + 1, y + 1, 1, 1, c)
    if mood == "sick":
        return _r(cx - 1, y, 1, 1, c) + _r(cx, y + 1, 1, 1, c) + _r(cx + 1, y, 1, 1, c)
    return (_r(cx - 1, y, 1, 1, c) + _r(cx, y + 1, 2, 1, c)
            + _r(cx + 1, y, 1, 1, c))


def _cheeks(lx, rx, y, mood, pal):
    if mood == "sick":
        return ""
    c = pal["accent"]
    o = 0.9 if mood == "happy" else 0.55
    return _r(lx, y, 2, 1, c, o) + _r(rx, y, 2, 1, c, o)


def _mood_prop(mood, pal):
    """情绪角标：像素小方块。"""
    if mood == "sick":
        return (_r(24, 1, 4, 4, "#7B2D26") + _r(25, 2, 2, 1, "#FFE1DC")
                + _r(25.5, 1.5, 1, 2, "#FFE1DC"))
    if mood == "sad":
        return (_r(24, 1, 4, 4, "#3F4A63") + _r(25.5, 2, 1, 2, "#DCE6F7")
                + _r(25, 4, 2, 1, "#DCE6F7"))
    return ""


def _star_deco(pal, head_top):
    """星辉皮肤专属：小皇冠 + 四角星点。"""
    out = []
    gold, light = "#FFD54A", "#FFF3B0"
    base = max(0, head_top - 1)
    out.append(_r(12, base, 6, 1, gold))
    for x in (12, 14, 16, 18):
        h = 2 if x in (14, 16) else 1
        if base - h >= 0:
            out.append(_r(x, base - h, 1, h, gold))
    out.append(_r(13, base, 1, 1, light))
    out.append(_r(17, base, 1, 1, light))
    for (x, y) in ((2, 1), (26, 2), (2, 25), (26, 24)):
        out.append(_r(x + 1, y, 1, 3, gold, .9))
        out.append(_r(x, y + 1, 3, 1, gold, .9))
    return "".join(out)


_TAIL = {
    "猫": ((22, 18, 2, 2), (24, 16, 2, 2), (25, 13, 2, 3)),
    "狗": ((22, 16, 2, 2), (23, 13, 2, 3)),
    "豹子": ((22, 18, 2, 2), (24, 16, 2, 2), (25, 13, 2, 3)),
}


def _legs(pal, y=24, w=3, h=2):
    return (_r(11, y, w, h, pal["light"]) + _r(11, y, w, 1, pal["shade"])
            + _r(16, y, w, h, pal["light"]) + _r(16, y, w, 1, pal["shade"]))


def _sp_cat(pal, mood, star):
    s = []
    for (x, y, w, h) in _TAIL["猫"]:
        s.append(_r(x, y, w, h, pal["shade"]))
    s.append(_r(25, 13, 1, 1, pal["light"]))
    s.append(_r(8, 8, 4, 2, pal["out"]) + _r(8, 6, 3, 2, pal["out"]) + _r(9, 4, 2, 2, pal["out"]))
    s.append(_r(9, 6, 2, 3, pal["base"]) + _r(10, 5, 1, 1, pal["base"]))
    s.append(_r(10, 7, 1, 1, pal["accent"]))
    s.append(_r(18, 8, 4, 2, pal["out"]) + _r(19, 6, 3, 2, pal["out"]) + _r(19, 4, 2, 2, pal["out"]))
    s.append(_r(19, 6, 2, 3, pal["base"]) + _r(19, 5, 1, 1, pal["base"]))
    s.append(_r(19, 7, 1, 1, pal["accent"]))
    s.append(_outline(15, 21.5, 6, 4, pal))
    s.append(_blob(15, 23, 3, 2, pal["belly"]))
    s.append(_legs(pal))
    s.append(_outline(15, 12, 6.5, 5.5, pal))
    s.append(_blob(15, 15, 4, 2, pal["light"]))
    s.append(_r(13, 9, 1, 1, pal["shade"]) + _r(15, 8, 1, 1, pal["shade"])
             + _r(17, 9, 1, 1, pal["shade"]))
    s.append(_eyes(11, 17, 10, mood, pal, star))
    s.append(_r(15, 14, 1, 1, pal["accent"]))
    s.append(_mouth(15, 15, mood, pal))
    s.append(_cheeks(9, 19, 14, mood, pal))
    for d in (0, 1):
        s.append(_r(7 + d, 13 + d, 2, 1, pal["light"]))
        s.append(_r(7 + d, 15 - d, 2, 1, pal["light"]))
        s.append(_r(21 - d, 13 + d, 2, 1, pal["light"]))
        s.append(_r(21 - d, 15 - d, 2, 1, pal["light"]))
    return "".join(s)


def _sp_dog(pal, mood, star):
    s = []
    for (x, y, w, h) in _TAIL["狗"]:
        s.append(_r(x, y, w, h, pal["shade"]))
    s.append(_r(6, 8, 3, 6, pal["out"]) + _r(7, 9, 1, 4, pal["shade"]))
    s.append(_r(21, 8, 3, 6, pal["out"]) + _r(22, 9, 1, 4, pal["shade"]))
    s.append(_outline(15, 21.5, 6, 4, pal))
    s.append(_blob(15, 23, 3, 2, pal["belly"]))
    s.append(_legs(pal))
    s.append(_outline(15, 12, 6.5, 5.5, pal))
    s.append(_blob(15, 16.5, 3.5, 2, pal["light"]))
    s.append(_blob(15, 9, 3, 1.5, pal["light"]))
    s.append(_eyes(11, 17, 10, mood, pal, star))
    s.append(_r(14, 15, 2, 1, pal["eye"]))
    s.append(_mouth(15, 17, mood, pal))
    s.append(_r(15, 18, 1, 1, pal["accent"]))
    s.append(_cheeks(9, 19, 14, mood, pal))
    return "".join(s)


def _sp_robot(pal, mood, star):
    s = []
    s.append(_r(15, 2, 1, 3, pal["shade"]))
    s.append(_r(14, 1, 2, 1, pal["accent"]))
    s.append(_r(9, 18, 12, 7, pal["out"]))
    s.append(_r(10, 19, 10, 5, pal["base"]))
    s.append(_r(10, 19, 10, 1, pal["light"]))
    s.append(_r(13, 21, 4, 2, pal["belly"]))
    s.append(_r(14, 21.5, 1, 1, "#FFFFFF"))
    s.append(_r(7, 19, 2, 5, pal["out"]) + _r(7, 19, 2, 4, pal["shade"]))
    s.append(_r(21, 19, 2, 5, pal["out"]) + _r(21, 19, 2, 4, pal["shade"]))
    s.append(_r(10, 25, 3, 2, pal["out"]) + _r(17, 25, 3, 2, pal["out"]))
    s.append(_r(8, 5, 14, 13, pal["out"]))
    s.append(_r(9, 6, 12, 11, pal["base"]))
    s.append(_r(9, 6, 12, 2, pal["light"]))
    s.append(_r(6, 10, 2, 3, pal["shade"]))
    s.append(_r(22, 10, 2, 3, pal["shade"]))
    if mood == "sick":
        s.append(_r(11, 10, 2, 1, pal["eye"]) + _r(12, 9, 1, 3, pal["eye"]))
        s.append(_r(17, 10, 2, 1, pal["eye"]) + _r(18, 9, 1, 3, pal["eye"]))
        s.append(_r(13, 14, 1, 1, pal["eye"]) + _r(15, 14, 1, 1, pal["eye"]))
    else:
        s.append(_r(11, 9, 3, 2, pal["eye"]) + _r(16, 9, 3, 2, pal["eye"]))
        s.append(_r(12, 9, 1, 1, pal["belly"]) + _r(17, 9, 1, 1, pal["belly"]))
        if star:
            s.append(_r(11, 8, 1, 1, "#FFE066") + _r(13, 8, 1, 1, "#FFE066"))
            s.append(_r(16, 8, 1, 1, "#FFE066") + _r(18, 8, 1, 1, "#FFE066"))
        s.append(_mouth(15, 14, mood, pal))
    s.append(_r(15, 17, 2, 1, pal["accent"]))
    return "".join(s)


def _sp_sheep(pal, mood, star):
    """小羊：羊毛云朵头 + 圆身体 + 短腿。"""
    s = []
    # 腿
    for x in (11.8, 17.2):
        s.append(_r(x, 22.8, 2, 3, pal["out"]))
        s.append(_r(x, 22.8, 2, 1.4, pal["base"]))
    # 小尾巴
    s.append(_blob(23.4, 20.4, 1.6, 1.3, pal["out"]))
    s.append(_blob(23.4, 20.4, 1.1, 0.8, pal["light"]))
    # 身体（头后面）
    s.append(_blob(15, 19.6, 4.7, 3.5, pal["out"]))
    s.append(_blob(15, 19.6, 4.0, 2.8, pal["base"]))
    for (cx, cy, rx, ry) in ((12.2, 17.4, 1.4, 1.0), (17.8, 17.4, 1.4, 1.0),
                             (15, 21.8, 1.8, 0.8), (11.4, 20.6, 1.2, 0.9),
                             (18.6, 20.6, 1.2, 0.9)):
        s.append(_blob(cx, cy, rx, ry, pal["light"]))
    # 耳朵（外侧）
    s.append(_blob(8.6, 10.6, 1.6, 1.2, pal["out"]))
    s.append(_blob(8.6, 10.6, 1.0, 0.7, pal["shade"]))
    s.append(_blob(21.4, 10.6, 1.6, 1.2, pal["out"]))
    s.append(_blob(21.4, 10.6, 1.0, 0.7, pal["shade"]))
    # 羊毛云朵头
    s.append(_blob(15, 11.4, 5.1, 4.1, pal["out"]))
    s.append(_blob(15, 11.4, 4.4, 3.4, pal["base"]))
    for (cx, cy, rx, ry) in ((12.0, 9.6, 1.4, 1.0), (18.0, 9.6, 1.4, 1.0),
                             (15, 8.4, 1.5, 0.9), (11.6, 13.2, 1.3, 0.9),
                             (18.4, 13.2, 1.3, 0.9)):
        s.append(_blob(cx, cy, rx, ry, pal["light"]))
    # 浅色小脸
    s.append(_blob(15, 12.6, 2.4, 2.0, pal["light"]))
    s.append(_eyes(12.6, 17.4, 11.8, mood, pal, star))
    s.append(_r(15, 13.2, 1, 1, pal["accent"]))
    s.append(_mouth(15, 13.8, mood, pal))
    s.append(_cheeks(10.6, 19.4, 14.0, mood, pal))
    return "".join(s)


def _sp_chick(pal, mood, star):
    s = []
    s.append(_r(13, 25, 1, 2, pal["accent"]) + _r(12, 26, 2, 1, pal["accent"]))
    s.append(_r(17, 25, 1, 2, pal["accent"]) + _r(17, 26, 2, 1, pal["accent"]))
    s.append(_outline(15, 20, 6, 5, pal))
    s.append(_blob(15, 22, 3, 2.5, pal["belly"]))
    s.append(_r(9, 19, 2, 3, pal["shade"]) + _r(19, 19, 2, 3, pal["shade"]))
    s.append(_outline(15, 11.5, 5.5, 5, pal))
    s.append(_r(14, 4, 1, 2, pal["shade"]) + _r(15, 3, 1, 1, pal["shade"]))
    s.append(_eyes(11, 17, 10, mood, pal, star))
    s.append(_r(14, 14, 2, 1, pal["accent"]) + _r(15, 15, 2, 1, pal["accent"]))
    s.append(_cheeks(9, 19, 13, mood, pal))
    return "".join(s)


def _sp_leopard(pal, mood, star):
    s = []
    for i, (x, y, w, h) in enumerate(_TAIL["豹子"]):
        s.append(_r(x, y, w, h, pal["base"] if i % 2 == 0 else pal["shade"]))
    s.append(_r(11, 8, 2, 1, pal["out"]) + _r(17, 8, 2, 1, pal["out"]))
    s.append(_outline(15, 21.5, 6, 4, pal))
    s.append(_blob(15, 23, 3, 2, pal["belly"]))
    s.append(_legs(pal))
    s.append(_blob(10, 6, 2.2, 2.2, pal["out"]) + _blob(10, 6, 1.4, 1.4, pal["base"]))
    s.append(_r(9, 5, 1, 1, pal["accent"]))
    s.append(_blob(20, 6, 2.2, 2.2, pal["out"]) + _blob(20, 6, 1.4, 1.4, pal["base"]))
    s.append(_r(20, 5, 1, 1, pal["accent"]))
    s.append(_outline(15, 12.5, 6.5, 5.5, pal))
    s.append(_blob(15, 16, 3.5, 2, pal["belly"]))
    for (x, y) in ((10, 8), (18, 8), (9, 15), (20, 16), (13, 25), (18, 21)):
        s.append(_r(x, y, 1, 1, pal["shade"]))
    s.append(_eyes(11, 17, 10.5, mood, pal, star))
    s.append(_r(15, 14.5, 1, 1, pal["out"]))
    s.append(_mouth(15, 15.5, mood, pal))
    s.append(_cheeks(9, 19, 14, mood, pal))
    return "".join(s)


def _sp_rabbit(pal, mood, star):
    s = []
    for x in (10, 17):
        s.append(_r(x - 1, 1, 4, 9, pal["out"]))
        s.append(_r(x, 2, 2, 7, pal["base"]))
        s.append(_r(x, 3, 1, 5, pal["accent"], .75))
        s.append(_r(x, 9, 2, 1, pal["shade"]))
    s.append(_blob(21, 21, 2.2, 2, pal["out"]))
    s.append(_blob(21, 21, 1.5, 1.4, pal["light"]))
    s.append(_outline(15, 21.5, 5.5, 4, pal))
    s.append(_blob(15, 22.5, 2.6, 2, pal["belly"]))
    s.append(_legs(pal, y=25, w=3, h=2))
    s.append(_outline(15, 13, 6, 5, pal))
    s.append(_blob(15, 15.5, 3, 1.6, pal["light"]))
    s.append(_eyes(11.5, 16.5, 11, mood, pal, star))
    s.append(_r(15, 14, 1, 1, pal["accent"]))
    s.append(_mouth(15, 15.5, mood, pal))
    s.append(_cheeks(9, 19, 15, mood, pal))
    for d in (0, 1):
        s.append(_r(8 - d, 13 + d, 2, 1, pal["light"]))
        s.append(_r(20 + d, 13 + d, 2, 1, pal["light"]))
    return "".join(s)


def _sp_hamster(pal, mood, star):
    """仓鼠：圆滚滚一颗，腮帮子鼓、耳朵小、尾巴短。"""
    s = []
    s.append(_r(22.4, 21.5, 2, 1, pal["shade"]))
    s.append(_outline(15, 21, 6.6, 4.6, pal))
    s.append(_blob(15, 22.6, 3.6, 2.2, pal["belly"]))
    s.append(_r(12.4, 23.6, 2, 1, pal["light"]) + _r(16.6, 23.6, 2, 1, pal["light"]))
    s.append(_r(10.8, 25.2, 3, 1.6, pal["shade"]) + _r(16.2, 25.2, 3, 1.6, pal["shade"]))
    for cx in (9.8, 20.2):
        s.append(_blob(cx, 7.8, 1.6, 1.4, pal["out"]))
        s.append(_blob(cx, 7.8, 1.0, 0.8, pal["accent"]))
    s.append(_outline(15, 11.8, 6.6, 5.2, pal))
    s.append(_blob(9.8, 13.2, 2.4, 2.0, pal["light"]))
    s.append(_blob(20.2, 13.2, 2.4, 2.0, pal["light"]))
    s.append(_blob(15, 9.2, 3.6, 2.2, pal["light"]))
    s.append(_eyes(11, 17, 10, mood, pal, star))
    s.append(_r(15, 12.8, 1, 1, pal["accent"]))
    s.append(_mouth(15, 14, mood, pal))
    s.append(_cheeks(10, 18, 13.6, mood, pal))
    return "".join(s)


def _sp_fox(pal, mood, star):
    """狐狸：尖耳朵、白口鼻、大蓬尾巴。"""
    s = []
    s.append(_blob(24.2, 19.6, 3.2, 3.6, pal["out"]))
    s.append(_blob(24.2, 19.6, 2.4, 2.9, pal["base"]))
    s.append(_blob(25.2, 22.2, 1.5, 1.3, pal["light"]))
    s.append(_outline(15, 21.5, 6, 4, pal))
    s.append(_blob(15, 23, 3.2, 2, pal["belly"]))
    s.append(_legs(pal))
    for x0 in (8.2, 18.2):
        s.append(_r(x0 + 2.6, 2.6, 1, 1.4, pal["out"]))
        s.append(_r(x0 + 2, 3.6, 2, 1.4, pal["out"]))
        s.append(_r(x0 + 1, 4.8, 4, 3, pal["out"]))
        s.append(_r(x0 + 2.4, 4.4, 1, 1.4, pal["shade"])
                 + _r(x0 + 1.8, 5.4, 1.2, 1.6, pal["shade"]))
    s.append(_outline(15, 12.5, 6.4, 5.4, pal))
    s.append(_blob(15, 16.4, 3.4, 2.2, pal["light"]))
    s.append(_eyes(11, 17, 10.4, mood, pal, star))
    s.append(_blob(15, 14.4, 1.1, 0.8, pal["out"]))
    s.append(_mouth(15, 15.2, mood, pal))
    s.append(_cheeks(9, 19, 13.8, mood, pal))
    for d in (0, 1):
        s.append(_r(7 + d, 13 + d, 2, 1, pal["light"]))
        s.append(_r(21 - d, 13 + d, 2, 1, pal["light"]))
    return "".join(s)


def _sp_penguin(pal, mood, star):
    """企鹅：竖长身子、白肚皮、小鳍、橙脚丫。"""
    s = []
    s.append(_blob(15, 18.6, 7.2, 8.6, pal["out"]))
    s.append(_blob(15, 18.6, 6.4, 7.8, pal["base"]))
    s.append(_blob(15, 19.6, 4.4, 6.4, pal["belly"]))
    s.append(_r(15, 6.4, 1, 2, pal["shade"]))
    for cx in (7.4, 22.6):
        s.append(_blob(cx, 17.4, 1.8, 4.4, pal["out"]))
        s.append(_blob(cx, 17.4, 1.2, 3.6, pal["shade"]))
    # 脚丫画在身体之后，露在外侧才不会被子盖住
    s.append(_r(9.6, 25.4, 4, 1.6, pal["accent"]))
    s.append(_r(16.4, 25.4, 4, 1.6, pal["accent"]))
    s.append(_r(10, 27, 3, 0.8, pal["accent"]))
    s.append(_r(17, 27, 3, 0.8, pal["accent"]))
    s.append(_eyes(11.4, 16.4, 12, mood, pal, star))
    s.append(_r(13.6, 14.4, 3.2, 1, pal["accent"]) + _r(14.8, 15.4, 1, 1, pal["accent"]))
    s.append(_cheeks(9.4, 18.6, 15, mood, pal))
    return "".join(s)


def _sp_frog(pal, mood, star):
    """青蛙：扁身子、头顶两颗大眼球、宽嘴。"""
    s = []
    s.append(_blob(7.6, 24, 3, 1.7, pal["out"]))
    s.append(_blob(7.6, 24, 2.4, 1.2, pal["shade"]))
    s.append(_blob(22.4, 24, 3, 1.7, pal["out"]))
    s.append(_blob(22.4, 24, 2.4, 1.2, pal["shade"]))
    s.append(_blob(15, 20.5, 8.2, 5.2, pal["out"]))
    s.append(_blob(15, 20.5, 7.4, 4.5, pal["base"]))
    s.append(_blob(15, 22.8, 5, 2.5, pal["belly"]))
    for cx in (10.2, 19.8):
        s.append(_blob(cx, 12.4, 2.7, 2.7, pal["out"]))
        s.append(_blob(cx, 12.4, 2.0, 2.0, pal["light"]))
    s.append(_eyes(9.2, 18.8, 12, mood, pal, star))
    mouth = pal.get("mouth", pal["eye"])
    if mood == "sad":
        s.append(_r(12, 17.6, 6, 1, mouth) + _r(12, 18.6, 2, 1, mouth)
                 + _r(16, 18.6, 2, 1, mouth))
    elif mood == "sick":
        s.append(_r(12, 17.6, 6, 1, mouth))
    else:
        s.append(_r(11.6, 17.4, 7, 1, mouth))
        s.append(_r(11.6, 16.4, 2, 1, mouth) + _r(17.4, 16.4, 2, 1, mouth))
    s.append(_cheeks(8.4, 20.4, 14.6, mood, pal))
    return "".join(s)


def _sp_bear(pal, mood, star):
    """小熊：圆耳朵、浅色口鼻、敦实身子。"""
    s = []
    s.append(_blob(22.4, 21, 1.7, 1.4, pal["out"]))
    s.append(_blob(22.4, 21, 1.0, 0.7, pal["light"]))
    s.append(_outline(15, 21.5, 6.6, 4.6, pal))
    s.append(_blob(15, 23, 3.4, 2.2, pal["belly"]))
    s.append(_legs(pal, y=25, w=3, h=1.5))
    for cx in (9.4, 20.6):
        s.append(_blob(cx, 7.4, 2.4, 2.2, pal["out"]))
        s.append(_blob(cx, 7.4, 1.6, 1.4, pal["base"]))
        s.append(_blob(cx, 7.6, 0.9, 0.7, pal["shade"]))
    s.append(_outline(15, 12, 7, 5.6, pal))
    s.append(_blob(15, 14.4, 3.4, 2.4, pal["light"]))
    s.append(_eyes(10.8, 17.2, 10, mood, pal, star))
    s.append(_blob(15, 13.6, 1.2, 0.9, pal["eye"]))
    s.append(_mouth(15, 15.6, mood, pal))
    s.append(_cheeks(9, 19, 14.8, mood, pal))
    return "".join(s)


def _sp_mech_bee(pal, mood, star):
    """机械蜂：金属圆身 + 工蜂条纹 + 舱体护目镜 + 一对薄翼。"""
    s = []
    # 天线
    s.append(_r(12, 5, 1, 3, pal["out"]))
    s.append(_r(17, 5, 1, 3, pal["out"]))
    s.append(_blob(12.5, 4.4, 0.9, 0.9, pal["accent"]))
    s.append(_blob(17.5, 4.4, 0.9, 0.9, pal["accent"]))
    # 薄翼（金属膜，半透）
    for cx in (7.4, 22.6):
        s.append(_blob(cx, 14.2, 2.7, 1.9, pal["out"]))
        s.append(_blob(cx, 14.2, 2.2, 1.4, pal["light"], .92))
        s.append(_blob(cx - 0.4, 13.4, 1.2, 0.7, "#FFFFFF", .85))
    # 尾针与六足
    s.append(_r(14, 25, 1, 2.4, pal["out"]))
    s.append(_r(15, 25, 1, 1.8, pal["out"]))
    s.append(_r(14, 26.6, 1, 0.8, pal["accent"]))
    s.append(_r(8.4, 22, 1.6, 1, pal["out"]))
    s.append(_r(20, 22, 1.6, 1, pal["out"]))
    # 身体：逐行切片的黑黄条纹
    s.append(_blob(15, 19.6, 6.4, 5.0, pal["out"]))
    for gy in range(-4, 5):
        k = 1 - (gy / 4.45) ** 2
        if k <= 0:
            continue
        w = int(round(5.6 * (k ** 0.5)))
        if w <= 0:
            continue
        c = pal["belly"] if gy % 3 == 0 else pal["base"]
        s.append(_r(15 - w, 19.6 + gy, w * 2, 1, c))
    s.append(_r(13, 21, 1, 1, pal["light"]))
    s.append(_r(16, 22, 1, 1, pal["light"]))
    s.append(_r(14, 23, 2, 0.6, pal["shade"]))
    # 头部舱体
    s.append(_outline(15, 11.2, 4.6, 3.8, pal))
    s.append(_blob(15, 10, 3.4, 1.4, pal["light"]))
    # 护目镜面罩
    s.append(_r(11, 10.2, 8, 2, pal["eye"]))
    s.append(_r(11, 10.2, 8, 0.6, pal["accent"]))
    s.append(_r(12, 10.8, 1, 1, "#FFFFFF"))
    s.append(_r(17, 10.8, 1, 1, "#FFFFFF"))
    if mood == "sick":
        s.append(_r(12, 12.8, 6, 1, pal["shade"]))
    elif mood == "sad":
        s.append(_r(13, 12.8, 4, 1, pal["shade"]))
    else:
        s.append(_r(13, 12.8, 4, 1, pal["accent"]))
        s.append(_r(13, 12.8, 1, 1, pal["light"]))
    s.append(_cheeks(9.8, 18.6, 12.6, mood, pal))
    return "".join(s)


def _sp_deer(pal, mood, star):
    """小鹿：细枝鹿角、长耳朵、浅口鼻、背上白点。"""
    s = []
    # 鹿角
    for x0 in (10.6, 17.4):
        s.append(_r(x0, 4.2, 1, 4.6, pal["out"]))
        s.append(_r(x0 - 1.4, 5.4, 1.4, 1, pal["out"]))
        s.append(_r(x0 + 1, 6.4, 1.6, 1, pal["out"]))
        s.append(_r(x0, 4.2, 1, 0.8, pal["accent"]))
    # 长耳朵
    for cx in (8.4, 21.6):
        s.append(_blob(cx, 10.8, 1.8, 2.6, pal["out"]))
        s.append(_blob(cx, 10.8, 1.2, 2.0, pal["light"]))
        s.append(_blob(cx, 10.8, 0.7, 1.4, pal["accent"], .8))
    # 小尾巴
    s.append(_blob(22.4, 19.4, 1.4, 1.2, pal["out"]))
    s.append(_blob(22.4, 19.4, 0.9, 0.7, pal["light"]))
    # 身体与四肢
    s.append(_outline(15, 21.4, 5.8, 4.0, pal))
    s.append(_blob(15, 22.6, 3.2, 2.2, pal["belly"]))
    s.append(_legs(pal, y=24, w=2, h=3))
    for (x, y) in ((10.4, 19.6), (13.4, 24), (18.4, 19.2), (16.4, 22.4)):
        s.append(_r(x, y, 1, 1, pal["light"]))
    # 头与口鼻
    s.append(_outline(15, 12.4, 5.4, 4.4, pal))
    s.append(_blob(15, 15.2, 2.6, 1.8, pal["light"]))
    s.append(_eyes(11.4, 16.6, 10.6, mood, pal, star))
    s.append(_blob(15, 14.2, 1.1, 0.7, pal["out"]))
    s.append(_mouth(15, 15.4, mood, pal))
    s.append(_cheeks(9.6, 19, 14.2, mood, pal))
    return "".join(s)


def _sp_dragon(pal, mood, star):
    """小龙：金色直角、背鳍、圆肚甲片、卷尾巴。"""
    s = []
    # 卷尾
    s.append(_blob(22.4, 22.6, 2.6, 1.6, pal["out"]))
    s.append(_blob(22.4, 22.6, 1.9, 1.0, pal["base"]))
    s.append(_blob(24.4, 21.2, 1.2, 1.6, pal["out"]))
    s.append(_blob(24.4, 21.2, 0.8, 1.1, pal["shade"]))
    # 背鳍
    for (x, y) in ((12.4, 16.2), (15, 15.2), (17.6, 16.2)):
        s.append(_r(x, y - 1.6, 1, 1.6, pal["accent"]))
        s.append(_r(x, y - 1.6, 1, 0.8, pal["light"], .7))
    # 身体
    s.append(_outline(15, 21, 5.6, 4.4, pal))
    s.append(_blob(15, 21.8, 3.6, 2.8, pal["belly"]))
    for y in (19.6, 21.6, 23.4):
        s.append(_r(12, y, 6, 0.4, pal["shade"], .55))
    s.append(_legs(pal, y=24.2, w=2, h=2.2))
    # 小翅膀
    for x0 in (7.2, 21.4):
        s.append(_r(x0, 15.4, 1.8, 3.2, pal["accent"]))
        s.append(_r(x0, 15.4, 1.4, 1.2, pal["light"], .8))
        s.append(_r(x0, 18.2, 1.8, 0.4, pal["shade"]))
    # 头
    s.append(_outline(15, 12.4, 5.6, 4.6, pal))
    s.append(_blob(15, 14.8, 2.8, 1.8, pal["light"]))
    # 直角
    s.append(_r(10.2, 7.4, 1, 3, pal["accent"]))
    s.append(_r(18.8, 7.4, 1, 3, pal["accent"]))
    s.append(_r(10.2, 6.6, 1, 0.8, pal["light"]))
    s.append(_r(18.8, 6.6, 1, 0.8, pal["light"]))
    s.append(_eyes(11.4, 16.6, 10.4, mood, pal, star))
    s.append(_r(14, 13.8, 1, 0.8, pal["out"]))
    s.append(_r(16, 13.8, 1, 0.8, pal["out"]))
    s.append(_mouth(15, 15.2, mood, pal))
    s.append(_cheeks(9.8, 19.2, 13.6, mood, pal))
    return "".join(s)


def _sp_slime(pal, mood, star):
    """史莱姆：果冻圆顶 + 平底，通体半透，没有腿。"""
    s = []
    s.append(_blob(15, 17.6, 7.2, 7.4, pal["out"]))
    s.append(_r(7.6, 19.4, 14.8, 5.6, pal["out"]))
    s.append(_r(7.4, 24, 15.2, 1, pal["out"]))
    s.append(_blob(15, 17.6, 6.4, 6.5, pal["base"]))
    s.append(_r(8.4, 19.4, 13.2, 4.8, pal["base"]))
    s.append(_r(8.4, 24, 13.2, 0.8, pal["base"]))
    # 底部凝亮层
    s.append(_r(9.6, 21.8, 10.8, 2.8, pal["belly"], .85))
    # 高光与气泡
    s.append(_r(10, 12.4, 2, 1, pal["light"], .9))
    s.append(_r(9.6, 13.2, 1, 1, pal["light"], .9))
    s.append(_r(19, 14, 1, 1, pal["light"], .7))
    for (x, y) in ((12.6, 21), (17.4, 22.2), (15.2, 23.4)):
        s.append(_r(x, y, 0.6, 0.6, pal["light"], .8))
    s.append(_eyes(11.2, 16.8, 14.4, mood, pal, star))
    s.append(_mouth(15, 17.2, mood, pal))
    s.append(_cheeks(9.4, 19.6, 18.8, mood, pal))
    return "".join(s)


def _sp_pudding(pal, mood, star):
    """布丁：梯形奶冻身子 + 焦糖顶 + 樱桃，Q 弹无腿。"""
    s = []
    rows = [(13.6, 4.6), (14.6, 5.4), (15.6, 6.0), (16.6, 6.6),
            (17.6, 7.0), (18.6, 7.4), (19.6, 7.6), (20.6, 7.8),
            (21.6, 8.0), (22.6, 8.0), (23.6, 7.6), (24.4, 6.8)]
    for (y, w) in rows:
        s.append(_r(15 - w, y, w * 2, 1, pal["out"]))
    for (y, w) in rows:
        s.append(_r(15 - w + 0.6, y + 0.2, w * 2 - 1.2, 0.8, pal["base"]))
    # 焦糖顶（含挂边）
    for (y, w) in rows[:4]:
        s.append(_r(15 - w + 0.6, y + 0.2, w * 2 - 1.2, 0.8, pal["top"]))
    s.append(_r(9, 16.8, 2, 1.2, pal["top"]))
    s.append(_r(14, 16.8, 2, 1.8, pal["top"]))
    s.append(_r(19, 16.8, 2, 1.2, pal["top"]))
    # 奶霜高光
    s.append(_r(9.6, 19, 1, 3, pal["light"], .85))
    s.append(_r(19.4, 20, 1, 2.4, pal["light"], .85))
    s.append(_r(11, 17.4, 3, 0.8, pal["light"], .55))
    # 樱桃
    s.append(_r(15, 9.4, 1, 4, pal["out"]))
    s.append(_r(16, 9.4, 1, 1.6, pal["out"]))
    s.append(_blob(14.6, 11.2, 1.9, 1.7, pal["out"]))
    s.append(_blob(14.6, 11.2, 1.3, 1.1, "#E8455F"))
    s.append(_r(13.8, 10.4, 0.6, 0.6, "#FF9CAC"))
    # 脸
    s.append(_eyes(11, 17, 18.4, mood, pal, star))
    s.append(_mouth(15, 20.2, mood, pal))
    s.append(_cheeks(9.2, 19.8, 19.6, mood, pal))
    s.append(_r(12, 24.6, 6, 0.6, pal["shade"], .45))
    return "".join(s)


def _sp_mech_mouse(pal, mood, star):
    """机械鼠：齿轮大耳 + 金属圆壳 + 发条尾巴 + 履带脚。"""
    s = []
    # 发条尾巴
    s.append(_r(19.6, 22.4, 2.4, 1, pal["shade"]))
    s.append(_r(21.6, 19.4, 1, 3.4, pal["shade"]))
    s.append(_r(22.6, 18.4, 2, 1, pal["shade"]))
    s.append(_blob(25.2, 18, 1.2, 1.2, pal["out"]))
    s.append(_blob(25.2, 18, 0.7, 0.7, pal["accent"]))
    # 齿轮耳
    for cx in (9.4, 20.6):
        for (dx, dy) in ((0, -2.4), (0, 2.4), (-2.4, 0), (2.4, 0)):
            s.append(_r(cx + dx - 0.5, 7.6 + dy - 0.5, 1, 1, pal["out"]))
        s.append(_blob(cx, 7.6, 2.8, 2.8, pal["out"]))
        s.append(_blob(cx, 7.6, 2.0, 2.0, pal["shade"]))
        s.append(_r(cx - 0.5, 7.1, 1, 1, pal["light"]))
    # 履带脚
    s.append(_r(10, 24.8, 4.4, 1.8, pal["out"]))
    s.append(_r(15.6, 24.8, 4.4, 1.8, pal["out"]))
    s.append(_r(10.6, 25.2, 3.2, 0.8, pal["shade"]))
    s.append(_r(16.2, 25.2, 3.2, 0.8, pal["shade"]))
    # 金属身体
    s.append(_outline(15, 21.6, 5.0, 3.6, pal))
    s.append(_r(10.6, 18.6, 8.8, 1, pal["light"]))
    s.append(_r(13.4, 20.8, 3.2, 2.4, pal["belly"]))
    s.append(_r(14.2, 21.2, 1, 1, "#FFFFFF"))
    # 圆头 + 护目镜
    s.append(_outline(15, 11.6, 5.6, 4.6, pal))
    s.append(_r(10, 9.4, 10, 2.2, pal["eye"]))
    s.append(_r(10, 9.4, 10, 0.6, pal["accent"]))
    s.append(_r(11.6, 9.8, 1.2, 1, "#FFFFFF") + _r(17.2, 9.8, 1.2, 1, "#FFFFFF"))
    s.append(_r(15, 12.2, 0.8, 0.8, pal["shade"]))
    if mood == "sad":
        s.append(_r(13, 14.4, 1.2, 1, pal["shade"]) + _r(16.4, 14.4, 1.2, 1, pal["shade"]))
    elif mood == "sick":
        s.append(_r(13.2, 14.6, 3.6, 1, pal["shade"]))
    else:
        s.append(_r(13.4, 14.4, 1.2, 1, pal["accent"]) + _r(15.4, 14.4, 1.2, 1, pal["accent"]))
    s.append(_cheeks(9, 19.6, 12.8, mood, pal))
    return "".join(s)


def _sp_mech_rabbit(pal, mood, star):
    """机甲兔：铆钉金属长耳、方头面罩、机械臂与履带。"""
    s = []
    # 机械长耳
    for x0 in (9.2, 17.4):
        s.append(_r(x0, 1.4, 3.4, 9, pal["out"]))
        s.append(_r(x0 + 0.6, 2.2, 2.2, 7.6, pal["base"]))
        s.append(_r(x0 + 0.6, 2.2, 2.2, 0.8, pal["light"]))
        for y in (3.6, 5.6, 7.6):
            s.append(_r(x0 + 1.4, y, 0.7, 0.7, pal["accent"]))
    # 弹簧尾巴
    s.append(_r(20.4, 19.6, 2.4, 1, pal["shade"]))
    s.append(_r(22.4, 20.6, 2, 1, pal["shade"]))
    s.append(_r(20.4, 21.6, 2.4, 1, pal["shade"]))
    # 圆金属身体
    s.append(_outline(15, 21.2, 5.4, 4.0, pal))
    s.append(_r(10.6, 18.4, 8.8, 1, pal["light"]))
    s.append(_r(13, 20.4, 4, 2.2, pal["belly"]))
    s.append(_r(14.2, 20.8, 1, 1, "#FFFFFF"))
    # 机械臂
    s.append(_r(7.6, 18.6, 3, 1.4, pal["out"]) + _r(8, 18.8, 2.2, 0.9, pal["shade"]))
    s.append(_r(19.4, 18.6, 3, 1.4, pal["out"]) + _r(19.8, 18.8, 2.2, 0.9, pal["shade"]))
    # 履带
    s.append(_r(11, 24.8, 4, 1.6, pal["out"]) + _r(11.6, 25.2, 2.8, 0.7, pal["shade"]))
    s.append(_r(15.4, 24.8, 4, 1.6, pal["out"]) + _r(16, 25.2, 2.8, 0.7, pal["shade"]))
    # 方头 + 口鼻
    s.append(_outline(15, 11.4, 5.4, 4.4, pal))
    s.append(_blob(15, 15.8, 2.8, 1.6, pal["light"], .7))
    s.append(_eyes(11.2, 17.2, 10.2, mood, pal, star))
    s.append(_r(14.4, 12.8, 1, 1, pal["accent"]))
    s.append(_mouth(15, 14.2, mood, pal))
    s.append(_cheeks(9.4, 19.4, 13.2, mood, pal))
    return "".join(s)


def _sp_duck(pal, mood, star):
    """小鸭：黄色圆身 + 橘色扁嘴 + 小翅膀与脚蹼。"""
    s = []
    # 脚蹼
    s.append(_r(11.4, 25.8, 2, 1, pal["accent"]) + _r(10.6, 26.4, 3.4, 1, pal["accent"]))
    s.append(_r(17, 25.8, 2, 1, pal["accent"]) + _r(16.2, 26.4, 3.4, 1, pal["accent"]))
    # 翘起的小尾巴
    s.append(_r(21.4, 19.2, 2.4, 1, pal["shade"]) + _r(22.8, 18.2, 1.4, 1.4, pal["shade"]))
    # 身体
    s.append(_blob(15, 21.6, 5.6, 4.4, pal["out"]))
    s.append(_blob(15, 21.6, 4.9, 3.7, pal["base"]))
    s.append(_blob(15, 22.4, 3.2, 2.6, pal["belly"]))
    # 翅膀
    s.append(_blob(9.6, 20.4, 1.8, 2.6, pal["shade"]))
    s.append(_blob(20.4, 20.4, 1.8, 2.6, pal["shade"]))
    s.append(_blob(9.6, 19.8, 1.2, 1.8, pal["light"], .8))
    s.append(_blob(20.4, 19.8, 1.2, 1.8, pal["light"], .8))
    # 头
    s.append(_outline(15, 11.6, 5.2, 4.6, pal))
    s.append(_blob(15, 8.4, 2.6, 1.4, pal["light"]))
    # 呆毛
    s.append(_r(14.4, 3.6, 1, 2.6, pal["shade"]) + _r(15.2, 2.8, 1, 1.4, pal["shade"]))
    # 扁嘴
    if mood == "sad":
        s.append(_r(12.6, 14, 4.8, 1.4, pal["accent"]))
        s.append(_r(13.4, 15.4, 2, 0.6, pal["accent"]))
    elif mood == "sick":
        s.append(_r(12.8, 14.2, 4.4, 1.2, pal["shade"]))
    else:
        s.append(_r(12.4, 13.4, 5.2, 1.6, pal["accent"]))
        s.append(_r(12.4, 13.4, 5.2, 0.6, pal["light"], .7))
        s.append(_r(13.6, 15, 2, 0.6, pal["accent"]))
    s.append(_eyes(10.6, 17.4, 10.4, mood, pal, star))
    s.append(_cheeks(9, 20, 12.6, mood, pal))
    return "".join(s)


def _sp_panda(pal, mood, star):
    """熊猫：黑耳黑眼圈 + 白胖身子，前肢与腿是黑的。"""
    s = []
    # 黑耳
    s.append(_blob(9.4, 7.6, 2.2, 2.2, pal["out"]))
    s.append(_blob(20.6, 7.6, 2.2, 2.2, pal["out"]))
    # 身体
    s.append(_outline(15, 21.2, 5.8, 4.2, pal))
    s.append(_blob(15, 22.2, 3.4, 2.4, pal["belly"]))
    # 黑色肩带与前肢
    s.append(_r(10.2, 18.8, 2.8, 3.6, pal["out"]))
    s.append(_r(17, 18.8, 2.8, 3.6, pal["out"]))
    # 黑腿
    s.append(_r(11, 24, 3, 2, pal["out"]) + _r(16, 24, 3, 2, pal["out"]))
    s.append(_r(11.4, 24.4, 2.2, 0.8, pal["shade"]) + _r(16.4, 24.4, 2.2, 0.8, pal["shade"]))
    # 白头
    s.append(_outline(15, 12, 6.2, 5.2, pal))
    # 黑眼圈
    s.append(_blob(11.4, 11, 2.2, 2.2, pal["out"]))
    s.append(_blob(18.6, 11, 2.2, 2.2, pal["out"]))
    s.append(_eyes(10.4, 17.6, 10, mood, pal, star))
    if mood == "happy":
        s.append(_r(11.2, 10.6, 1, 1, "#2A2A32") + _r(18.2, 10.6, 1, 1, "#2A2A32"))
    # 鼻子与嘴
    s.append(_r(14.6, 13.6, 1, 1, pal["out"]))
    s.append(_mouth(15, 14.4, mood, pal))
    s.append(_cheeks(9.4, 19.4, 14.2, mood, pal))
    return "".join(s)


def _sp_wolf(pal, mood, star):
    """小狼：尖耳朵、灰蓝毛皮、白口鼻与蓬松大尾巴。"""
    s = []
    # 蓬松尾巴
    s.append(_blob(24.2, 20.6, 2.6, 3.2, pal["out"]))
    s.append(_blob(24.2, 20.6, 2.0, 2.6, pal["shade"]))
    s.append(_blob(24.6, 22.8, 1.4, 1.6, pal["light"]))
    # 三角尖耳
    for cx in (9.4, 20.6):
        s.append(_r(cx - 1.4, 5.6, 2.8, 1, pal["out"])
                 + _r(cx - 1.0, 6.6, 2.0, 1, pal["out"])
                 + _r(cx - 0.6, 7.6, 1.2, 1.6, pal["out"]))
        s.append(_r(cx - 0.9, 6.8, 1.4, 1, pal["base"])
                 + _r(cx - 0.5, 7.7, 0.8, 1.2, pal["base"]))
    # 身体
    s.append(_outline(15, 21.2, 5.8, 4.0, pal))
    s.append(_blob(15, 22.2, 3.2, 2.2, pal["belly"]))
    s.append(_legs(pal))
    # 头
    s.append(_outline(15, 12, 6.0, 5.0, pal))
    # 脸颊毛（狼的毛领）
    for (x, y, w, h) in ((8.2, 11.8, 1.6, 1.4), (20.2, 11.8, 1.6, 1.4),
                         (8.8, 13.2, 1.4, 1.2), (20.0, 13.2, 1.4, 1.2)):
        s.append(_r(x, y, w, h, pal["light"], .9))
    # 额前毛
    s.append(_r(11.6, 7.4, 1.6, 1.2, pal["light"]) + _r(15, 6.8, 1.6, 1.2, pal["light"])
             + _r(17, 7.4, 1.6, 1.2, pal["light"]))
    # 白口鼻
    s.append(_blob(15, 14.8, 2.6, 1.9, pal["belly"]))
    s.append(_eyes(11.2, 16.6, 10.2, mood, pal, star))
    s.append(_blob(15, 13.2, 0.9, 0.7, pal["out"]))
    s.append(_mouth(15, 15.2, mood, pal))
    s.append(_cheeks(9.4, 19.2, 13.6, mood, pal))
    return "".join(s)


def _sp_pony(pal, mood, star):
    """小马：长脸、短鬃毛、四只小蹄子和垂下来的尾巴。"""
    s = []
    # 尾巴（上宽下窄）
    for (cx, cy, rx, ry) in ((23.4, 19.4, 1.5, 1.8), (23.8, 21.4, 1.2, 1.5),
                             (23.4, 23.0, 1.0, 1.2)):
        s.append(_blob(cx, cy, rx, ry, pal["out"]))
        s.append(_blob(cx, cy, rx - 0.6, ry - 0.6, pal["shade"]))
    # 脖子鬃毛（斜向阶梯）
    for (x, y, w, h) in ((9.0, 8.4, 2.6, 1.6), (8.6, 9.8, 2.4, 1.6),
                         (8.8, 11.2, 2.2, 1.6), (9.4, 12.6, 2.0, 1.6)):
        s.append(_r(x, y, w, h, pal["shade"]))
    # 身体
    s.append(_outline(15, 21, 6.0, 4.4, pal))
    s.append(_blob(15, 21.8, 3.4, 2.8, pal["belly"]))
    # 腿与蹄
    for x in (11, 17.4):
        s.append(_r(x, 22.6, 2, 3, pal["out"]))
        s.append(_r(x, 22.6, 2, 2.4, pal["base"]))
        s.append(_r(x, 25.2, 2, 0.8, pal["out"]))
    # 长脸
    s.append(_outline(15, 12.6, 5.0, 4.6, pal))
    s.append(_blob(15, 15.6, 2.6, 1.9, pal["light"]))
    # 耳朵
    s.append(_blob(10.4, 7.8, 1.6, 2.0, pal["out"]))
    s.append(_blob(10.4, 7.8, 1.0, 1.4, pal["base"]))
    s.append(_blob(19.6, 7.8, 1.6, 2.0, pal["out"]))
    s.append(_blob(19.6, 7.8, 1.0, 1.4, pal["base"]))
    # 额前鬃
    s.append(_r(13, 7.6, 4, 1.4, pal["shade"]))
    s.append(_r(12, 8.6, 1.4, 1.6, pal["shade"]))
    s.append(_eyes(11.2, 16.6, 10.6, mood, pal, star))
    s.append(_r(14, 13.8, 1, 0.8, pal["out"]) + _r(16, 13.8, 1, 0.8, pal["out"]))
    s.append(_mouth(15, 15.4, mood, pal))
    s.append(_cheeks(9.6, 19.2, 14, mood, pal))
    return "".join(s)


def _sp_unicorn(pal, mood, star):
    """独角兽：雪白身子 + 金螺旋角 + 粉蓝双色彩鬃。"""
    s = []
    # 金螺旋角
    s.append(_r(14.2, 2.4, 1.8, 5.0, pal["horn"]))
    s.append(_r(14.2, 2.4, 1.8, 1.0, "#FFF0B8"))
    for y in (3.6, 4.8, 6.0):
        s.append(_r(14.2, y, 1.8, 0.6, "#E0A93A"))
    # 耳朵
    for cx in (10.4, 19.6):
        s.append(_blob(cx, 8.6, 1.6, 2.0, pal["out"]))
        s.append(_blob(cx, 8.6, 1.0, 1.4, pal["base"]))
    # 双色彩鬃（阶梯状）
    for i, (x, y, w, h) in enumerate(((9.2, 8.6, 2.4, 1.6), (8.8, 10.0, 2.4, 1.6),
                                      (8.8, 11.4, 2.2, 1.6), (9.4, 12.8, 2.0, 1.4))):
        s.append(_r(x, y, w, h, "#FFB0D6" if i % 2 == 0 else "#8FE3FF"))
    s.append(_r(8.2, 10.6, 1.2, 2.6, "#FFB0D6"))
    # 彩虹尾巴
    for (cx, cy, rx, ry) in ((23.2, 19.4, 1.8, 2.2), (23.6, 21.8, 1.4, 1.8),
                             (23.2, 23.6, 1.1, 1.3)):
        s.append(_blob(cx, cy, rx, ry, "#FFB0D6"))
        s.append(_blob(cx + 0.6, cy + 0.4, rx - 0.8, ry - 0.8, "#8FE3FF"))
    # 身体
    s.append(_outline(15, 21.0, 5.8, 4.2, pal))
    s.append(_blob(15, 22.0, 3.2, 2.4, pal["belly"]))
    s.append(_legs(pal))
    # 头
    s.append(_outline(15, 12.6, 5.4, 4.4, pal))
    s.append(_blob(15, 15.6, 2.6, 1.9, pal["light"]))
    s.append(_eyes(11.4, 16.6, 10.8, mood, pal, star))
    s.append(_r(14, 13.8, 1, 0.8, pal["out"]) + _r(16, 13.8, 1, 0.8, pal["out"]))
    s.append(_mouth(15, 15.4, mood, pal))
    s.append(_cheeks(9.6, 19.2, 14, mood, pal))
    # 额头星点
    s.append(_r(12.4, 8.6, 1, 1, "#FFF3B0") + _r(17.4, 9.4, 1, 1, "#FFF3B0"))
    return "".join(s)


def _sp_qilin(pal, mood, star):
    """麒麟：金鳞身子 + 赤色火焰鬃角，蹄下踩着云纹。"""
    s = []
    # 云纹
    for (cx, cy, rx, ry) in ((8.4, 25.6, 2.4, 1.0), (19.6, 25.6, 2.6, 1.0)):
        s.append(_blob(cx, cy, rx, ry, pal["light"], .8))
    # 火焰鬃（三簇火苗贴着背）
    for (cx, cy, rx, ry, c) in ((9.6, 9.4, 2.0, 2.6, pal["accent"]),
                                (8.4, 11.4, 1.4, 1.8, "#FFB03A"),
                                (11.4, 8.0, 1.2, 1.8, pal["accent"])):
        s.append(_blob(cx, cy, rx, ry, c))
    s.append(_r(9.8, 6.4, 1, 1.6, "#FFE0A0"))
    s.append(_r(8.4, 10.6, 0.8, 1.2, "#FFE0A0"))
    # 金角（角根带赤）
    s.append(_r(14.4, 2.8, 1.4, 4.6, "#FFD54A"))
    s.append(_r(14.4, 2.8, 0.6, 1.2, "#FFF6C8"))
    s.append(_r(14.4, 6.2, 1.4, 1.2, pal["accent"]))
    # 火焰尾巴（向上卷）
    for (cx, cy, rx, ry, c) in ((23.4, 19.4, 1.8, 2.2, pal["accent"]),
                                (22.8, 21.6, 1.6, 1.8, "#FFB03A"),
                                (23.8, 23.0, 1.2, 1.2, pal["accent"])):
        s.append(_blob(cx, cy, rx, ry, c))
    s.append(_r(23.4, 17.4, 1, 1.4, "#FFE0A0"))
    # 身体与鳞片
    s.append(_outline(15, 21.0, 5.8, 4.2, pal))
    s.append(_blob(15, 22.0, 3.4, 2.4, pal["belly"]))
    for (x, y) in ((11, 19.2), (13.4, 20.8), (16.4, 19.0), (18, 21.2)):
        s.append(_r(x, y, 1.4, 0.8, pal["shade"], .8))
        s.append(_r(x + 0.4, y + 0.8, 0.6, 0.8, pal["shade"], .8))
    s.append(_legs(pal, y=24, w=2.4, h=2.4))
    # 头
    s.append(_outline(15, 12.6, 5.4, 4.4, pal))
    s.append(_blob(15, 15.6, 2.6, 1.9, pal["light"]))
    s.append(_eyes(11.4, 16.6, 10.8, mood, pal, star))
    s.append(_r(14, 14.2, 1, 0.8, pal["out"]) + _r(16, 14.2, 1, 0.8, pal["out"]))
    s.append(_mouth(15, 15.6, mood, pal))
    s.append(_cheeks(9.6, 19.2, 14.2, mood, pal))
    return "".join(s)


def _sp_bean(pal, mood, star):
    """豆豆：吃豆人世界的小黄豆，圆身大嘴，身边飘着豆点。"""
    s = []
    # 飘浮豆点
    for (x, y) in ((2.4, 6.4), (3.4, 11.4), (23.6, 6.6)):
        s.append(_blob(x, y, 1.0, 1.0, pal["shade"], .85))
    # 小脚
    s.append(_blob(11.4, 24.6, 1.6, 1.4, pal["out"]))
    s.append(_blob(18.6, 24.6, 1.6, 1.4, pal["out"]))
    # 圆身
    s.append(_blob(15, 15.8, 8.0, 7.8, pal["out"]))
    s.append(_blob(15, 15.8, 7.2, 7.0, pal["base"]))
    s.append(_blob(11.2, 10.4, 2.2, 1.7, pal["light"], .8))
    # 眼睛
    s.append(_eyes(10.8, 16.4, 11.4, mood, pal, star))
    # 大嘴
    c = pal["out"]
    if mood == "sad":
        s.append(_r(13, 19.6, 4, 1, c) + _r(12.4, 20.4, 1, 0.8, c)
                 + _r(16.6, 20.4, 1, 0.8, c))
    elif mood == "sick":
        s.append(_r(12.6, 19.4, 4.8, 1, c) + _r(15.2, 20.2, 1.4, 0.8, pal["accent"]))
    else:
        s.append(_r(12.2, 18.6, 5.6, 1, c))
        s.append(_r(13, 19.6, 4, 1, c))
        s.append(_r(14, 20.6, 2, 0.8, c))
        s.append(_r(13.4, 19.6, 3.2, 0.8, pal["accent"], .85))
    s.append(_cheeks(9.4, 19.4, 16.2, mood, pal))
    return "".join(s)


def _sp_mushroom(pal, mood, star):
    """蘑菇仔：红伞盖带白点，伞下白胖柄身子长着小脸。"""
    s = []
    # 柄身
    s.append(_r(10.4, 15.2, 9.2, 9.0, pal["out"]))
    s.append(_r(11.2, 16.0, 7.6, 7.4, pal["base"]))
    s.append(_r(11.2, 16.0, 7.6, 1, pal["light"]))
    s.append(_r(13, 18.6, 4, 3, pal["belly"]))
    # 小脚
    s.append(_r(10.4, 23.6, 3.2, 1.6, pal["out"]) + _r(16.4, 23.6, 3.2, 1.6, pal["out"]))
    # 伞盖
    s.append(_blob(15, 11.8, 8.4, 4.6, pal["out"]))
    s.append(_blob(15, 11.8, 7.6, 3.8, pal["cap"]))
    s.append(_r(7.4, 13.4, 15.2, 1.6, pal["cap"]))
    s.append(_r(7.4, 13.4, 15.2, 0.6, pal["light"], .4))
    # 白点
    for (cx, cy, rx, ry) in ((10.4, 10.4, 1.4, 1.0), (15, 8.8, 1.6, 1.2),
                             (19.6, 10.6, 1.2, 0.9)):
        s.append(_blob(cx, cy, rx, ry, pal["light"]))
    # 脸
    s.append(_eyes(12.2, 16.2, 17.6, mood, pal, star))
    s.append(_mouth(15, 19.6, mood, pal))
    s.append(_cheeks(11, 18.6, 18.6, mood, pal))
    return "".join(s)


def _sp_donut(pal, mood, star):
    """甜甜圈：面包圆环 + 粉色糖霜 + 彩针，脸画在糖霜上。"""
    s = []
    # 圆环
    s.append(_blob(15, 16.4, 8.6, 8.2, pal["out"]))
    s.append(_blob(15, 16.4, 7.8, 7.4, pal["base"]))
    # 糖霜
    s.append(_blob(15, 12.8, 7.2, 5.4, pal["icing"]))
    for (x, y, w, h) in ((8.2, 14.2, 1.6, 2.2), (10.6, 15.2, 1.4, 3.0),
                         (17.6, 15.0, 1.6, 2.4), (19.8, 14.0, 1.2, 2.0)):
        s.append(_r(x, y, w, h, pal["icing"]))
    s.append(_blob(11.4, 9.4, 2.2, 1.1, pal["light"], .55))
    # 中间的洞（小一号，靠下）
    s.append(_blob(15, 20.6, 2.6, 2.2, pal["out"]))
    s.append(_blob(15, 20.6, 1.8, 1.4, pal["shade"]))
    # 彩针
    for (x, y, c) in ((9.8, 10.6, "#FFD54A"), (12.2, 9.2, "#8FE3FF"),
                      (17.4, 10.4, "#9CFFB0"), (19.6, 12.0, "#FFD54A"),
                      (8.4, 12.8, "#FF9AC4")):
        s.append(_r(x, y, 1.2, 0.6, c))
    # 脸
    s.append(_eyes(10.8, 16.8, 11.8, mood, pal, star))
    s.append(_mouth(15, 16.2, mood, pal))
    s.append(_cheeks(9, 19.4, 14.4, mood, pal))
    return "".join(s)


def _sp_onigiri(pal, mood, star):
    """饭团：三角饭团裹海苔，白米上撒几粒芝麻。"""
    s = []
    rows = [(10.6, 2.6), (11.6, 3.8), (12.6, 5.0), (13.6, 6.2), (14.6, 7.4),
            (15.6, 8.4), (16.6, 9.2), (17.6, 9.8), (18.6, 10.4), (19.6, 10.8),
            (20.6, 11.0), (21.6, 11.2), (22.6, 11.2), (23.6, 11.2)]
    for (y, w) in rows:
        s.append(_r(15 - w, y, w * 2, 1, pal["out"]))
    for (y, w) in rows:
        s.append(_r(15 - w + 1, y, w * 2 - 2, 1, pal["base"]))
    # 海苔
    s.append(_r(12.6, 20.4, 4.8, 4.2, pal["nori"]))
    s.append(_r(12.6, 20.4, 4.8, 0.6, "#4E7A5C"))
    # 芝麻
    for (x, y) in ((10.6, 17.6), (19, 17.2), (15.4, 14.4), (20, 20.4), (9.8, 21.2)):
        s.append(_r(x, y, 0.7, 0.5, pal["shade"]))
    # 脸
    s.append(_eyes(11.6, 16.4, 15.0, mood, pal, star))
    s.append(_mouth(15, 17.2, mood, pal))
    s.append(_cheeks(10, 18.2, 16.4, mood, pal))
    return "".join(s)


def _sp_mech_turtle(pal, mood, star):
    """机甲龟：厚装甲龟壳刻着电路纹，四只机械短腿。"""
    s = []
    # 尾部推进器
    s.append(_r(22.4, 21.4, 2.2, 2, pal["out"]))
    s.append(_r(23, 21.8, 1.4, 1.2, pal["accent"]))
    # 四只机械腿
    for x in (10.4, 18.4):
        s.append(_r(x, 24.2, 2.6, 2, pal["out"]))
        s.append(_r(x + 0.4, 24.6, 1.8, 1.2, pal["shade"]))
    # 龟壳
    s.append(_outline(15, 21, 7.6, 4.6, pal))
    s.append(_blob(15, 21, 6.4, 3.6, pal["belly"], .55))
    # 电路纹
    for (x, y, w, h) in ((10.6, 19.4, 6.4, 0.6), (13, 21.6, 5, 0.6),
                         (10.8, 23, 3, 0.6), (17.4, 23, 3, 0.6)):
        s.append(_r(x, y, w, h, pal["shade"], .9))
    s.append(_r(13.6, 21.6, 1.6, 1.6, pal["accent"]))
    s.append(_r(14.2, 22.2, 0.6, 0.6, pal["light"]))
    # 头
    s.append(_outline(15, 11.0, 5.0, 4.2, pal))
    # 护目镜：镜片里透出两只机械眼，而不是一条黑带
    s.append(_r(9.8, 9.2, 10.4, 3.0, pal["out"]))
    s.append(_r(10.2, 9.6, 9.6, 2.2, pal["eye"]))
    s.append(_r(12.2, 10.2, 1.6, 1.2, pal["accent"]))
    s.append(_r(16.2, 10.2, 1.6, 1.2, pal["accent"]))
    s.append(_r(12.5, 10.5, 0.6, 0.6, "#FFFFFF"))
    s.append(_r(16.5, 10.5, 0.6, 0.6, "#FFFFFF"))
    # 镜梁
    s.append(_r(14.8, 9.6, 0.4, 2.2, pal["out"]))
    s.append(_mouth(15, 13.8, mood, pal))
    s.append(_cheeks(9.6, 18.4, 13.4, mood, pal))
    return "".join(s)


def _sp_mech_lion(pal, mood, star):
    """机械狮：一圈齿轮当鬃毛，方下巴装甲头。"""
    s = []
    # 齿轮鬃毛
    for (dx, dy) in ((0, -5.0), (0, 5.0), (-5.0, 0), (5.0, 0),
                     (-3.6, -3.6), (3.6, -3.6), (-3.6, 3.6), (3.6, 3.6)):
        s.append(_r(15 + dx - 0.9, 11.4 + dy - 0.9, 1.8, 1.8, pal["shade"]))
    s.append(_blob(15, 11.4, 5.6, 5.2, pal["shade"]))
    s.append(_blob(15, 11.4, 4.6, 4.2, pal["base"]))
    # 身体
    s.append(_outline(15, 21.6, 5.2, 3.8, pal))
    s.append(_blob(15, 22.4, 3.0, 2.2, pal["light"]))
    # 机械前爪
    s.append(_r(9.8, 20.0, 2.4, 3.6, pal["out"]) + _r(10.2, 20.4, 1.6, 2.8, pal["shade"]))
    s.append(_r(17.8, 20.0, 2.4, 3.6, pal["out"]) + _r(18.2, 20.4, 1.6, 2.8, pal["shade"]))
    # 尾巴 + 齿轮尖
    s.append(_r(20.8, 20.8, 2.4, 1, pal["shade"]))
    s.append(_blob(24.2, 19.6, 1.6, 1.6, pal["out"]))
    s.append(_blob(24.2, 19.6, 0.9, 0.9, pal["accent"]))
    # 脸
    s.append(_eyes(11.4, 16.6, 10.2, mood, pal, star))
    s.append(_r(14.4, 12.6, 1.2, 1, pal["shade"]))
    s.append(_mouth(15, 14, mood, pal))
    s.append(_cheeks(10, 18.2, 13, mood, pal))
    return "".join(s)


def _sp_hedgehog(pal, mood, star):
    """小刺猬：背上一排小尖刺，肚子软软一张脸。"""
    s = []
    # 背刺：沿头顶排一圈，尖端朝上，整体藏在身体轮廓后面
    spikes = ((9.4, 13.2), (11.4, 11.4), (13.4, 10.2), (15.4, 9.8),
              (17.4, 10.4), (19.4, 12.0), (21.0, 13.8))
    for (cx, top) in spikes:
        s.append(_r(cx - 1.4, top + 2.0, 2.8, 1.0, pal["shade"]))
        s.append(_r(cx - 1.0, top + 1.0, 2.0, 1.0, pal["shade"]))
        s.append(_r(cx - 0.5, top, 1.0, 1.0, pal["shade"]))
    # 身体
    s.append(_blob(15, 20.0, 7.4, 5.2, pal["out"]))
    s.append(_blob(15, 20.0, 6.6, 4.4, pal["base"]))
    s.append(_blob(15, 22.0, 4.4, 2.6, pal["belly"]))
    # 小脚
    s.append(_r(11.4, 24.6, 2.6, 1.4, pal["accent"]))
    s.append(_r(16.2, 24.6, 2.6, 1.4, pal["accent"]))
    # 脸
    s.append(_blob(15, 18.8, 4.4, 3.4, pal["light"]))
    s.append(_eyes(12.0, 17.6, 17.4, mood, pal, star))
    s.append(_r(14.8, 19.8, 1, 1, pal["out"]))
    s.append(_mouth(15, 21.4, mood, pal))
    s.append(_cheeks(10.6, 19.4, 19.6, mood, pal))
    return "".join(s)


def _sp_pig(pal, mood, star):
    """小猪：粉团子身子 + 猪鼻子 + 卷卷尾。"""
    s = []
    # 卷尾巴
    s.append(_blob(23.4, 21.2, 1.6, 1.4, pal["out"]))
    s.append(_blob(23.8, 20, 1.2, 1.0, pal["shade"]))
    # 三角耳
    for cx in (10.2, 19.8):
        s.append(_r(cx - 1.2, 6.6, 2.4, 1, pal["out"])
                 + _r(cx - 0.6, 7.6, 1.6, 1.4, pal["out"]))
        s.append(_r(cx - 0.7, 6.8, 1.2, 1, pal["accent"])
                 + _r(cx - 0.2, 7.8, 0.8, 1, pal["accent"]))
    # 身体
    s.append(_outline(15, 21, 6.2, 4.4, pal))
    s.append(_blob(15, 22, 3.4, 2.6, pal["belly"]))
    s.append(_legs(pal))
    # 头
    s.append(_outline(15, 12, 6.2, 5.0, pal))
    # 猪鼻子
    s.append(_r(12.6, 14.4, 4.8, 2.4, pal["accent"]))
    s.append(_r(13.6, 15, 0.8, 1.2, pal["shade"]))
    s.append(_r(16.2, 15, 0.8, 1.2, pal["shade"]))
    s.append(_eyes(10.6, 17.4, 10.4, mood, pal, star))
    s.append(_mouth(15, 17.4, mood, pal))
    s.append(_cheeks(9.2, 19.8, 13.4, mood, pal))
    return "".join(s)


def _sp_squirrel(pal, mood, star):
    """小松鼠：蓬蓬大尾巴立在后头，门牙两颗。"""
    s = []
    # 大尾巴
    s.append(_blob(23.4, 18.6, 3.0, 4.6, pal["out"]))
    s.append(_blob(23.4, 18.6, 2.3, 3.9, pal["shade"]))
    s.append(_blob(23.2, 15.2, 1.4, 1.8, pal["shade"]))
    s.append(_blob(24.0, 19.8, 1.2, 2.2, pal["light"], .8))
    # 耳朵
    for cx in (10.2, 19.8):
        s.append(_r(cx - 1.2, 6.2, 2.4, 1.2, pal["out"])
                 + _r(cx - 0.6, 7.2, 1.6, 1.6, pal["out"]))
        s.append(_r(cx - 0.7, 6.6, 1.2, 1.0, pal["accent"])
                 + _r(cx - 0.2, 7.4, 0.8, 1.2, pal["accent"]))
    # 身体
    s.append(_outline(15, 21.2, 5.6, 4.0, pal))
    s.append(_blob(15, 22.2, 3.0, 2.2, pal["belly"]))
    s.append(_legs(pal, y=24, w=3, h=2))
    # 头
    s.append(_outline(15, 12.2, 5.8, 4.8, pal))
    s.append(_blob(15, 15.4, 2.2, 1.6, pal["light"]))
    s.append(_eyes(11.4, 16.6, 10.6, mood, pal, star))
    s.append(_blob(15, 13.8, 0.9, 0.7, pal["out"]))
    # 门牙
    s.append(_r(14.4, 16, 1, 1.2, pal["light"]))
    s.append(_r(15.4, 16, 1, 1.2, pal["light"]))
    s.append(_mouth(15, 17.2, mood, pal))
    s.append(_cheeks(9.4, 19.2, 14.4, mood, pal))
    return "".join(s)


def _sp_phoenix(pal, mood, star):
    """凤凰：金红羽衣 + 三根火焰尾羽 + 头顶冠羽。"""
    s = []
    # 火焰尾羽
    for i, (x, y, w, h) in enumerate(((20.4, 16.4, 2.0, 5.6), (18, 18.0, 1.8, 4.4),
                                      (22.6, 18.4, 1.6, 4.0))):
        c = pal["accent"] if i % 2 == 0 else "#FFC93D"
        s.append(_r(x, y, w, h, c))
        s.append(_r(x + 0.4, y - 1.4, w - 0.8, 1.6, c))
    # 身体
    s.append(_outline(15, 20.4, 4.6, 4.6, pal))
    s.append(_blob(15, 21.4, 2.8, 2.6, pal["belly"]))
    # 翅膀
    for x0 in (8.6, 21.4):
        s.append(_r(x0, 15.4, 2.2, 4.4, pal["accent"]))
        s.append(_r(x0, 15.4, 1.4, 2.4, pal["light"], .8))
    # 脚
    s.append(_r(12.4, 24.4, 1.4, 1.6, "#FFC93D"))
    s.append(_r(16.2, 24.4, 1.4, 1.6, "#FFC93D"))
    # 头
    s.append(_outline(15, 11.4, 4.6, 4.0, pal))
    # 冠羽
    s.append(_r(14.4, 5.2, 1, 2.6, pal["accent"]))
    s.append(_r(15.4, 4.2, 1, 3.4, pal["accent"]))
    s.append(_r(15.4, 4.2, 1, 1, "#FFF0B8"))
    # 喙
    s.append(_r(13.4, 13.4, 3.2, 1.2, "#FFC93D"))
    s.append(_eyes(11, 17.2, 10.4, mood, pal, star))
    s.append(_cheeks(9.8, 18.4, 12.6, mood, pal))
    return "".join(s)


def _sp_pixiu(pal, mood, star):
    """貔貅：金身独角大眼，尾巴上串一枚铜钱。"""
    s = []
    # 云纹底座
    s.append(_blob(8.4, 25.6, 2.4, 1.0, pal["light"], .8))
    s.append(_blob(19.6, 25.6, 2.6, 1.0, pal["light"], .8))
    # 卷尾 + 铜钱
    s.append(_blob(23.2, 20.4, 2.0, 2.4, pal["out"]))
    s.append(_blob(23.2, 20.4, 1.4, 1.8, pal["accent"]))
    s.append(_blob(23.2, 20.4, 0.7, 0.7, pal["out"]))
    # 身体
    s.append(_outline(15, 21, 5.8, 4.2, pal))
    s.append(_blob(15, 22, 3.2, 2.4, pal["belly"]))
    s.append(_legs(pal, y=24, w=2.6, h=2.2))
    # 头
    s.append(_outline(15, 12.4, 5.6, 4.6, pal))
    # 独角
    s.append(_r(14.4, 4.2, 1.4, 3.8, "#FFD54A"))
    s.append(_r(14.4, 4.2, 0.6, 1.2, "#FFF6C8"))
    # 大眼
    s.append(_eyes(11, 17, 10.6, mood, pal, star))
    # 鼻与嘴
    s.append(_r(13.4, 13.8, 3.2, 1.2, pal["accent"]))
    s.append(_mouth(15, 15.4, mood, pal))
    s.append(_cheeks(9.4, 19.2, 13.8, mood, pal))
    # 金链
    s.append(_r(12, 18.2, 6, 1, "#FFD54A", .9))
    return "".join(s)


def _sp_block(pal, mood, star):
    """方块仔：一整块方头方脑的身子，肩上顶着掉下来的小方块。"""
    s = []
    # 周围下落的小方块
    for (x, y) in ((3.6, 8.2), (4.2, 14.6), (23.6, 6.6)):
        s.append(_r(x, y, 1.6, 1.6, pal["shade"], .85))
    # 肩上搭着的一块方砖（俄罗斯方块既视感）
    s.append(_r(17.6, 9.4, 3.0, 3.0, pal["out"]))
    s.append(_r(18.2, 10.0, 1.8, 1.8, pal["base"]))
    # 整块身子
    s.append(_r(9.4, 12.2, 11.2, 11.6, pal["out"]))
    s.append(_r(10.2, 13.0, 9.6, 10.0, pal["base"]))
    s.append(_r(10.2, 13.0, 9.6, 0.6, pal["light"], .9))
    s.append(_r(10.2, 13.6, 0.6, 3.0, pal["light"], .55))
    # 脸
    s.append(_eyes(11.2, 16.8, 15.2, mood, pal, star))
    s.append(_mouth(15, 17.6, mood, pal))
    s.append(_cheeks(9.8, 18.4, 16.6, mood, pal))
    # 小手小脚
    s.append(_r(7.8, 19.6, 1.4, 2.4, pal["accent"]))
    s.append(_r(20.8, 19.6, 1.4, 2.4, pal["accent"]))
    s.append(_r(11, 23.6, 2.4, 1.4, pal["accent"]))
    s.append(_r(16.4, 23.6, 2.4, 1.4, pal["accent"]))
    return "".join(s)


def _sp_bomb(pal, mood, star):
    """炸弹仔：黑铁圆身 + 引线火花，一脸认真地准备炸开。"""
    s = []
    # 引线 + 火花
    s.append(_r(15.4, 4.4, 1, 4.2, pal["shade"]))
    s.append(_r(16.2, 5.4, 1, 1.6, pal["shade"]))
    s.append(_blob(15.9, 3.4, 1.2, 1.2, "#FFC93D"))
    s.append(_r(15.5, 2.4, 0.8, 1.2, "#FFF0B8"))
    # 铁球身体
    s.append(_blob(15, 15.6, 8.2, 8.0, pal["out"]))
    s.append(_blob(15, 15.6, 7.4, 7.2, pal["base"]))
    s.append(_blob(11.4, 10.4, 2.4, 1.8, pal["light"], .55))
    # 脸
    s.append(_eyes(10.8, 16.4, 12.6, mood, pal, star))
    if mood == "sad":
        s.append(_r(13, 17.6, 4, 1, pal["shade"]))
        s.append(_r(12.6, 18.4, 1, 0.8, pal["shade"]))
    elif mood == "sick":
        s.append(_r(13, 17.6, 4, 1, pal["shade"]))
    else:
        s.append(_r(12.6, 17, 5, 1, pal["accent"]))
        s.append(_r(13.4, 18, 3.2, 0.8, pal["accent"], .85))
    # 保险销
    s.append(_r(19.4, 8.2, 2.6, 0.8, pal["accent"]))
    # 小脚
    s.append(_blob(11.6, 24.4, 1.5, 1.2, pal["shade"]))
    s.append(_blob(18.4, 24.4, 1.5, 1.2, pal["shade"]))
    return "".join(s)


def _sp_bun(pal, mood, star):
    """小笼包：白胖十八褶，坐在竹笼里冒热气。"""
    s = []
    # 竹笼
    s.append(_r(8.2, 21.4, 13.6, 2.8, pal["shade"]))
    s.append(_r(8.2, 21.4, 13.6, 0.6, pal["light"], .7))
    s.append(_r(8.2, 21.4, 0.6, 2.8, pal["out"], .6))
    s.append(_r(21.2, 21.4, 0.6, 2.8, pal["out"], .6))
    # 蒸汽（浅蓝灰，浅色背景上也能看见）
    for (x, y) in ((8.4, 7.0), (20.6, 7.4), (12.4, 4.6)):
        s.append(_blob(x, y, 1.3, 1.1, "#CBDDE8", .85))
        s.append(_blob(x + 0.6, y - 1.4, 0.9, 0.7, "#CBDDE8", .7))
    # 包子身
    s.append(_blob(15, 16.4, 7.2, 6.0, pal["out"]))
    s.append(_blob(15, 16.4, 6.4, 5.2, pal["base"]))
    # 顶部收口（一个小揪）
    s.append(_blob(15, 10.6, 1.8, 1.6, pal["out"]))
    s.append(_blob(15, 10.6, 1.2, 1.0, pal["shade"]))
    # 褶子：从收口向下收的放射折痕，全部落在包子轮廓内
    for (x, y, w, h) in ((10.6, 13.2, 3.6, 0.7), (16.6, 13.2, 3.6, 0.7),
                         (11.4, 16.0, 3.4, 0.7), (16.4, 16.0, 3.2, 0.7),
                         (12.8, 18.6, 3.0, 0.7), (16.2, 18.6, 2.4, 0.7)):
        s.append(_r(x, y, w, h, pal["shade"], .5))
    s.append(_r(13.0, 12.0, 0.8, 1.6, pal["shade"], .65))
    s.append(_r(16.2, 12.0, 0.8, 1.6, pal["shade"], .65))
    # 脸
    s.append(_eyes(12.0, 17.6, 15.0, mood, pal, star))
    s.append(_mouth(15, 17.6, mood, pal))
    s.append(_cheeks(9.8, 19.2, 16.6, mood, pal))
    return "".join(s)


def _sp_icecream(pal, mood, star):
    """冰淇淋：奶油球堆在蛋筒上，顶一颗樱桃。"""
    s = []
    # 蛋筒（逐行收窄的倒三角）
    rows = [(18.4, 3.8), (19.4, 3.4), (20.4, 3.0), (21.4, 2.6),
            (22.4, 2.1), (23.4, 1.6)]
    for (y, w) in rows:
        s.append(_r(15 - w, y, w * 2, 1, pal["out"]))
    for (y, w) in rows:
        s.append(_r(15 - w + 1, y, w * 2 - 2, 1, pal["cone"]))
    # 蛋筒格纹
    for (x, y) in ((12.6, 19.6), (15.4, 20.6), (13.4, 21.6), (16.2, 22.6)):
        s.append(_r(x, y, 1.4, 0.4, pal["shade"], .75))
    # 奶油球：先画上层小球，再画下层大球压住接缝，避免深色描边横穿奶油面
    s.append(_blob(15, 9.4, 4.4, 3.2, pal["out"]))
    s.append(_blob(15, 9.4, 3.7, 2.5, pal["base"]))
    s.append(_blob(15, 14.0, 7.2, 5.2, pal["out"]))
    s.append(_blob(15, 14.0, 6.4, 4.4, pal["base"]))
    # 樱桃
    s.append(_r(14.9, 4.2, 0.6, 1.6, "#5C8A3A"))
    s.append(_blob(15, 6.0, 1.6, 1.4, "#E8455F"))
    s.append(_r(14.4, 5.6, 0.6, 0.6, "#FF9CAC"))
    # 彩糖针（都落在奶油球内部）
    for (x, y, c) in ((10.8, 11.6, "#FFD54A"), (19.0, 12.2, "#8FE3FF"),
                      (12.4, 16.4, "#9CFFB0"), (17.6, 16.6, "#FFD54A")):
        s.append(_r(x, y, 0.9, 0.5, c))
    # 脸
    s.append(_eyes(11.8, 17.2, 13.8, mood, pal, star))
    s.append(_mouth(15, 16.2, mood, pal))
    s.append(_cheeks(10.2, 19.8, 15.6, mood, pal))
    return "".join(s)


_PET_BODY = {
    "猫": _sp_cat,
    "狗": _sp_dog,
    "机器人": _sp_robot,
    "小羊": _sp_sheep,
    "小鸡": _sp_chick,
    "豹子": _sp_leopard,
    "兔子": _sp_rabbit,
    "仓鼠": _sp_hamster,
    "狐狸": _sp_fox,
    "企鹅": _sp_penguin,
    "青蛙": _sp_frog,
    "小熊": _sp_bear,
    "机械蜂": _sp_mech_bee,
    "小鹿": _sp_deer,
    "小龙": _sp_dragon,
    "史莱姆": _sp_slime,
    "布丁": _sp_pudding,
    "机械鼠": _sp_mech_mouse,
    "机甲兔": _sp_mech_rabbit,
    "小鸭": _sp_duck,
    "熊猫": _sp_panda,
    "小狼": _sp_wolf,
    "小马": _sp_pony,
    "独角兽": _sp_unicorn,
    "麒麟": _sp_qilin,
    "豆豆": _sp_bean,
    "蘑菇仔": _sp_mushroom,
    "甜甜圈": _sp_donut,
    "饭团": _sp_onigiri,
    "机甲龟": _sp_mech_turtle,
    "机械狮": _sp_mech_lion,
    "小刺猬": _sp_hedgehog,
    "小猪": _sp_pig,
    "小松鼠": _sp_squirrel,
    "凤凰": _sp_phoenix,
    "貔貅": _sp_pixiu,
    "方块仔": _sp_block,
    "炸弹仔": _sp_bomb,
    "小笼包": _sp_bun,
    "冰淇淋": _sp_icecream,
}

# 普通皮肤配色
_PET_SKIN = {
    "猫": {"out": "#7A4A22", "base": "#F3A85C", "shade": "#D98A3F",
           "light": "#FFD9A8", "belly": "#FFF1DC", "accent": "#FF8FA3", "eye": "#3A2E2A"},
    "狗": {"out": "#5E3A1C", "base": "#C98A52", "shade": "#A9682F",
           "light": "#EFC9A2", "belly": "#F7E3CC", "accent": "#F27C8D", "eye": "#3A2E2A"},
    "机器人": {"out": "#3D4655", "base": "#AEC4D8", "shade": "#8FA6BD",
              "light": "#E4F0FA", "belly": "#2DD4BF", "accent": "#F59E0B", "eye": "#124E4A"},
    "小羊": {"out": "#4A3F55", "base": "#FBF6EC", "shade": "#DDD3C2",
            "light": "#FFFFFF", "belly": "#4B4453", "accent": "#F9A8C9",
            "eye": "#2B2536", "eyebg": "#FFFFFF", "mouth": "#4B4453"},
    "小鸡": {"out": "#B07A1C", "base": "#FFD166", "shade": "#F2BC43",
            "light": "#FFF0B8", "belly": "#FFF6D6", "accent": "#F59E0B", "eye": "#3A2E2A"},
    "豹子": {"out": "#6B3F18", "base": "#F4BE55", "shade": "#DE9F35",
            "light": "#FBE7C2", "belly": "#FBE7C2", "accent": "#F9A8C9", "eye": "#3A2E2A"},
    "兔子": {"out": "#8C6F7C", "base": "#FFF6F0", "shade": "#E4D2D8",
            "light": "#FFFFFF", "belly": "#FFE6EE", "accent": "#FF9EBB", "eye": "#4A3038"},
    "仓鼠": {"out": "#8A6038", "base": "#F6C98A", "shade": "#DFA766",
            "light": "#FFE4BC", "belly": "#FFF6E8", "accent": "#FFB4C8", "eye": "#3A2E2A"},
    "狐狸": {"out": "#7C3A16", "base": "#F08A3C", "shade": "#CE6A22",
            "light": "#FFD9B0", "belly": "#FFF3E0", "accent": "#F28FA6", "eye": "#3A2E2A"},
    "企鹅": {"out": "#1A2438", "base": "#46608F", "shade": "#334C76",
            "light": "#BBD3EC", "belly": "#FFFFFF", "accent": "#F5A93B", "eye": "#10203A"},
    "青蛙": {"out": "#2F5B24", "base": "#8CCB5A", "shade": "#6BAA44",
            "light": "#E0F3B4", "belly": "#F4FBDC", "accent": "#E78CA8", "eye": "#1F3A16"},
    "小熊": {"out": "#4A3524", "base": "#C08A5A", "shade": "#9E6C3E",
            "light": "#EACBA2", "belly": "#F8E5CE", "accent": "#E89BAA", "eye": "#2E2116"},
    "机械蜂": {"out": "#3A3420", "base": "#FFC63D", "shade": "#E0A227",
              "light": "#FFF0B8", "belly": "#2C3446", "accent": "#6FE7F2",
              "eye": "#1B2233"},
    "小鹿": {"out": "#7A4A22", "base": "#E0A263", "shade": "#C4833F",
            "light": "#FFF1D9", "belly": "#FFF7E8", "accent": "#FFB4C4", "eye": "#3A2A20"},
    "小龙": {"out": "#2A5B47", "base": "#7FD9AE", "shade": "#5CBB90",
            "light": "#DCFFEC", "belly": "#FFF3C2", "accent": "#FFC93D", "eye": "#1F4237"},
    "史莱姆": {"out": "#2A6E8C", "base": "#84DCF4", "shade": "#59BDDC",
              "light": "#E2F8FF", "belly": "#C9F2FF", "accent": "#FF9ECB",
              "eye": "#183748", "eyebg": "#FFFFFF"},
    "布丁": {"out": "#8A5A20", "base": "#FFE38F", "shade": "#F5C95F",
            "light": "#FFF8DA", "belly": "#FFD575", "accent": "#E8455F",
            "eye": "#4A3218", "top": "#B4692B"},
    "机械鼠": {"out": "#3D4655", "base": "#B8C4D4", "shade": "#93A1B6",
              "light": "#E8F1FA", "belly": "#57C9E0", "accent": "#F59E0B",
              "eye": "#12414E"},
    "机甲兔": {"out": "#3A3F4C", "base": "#D8DEE8", "shade": "#B0B9C8",
              "light": "#F5F8FF", "belly": "#8FA6BD", "accent": "#F472B6",
              "eye": "#1B2A3A"},
    "小鸭": {"out": "#B07A1C", "base": "#FFDF5E", "shade": "#F2C33E",
            "light": "#FFF3B8", "belly": "#FFF7DA", "accent": "#F08A3C",
            "eye": "#3A2E2A"},
    "熊猫": {"out": "#2A2A32", "base": "#FFFFFF", "shade": "#E2E6EE",
            "light": "#FFFFFF", "belly": "#F6F8FC", "accent": "#FF9EC4",
            "eye": "#FFFFFF"},
    "小狼": {"out": "#4A5568", "base": "#A8B6C9", "shade": "#8A99AE",
            "light": "#E6EDF6", "belly": "#F5F8FC", "accent": "#FF9EBB",
            "eye": "#2B3444"},
    "小马": {"out": "#6B4326", "base": "#D89A5C", "shade": "#B57A3E",
            "light": "#F3D6B0", "belly": "#FFF1DC", "accent": "#EE8FA6",
            "eye": "#3A2A20"},
    "独角兽": {"out": "#6C5C8E", "base": "#FFFFFF", "shade": "#E8E1F5",
              "light": "#FFFFFF", "belly": "#F6F1FF", "accent": "#FFB0D6",
              "eye": "#3B2E55", "horn": "#FFD54A"},
    "麒麟": {"out": "#8A4A16", "base": "#FFC96B", "shade": "#EFA93C",
            "light": "#FFF0C4", "belly": "#FFF7DF", "accent": "#E8455F",
            "eye": "#40301A"},
    "豆豆": {"out": "#B07E10", "base": "#FFD84D", "shade": "#F0BC2E",
            "light": "#FFF3A8", "belly": "#FFF8D2", "accent": "#FF8FA3",
            "eye": "#3A2E12"},
    "蘑菇仔": {"out": "#8A3A22", "base": "#FFF6EC", "shade": "#EAD9C6",
              "light": "#FFFFFF", "belly": "#FFF9F0", "accent": "#FF9EBB",
              "eye": "#4A2A20", "cap": "#E86A5C"},
    "甜甜圈": {"out": "#8A5A20", "base": "#FFDF9E", "shade": "#F0C471",
              "light": "#FFF6DC", "belly": "#FFF3D2", "accent": "#FF7FA8",
              "eye": "#5A3A18", "icing": "#FF9FC0"},
    "饭团": {"out": "#4A4A44", "base": "#FFFFFF", "shade": "#E4E6E2",
            "light": "#FFFFFF", "belly": "#F7F8F4", "accent": "#FF9EB8",
            "eye": "#2E2E2A", "nori": "#2C4A34"},
    "机甲龟": {"out": "#2F5A56", "base": "#9FE3D2", "shade": "#6FC3B0",
              "light": "#E4FFF8", "belly": "#3A7A72", "accent": "#FFB03A",
              "eye": "#10403A"},
    "机械狮": {"out": "#4A3A1E", "base": "#E8C26A", "shade": "#C79B3E",
              "light": "#FFF0C2", "belly": "#6B7E92", "accent": "#FF6B4A",
              "eye": "#3A2A12"},
    "小刺猬": {"out": "#5A4432", "base": "#C89A6A", "shade": "#A97B4C",
              "light": "#F3DCC2", "belly": "#FFF3E4", "accent": "#F08CA0",
              "eye": "#3A2A1E"},
    "小猪": {"out": "#B26A7A", "base": "#FFC2CE", "shade": "#F2A2B4",
            "light": "#FFE6EC", "belly": "#FFF2F5", "accent": "#E8577A",
            "eye": "#5A2A38"},
    "小松鼠": {"out": "#7A4A22", "base": "#E8A45C", "shade": "#C57F38",
              "light": "#FFE2BC", "belly": "#FFF4E2", "accent": "#FF9EBB",
              "eye": "#3A2A1C"},
    "凤凰": {"out": "#8A2A16", "base": "#FF8A4A", "shade": "#E8632E",
            "light": "#FFD8A8", "belly": "#FFE2B0", "accent": "#FFD54A",
            "eye": "#5A1A0E"},
    "貔貅": {"out": "#7A4A10", "base": "#FFC94A", "shade": "#E0A22A",
            "light": "#FFF0B8", "belly": "#FFF6D8", "accent": "#E8455F",
            "eye": "#4A3208"},
    "方块仔": {"out": "#3A2A5A", "base": "#8FC6FF", "shade": "#6AA6E8",
              "light": "#DCF0FF", "belly": "#C7E4FF", "accent": "#FF7AA8",
              "eye": "#1E2A4A"},
    "炸弹仔": {"out": "#12121A", "base": "#3C4256", "shade": "#2A2E3C",
              "light": "#7C86A0", "belly": "#2A2E3C", "accent": "#FF7A45",
              "eye": "#FFE066"},
    "小笼包": {"out": "#8A7A6A", "base": "#FFFDF8", "shade": "#EDE2D4",
              "light": "#FFFFFF", "belly": "#FFF8EE", "accent": "#FF9EB8",
              "eye": "#5A4A3A"},
    "冰淇淋": {"out": "#8A5A2A", "base": "#FFE7F2", "shade": "#F5C4DC",
              "light": "#FFFFFF", "belly": "#FFF6FA", "accent": "#FF7AA8",
              "eye": "#5A3A48", "cone": "#E8B36A"},
}

# 星辉皮肤配色：深空紫底 + 金色星纹，每只宠物一个专属高光色
_STAR_SKIN = {
    "猫": {"out": "#140F26", "base": "#A99CFF", "shade": "#7F6BE8",
           "light": "#DCD6FF", "belly": "#FFF0C2", "accent": "#FF8FD0", "eye": "#FFD54A"},
    "狗": {"out": "#140F26", "base": "#9686FF", "shade": "#6E5AE0",
           "light": "#D3CCFF", "belly": "#FFF0C2", "accent": "#FFB86B", "eye": "#FFD54A"},
    "机器人": {"out": "#0B1226", "base": "#5AC8FA", "shade": "#2E9BD6",
              "light": "#C4F0FF", "belly": "#7CFFE4", "accent": "#FFE066", "eye": "#FFE066"},
    "小羊": {"out": "#241B42", "base": "#F2ECFF", "shade": "#C9BAF5",
            "light": "#FFFFFF", "belly": "#4E3F86", "accent": "#FF8FD0",
            "eye": "#FFD54A", "eyebg": "#FFFFFF", "mouth": "#5A4790"},
    "小鸡": {"out": "#2A1D08", "base": "#FFE066", "shade": "#F5C33B",
            "light": "#FFF6C0", "belly": "#FFF1A8", "accent": "#FF9E4A", "eye": "#8A5A08"},
    "豹子": {"out": "#180E28", "base": "#C9AEFF", "shade": "#9C79E8",
            "light": "#F0E8FF", "belly": "#FFF0C2", "accent": "#FFA14A", "eye": "#FFD54A"},
    "兔子": {"out": "#16202E", "base": "#D8F5FF", "shade": "#A7D8EE",
            "light": "#FFFFFF", "belly": "#A7F3D0", "accent": "#7CE7C4", "eye": "#FFD54A"},
    "仓鼠": {"out": "#140F26", "base": "#B7A6FF", "shade": "#8E77E8",
            "light": "#E4DCFF", "belly": "#FFEFC6", "accent": "#FF9ECB", "eye": "#FFD54A"},
    "狐狸": {"out": "#180E28", "base": "#A489FF", "shade": "#7C63E0",
            "light": "#D9D0FF", "belly": "#FFF0C2", "accent": "#FFB05A", "eye": "#FFD54A"},
    "企鹅": {"out": "#0A1428", "base": "#6FA0E8", "shade": "#4778C4",
            "light": "#CFE4FF", "belly": "#FFF6DA", "accent": "#FFD24A", "eye": "#FFF0A0"},
    "青蛙": {"out": "#0E2216", "base": "#9CFFB0", "shade": "#6AD88A",
            "light": "#D8FFE0", "belly": "#FFF7C2", "accent": "#FF9ECB", "eye": "#FFE66A"},
    "小熊": {"out": "#160F22", "base": "#C9A6FF", "shade": "#9E7EE0",
            "light": "#EADFFF", "belly": "#FFF0C2", "accent": "#FFB07A", "eye": "#FFD54A"},
    "机械蜂": {"out": "#0A1220", "base": "#FFE066", "shade": "#F0BE3A",
              "light": "#FFF8CE", "belly": "#3A5AA8", "accent": "#7CFFE4",
              "eye": "#FFE066"},
    "小鹿": {"out": "#241A2E", "base": "#FFD9A8", "shade": "#E5B87A",
            "light": "#FFFBF0", "belly": "#FFF6E2", "accent": "#9FD8FF", "eye": "#FFD54A"},
    "小龙": {"out": "#0B2A22", "base": "#A8FFD2", "shade": "#6FE0AC",
            "light": "#E9FFF4", "belly": "#FFF3B0", "accent": "#FFE066", "eye": "#FFF0A0"},
    "史莱姆": {"out": "#0A2438", "base": "#BFF3FF", "shade": "#8ADCF5",
              "light": "#FFFFFF", "belly": "#E4FBFF", "accent": "#FFB0D6",
              "eye": "#FFD54A", "eyebg": "#FFFFFF"},
    "布丁": {"out": "#2A1A38", "base": "#FFF0B8", "shade": "#F5D98A",
            "light": "#FFFFF0", "belly": "#FFE7A0", "accent": "#FF5C7A",
            "eye": "#FFD54A", "top": "#FFC94D"},
    "机械鼠": {"out": "#0B1226", "base": "#8FD8FF", "shade": "#5FB2E6",
              "light": "#DCF3FF", "belly": "#7CFFE4", "accent": "#FFE066",
              "eye": "#FFE066"},
    "机甲兔": {"out": "#101A2E", "base": "#D9C6FF", "shade": "#B49BE8",
              "light": "#F2EAFF", "belly": "#9CF0FF", "accent": "#FFD54A",
              "eye": "#FFE066"},
    "小鸭": {"out": "#2A1D08", "base": "#FFE97A", "shade": "#F5C93B",
            "light": "#FFF8C8", "belly": "#FFF2A8", "accent": "#FF9E4A",
            "eye": "#8A5A08"},
    "熊猫": {"out": "#150F24", "base": "#F4EDFF", "shade": "#CFC0F0",
            "light": "#FFFFFF", "belly": "#FFF0C2", "accent": "#FF8FD0",
            "eye": "#FFD54A"},
    "小狼": {"out": "#0E1626", "base": "#B9CBFF", "shade": "#8FA6E8",
            "light": "#E6EEFF", "belly": "#FFF6DA", "accent": "#FFB86B",
            "eye": "#FFD54A"},
    "小马": {"out": "#241305", "base": "#FFD9A8", "shade": "#E0B072",
            "light": "#FFFBF0", "belly": "#FFF6E2", "accent": "#9FD8FF",
            "eye": "#FFD54A"},
    "独角兽": {"out": "#120E2A", "base": "#F4EEFF", "shade": "#CBB8F0",
              "light": "#FFFFFF", "belly": "#FFF0C2", "accent": "#FF8FD0",
              "eye": "#FFD54A", "horn": "#FFE9A0"},
    "麒麟": {"out": "#180E14", "base": "#FFD98A", "shade": "#EFBA4A",
            "light": "#FFF6C8", "belly": "#FFF0C2", "accent": "#FF6E86",
            "eye": "#FFD54A"},
    "豆豆": {"out": "#1A1204", "base": "#FFF07A", "shade": "#F5D84A",
            "light": "#FFFBC8", "belly": "#FFFBD2", "accent": "#FF9ECB",
            "eye": "#FFE066"},
    "蘑菇仔": {"out": "#1A0E14", "base": "#FFF3EA", "shade": "#E2CBD6",
              "light": "#FFFFFF", "belly": "#FFF7F2", "accent": "#FF9ECB",
              "eye": "#FFD54A", "cap": "#FF8FD0"},
    "甜甜圈": {"out": "#1E1224", "base": "#FFE7BC", "shade": "#EFC98A",
              "light": "#FFFFF0", "belly": "#FFF3D2", "accent": "#FF7FA8",
              "eye": "#FFD54A", "icing": "#C3A6FF"},
    "饭团": {"out": "#12141A", "base": "#FFFFFF", "shade": "#DDE3EC",
            "light": "#FFFFFF", "belly": "#F7F9FC", "accent": "#FF9ECB",
            "eye": "#FFD54A", "nori": "#24402E"},
    "机甲龟": {"out": "#0A1E24", "base": "#8FF5E4", "shade": "#5FD0BE",
              "light": "#E0FFF8", "belly": "#2E6A6A", "accent": "#FFE066",
              "eye": "#FFE66A"},
    "机械狮": {"out": "#180F16", "base": "#FFD98A", "shade": "#EFBA4A",
              "light": "#FFF6C8", "belly": "#5A6A94", "accent": "#FF8A6B",
              "eye": "#FFD54A"},
    "小刺猬": {"out": "#1A1410", "base": "#E8C69A", "shade": "#C4A074",
              "light": "#FFF2E0", "belly": "#FFF6EC", "accent": "#FF9ECB",
              "eye": "#FFD54A"},
    "小猪": {"out": "#241018", "base": "#FFD4E0", "shade": "#F5AEC2",
            "light": "#FFF2F7", "belly": "#FFF4F8", "accent": "#FF6E96",
            "eye": "#FFD54A"},
    "小松鼠": {"out": "#1C1006", "base": "#FFC98A", "shade": "#E0A05C",
              "light": "#FFF0D4", "belly": "#FFF8EC", "accent": "#FFB0D6",
              "eye": "#FFD54A"},
    "凤凰": {"out": "#200A06", "base": "#FFB07A", "shade": "#EF8552",
            "light": "#FFE0BC", "belly": "#FFEFC0", "accent": "#FFE066",
            "eye": "#FFF0A0"},
    "貔貅": {"out": "#1A120A", "base": "#FFDD8A", "shade": "#EFC04A",
            "light": "#FFF8CE", "belly": "#FFF6DC", "accent": "#FF6E86",
            "eye": "#FFD54A"},
    "方块仔": {"out": "#100C22", "base": "#AFDCFF", "shade": "#7CBCF0",
              "light": "#E8F6FF", "belly": "#D4ECFF", "accent": "#FF9ECB",
              "eye": "#FFD54A"},
    "炸弹仔": {"out": "#04040A", "base": "#6A7490", "shade": "#4C5570",
              "light": "#AEB8D2", "belly": "#4C5570", "accent": "#FFA46B",
              "eye": "#FFE066"},
    "小笼包": {"out": "#16120E", "base": "#FFFFFF", "shade": "#E8E0D8",
              "light": "#FFFFFF", "belly": "#FFFAF4", "accent": "#FF9ECB",
              "eye": "#FFD54A"},
    "冰淇淋": {"out": "#1A1014", "base": "#FFF0F8", "shade": "#F5CBDD",
              "light": "#FFFFFF", "belly": "#FFF8FC", "accent": "#FF8FD0",
              "eye": "#FFD54A", "cone": "#FFD9A0"},
}

_PET_BG = {
    "猫": ("#FFF3E2", "#FFE2C4"),
    "狗": ("#FFF4E8", "#F8DCC6"),
    "机器人": ("#EAF3FC", "#D3E6F7"),
    "小羊": ("#F9F6FF", "#E8E2F8"),
    "小鸡": ("#FFFBE4", "#FFEFB4"),
    "豹子": ("#FFF8E4", "#FFE7BB"),
    "兔子": ("#FDF6FA", "#F5E4EE"),
    "仓鼠": ("#FFF7EA", "#FFEBCE"),
    "狐狸": ("#FFF4E6", "#FFE2C6"),
    "企鹅": ("#F0F7FE", "#D8E8F8"),
    "青蛙": ("#F4FCE4", "#DDF2C2"),
    "小熊": ("#FFF5E6", "#FFE5C6"),
    "机械蜂": ("#F4F9FF", "#DCE9F7"),
    "小鹿": ("#FFF7EC", "#F7E2C8"),
    "小龙": ("#EFFCF4", "#D2F0E0"),
    "史莱姆": ("#EFFAFF", "#D3F0FD"),
    "布丁": ("#FFFAE8", "#FFEDC2"),
    "机械鼠": ("#EFF4FA", "#D7E4F0"),
    "机甲兔": ("#F4F1FD", "#E0D9F4"),
    "小鸭": ("#FFFCE8", "#FFF1BE"),
    "熊猫": ("#F7F8FB", "#E4E7EE"),
    "小狼": ("#F2F6FB", "#DCE4EF"),
    "小马": ("#FFF6EC", "#F6E0C6"),
    "独角兽": ("#FFF5FA", "#FBE3F1"),
    "麒麟": ("#FFF7E6", "#FFE9BE"),
    "豆豆": ("#FFFDEC", "#FFF3BE"),
    "蘑菇仔": ("#FFF7F2", "#FDE6DC"),
    "甜甜圈": ("#FFF6F3", "#FFE6EB"),
    "饭团": ("#F8FAF7", "#E5EDE6"),
    "机甲龟": ("#EFFAF7", "#D6EFE6"),
    "机械狮": ("#FFF6E4", "#F7E3BC"),
    "小刺猬": ("#FFF6EC", "#F6E3CE"),
    "小猪": ("#FFF5F8", "#FBE0E9"),
    "小松鼠": ("#FFF7EA", "#F8E1C6"),
    "凤凰": ("#FFF3E8", "#FFDCC6"),
    "貔貅": ("#FFF9E8", "#FFECC0"),
    "方块仔": ("#EEF6FF", "#D6E8FB"),
    "炸弹仔": ("#EDEEF4", "#D6D9E4"),
    "小笼包": ("#FDFAF4", "#EFE7DA"),
    "冰淇淋": ("#FFF6FA", "#FDE0EC"),
}

_STAR_BG = ("#2A2154", "#3A2D6C")


def _to_hue(hex_color, hue_deg, sat=1.0):
    """把颜色统一拉到主题色相（保留明暗与饱和度比例），让同类皮肤配色成套。"""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    _, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    ss = max(0.0, min(1.0, ss * sat))
    r2, g2, b2 = colorsys.hsv_to_rgb(hue_deg / 360.0, ss, vv)
    return "#%02X%02X%02X" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))


def _theme_pal(pal, theme):
    th = SKIN_THEMES.get(theme or "")
    if not th:
        return pal
    out = dict(pal)
    for key in ("base", "shade", "light", "accent", "belly"):
        if key in out:
            out[key] = _to_hue(out[key], th["hue"], th["sat"])
    return out


def _pet_group(species, mood="happy", star=False, skin=""):
    """返回 240×240 坐标系里的宠物本体（立绘与房间共用）。"""
    sp = species if species in PET_SPECIES else "猫"
    if mood not in ("happy", "sad", "sick"):
        mood = "happy"
    pal = dict(_STAR_SKIN[sp] if star else _PET_SKIN[sp])
    pal = _theme_pal(pal, skin)
    s = [_PET_BODY[sp](pal, mood, star)]
    head_top = {"机器人": 6, "小鸡": 6, "小羊": 8, "兔子": 1,
                "狗": 7, "猫": 4, "豹子": 4,
                "仓鼠": 6, "狐狸": 3, "企鹅": 9, "青蛙": 8, "小熊": 6,
                "机械蜂": 5, "小鹿": 4, "小龙": 7, "史莱姆": 10, "布丁": 9,
                "机械鼠": 6, "机甲兔": 6, "小鸭": 6, "熊猫": 6, "小狼": 6,
                "小马": 7, "独角兽": 9, "麒麟": 9, "豆豆": 6, "蘑菇仔": 6,
                "甜甜圈": 6, "饭团": 9,
                "机甲龟": 7, "机械狮": 5, "小刺猬": 9, "小猪": 7, "小松鼠": 7,
                "凤凰": 6, "貔貅": 7, "方块仔": 11, "炸弹仔": 6,
                "小笼包": 9, "冰淇淋": 5}.get(sp, 4)
    if star:
        # 胸口金色星纹，和普通皮肤拉开差别
        s.append(_r(15, 21, 1, 3, "#FFD54A"))
        s.append(_r(14, 22, 3, 1, "#FFD54A"))
        s.append(_r(15, 20, 1, 1, "#FFF3B0"))
        s.append(_star_deco(pal, head_top))
    s.append(_mood_prop(mood, pal))
    return "".join(s)


def _frame(size=240, star=False):
    """像素风外框：四角缺格，做出 8-bit 边框感。"""
    edge = "#120E28" if star else "#3B2A1B"
    parts = []
    step = 16
    for i in range(8, size - 8, step):
        parts.append(f'<rect x="{i}" y="0" width="{step}" height="8" fill="{edge}"/>')
        parts.append(f'<rect x="{i}" y="{size - 8}" width="{step}" height="8" fill="{edge}"/>')
        parts.append(f'<rect x="0" y="{i}" width="8" height="{step}" fill="{edge}"/>')
        parts.append(f'<rect x="{size - 8}" y="{i}" width="8" height="{step}" fill="{edge}"/>')
    return "".join(parts)


def pet_svg(species, mood="happy", star=False, skin=""):
    sp = species if species in PET_SPECIES else "猫"
    if mood not in ("happy", "sad", "sick"):
        mood = "happy"
    th = SKIN_THEMES.get(skin or "")
    bg1, bg2 = th["bg"] if th else (_STAR_BG if star else _PET_BG[sp])
    parts = [
        f'<rect x="8" y="8" width="224" height="224" fill="{bg1}"/>',
        f'<rect x="8" y="152" width="224" height="80" fill="{bg2}"/>',
        '<g opacity=".35">',
    ]
    for gy in range(2, 14):
        for gx in range(2, 28, 3):
            if (gx + gy) % 3 == 0:
                parts.append(_r(gx, gy, 1, 1, bg2))
    parts.append("</g>")
    if star:
        for (x, y) in ((4, 3), (23, 4), (5, 25), (25, 22), (14, 2), (26, 12)):
            parts.append(_r(x, y, 1, 1, "#FFE066", .9))
    parts.append(_blob(15, 26, 8, 1.2, "#000000" if star else "#B98A5E", .18))
    if th:
        parts.append(f'<circle cx="120" cy="126" r="82" fill="{th["glow"]}" opacity=".20"/>')
        parts.append(_pet_group(sp, mood, star, skin))
        # 佩戴标记：主题色肩带，证明皮肤已穿上
        parts.append(_r(9, 26, 2, 1, th["glow"]))
        parts.append(_r(9, 27, 1, 1, th["glow"]))
    else:
        parts.append(_pet_group(sp, mood, star))
    parts.append(_frame(240, star))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" '
            'width="240" height="240" shape-rendering="crispEdges">'
            + "".join(parts) + "</svg>")


def pet_mood(pet):
    if pet.get("health", 150) < 30:
        return "sick"
    if min(pet.get("hn", 150), pet.get("ha", 150), pet.get("cl", 150)) < 35:
        return "sad"
    return "happy"


def star_art(pet):
    """是否用星辉立绘：真星辉形态，或旧版「星光皮肤券」换的外观。"""
    return bool(pet.get("is_star", False)) or pet.get("skin") == "star"


def skin_theme(pet):
    """当前穿着的主题皮肤，没穿返回空字符串。"""
    s = pet.get("skin")
    return s if s in SKIN_THEMES else ""


def pet_art(pet):
    return pet_svg(species_of(pet), pet_mood(pet), star_art(pet), skin_theme(pet))


# ===================== 存档工具 =====================


def _save_candidates():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")
    return [
        os.path.join(script_dir, "player_pet.txt"),
        os.path.join(home, "Documents", "宠物游戏", "player_pet.txt"),
        os.path.join(home, "player_pet.txt"),
    ]


def _can_write(path):
    folder = os.path.dirname(path) or "."
    try:
        os.makedirs(folder, exist_ok=True)
        probe = os.path.join(folder, ".save_write_probe.tmp")
        with open(probe, "w", encoding="utf-8") as fp:
            fp.write("ok")
        os.remove(probe)
    except OSError:
        return False
    if os.path.exists(path):
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except OSError:
            return False
    return True


def _pick_save_path():
    for p in _save_candidates():
        if _can_write(p):
            return p
    return _save_candidates()[0]


def _next_writable(current):
    for p in _save_candidates():
        if os.path.abspath(p) != os.path.abspath(current) and _can_write(p):
            return p
    return None


SAVE_PATH = _pick_save_path()


# ===================== 游戏逻辑工具 =====================


def add_log(msg, log_list, max_len=12):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_list.append(f"[{t}] {msg}")
    if len(log_list) > max_len:
        log_list.pop(0)
    return log_list


def check_levelup(pet, game_log):
    need_exp = pet["lv"] * 50
    msgs = []
    while pet["exp"] >= need_exp:
        pet["exp"] -= need_exp
        pet["lv"] += 1
        pet["hn"] += 20
        pet["ha"] += 20
        pet["hn"] = max(0.0, min(pet["hn"], 150.0))
        pet["ha"] = max(0.0, min(pet["ha"], 150.0))
        msgs.append(f"升级啦！【{pet['name']}】升到 Lv.{pet['lv']}！开心 +20，饱腹 +20")
        add_log(f"{pet['name']}升级到Lv.{pet['lv']}", game_log)
        need_exp = pet["lv"] * 50
    return msgs


def fix_petlist_is_star(pet_list):
    for p in pet_list:
        normalize_pet(p)
    return pet_list


def _serialize_star_cd(cd):
    out = {}
    for k, v in cd.items():
        if k == "goodluck_stack":
            out[k] = v
        elif isinstance(v, datetime):
            out[k] = v.timestamp()
        else:
            out[k] = v
    return out


def save_game(state):
    global SAVE_PATH
    content = (
        f"df = {state['df']}\n"
        f"storehouse = {state['storehouse']}\n"
        f"pet_list = {state['pet_list']}\n"
        f"current_pet_idx = {state['current_pet_idx']}\n"
        f"last_get_df_date = {state['last_get_date'].strftime('%Y-%m-%d')}\n"
        f"last_play_time = {state['last_play_time']}\n"
        f"last_bath_time = {state['last_bath_time']}\n"
        f"last_auto_hour_time = {state['last_auto_hour_time']}\n"
        f"task_finished = {state['task_finished']}\n"
        f"task_day = {state['task_day'].strftime('%Y-%m-%d')}\n"
        f"task_feed_flag = {state['task_feed_flag']}\n"
        f"unlock_ach = {state['unlock_ach']}\n"
        f"total_task = {state['total_task']}\n"
        f"total_feed = {state['total_feed']}\n"
        f"big_win_flag = {state['big_win_flag']}\n"
        f"first_pet_flag = {state['first_pet_flag']}\n"
        f"rand_event_switch = {state['rand_event_switch']}\n"
        f"last_rand_event_time = {state.get('last_rand_event_time', datetime.now())}\n"
        f"today_event_log = {state['today_event_log']}\n"
        f"game_log = {state['game_log']}\n"
        f"auto_save_switch = {state['auto_save_switch']}\n"
        f"last_switch_pet_time = {state['last_switch_pet_time']}\n"
        f"last_explore_time = {state['last_explore_time']}\n"
        f"total_explore = {state['total_explore']}\n"
        f"explore_rare_once_flag = {state['explore_rare_once_flag']}\n"
        f"star_skill_cd = {_serialize_star_cd(state['star_skill_cd'])}\n"
        f"total_star_explore = {state['total_star_explore']}\n"
        f"total_star_skill_use = {state['total_star_skill_use']}\n"
        f"sign_streak = {state.get('sign_streak', 1)}\n"
        f"total_lottery = {state.get('total_lottery', 0)}\n"
        f"lottery_history = {state.get('lottery_history', [])}\n"
        f"week_key = {state.get('week_key', '')}\n"
        f"week_base = {state.get('week_base', {})}\n"
        f"week_done = {state.get('week_done', [])}\n"
        f"bad_streak = {state.get('bad_streak', 0)}\n"
        f"last_season = {state.get('last_season', '')}\n"
        f"dex = {state.get('dex', [])}\n"
        f"dex_claimed = {state.get('dex_claimed', [])}\n"
    )
    for _try in range(3):
        try:
            with open(SAVE_PATH, mode="w", encoding="utf-8") as f:
                f.write(content)
            return True, f"存档已保存到 {SAVE_PATH}"
        except OSError:
            SAVE_PATH = _next_writable(SAVE_PATH)
            if not SAVE_PATH:
                return False, "没有可写的存档位置，本次进度未保存！"
    return False, "保存失败"


def parse_dt(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def load_game():
    if not os.path.exists(SAVE_PATH):
        return None
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        line = line.strip()
        if not line or " = " not in line:
            continue
        k, v = line.split(" = ", 1)
        data[k] = v
    st = {}
    st["df"] = int(data["df"])
    st["storehouse"] = eval(data["storehouse"])
    st["pet_list"] = eval(data["pet_list"])
    st["pet_list"] = fix_petlist_is_star(st["pet_list"])
    st["current_pet_idx"] = int(data["current_pet_idx"])
    st["last_get_date"] = datetime.strptime(
        data["last_get_df_date"], "%Y-%m-%d").date()
    st["last_play_time"] = parse_dt(data["last_play_time"])
    st["last_bath_time"] = parse_dt(data["last_bath_time"])
    st["last_auto_hour_time"] = parse_dt(data["last_auto_hour_time"])
    st["task_finished"] = eval(data["task_finished"])
    st["task_day"] = datetime.strptime(data["task_day"], "%Y-%m-%d").date()
    st["task_feed_flag"] = int(data["task_feed_flag"])
    st["unlock_ach"] = eval(data["unlock_ach"])
    st["total_task"] = int(data["total_task"])
    st["total_feed"] = int(data["total_feed"])
    st["big_win_flag"] = int(data["big_win_flag"])
    st["first_pet_flag"] = int(data["first_pet_flag"])
    st["rand_event_switch"] = int(data["rand_event_switch"])
    if "last_rand_event_time" in data:
        st["last_rand_event_time"] = parse_dt(data["last_rand_event_time"])
    else:
        st["last_rand_event_time"] = datetime.now()
    st["today_event_log"] = eval(data["today_event_log"])
    st["game_log"] = eval(data["game_log"])
    st["auto_save_switch"] = int(data["auto_save_switch"])
    st["last_switch_pet_time"] = parse_dt(data["last_switch_pet_time"])

    if "last_explore_time" in data:
        st["last_explore_time"] = parse_dt(data["last_explore_time"])
    else:
        st["last_explore_time"] = datetime.now() - EXPLORE_BASE_COOLDOWN
    if "total_explore" in data:
        st["total_explore"] = int(data["total_explore"])
    else:
        st["total_explore"] = 0
    if "explore_rare_once_flag" in data:
        st["explore_rare_once_flag"] = int(data["explore_rare_once_flag"])
    else:
        st["explore_rare_once_flag"] = 0

    if "star_skill_cd" in data:
        raw_cd = eval(data["star_skill_cd"])
        scd = {}
        for k, ts in raw_cd.items():
            if k == "goodluck_stack":
                scd[k] = int(ts)
            else:
                scd[k] = datetime.fromtimestamp(float(ts))
        st["star_skill_cd"] = scd
    else:
        st["star_skill_cd"] = {
            "star_mu": datetime.now() - timedelta(minutes=40),
            "star_heal": datetime.now() - timedelta(minutes=60),
            "star_full": datetime.now() - timedelta(minutes=50),
            "star_goodluck": datetime.now() - timedelta(minutes=120),
            "goodluck_stack": 0
        }
    if "total_star_explore" in data:
        st["total_star_explore"] = int(data["total_star_explore"])
    else:
        st["total_star_explore"] = 0
    if "total_star_skill_use" in data:
        st["total_star_skill_use"] = int(data["total_star_skill_use"])
    else:
        st["total_star_skill_use"] = 0
    # ---- 新增字段（老存档缺失时给默认值，保证能平滑升级）----
    st["sign_streak"] = int(data["sign_streak"]) if "sign_streak" in data else 1
    st["total_lottery"] = int(data["total_lottery"]) if "total_lottery" in data else 0
    if "lottery_history" in data:
        st["lottery_history"] = eval(data["lottery_history"])
    else:
        st["lottery_history"] = []
    st["week_key"] = data["week_key"].strip() if "week_key" in data else ""
    if "week_base" in data:
        st["week_base"] = eval(data["week_base"])
    else:
        st["week_base"] = {}
    if "week_done" in data:
        st["week_done"] = eval(data["week_done"])
    else:
        st["week_done"] = []
    st["bad_streak"] = int(data["bad_streak"]) if "bad_streak" in data else 0
    st["last_season"] = data["last_season"].strip() if "last_season" in data else ""
    st["dex"] = eval(data["dex"]) if "dex" in data else []
    st["dex_claimed"] = eval(data["dex_claimed"]) if "dex_claimed" in data else []
    return st


def new_game(pet_name):
    today = date.today()
    state = {}
    state["pet_list"] = [{
        "name": pet_name, "species": pet_name, "lv": 1, "hn": 100.0, "ha": 100.0,
        "cl": 100.0, "health": 150.0, "exp": 0.0, "is_star": False
    }]
    state["current_pet_idx"] = 0
    state["df"] = 100
    state["storehouse"] = []
    state["last_get_date"] = today
    state["last_bath_time"] = datetime.now() - timedelta(hours=2)
    state["last_auto_hour_time"] = datetime.now()
    state["last_play_time"] = datetime.now() - timedelta(hours=2)
    state["last_switch_pet_time"] = datetime.now() - timedelta(minutes=3)
    state["last_explore_time"] = datetime.now() - EXPLORE_BASE_COOLDOWN
    state["total_explore"] = 0
    state["explore_rare_once_flag"] = 0
    state["star_skill_cd"] = {
        "star_mu": datetime.now() - timedelta(minutes=40),
        "star_heal": datetime.now() - timedelta(minutes=60),
        "star_full": datetime.now() - timedelta(minutes=50),
        "star_goodluck": datetime.now() - timedelta(minutes=120),
        "goodluck_stack": 0
    }
    state["total_star_explore"] = 0
    state["total_star_skill_use"] = 0
    state["task_finished"] = []
    state["task_day"] = today
    state["task_feed_flag"] = 0
    state["unlock_ach"] = []
    state["total_task"] = 0
    state["total_feed"] = 0
    state["big_win_flag"] = 0
    state["first_pet_flag"] = 1
    state["rand_event_switch"] = 1
    state["last_rand_event_time"] = datetime.now() - RAND_EVENT_INTERVAL
    state["today_event_log"] = []
    state["game_log"] = []
    state["auto_save_switch"] = 1
    state["sign_streak"] = 1
    state["total_lottery"] = 0
    state["lottery_history"] = []
    state["week_key"] = ""
    state["week_base"] = {}
    state["week_done"] = []
    state["bad_streak"] = 0
    state["last_season"] = ""
    state["dex"] = []
    state["dex_claimed"] = []
    return state


# ===================== 页面样式与 HTML 组件 =====================

# ===================== 场景与界面组件 =====================


RQ = 20                       # 房间：一个像素格 = 20 单位，画布 60×31 格 = 1200×620


def _qr(x, y, w, h, c, o=None):
    """房间像素矩形（按 20 单位一格）。"""
    op = "" if o is None else f' opacity="{o}"'
    return (f'<rect x="{int(round(x * RQ))}" y="{int(round(y * RQ))}" '
            f'width="{int(round(w * RQ))}" height="{int(round(h * RQ))}" '
            f'fill="{c}"{op}/>')


def _rz(cx, cy, rx, ry, c, o=None):
    """房间像素椭圆（横条切片）。"""
    out = []
    ry_i = max(1, int(round(ry)))
    for gy in range(-ry_i, ry_i + 1):
        k = 1 - (gy / (ry_i + 0.4)) ** 2
        if k <= 0:
            continue
        w = int(round(rx * (k ** 0.5)))
        if w <= 0:
            continue
        out.append(_qr(cx - w, cy + gy, w * 2, 1, c, o))
    return "".join(out)


def room_svg(species, mood="happy", star=False, skin=""):
    """像素风小屋场景：普通白天房间 / 星辉夜晚房间 / 主题皮肤房间。"""
    sp = species if species in PET_SPECIES else "猫"
    if mood not in ("happy", "sad", "sick"):
        mood = "happy"
    th = SKIN_THEMES.get(skin or "")
    rm = th["room"] if th else None
    if rm:
        wall, wall2, skirt = rm["wall"], rm["wall2"], rm["skirt"]
        floor, floor2 = rm["floor"], rm["floor2"]
        sky, cloud = rm["sky"], rm["cloud"]
        wood, wood_d, frame = rm["wood2"], rm["wood"], rm["frame"]
        night = bool(rm["night"]) or star
    elif star:
        wall, wall2, skirt = "#241C44", "#2E2456", "#3F3470"
        floor, floor2 = "#1B1540", "#241B4E"
        sky, cloud = "#101838", "#3A4A86"
        wood, wood_d, frame = "#7A6142", "#5E4A32", "#3A2A20"
        night = True
    else:
        wall, wall2, skirt = "#F7E9CC", "#EFDFBE", "#C79A63"
        floor, floor2 = "#D3A26C", "#C08A57"
        sky, cloud = "#BFE8FA", "#FFFDF2"
        wood, wood_d, frame = "#C08A57", "#A9744A", "#6B4423"
        night = False

    p = [_qr(0, 0, 60, 19, wall)]
    for x in range(0, 60, 4):
        p.append(_qr(x, 0, 1, 19, wall2, .6))
    p.append(_qr(0, 19, 60, 2, skirt))
    p.append(_qr(0, 21, 60, 10, floor))
    for y in range(22, 31, 2):
        p.append(_qr(0, y, 60, 1, floor2, .75))
    for i, x in enumerate(range(2, 60, 8)):
        p.append(_qr(x, 22 + (i % 2) * 2, 1, 2, floor2, .55))

    # ---------- 窗户 ----------
    p.append(_qr(5, 2, 14, 12, frame))
    p.append(_qr(6, 3, 12, 10, sky))
    if night:
        for (x, y) in ((7, 4), (10, 6), (14, 4), (16, 9), (9, 10), (13, 11)):
            p.append(_qr(x, y, 1, 1, "#FFE066", .9))
        p.append(_qr(13, 4, 2, 2, "#FFF3B0"))
        p.append(_qr(13, 3.4, 1, 1, "#FFF3B0"))
        p.append(_qr(12.6, 4.6, 1, 1, "#FFF3B0"))
    else:
        p.append(_qr(15, 3.5, 2, 2, "#FFF3B0"))
        p.append(_qr(7, 5, 3, 1, cloud, .95))
        p.append(_qr(8, 4, 2, 1, cloud, .95))
        p.append(_qr(12, 8, 3, 1, cloud, .8))
        p.append(_qr(7, 10, 12, 3, "#A8CE96"))
        p.append(_qr(7, 9.4, 2, 1, "#A8CE96"))
        p.append(_qr(16, 9.6, 3, 1, "#A8CE96"))
    p.append(_qr(11.4, 3, 1.2, 10, frame))
    p.append(_qr(6, 7.4, 12, 1.2, frame))
    p.append(_qr(6, 12, 12, 1, frame))
    # 窗帘
    for x0 in (4.2, 16.8):
        p.append(_qr(x0, 2, 3, 11, "#F6DFB8"))
        p.append(_qr(x0 + 0.6, 2.6, 1, 10, "#E8CC9E", .9))
        p.append(_qr(x0 - 0.4, 1.4, 3.8, 1, frame))
    # 窗台 + 阳光
    p.append(_qr(4, 13.6, 16, 1, "#E3C9A2"))
    if not night:
        p.append('<polygon points="260 300 400 300 520 620 320 620" fill="#FFF7D8" '
                 'opacity=".18"/>')

    # ---------- 小床 ----------
    p.append(_qr(33, 12.6, 1.4, 8, wood_d))
    p.append(_qr(48, 12.6, 1.4, 8, wood_d))
    p.append(_qr(34, 15, 14, 5, wood_d))
    p.append(_qr(34.4, 13.6, 13.2, 2, "#FFF3DC"))
    p.append(_qr(38, 15.4, 9.6, 4.2, "#B7D8E6"))
    p.append(_qr(38, 15.4, 9.6, 1, "#D9EBF4"))
    p.append(_qr(34.6, 13.2, 3.6, 2, "#FFE7A6"))
    p.append(_qr(34.6, 13.2, 3.6, 1, "#FFF3C9"))
    p.append(_qr(34, 19.6, 1.2, 1.4, wood_d))
    p.append(_qr(46.8, 19.6, 1.2, 1.4, wood_d))

    # ---------- 小书架 ----------
    p.append(_qr(24, 12, 8, 1, wood))
    p.append(_qr(24, 12.4, 8, 0.6, wood_d))
    for i, c in enumerate(("#7FA8C9", "#C97B6E", "#E0B15D", "#8BAE7B")):
        p.append(_qr(24.6 + i * 1.6, 9.2, 1.4, 2.8, c))
    p.append(_qr(30.4, 10, 1.2, 2, "#D9B98F"))

    # ---------- 挂钟 ----------
    p.append(_qr(41.6, 2.4, 0.8, 0.6, wood_d))
    p.append(_qr(40, 3, 4, 4, "#3B2A1B"))
    p.append(_qr(40.4, 3.4, 3.2, 3.2, "#FBF3DF"))
    for (x, y) in ((41.8, 3.4), (41.8, 5.8), (40.4, 4.4), (43.2, 4.4)):
        p.append(_qr(x, y, 0.4, 0.4, "#B99250"))
    p.append(_qr(41.6, 4.4, 0.4, 1.4, "#8A6328"))
    p.append(_qr(41.6, 4.4, 1.2, 0.4, "#8A6328"))

    # ---------- 猫爬架 / 爬架 ----------
    p.append(_qr(52, 6, 3, 14, "#E6C99E"))
    p.append(_qr(52, 6, 3, 1, wood))
    p.append(_qr(53.4, 7, 1.2, 13, "#D3B183", .8))
    p.append(_qr(50.4, 9, 7, 1.4, wood))
    p.append(_qr(50.4, 9, 7, 0.6, "#F3E1C2"))
    p.append(_qr(47, 16, 6, 1.4, wood))
    p.append(_qr(47, 16, 6, 0.6, "#F3E1C2"))
    p.append(_qr(55.6, 8, 1, 3, "#C99A5A"))
    p.append(_qr(55.4, 11, 1.4, 1.4, "#E8B44C"))

    # ---------- 绿植 ----------
    p.append(_qr(2.4, 17.4, 4, 2, "#E8D3B2"))
    p.append(_qr(2.6, 19, 3.6, 1.4, "#D9BE96"))
    p.append(_qr(3.4, 14.6, 1.4, 3, "#6FA96B"))
    p.append(_qr(2, 15.6, 1.6, 1.4, "#8CC47E"))
    p.append(_qr(5, 15.2, 1.6, 1.4, "#7FB875"))
    p.append(_qr(3.6, 13.4, 1, 1.4, "#5E9A5C"))

    # ---------- 地毯 ----------
    if rm:
        rug1, rug2, rug3 = rm["rug1"], rm["rug2"], rm["rug3"]
    elif star:
        rug1, rug2, rug3 = "#5B4A94", "#7A66BC", "#4A3C7E"
    else:
        rug1, rug2, rug3 = "#E3C58C", "#F6E5C2", "#CBA96C"
    p.append(_rz(26, 27.4, 12.5, 3.2, rug1))
    p.append(_rz(26, 27.4, 10.8, 2.4, rug2))
    p.append(_rz(26, 27.4, 7, 1.3, rug3))

    # ---------- 食盆 ----------
    p.append(_qr(38.4, 28.4, 5, 1.6, "#EFE3CB"))
    p.append(_qr(38.4, 28, 5, 0.8, "#FFFDF6"))
    p.append(_qr(39, 28.2, 1.4, 0.8, "#E8A15C"))
    p.append(_qr(41.4, 28.2, 1.2, 0.8, "#E8A15C"))

    # ---------- 宠物 ----------
    if star:
        p.append(_rz(25, 24, 11, 4.6, "#6C5CE7", .3))
        p.append(_rz(25, 24, 6.4, 2.8, "#8F7CFF", .28))
    p.append(_rz(25, 26.4, 8.4, 1.2, "#000000", .18))
    p.append(f'<g transform="translate(330 233) scale(1.5)">'
             f'{_pet_group(sp, mood, star, skin)}</g>')

    if star:
        for (x, y) in ((4, 3), (18, 2), (36, 2), (56, 4), (6, 20), (50, 22), (57, 18)):
            p.append(_qr(x, y, 0.6, 1.8, "#FFD54A", .95))
            p.append(_qr(x - 0.6, y + 0.6, 1.8, 0.6, "#FFD54A", .95))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 620" '
            'width="1200" height="620" shape-rendering="crispEdges">'
            + "".join(p) + "</svg>")


_CSS = """
<style>
/* ================= 像素风主题：8-bit 小屋 ================= */
*, *::before, *::after { box-sizing: border-box !important; }

/* 像素配色，全局变量 */
:root{
    --ink:#2B1D10;      --ink2:#4A3218;
    --cream:#FFF4D9;    --cream2:#FFE9BE;   --wood:#C79A63;
    --gold:#FFC94D;     --gold2:#E8A83B;
    --leaf:#9FD69B;     --leafbg:#EAF3D8;
    --sky:#7FC7E8;
}
[data-testid="stAppViewContainer"] {
    background-color:#F4E3C0;
    background-image:
        repeating-linear-gradient(0deg, rgba(160,120,60,.10) 0 2px, transparent 2px 16px),
        repeating-linear-gradient(90deg, rgba(160,120,60,.10) 0 2px, transparent 2px 16px);
}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stToolbar"], [data-testid="stAppDeployButton"] {display:none !important;}
[data-testid="stToolbar"] {right: .8rem;}
[data-testid="stAppViewContainer"] {overflow-x:hidden;}
.block-container {padding:1.3rem 1.1rem 2.6rem; max-width:1280px;}

html, body, [class*="css"] {
    font-family:"Zpix","Fusion Pixel","Cascadia Mono","SimHei","黑体",
                "Microsoft YaHei",monospace;
    letter-spacing:.3px;
    -webkit-font-smoothing:none;
}
/* 像素图不锐化的反例：宠物与房间必须保持硬边 */
.st-key-scene img, [data-testid="stImage"] img {image-rendering:pixelated;}

/* 说明文字：深色 + 高对比，米色底上必须看清 */
[data-testid="stCaptionContainer"] p {
    color:#4A3218 !important; font-weight:700 !important;
    line-height:1.55 !important; opacity:1 !important;
}

/* ================= 顶部 HUD ================= */
.game-hud {
    display:flex; align-items:flex-end; justify-content:space-between; gap:16px;
    margin-bottom:14px; flex-wrap:wrap;
}
.hud-title {
    font-size:1.65rem; font-weight:900; color:#3B2A18; letter-spacing:2px;
    line-height:1.3; text-shadow:3px 3px 0 #FFC94D;
    word-wrap:break-word;
}
.hud-sub {font-size:.82rem; color:#4A3218; font-weight:700; margin-top:4px;
    word-wrap:break-word; line-height:1.5;}
.season-chip {display:inline-block; margin:0 6px; padding:1px 7px; font-size:.78rem;
    font-weight:900; border:2px solid var(--ink); border-radius:0; white-space:nowrap;
    box-shadow:2px 2px 0 var(--wood);}
.season-chip.season-春 {background:#BEE0A8; color:#2F4A1E;}
.season-chip.season-夏 {background:#B7E4F5; color:#1F4658;}
.season-chip.season-秋 {background:#FFD08A; color:#6B3F0C;}
.season-chip.season-冬 {background:#E4EEF6; color:#2C4358;}
.hud-money {display:flex; gap:10px; flex-wrap:wrap;}
.money-pill {
    display:flex; align-items:center; gap:8px; padding:6px 14px; border-radius:0;
    background:var(--cream); border:3px solid var(--ink);
    box-shadow:5px 5px 0 var(--wood); color:#3B2A18;
    font-weight:900; font-size:1rem; white-space:nowrap;
    flex-shrink:0; line-height:1.3;
}
.money-pill .m-ico {display:flex; align-items:center;}
.money-pill.gem {background:#DCEFFC; border-color:#26405C;
    box-shadow:5px 5px 0 #7FB3D8; color:#1E3A55;}

/* ================= 房间场景 ================= */
.st-key-scene img {
    border-radius:0; border:4px solid var(--ink);
    box-shadow:8px 8px 0 var(--wood); display:block;
    max-width:100%; height:auto;
}

/* ================= 宠物面板 ================= */
.pet-panel {
    background:var(--cream); border:4px solid var(--ink);
    border-radius:0; padding:12px 13px 10px;
    box-shadow:8px 8px 0 var(--wood);
    overflow:hidden; min-width:0;
}
.panel-head {display:flex; align-items:center; gap:10px; flex-wrap:wrap; min-width:0;
    row-gap:6px;}
.avatar {width:56px; height:56px; flex:none; border-radius:0; padding:0;
    background:var(--gold); border:3px solid var(--ink);
    box-shadow:4px 4px 0 var(--wood); flex-shrink:0;}
.avatar svg {width:100%; height:100%; display:block;}
.lv-box {display:flex; flex-direction:column; align-items:center; color:#3B2A18;
    flex-shrink:0; min-width:0;}
.lv-box span {font-size:.7rem; letter-spacing:3px; font-weight:700;}
.lv-box b {font-size:1.5rem; line-height:1.05; color:#B8690E;
    text-shadow:2px 2px 0 #FFC94D;}
.star-badge {margin-left:auto; width:38px; height:38px; border-radius:0; flex-shrink:0;
    background:var(--cream2); border:3px solid var(--ink);
    box-shadow:3px 3px 0 var(--wood);
    display:flex; align-items:center; justify-content:center; color:#B8690E;}
.pet-name {
    text-align:center; margin-top:7px; font-size:1.2rem; font-weight:900;
    color:#2B1D10; line-height:1.35;
    word-wrap:break-word; overflow-wrap:anywhere; padding:0 2px;
}
.pet-name small {display:block; font-size:.76rem; color:#5A3E1E; font-weight:800;
    margin:3px 0 0; white-space:nowrap; letter-spacing:1px;}
.pet-status {text-align:center; font-size:.78rem; color:#4A3218; font-weight:800;
    margin-top:3px; line-height:1.4; display:flex; align-items:center;
    justify-content:center; gap:6px; flex-wrap:wrap;}
.mood-tag {font-size:.7rem; font-weight:800; padding:2px 7px; border:2px solid var(--ink);
    border-radius:0; white-space:nowrap; line-height:1.3;}
.mood-tag.mood-great {background:#FFE07A; color:#7A4A08; box-shadow:2px 2px 0 #C08A1E;}
.mood-tag.mood-low {background:#DDE6EC; color:#37505F; box-shadow:2px 2px 0 #8FA6B4;}
.mood-tag.mood-normal {background:var(--cream2); color:#5A3E1E; box-shadow:2px 2px 0 var(--wood);}
.mood-note {text-align:center; font-size:.68rem; color:#6B4A22; font-weight:600;
    margin-top:2px; opacity:1;}
.bonus-line {margin-top:5px; font-size:.66rem; font-weight:700; color:#4A3218;
    background:#FFEBC0; border:2px solid #C79A63; padding:3px 6px; line-height:1.4;
    text-align:center; word-break:break-word;}
.dex-lock {width:64px; height:64px; border:2px dashed #B58A4E; background:#EFE0C4;
    color:#A98455; font-weight:900; font-size:1.6rem; display:flex;
    align-items:center; justify-content:center; margin:0 auto;}
/* 图鉴分类标题条 */
.dex-cat {display:flex; align-items:center; gap:10px; flex-wrap:wrap;
    margin:14px 0 6px; padding:5px 10px; background:#FFE9BE;
    border:3px solid var(--ink); box-shadow:4px 4px 0 var(--wood);}
.dex-cat-name {font-weight:900; font-size:.92rem; color:#3B2A18; letter-spacing:1.5px;}
.dex-cat-desc {font-size:.7rem; font-weight:700; color:#6B4A22;}
.dex-cat.dex-mech {background:#D9E7F5;}
.dex-cat.dex-cute {background:#FFE4EC;}
.dex-cat.dex-myth {background:#E7DCFF;}
.dex-cat.dex-game {background:#D9F5E6;}
.dex-cat.dex-food {background:#FFEFC2;}
.dex-item {border:2px solid #C79A63; background:#FFE9BE; padding:6px; display:flex;
    flex-direction:column; align-items:center; gap:3px; font-size:.7rem;
    font-weight:800; color:#3B2A18; box-shadow:2px 2px 0 #C79A63;}
.exp-left {margin-top:5px; font-size:.72rem; color:#4A3218; font-weight:800;
    text-align:right; letter-spacing:.2px;}
.exp-left b {color:#A9600F;}

.stat-list {margin-top:9px; display:flex; flex-direction:column; gap:6px;}
.stat-row {
    display:flex; align-items:center; gap:8px;
    background:var(--leafbg); border:2px solid #6E8A4B;
    border-radius:0; padding:4px 8px; flex-wrap:nowrap; min-width:0;
    box-shadow:inset -2px -2px 0 rgba(110,138,75,.25);
}
.stat-ico {width:28px; height:28px; border-radius:0; display:flex; align-items:center;
    justify-content:center; flex:none;
    flex-shrink:0; border:2px solid #6E8A4B;}
/* 标签不压缩、数值右对齐，两者互不侵占 */
.stat-label {font-size:.88rem; font-weight:900; color:#33421A; white-space:nowrap;
    flex:0 0 auto;}
.stat-value {margin-left:auto; text-align:right; font-size:1rem;
    font-weight:900; color:#2F4A12; background:transparent; border-radius:0;
    padding:2px 4px; flex:0 1 auto; min-width:0; font-variant-numeric:tabular-nums;
    line-height:1.2;}

.exp-box {margin-top:8px; background:var(--cream); border:2px solid #B58A4E;
    border-radius:0; padding:6px 9px;}
.exp-top {display:flex; justify-content:space-between; align-items:center;
    font-size:.8rem; color:#4A3218; font-weight:800; flex-wrap:wrap; gap:4px;
    line-height:1.45;}
.exp-top .exp-label {display:flex; align-items:center; gap:5px; flex:none;}
.exp-top b {font-variant-numeric:tabular-nums;}
.exp-bar {height:12px; border-radius:0; background:#C9A470; overflow:hidden;
    margin-top:6px; border:2px solid var(--ink);
    /* 分段格子，像 8-bit 血条 */
    background-image:repeating-linear-gradient(90deg,
        rgba(43,29,16,.35) 0 2px, transparent 2px 10px);}
.exp-bar i {display:block; height:100%; border-radius:0;
    background:linear-gradient(180deg,#FFE07A,#E8A83B);
    box-shadow:inset 0 -2px 0 rgba(120,80,20,.35);}
.panel-tags {display:flex; gap:5px; flex-wrap:wrap; margin-top:8px;}
.panel-tag {font-size:.72rem; color:#3B2A18; font-weight:800; background:var(--cream2);
    border:2px solid #A9793F; border-radius:0; padding:2px 8px; white-space:nowrap;}

/* ================= 底部操作 dock 栏 ================= */
.st-key-dock {max-width:660px; margin:18px auto 4px;}
.st-key-dock [data-testid="stHorizontalBlock"] {gap:10px; align-items:stretch;}
div[class*="st-key-act_"] [data-testid="stButton"],
div[class*="st-key-quick_"] [data-testid="stPopover"] {width:100%;}
div[class*="st-key-act_"] button,
div[class*="st-key-quick_"] button {
    width:100%; min-height:78px; padding:8px 4px; border-radius:0;
    background:var(--cream); border:3px solid var(--ink);
    box-shadow:5px 5px 0 var(--wood);
    color:#2B1D10; font-weight:900; font-size:.88rem;
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px;
    transition:none;
    white-space:normal !important; word-wrap:break-word !important;
    overflow-wrap:anywhere !important; line-height:1.25;
    text-align:center; overflow:hidden;
}
div[class*="st-key-act_"] button:hover,
div[class*="st-key-quick_"] button:hover {
    transform:translate(-1px,-1px);
    border-color:var(--ink);
    box-shadow:6px 6px 0 var(--gold2); color:#2B1D10;
    background:var(--cream2);
}
div[class*="st-key-act_"] button:active,
div[class*="st-key-quick_"] button:active {
    transform:translate(5px,5px); box-shadow:0 0 0 var(--wood);
}
div[class*="st-key-act_"] button [data-testid="stIconMaterial"],
div[class*="st-key-quick_"] button [data-testid="stIconMaterial"] {
    font-size:26px; width:26px; height:26px; color:#8A5A1C;
}
div[class*="st-key-act_"] button p,
div[class*="st-key-quick_"] button p {
    font-size:.86rem; font-weight:900; margin:0; line-height:1.2;
    white-space:normal !important;
}
div[class*="st-key-act_"] button > div,
div[class*="st-key-quick_"] button > div {
    flex-direction:column; align-items:center; justify-content:center; gap:2px !important;
}
div[class*="st-key-act_"] button > div > span,
div[class*="st-key-quick_"] button > div > span {
    flex-direction:column; align-items:center; justify-content:center; gap:2px;
}
div[class*="st-key-quick_"] button > div > div:not([aria-hidden="true"]) {
    flex-direction:column; align-items:center; justify-content:center; gap:2px;
}
[data-testid="stPopoverButton"] > div > div[aria-hidden="true"] {display:none;}
div[data-testid="stPopoverContent"] {padding:1rem !important;
    border:3px solid var(--ink) !important; border-radius:0 !important;
    box-shadow:6px 6px 0 var(--wood) !important; background:var(--cream) !important;}

/* ================= 通用控件 ================= */
[data-testid="stButton"] button {
    border-radius:0; border:3px solid var(--ink); color:#2B1D10; font-weight:900;
    background:var(--cream); box-shadow:4px 4px 0 var(--wood);
    white-space:normal !important; word-wrap:break-word !important;
}
[data-testid="stButton"] button:hover {background:var(--cream2); color:#2B1D10;}
[data-testid="stButton"] button[data-testid^="stBaseButton-primary"] {
    background:var(--gold); border-color:var(--ink); color:#3B2A18;
    box-shadow:4px 4px 0 var(--gold2);
}
[data-testid="stPopover"] button {border-radius:0; border:3px solid var(--ink);
    color:#2B1D10; background:var(--cream); font-weight:900; white-space:normal;
    box-shadow:4px 4px 0 var(--wood);}
[data-testid="stWidgetLabel"] p {color:#3B2A18; font-weight:900; word-wrap:break-word;}
[data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSelectbox"] input {
    background:var(--cream); border-color:var(--ink); border-radius:0; color:#2B1D10;}
[data-testid="stSelectbox"] .react-aria-ComboBox > div {
    background:var(--cream); border:3px solid var(--ink); border-radius:0;}
[data-testid="stSelectbox"] input[role="combobox"] {
    background:transparent; color:#2B1D10; font-weight:800;}
[data-testid="stTextInput"] input {background:var(--cream); border-color:#8A5A2C;
    color:#2B1D10; border-radius:0;}
[data-testid="stRadio"] [role="radio"] {border-color:#8A5A2C;}

/* ================= 标签页 ================= */
[data-testid="stTabs"] [role="tablist"] {gap:6px; flex-wrap:wrap; border-bottom:none;}
[data-testid="stTabs"] [role="tab"] {
    height:auto; min-height:44px; padding:8px 14px; border-radius:0;
    background:var(--cream2); border:3px solid #B58A4E; color:#3B2A18; font-weight:900;
    white-space:normal; line-height:1.3; text-align:center;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background:var(--gold); border-color:var(--ink); color:#2B1D10;
    box-shadow:3px 3px 0 var(--ink);}
[data-testid="stTabs"] .react-aria-SelectionIndicator {display:none;}

/* ================= 区块标题 ================= */
.pe-sec {
    display:flex; align-items:center; gap:7px; font-size:.95rem; font-weight:900;
    color:#2B1D10; background:var(--gold); border:3px solid var(--ink);
    border-radius:0; padding:5px 10px; margin:.2rem 0 .6rem;
    flex-wrap:wrap; line-height:1.35; box-shadow:4px 4px 0 var(--wood);
}
.pe-sec .ico {flex:none;}

/* ================= 任务卡片 ================= */
.pe-task {
    display:flex; align-items:flex-start; gap:8px; padding:8px 10px;
    border:2px solid #B58A4E; border-radius:0; background:var(--cream);
    margin-bottom:6px; flex-wrap:nowrap; min-width:0;
    box-shadow:inset -2px -2px 0 rgba(181,138,78,.25);
}
.pe-task.done {background:#E7F2CF; border-color:#7E9B4F;}
.pe-task > div {min-width:0; flex:1 1 auto;}
.pe-task-title {font-size:.86rem; font-weight:900; color:#2B1D10; line-height:1.35;
    word-wrap:break-word; overflow-wrap:anywhere;}
.pe-task-desc {font-size:.78rem; color:#4A3218; font-weight:700; margin-top:1px;
    line-height:1.45; word-wrap:break-word; overflow-wrap:anywhere;}
.pe-task-reward {margin-left:auto; font-size:.8rem; font-weight:900; color:#3B2A18;
    background:var(--gold); border:2px solid var(--ink); border-radius:0;
    padding:2px 8px; flex:0 0 auto; white-space:nowrap; align-self:center;}

/* ================= 消息广播 ================= */
.pe-msg {
    display:flex; gap:8px; padding:8px 10px; border-radius:0; background:var(--cream);
    border:2px solid #B58A4E; border-left:6px solid var(--gold2); margin-bottom:6px;
    font-size:.86rem; color:#2B1D10; font-weight:700; line-height:1.55;
    word-wrap:break-word; overflow-wrap:anywhere;
}
.pe-msg .ico {flex:none; margin-top:2px;}
.pe-empty {padding:12px; border-radius:0; background:var(--cream); border:2px dashed #A9793F;
    color:#4A3218; font-weight:700; font-size:.86rem; text-align:center;
    line-height:1.55; word-wrap:break-word;}

/* ================= 商店商品卡片 ================= */
.pe-item {
    display:flex; align-items:flex-start; gap:12px; padding:12px;
    border:3px solid var(--ink); border-radius:0; background:var(--cream);
    flex-wrap:wrap; min-width:0; box-shadow:5px 5px 0 var(--wood);
}
.pe-item-ico {width:56px; height:56px; flex:none; border-radius:0;
    background:var(--gold); color:#5A3A10; border:3px solid var(--ink);
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
    box-shadow:3px 3px 0 var(--wood);}
.pe-item > div:not(.pe-item-ico):not(.pe-item-price) {min-width:0; flex:1 1 auto;}
.pe-item-name {font-weight:900; color:#2B1D10; font-size:.98rem; line-height:1.35;
    word-wrap:break-word; overflow-wrap:anywhere;}
.pe-item-desc {font-size:.8rem; color:#4A3218; font-weight:700; margin-top:2px;
    line-height:1.45; word-wrap:break-word; overflow-wrap:anywhere;}
.pe-item-price {margin-left:auto; display:flex; align-items:center; gap:4px;
    font-weight:900; color:#B8690E; white-space:nowrap; flex:0 0 auto;}

/* ================= 仓库网格 ================= */
.pe-inv {display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:8px;}
.pe-inv-item {
    display:flex; align-items:center; gap:6px; padding:7px 9px; border:2px solid #B58A4E;
    border-radius:0; background:var(--cream); font-size:.8rem; color:#3B2A18;
    word-wrap:break-word; overflow-wrap:anywhere;
    box-shadow:inset -2px -2px 0 rgba(181,138,78,.22);
}
.pe-inv-item b {margin-left:auto; color:#B8690E; flex-shrink:0;}

/* ================= 成就卡片 ================= */
.pe-ach {
    display:flex; align-items:flex-start; gap:9px; padding:8px 10px;
    border:2px solid #B58A4E; border-radius:0; margin-bottom:6px; background:var(--cream);
    flex-wrap:nowrap; box-shadow:inset -2px -2px 0 rgba(181,138,78,.22);
}
.pe-ach.locked {opacity:.85; background:#F2E3C4;}
.pe-ach > div {min-width:0; flex:1 1 auto;}
.pe-ach-title {font-size:.86rem; font-weight:900; color:#2B1D10; line-height:1.35;
    word-wrap:break-word; overflow-wrap:anywhere;}
.pe-ach-desc {font-size:.78rem; color:#4A3218; font-weight:700; margin-top:1px;
    line-height:1.45; word-wrap:break-word; overflow-wrap:anywhere;}
.pe-ach-tag {margin-left:auto; font-size:.74rem; font-weight:900; color:#3E5A16;
    flex:0 0 auto; white-space:nowrap; align-self:center;}
.pe-ach.locked .pe-ach-tag {color:#5A3E1E;}
.pe-ach.locked .pe-ach-title {color:#4A3218;}

/* ================= 游戏日志：终端感 ================= */
.pe-log {
    max-height:280px; overflow:auto; background:#241A0E; border-radius:0;
    padding:10px 12px; font-family:"Cascadia Mono",Consolas,monospace; font-size:.8rem;
    line-height:1.75; color:#F7E2B4; border:3px solid var(--ink);
    white-space:pre-wrap;
    background-image:repeating-linear-gradient(0deg,
        rgba(255,255,255,.05) 0 1px, transparent 1px 4px);
}
.pe-log div {white-space:pre-wrap; word-wrap:break-word; overflow-wrap:anywhere;}

/* ================= 新游戏页面 ================= */
.newgame-title {text-align:center; font-size:1.8rem; font-weight:900; color:#3B2A18;
    margin:4px 0 2px; text-shadow:3px 3px 0 var(--gold); word-wrap:break-word; line-height:1.3;}
.newgame-sub {text-align:center; color:#4A3218; font-weight:700; font-size:.88rem;
    margin-bottom:12px; word-wrap:break-word; line-height:1.5;}
[data-testid="stImage"] {display:flex; justify-content:center; max-width:100%;}

/* ================= 响应式 ================= */
@media (max-width:1024px){
    .pet-panel {padding:10px 11px 9px; box-shadow:6px 6px 0 var(--wood);}
    .avatar {width:48px; height:48px;}
    .lv-box b {font-size:1.3rem;}
    .star-badge {width:32px; height:32px;}
    .st-key-scene img {box-shadow:6px 6px 0 var(--wood);}
}
@media (max-width:768px){
    .st-key-dock {max-width:100%; margin-top:12px;}
    .st-key-dock [data-testid="stHorizontalBlock"] {gap:8px;}
    div[class*="st-key-act_"] button,
    div[class*="st-key-quick_"] button {min-height:72px; font-size:.8rem; padding:6px 2px;}
    div[class*="st-key-act_"] button p,
    div[class*="st-key-quick_"] button p {font-size:.78rem;}
    .pe-inv {grid-template-columns:repeat(auto-fill,minmax(110px,1fr));}
    .game-hud {flex-direction:column; align-items:flex-start;}
    .hud-title {font-size:1.4rem;}
    .pe-msg, .pe-task-desc, .pe-ach-desc, .pe-item-desc, .pe-empty {font-size:.82rem;}
}
</style>
"""
def render(html_text):
    st.markdown(html_text, unsafe_allow_html=True)
def section(icon_name, title):
    render(
        f'<div class="pe-sec">{icon(icon_name, 18, "#9A6A2E")}'
        f'<span>{_html.escape(title)}</span></div>'
    )
def fmt_wait(seconds):
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    if h:
        return f"{h} 小时 {m} 分"
    if m:
        return f"{m} 分 {s} 秒"
    return f"{s} 秒"
def hud_block(gs, star_count):
    sd = season_of()
    return (
        '<div class="game-hud">'
        '<div class="hud-brand">'
        '<div class="hud-title">毛孩子的小屋</div>'
        f'<div class="hud-sub">{date.today().strftime("%Y年%m月%d日")}'
        f'<span class="season-chip season-{sd["key"]}">{sd["name"]} · 第 {sd["day_in_season"]}/{SEASON_DAYS} 天</span>'
        ' · 今天也要好好照顾它</div>'
        '</div>'
        '<div class="hud-money">'
        f'<div class="money-pill"><span class="m-ico">{icon("coin", 22, "#BB851F")}</span>'
        f'<b>{gs["df"]}</b></div>'
        f'<div class="money-pill gem"><span class="m-ico">{icon("gem", 22, "#3F7FC4")}</span>'
        f'<b>{star_count}</b></div>'
        '</div>'
        '</div>'
    )
def _stat_row(label, icon_name, color, bg, value):
    return (
        f'<div class="stat-row"><span class="stat-ico" style="background:{bg}">'
        f'{icon(icon_name, 18, color)}</span>'
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value:.0f}</span></div>'
    )
def _short_name(name, limit=10):
    """面板里的名字只展示前 limit 个字，超长名字不再撑破卡片（存档里的全名不变）。"""
    name = str(name)
    return name if len(name) <= limit else name[:limit] + "…"
def pet_panel_block(gs, pet, star_count):
    sp = species_of(pet)
    need = max(1, pet["lv"] * 50)
    pct = max(0.0, min(100.0, float(pet["exp"]) / need * 100.0))
    left_exp = max(0.0, need - float(pet["exp"]))
    status = {"happy": "心情不错", "sad": "需要照顾", "sick": "状态不佳"}[pet_mood(pet)]
    mt = mood_tag(pet)
    mood_note = {"great": "衰减-15% · 好事更多",
                 "low": "衰减+15% · 易遇坏事",
                 "normal": "无额外加成"}[mt["key"]]
    rows = "".join([
        _stat_row("心情", "happy", "#C08A1E", "#FFF1C4", pet["hn"]),
        _stat_row("饱食", "food", "#C9702C", "#FFE5D0", pet["ha"]),
        _stat_row("清洁", "clean", "#3E86B5", "#DCEEF9", pet["cl"]),
        _stat_row("健康", "heart", "#C05262", "#FFE1E5", pet["health"]),
    ])
    tags = [
        (f"星辉 Lv.{int(pet.get('star_lv', 1) or 1)}" if pet.get("is_star") else "普通皮肤"),
        (f"装扮 {skin_theme(pet)}" if skin_theme(pet) else "无装扮"),
        f"{season_of()['name']} 剩 {season_of()['left_days']} 天",
        f"探索 {gs['total_explore']} 次",
        "事件 开" if gs["rand_event_switch"] else "事件 关",
        "存档 开" if gs["auto_save_switch"] else "存档 关",
    ]
    if pet.get("evo_branch"):
        tags.append(f"{pet['evo_branch']}·{pet.get('element') or '无'} {int(pet.get('evo_lv', 0))}/5")
    if star_count:
        tags.append(f"星辉 {star_count} 只")
    tag_html = "".join(f'<span class="panel-tag">{t}</span>' for t in tags)
    badge = icon("star", 20, "#D9A63A")
    return (
        '<div class="pet-panel">'
        '<div class="panel-head">'
        f'<div class="avatar">{pet_art(pet)}</div>'
        f'<div class="lv-box"><span>等级</span><b>{pet["lv"]}</b></div>'
        f'<div class="star-badge">{badge}</div>'
        '</div>'
        f'<div class="pet-name">{_html.escape(_short_name(pet["name"]))}'
        f'<small>{PET_LABEL.get(sp, sp)}</small></div>'
        f'<div class="pet-status">{status}'
        f'<span class="mood-tag mood-{mt["key"]}">{mt["label"]}</span></div>'
        f'<div class="mood-note">{mood_note}</div>'
        f'<div class="bonus-line">{_html.escape(bonus_summary(pet))}</div>'
        f'<div class="stat-list">{rows}</div>'
        '<div class="exp-box">'
        f'<div class="exp-top"><span class="exp-label">{icon("star", 13, "#A9741F")}'
        f'<span>经验</span></span><b>{pet["exp"]:.0f} / {need}</b></div>'
        f'<div class="exp-bar"><i style="width:{pct:.1f}%"></i></div>'
        f'<div class="exp-left">距离 Lv.{pet["lv"] + 1} 还需要 <b>{left_exp:.0f}</b> 经验</div>'
        '</div>'
        f'<div class="panel-tags">{tag_html}</div>'
    )
def tasks_block(gs):
    rows = []
    for t in daily_task_list:
        done = t["id"] in gs["task_finished"]
        cls = "pe-task done" if done else "pe-task"
        ic = icon("check", 16, "#7E8F3F") if done else icon("task", 16, "#C0A57C")
        rows.append(
            f'<div class="{cls}">{ic}<div>'
            f'<div class="pe-task-title">{_html.escape(t["name"])}</div>'
            f'<div class="pe-task-desc">{_html.escape(t["desc"])}</div></div>'
            f'<div class="pe-task-reward">+{t["reward"]}</div></div>'
        )
    return "".join(rows)
def week_progress(gs):
    """按“总量 - 本周起点”算出每项周任务进度。"""
    base = gs.get("week_base", {}) or {}
    cur = {
        "feed": gs["total_feed"],
        "lottery": int(gs.get("total_lottery", 0)),
        "explore": gs["total_explore"],
    }
    out = {}
    for t in WEEK_TASK_LIST:
        b = int(base.get(t["metric"], cur[t["metric"]]))
        out[t["id"]] = max(0, cur[t["metric"]] - b)
    return out
def week_block(gs):
    prog = week_progress(gs)
    rows = []
    for t in WEEK_TASK_LIST:
        got = min(prog[t["id"]], t["target"])
        done = got >= t["target"]
        cls = "pe-task week done" if done else "pe-task week"
        ic = icon("check", 16, "#7E8F3F") if done else icon("task", 16, "#C0A57C")
        rows.append(
            f'<div class="{cls}">{ic}<div>'
            f'<div class="pe-task-title">{_html.escape(t["name"])}</div>'
            f'<div class="pe-task-desc">{_html.escape(t["desc"])}'
            f' · 进度 {got}/{t["target"]}</div></div>'
            f'<div class="pe-task-reward">+{t["reward"]}</div></div>'
        )
    return "".join(rows)
def messages_block(msgs, gs=None):
    tips = [
        "四项属性均衡时，健康值会慢慢恢复。",
        "每日任务每天刷新，完成后记得领取积分。",
        "宠物 10 级后使用宠物强化剂，可以觉醒星辉形态。",
        "玩耍和洗澡都有 2 小时冷却，合理安排时间。",
        "探索有 30 分钟冷却，长途探索更容易遇到稀有宝箱。",
    ]
    rows = ["<div class=\"pe-empty\">小屋很安静，来看看今天的小贴士：</div>"] if not msgs else []
    rows.extend(
        f'<div class="pe-msg">{icon("bell", 15, "#B7791F")}'
        f'<span>{_html.escape(str(m))}</span></div>'
        for m in msgs
    )
    rows.extend(
        f'<div class="pe-msg">{icon("info", 15, "#B7791F")}'
        f'<span>{_html.escape(t)}</span></div>'
        for t in tips
    )
    return "".join(rows)
def _item_icon_name(item):
    if item.startswith("皮肤·"):
        return "paint"
    return _ITEM_ICON.get(item, "box")


def item_card(item):
    return (
        f'<div class="pe-item"><div class="pe-item-ico">'
        f'{icon(_item_icon_name(item), 30, "#9A6A1E")}</div>'
        f'<div><div class="pe-item-name">{_html.escape(item)}</div>'
        f'<div class="pe-item-desc">{_html.escape(shop_desc.get(item, ""))}</div></div>'
        f'<div class="pe-item-price">{icon("coin", 15, "#B7791F")}'
        f'<b>{price_dict.get(item, 0)}</b></div></div>'
    )
def inventory_block(inv):
    if not inv:
        return '<div class="pe-empty">仓库空空如也，去商店买点东西吧</div>'
    counts = {}
    for it in inv:
        counts[it] = counts.get(it, 0) + 1
    cards = "".join(
        f'<div class="pe-inv-item">{icon(_item_icon_name(it), 20, "#9A6A1E")}'
        f'<span>{_html.escape(it)}</span><b>x{n}</b></div>'
        for it, n in counts.items()
    )
    return f'<div class="pe-inv">{cards}</div>'
def achievements_block(gs):
    rows = []
    for a in achievement_list:
        got = a["aid"] in gs["unlock_ach"]
        cls = "pe-ach" if got else "pe-ach locked"
        rows.append(
            f'<div class="{cls}">{icon("trophy", 18, "#C08A1E" if got else "#C0A57C")}'
            f'<div><div class="pe-ach-title">{_html.escape(a["title"])}</div>'
            f'<div class="pe-ach-desc">{_html.escape(a["desc"])}</div></div>'
            f'<span class="pe-ach-tag">{"已解锁" if got else "未解锁"}</span></div>'
        )
    return "".join(rows)
def log_block(log_lines):
    lines = log_lines or ["暂无日志"]
    return '<div class="pe-log">' + "".join(
        f"<div>{_html.escape(str(x))}</div>" for x in lines
    ) + "</div>"
def flash(msg):
    st.session_state.setdefault("flash", []).append(msg)
def unlock(gs, aid, out_msgs):
    if aid in gs["unlock_ach"]:
        return
    gs["unlock_ach"].append(aid)
    title = next((a["title"] for a in achievement_list if a["aid"] == aid), str(aid))
    out_msgs.append(f"解锁成就：【{title}】")
    add_log(f"解锁成就：{title}", gs["game_log"])
# ===================== Streamlit UI入口 =====================
st.set_page_config(page_title="毛孩子的小屋", layout="wide")
render(_CSS)
if "game_state" not in st.session_state:
    loaded = load_game()
    if loaded is None:
        render(
            '<div class="newgame-title">毛孩子的小屋</div>'
            '<div class="newgame-sub">选择你的第一只伙伴，开始温暖的陪伴</div>'
        )
        sel_pet = st.radio(
            "选择你的第一只宠物", PET_SPECIES, horizontal=True,
            label_visibility="collapsed",
        )
        with st.container(key="scene"):
            st.image(room_svg(sel_pet, "happy", False), width="stretch")
        _, mid, _ = st.columns([1, 1.2, 1])
        with mid:
            if st.button(
                "开始新游戏", type="primary", icon=":material/pets:",
                width="stretch",
            ):
                st.session_state.game_state = new_game(sel_pet)
                st.rerun()
        st.stop()
    else:
        st.session_state.game_state = loaded
if "flash" not in st.session_state:
    st.session_state.flash = []
gs = st.session_state.game_state
out_msgs = list(st.session_state.flash)
st.session_state.flash = []
# -------- 时间流逝、每日刷新、属性衰减（核心逻辑） --------
today = date.today()
if gs["current_pet_idx"] >= len(gs["pet_list"]):
    gs["current_pet_idx"] = 0
current_pet = gs["pet_list"][gs["current_pet_idx"]]
is_star = current_pet.get("is_star", False)
pet_species = species_of(current_pet)
# 图鉴同步：老存档里已有的宠物、仓库里的季节道具，自动补点亮（重复执行不会重复发积分）
dex_seed = []
for p in gs["pet_list"]:
    sp = species_of(p)
    dex_seed.append(f"{sp}|normal")
    if p.get("is_star"):
        dex_seed.append(f"{sp}|star")
dex_seed += [f"item|{it}" for it in gs["storehouse"] if it in DEX_SEASON_ITEMS]
dex_add(gs, dex_seed, out_msgs)
# 每日任务刷新
if gs["task_day"] != today:
    gs["task_finished"] = []
    gs["task_day"] = today
    gs["task_feed_flag"] = 0
    gs["today_event_log"] = []
    out_msgs.append("新的一天！每日任务已刷新！")
# 每日签到：连续第 1/2/3… 天分别 10 / 15 / 20…（+5 递增，上限 30），断签重置
if today > gs["last_get_date"]:
    gap = (today - gs["last_get_date"]).days
    if gap == 1:
        gs["sign_streak"] = int(gs.get("sign_streak", 1)) + 1
    else:
        gs["sign_streak"] = 1
    sign_reward = min(30, 10 + 5 * (gs["sign_streak"] - 1))
    tomorrow_reward = min(30, 10 + 5 * gs["sign_streak"])
    gs["df"] += sign_reward
    gs["last_get_date"] = today
    out_msgs.append(
        f"每日签到：连续第 {gs['sign_streak']} 天，积分 +{sign_reward}"
        f"（明天记得来，可得 {tomorrow_reward} 积分）"
    )
    add_log(f"每日签到 +{sign_reward}（连续 {gs['sign_streak']} 天）", gs["game_log"])
week_key = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
if gs.get("week_key") != week_key:
    gs["week_key"] = week_key
    gs["week_base"] = {
        "feed": gs["total_feed"], "lottery": gs.get("total_lottery", 0),
        "explore": gs["total_explore"],
    }
    gs["week_done"] = []
    out_msgs.append("新的一周！周任务进度已重置")
season = season_of(today)
if gs.get("last_season") != season["key"]:
    gs["last_season"] = season["key"]
    out_msgs.append(
        f"季节更替：进入{season['name']}（{season['note']}）"
        f"，本季持续到 {season['left_days']} 天后"
    )
    add_log(f"进入{season['name']}", gs["game_log"])
now = datetime.now()
delta_min = (now - gs["last_auto_hour_time"]).total_seconds() / 60
pet_cl = current_pet["cl"]
pet_ha = current_pet["ha"]
pet_hn = current_pet["hn"]
health = current_pet["health"]
exp = current_pet["exp"]
# 星辉等级 / 进化方向 / 五行元素统一的增益表（未觉醒时全部为 1）
bonus = pet_bonus(current_pet)
pet_cl_decay = 0.03 * bonus["cl"]
if pet_species == "小羊":
    pet_cl_decay *= 0.5
if pet_species == "企鹅":
    pet_cl_decay *= 0.9          # 企鹅自带羽毛防水，清洁掉得慢
if is_star and pet_species == "机器人":
    pet_cl_decay *= 0.7
if pet_species == "机械蜂":
    pet_cl_decay *= 0.85        # 金属外壳不沾灰
cur_mood = mood_tag(current_pet)
mood_decay = cur_mood["decay"]
if pet_species == "青蛙":
    mood_decay *= 0.92           # 青蛙心大，不怎么闹脾气
if pet_species == "小鹿":
    mood_decay *= 0.95           # 小鹿性子温顺
pet_cl_decay *= season["cl"] * mood_decay
pet_ha_mod = bonus["ha"] * season["ha"] * mood_decay
if pet_species == "仓鼠":
    pet_ha_mod *= 0.9            # 仓鼠爱囤粮，饿得慢
if pet_species == "史莱姆":
    pet_ha_mod *= 0.9            # 果冻身子耐饿
pet_hn_mod = bonus["hn"] * season["hn"] * mood_decay
if pet_species == "布丁":
    pet_hn_mod *= 0.95           # 甜品治愈，心情掉得慢
if pet_species == "小鸭":
    pet_cl_decay *= 0.9          # 羽毛防水，脏得慢
if pet_species == "机械鼠":
    pet_cl_decay *= 0.85         # 光滑金属壳不沾灰
if pet_species == "蘑菇仔":
    pet_cl_decay *= 0.92         # 伞盖替身子挡灰
if pet_species == "熊猫":
    pet_hn_mod *= 0.9            # 心宽体胖，心情掉得慢
if pet_species == "小狼":
    pet_ha_mod *= 0.92           # 耐力好，饿得慢
if pet_species == "小马":
    pet_ha_mod *= 0.88           # 能跑能扛，最耐饿
if pet_species == "饭团":
    pet_ha_mod *= 0.9            # 主食体质，最管饱
if pet_species == "机甲兔":
    mood_decay *= 0.95           # 机芯稳定，不闹脾气
if pet_species == "独角兽":
    mood_decay *= 0.93           # 圣洁心境
if pet_species == "豆豆":
    pet_hn_mod *= 0.94           # 天生乐天
if pet_species == "甜甜圈":
    pet_hn_mod *= 0.95           # 甜食治愈
if pet_species == "机甲龟":
    pet_cl_decay *= 0.9          # 硬壳防尘
if pet_species == "方块仔":
    pet_cl_decay *= 0.9          # 塑料方块不沾土
if pet_species == "机械狮":
    mood_decay *= 0.94           # 机芯稳定
if pet_species == "炸弹仔":
    mood_decay *= 0.92           # 心大到不像炸弹
if pet_species == "冰淇淋":
    mood_decay *= 0.94           # 冰甜安神
if pet_species == "小刺猬":
    pet_ha_mod *= 0.93           # 慢慢吃，耐饿
if pet_species == "小猪":
    pet_ha_mod *= 0.9            # 吃一顿顶很久
if pet_species == "小松鼠":
    pet_hn_mod *= 0.95           # 有存粮就安心
if pet_species == "貔貅":
    pet_hn_mod *= 0.92           # 只进不出的好心情
if pet_species == "小笼包":
    pet_ha_mod *= 0.92           # 白面顶饱
pet_cl -= delta_min * pet_cl_decay
pet_cl = max(0.0, min(pet_cl, 150.0))
pet_ha -= delta_min * 0.5 * pet_ha_mod
pet_ha = max(0.0, min(pet_ha, 150.0))
pet_hn -= delta_min * 0.1 * bonus["hn"] * season["hn"] * mood_decay
if pet_ha < 75:
    pet_hn -= delta_min * 0.5 * pet_hn_mod
if pet_cl < 60:
    pet_hn -= delta_min * 0.3 * pet_hn_mod
pet_hn = max(0.0, min(pet_hn, 150.0))
if pet_hn < 50:
    exp_loss_base = delta_min * 0.2
    if is_star:
        exp_loss_base *= 0.7
    exp -= exp_loss_base
    exp = max(0.0, exp)
health_loss = 0.0
if pet_ha < 50:
    health_loss += 0.15
elif pet_ha < 100:
    health_loss += 0.10
elif pet_ha < 125:
    health_loss += 0.05
if pet_cl < 50:
    health_loss += 0.15
elif pet_cl < 100:
    health_loss += 0.10
elif pet_cl < 125:
    health_loss += 0.05
if pet_hn < 50:
    health_loss += 0.15
elif pet_hn < 100:
    health_loss += 0.10
elif pet_hn < 125:
    health_loss += 0.05
health_loss *= bonus["guard"] * bonus["hloss"]
heal_rate = 0.12 * bonus["heal"]
if pet_species == "小熊":
    heal_rate *= 1.15            # 小熊皮实，恢复更快
if pet_species == "小龙":
    heal_rate *= 1.1             # 龙族体质
if pet_species == "麒麟":
    heal_rate *= 1.12            # 祥瑞护体，恢复最快
if pet_species == "凤凰":
    heal_rate *= 1.15            # 浴火重生，回血最强
if pet_ha >= 80 and pet_cl >= 80 and pet_hn >= 80:
    if is_star:
        heal_rate = 0.24
    health += delta_min * heal_rate
    health_loss = 0
health -= health_loss * delta_min
health = max(0.0, min(health, 150.0))
exp_loss = 0.0
if health < 30 and not (is_star and bonus["star_lv"] >= 4):
    exp_loss = delta_min * 0.8
elif 30 <= health < 50:
    exp_loss = delta_min * 0.2
exp -= exp_loss
exp = max(0.0, exp)
if health < 30:
    if is_star and bonus["star_lv"] >= 4:
        out_msgs.append(f"提醒：【{current_pet['name']}】健康低于 30，星辉护体（4 级起生效），不再快速损失经验！")
    elif is_star:
        out_msgs.append(f"警告：【{current_pet['name']}】健康低于 30！星辉等级不足 4 级，护体尚未生效，快去治疗！")
    else:
        out_msgs.append(f"严重警告：【{current_pet['name']}】健康低于 30！快去治疗！")
elif health < 50:
    out_msgs.append(f"提醒：【{current_pet['name']}】健康 30~50，正在缓慢损失经验！")
if "last_rand_event_time" not in gs:
    gs["last_rand_event_time"] = now - RAND_EVENT_INTERVAL
rand_ready_at = gs["last_rand_event_time"] + RAND_EVENT_INTERVAL
rand_event_due = now >= rand_ready_at
gs["rand_event_next_time"] = rand_ready_at
good_w = 6
if is_star:
    # 星辉等级越高、灵能阶数越高，好事权重越大；不再是“一觉醒就拿满”
    good_w += bonus["star_lv"] // 3 + bonus["luck"] // 2
bonus_weights = [good_w, 3, 2, 3, 2, good_w, good_w, 2, 2, 3]
if "幸运徽章" in gs["storehouse"]:
    bonus_weights = [w + 1 if i in (0, 5, 6) else w
                     for i, w in enumerate(bonus_weights)]
if cur_mood["luck"] == "good":
    bonus_weights = [8, 4, 3, 4, 1, 8, 8, 1, 1, 3]
elif cur_mood["luck"] == "bad":
    bonus_weights = [3, 2, 2, 2, 3, 3, 3, 4, 4, 3]
if int(gs.get("bad_streak", 0)) >= 2:
    bonus_weights = [b + 4 if i in (0, 5, 6) else b for i, b in enumerate(bonus_weights)]
goodluck_on = gs["star_skill_cd"]["goodluck_stack"] > 0
if goodluck_on:
    bonus_weights = [9, 3, 2, 3, 2, 9, 9, 2, 2, 3]
BAD_EVENT_TYPES = ("lose_health", "lose_ha", "lose_cl")
season_pool = [e for e in SEASON_EVENTS[season["key"]]]
if season["key"] == "冬":
    season_pool_weights = [3, 4]
elif season["key"] == "春":
    season_pool_weights = [5, 4]
else:
    season_pool_weights = [4, 4]
event_pool = random_event_list + season_pool
all_weights = bonus_weights + season_pool_weights
if gs["rand_event_switch"] == 1 and rand_event_due:
    gs["last_rand_event_time"] = now
    if goodluck_on:
        gs["star_skill_cd"]["goodluck_stack"] -= 1
    event = random.choices(event_pool, weights=all_weights, k=1)[0]
    out_msgs.append(f"随机事件：{event['msg']}")
    add_log(f"随机事件：{event['msg']}", gs["game_log"])
    gs["today_event_log"].append(event["msg"])
    if len(gs["today_event_log"]) > 10:
        gs["today_event_log"].pop(0)
    if event["type"] in BAD_EVENT_TYPES:
        gs["bad_streak"] = int(gs.get("bad_streak", 0)) + 1
    elif event["type"] != "none":
        gs["bad_streak"] = 0
    if event["type"] == "gain_df":
        val = event["val"]
        mult = bonus["df"] * (1.25 if (is_star and pet_species == "豹子") else 1.0)
        if mult > 1.001:
            val = max(1, int(round(val * mult)))
        gs["df"] += val
        out_msgs.append(f"积分 +{val}")
    elif event["type"] == "gain_item":
        gs["storehouse"].append(event["item"])
        out_msgs.append(f"获得道具：{event['item']}")
    elif event["type"] == "lose_health":
        health -= event["val"]
        out_msgs.append(f"健康 -{event['val']}")
    elif event["type"] == "gain_hn":
        pet_hn += event["val"]
        out_msgs.append(f"开心值 +{event['val']}")
    elif event["type"] == "lose_ha":
        pet_ha -= event["val"]
        out_msgs.append(f"饱腹值 -{event['val']}")
    elif event["type"] == "lose_cl":
        pet_cl -= event["val"]
        out_msgs.append(f"清洁值 -{event['val']}")
    pet_hn = max(0.0, min(pet_hn, 150))
    pet_ha = max(0.0, min(pet_ha, 150))
    pet_cl = max(0.0, min(pet_cl, 150))
    health = max(0.0, min(health, 150))
# 回写宠物属性
current_pet["hn"] = pet_hn
current_pet["ha"] = pet_ha
current_pet["cl"] = pet_cl
current_pet["health"] = health
current_pet["exp"] = exp
gs["last_auto_hour_time"] = now
# 成就判定
star_pet_count = sum(1 for p in gs["pet_list"] if p.get("is_star", False))
if gs["first_pet_flag"]:
    unlock(gs, 1, out_msgs)
if gs["total_task"] >= 10:
    unlock(gs, 2, out_msgs)
if gs["big_win_flag"] == 1:
    unlock(gs, 3, out_msgs)
if gs["total_feed"] >= 20:
    unlock(gs, 4, out_msgs)
if current_pet["lv"] >= 5:
    unlock(gs, 5, out_msgs)
if gs["total_explore"] >= 10:
    unlock(gs, 6, out_msgs)
if gs["total_explore"] >= 100:
    unlock(gs, 7, out_msgs)
if gs["explore_rare_once_flag"] == 1:
    unlock(gs, 8, out_msgs)
if star_pet_count >= 1:
    unlock(gs, 9, out_msgs)
if star_pet_count >= 3:
    unlock(gs, 10, out_msgs)
if gs["total_star_explore"] >= 50:
    unlock(gs, 11, out_msgs)
if gs["total_star_skill_use"] >= 50:
    unlock(gs, 12, out_msgs)
if len(gs.get("dex", [])) >= 7:
    unlock(gs, 13, out_msgs)
if any(int(p.get("evo_lv", 0) or 0) >= EVO_MAX_LV for p in gs["pet_list"]):
    unlock(gs, 14, out_msgs)
# 自动存档
if gs["auto_save_switch"] == 1:
    save_game(gs)
# ===================== 主界面 =====================
render(hud_block(gs, star_pet_count))
scene_col, panel_col = st.columns([2.85, 1], gap="large")
with scene_col:
    with st.container(key="scene"):
        st.image(room_svg(pet_species, pet_mood(current_pet), is_star,
                          skin_theme(current_pet)), width="stretch")
        _th_now = skin_theme(current_pet)
        if _th_now:
            st.caption(f"小屋主题：{_th_now}（随皮肤自动切换，脱下即回默认小屋）")
with panel_col:
    render(pet_panel_block(gs, current_pet, star_pet_count))
with st.container(key="dock"):
    d1, d2, d3, d4 = st.columns(4, gap="small")
    with d1:
        with st.popover(
            "喂食", key="quick_feed", icon=":material/restaurant:", width="stretch"
        ):
            inv = gs["storehouse"]
            if not inv:
                st.caption("仓库里还没有食物，先去商店买点吧。")
            else:
                feed_item = st.selectbox(
                    "选择食物", inv, key="dock_feed_item",
                    label_visibility="collapsed",
                )
                if st.button(
                    "投喂", key="dock_feed_go", type="primary", width="stretch"
                ):
                    item = feed_item
                    pre_ha = float(current_pet["ha"])
                    inv.remove(item)
                    theory_ha_add = 0
                    feed_exp_mod = bonus["exp"]
                    if is_star and pet_species == "小鸡":
                        feed_exp_mod *= 1.1
                    msg_feed = ""
                    if item == "面包":
                        theory_ha_add = 10
                        current_pet["ha"] += 10
                        msg_feed = "饱腹值 +10"
                    elif item == "电池":
                        if pet_species == "机器人":
                            theory_ha_add = 10 if not is_star else 20
                            current_pet["ha"] += theory_ha_add
                            msg_feed = f"机器人充电，饱腹值 +{theory_ha_add}"
                        else:
                            current_pet["ha"] -= 10
                            theory_ha_add = 0
                            msg_feed = "非机器人吃电池，饱腹值 -10"
                    elif item == "鲜鱼":
                        theory_ha_add = 10
                        current_pet["ha"] += 10
                        if pet_species == "猫":
                            addv = 5
                            if is_star:
                                addv += 5
                            current_pet["ha"] += addv
                            theory_ha_add += addv
                        msg_feed = f"饱腹值 +{theory_ha_add}"
                    elif item == "护发素":
                        current_pet["hn"] += 15
                        msg_feed = "开心值 +15"
                    elif item == "玩具":
                        current_pet["hn"] += 20
                        msg_feed = "开心值 +20"
                    elif item == "葡萄":
                        theory_ha_add = 30
                        current_pet["ha"] += 30
                        msg_feed = "饱腹值 +30"
                    elif item == "零食":
                        current_pet["hn"] += 25
                        msg_feed = "开心值 +25"
                    elif item == "药品":
                        current_pet["health"] += 40
                        msg_feed = "健康值 +40"
                    elif item == "急救针":
                        current_pet["health"] = 50.0
                        msg_feed = "健康值已拉到 50"
                    elif item == "全能营养膏":
                        theory_ha_add = 25
                        current_pet["ha"] += 25
                        current_pet["hn"] += 25
                        current_pet["health"] += 25
                        msg_feed = "饱腹/开心/健康各 +25"
                    elif item == "高级营养液":
                        theory_ha_add = 40
                        current_pet["ha"] += 40
                        current_pet["hn"] += 40
                        current_pet["health"] += 40
                        msg_feed = "饱腹/开心/健康各 +40"
                    elif item == "幸运徽章":
                        inv.append(item)
                        msg_feed = "幸运徽章是被动道具，已放回仓库"
                    elif item == "肥皂":
                        inv.append(item)
                        msg_feed = "肥皂只能在洗澡时使用，已放回仓库"
                    elif item == "除臭喷雾":
                        current_pet["cl"] += 45
                        msg_feed = "清洁值 +45（不占用洗澡冷却）"
                    elif item == "小零食礼包":
                        gifts = random.choices(["零食", "葡萄", "面包", "鲜鱼"], k=2)
                        inv.extend(gifts)
                        msg_feed = f"礼包打开，开出 {' + '.join(gifts)}，已放回仓库"
                    elif item == "经验果":
                        msg_feed = "经验 +35（不影响饱腹）"
                    elif item == "春日花束":
                        current_pet["hn"] += 30
                        msg_feed = "开心值 +30（春天的味道）"
                    elif item == "冰镇西瓜":
                        theory_ha_add = 25
                        current_pet["ha"] += 25
                        current_pet["cl"] += 10
                        msg_feed = "饱腹 +25、清洁 +10"
                    elif item == "丰收南瓜派":
                        theory_ha_add = 30
                        current_pet["ha"] += 30
                        current_pet["health"] += 10
                        msg_feed = "饱腹 +30、健康 +10"
                    elif item == "姜茶":
                        current_pet["health"] += 20
                        current_pet["hn"] += 10
                        msg_feed = "健康 +20、开心 +10"
                    elif item == "宠物强化剂":
                        if current_pet["lv"] >= 10 and not current_pet["is_star"]:
                            current_pet["is_star"] = True
                            current_pet["star_lv"] = 1
                            msg_feed = "星辉觉醒成功！星辉 Lv.1，去「图鉴 · 进化」页可以继续升阶"
                            add_log(f"{current_pet['name']}进化星辉形态", gs["game_log"])
                            dex_add(gs, [f"{pet_species}|star"], out_msgs)
                        else:
                            inv.append(item)
                            msg_feed = "等级不足或已是星辉形态，强化剂已放回仓库"
                    elif item in (STAR_DUST, STAR_CRYSTAL):
                        inv.append(item)
                        msg_feed = "这是进化材料，请到「图鉴」页使用"
                    elif item.startswith("皮肤·"):
                        inv.append(item)
                        msg_feed = "这是皮肤不是食物，请到商店下方「仓库」点穿戴"
                    elif item == "星光皮肤券":
                        if current_pet.get("skin") == "star":
                            current_pet["skin"] = "normal"
                            msg_feed = "已切回普通皮肤"
                        else:
                            current_pet["skin"] = "star"
                            msg_feed = "已换上星辉皮肤（纯外观，数值不变）"
                        add_log(f"{current_pet['name']} 换肤：{current_pet['skin']}", gs["game_log"])
                    if item == "经验果":
                        add_exp = 35.0
                    elif item in ("除臭喷雾", "小零食礼包"):
                        add_exp = 0.0
                    else:
                        add_exp = theory_ha_add / 2 * feed_exp_mod
                    current_pet["exp"] += add_exp
                    current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                    current_pet["ha"] = max(0, min(current_pet["ha"], 150))
                    current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                    current_pet["health"] = max(0, min(current_pet["health"], 150))
                    skip_items = ["肥皂", "幸运徽章", "宠物强化剂", "除臭喷雾", "小零食礼包",
                                  "经验果", STAR_DUST, STAR_CRYSTAL, "星光皮肤券"]
                    is_skin = item.startswith("皮肤·")
                    if not is_skin and item not in skip_items and gs["task_feed_flag"] == 0:
                        tsk = next(x for x in daily_task_list if x["action"] == "feed")
                        if tsk["id"] not in gs["task_finished"]:
                            gs["task_finished"].append(tsk["id"])
                            gs["df"] += tsk["reward"]
                            gs["total_task"] += 1
                            gs["task_feed_flag"] = 1
                    if item not in skip_items and not is_skin:
                        gs["total_feed"] += 1
                        add_log(f"投喂 {item} 给 {current_pet['name']}", gs["game_log"])
                    for m in check_levelup(current_pet, gs["game_log"]):
                        flash(m)
                    verb = "使用" if item in ("除臭喷雾", "小零食礼包", "经验果") else "投喂"
                    flash(f"{verb} {item}：{msg_feed}")
                    # 饱腹接近上限提醒：继续喂只涨经验，属性不再增加
                    if theory_ha_add > 0 and pre_ha >= 145:
                        flash(f"⚠️ 饱腹已接近上限（{pre_ha:.0f}/150），继续投喂仍会增加 {add_exp:.0f} 点经验，"
                              "但饱腹值不会继续上涨")
                    st.rerun()
    with d2:
        if st.button(
            "玩耍", key="act_play", icon=":material/toys:", width="stretch"
        ):
            now_b = datetime.now()
            if now_b - gs["last_play_time"] >= timedelta(hours=2):
                gs["last_play_time"] = now_b
                add_hn = 20
                if is_star and pet_species == "猫":
                    add_hn = 30
                current_pet["hn"] += add_hn
                current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                add_log(f"和宠物玩耍，开心+{add_hn}", gs["game_log"])
                tsk = next(x for x in daily_task_list if x["action"] == "play")
                if tsk["id"] not in gs["task_finished"]:
                    gs["task_finished"].append(tsk["id"])
                    gs["df"] += tsk["reward"]
                    gs["total_task"] += 1
                flash(f"和【{current_pet['name']}】玩耍，开心值 +{add_hn}")
            else:
                remain = timedelta(hours=2) - (now_b - gs["last_play_time"])
                flash(f"玩耍冷却中，还要等 {fmt_wait(remain.total_seconds())}")
            st.rerun()
    with d3:
        if st.button(
            "洗澡", key="act_bath", icon=":material/bathtub:", width="stretch"
        ):
            now_b = datetime.now()
            if now_b - gs["last_bath_time"] >= timedelta(hours=2):
                gs["last_bath_time"] = now_b
                wash_add = 20
                soap_add = 40
                if is_star and pet_species == "小羊":
                    wash_add = 30
                    soap_add = 55
                use_soap = False
                if "肥皂" in gs["storehouse"]:
                    use_soap = True
                    gs["storehouse"].remove("肥皂")
                    current_pet["cl"] += soap_add
                else:
                    current_pet["cl"] += wash_add
                current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                gained = soap_add if use_soap else wash_add
                add_log(f"洗澡，清洁+{gained}", gs["game_log"])
                tsk = next(x for x in daily_task_list if x["action"] == "bath")
                if tsk["id"] not in gs["task_finished"]:
                    gs["task_finished"].append(tsk["id"])
                    gs["df"] += tsk["reward"]
                    gs["total_task"] += 1
                flash(f"给【{current_pet['name']}】洗澡，清洁值 +{gained}")
            else:
                remain = timedelta(hours=2) - (now_b - gs["last_bath_time"])
                flash(f"洗澡冷却中，还要等 {fmt_wait(remain.total_seconds())}")
            st.rerun()
    with d4:
        with st.popover(
            "探索", key="quick_explore", icon=":material/explore:", width="stretch"
        ):
            exp_options = ["短途（10 积分）", "中途（25 积分）", "长途（50 积分）"]
            route = st.radio(
                "选择路线", exp_options, key="dock_route", label_visibility="collapsed"
            )
            if st.button(
                "出发", key="dock_explore_go", type="primary", width="stretch"
            ):
                now_b = datetime.now()
                if now_b - gs["last_explore_time"] < EXPLORE_BASE_COOLDOWN:
                    remain = EXPLORE_BASE_COOLDOWN - (now_b - gs["last_explore_time"])
                    flash(f"探索冷却中，还要等 {fmt_wait(remain.total_seconds())}")
                else:
                    cfg = explore_config[str(exp_options.index(route) + 1)]
                    if gs["df"] < cfg["cost"]:
                        flash("积分不足，无法出发探索")
                    else:
                        gs["df"] -= cfg["cost"]
                        gs["last_explore_time"] = now_b
                        gs["total_explore"] += 1
                        if is_star:
                            gs["total_star_explore"] += 1
                        rare_rate = cfg["rare_rate"]
                        if pet_species == "兔子":
                            rare_rate *= 1.35 if is_star else 1.18
                        if pet_species == "狐狸":
                            rare_rate += 0.03   # 狐狸鼻子灵，容易嗅到稀有事件
                        rare_rate += bonus["rare"]
                        get_rare = random.random() < min(0.98, rare_rate)
                        if get_rare:
                            evt = next(e for e in explore_event_pool if e["rare"])
                        else:
                            pool = [e for e in explore_event_pool if not e["rare"]]
                            evt = random.choice(pool)
                        add_log(f"探索:{evt['msg']}", gs["game_log"])
                        detail = f"探索：{evt['msg']}"
                        if evt["type"] == "gain_df":
                            lo, hi = evt["val_range"]
                            g = random.randint(lo, hi)
                            if bonus["df"] > 1.001:
                                g = max(1, int(round(g * bonus["df"])))
                            gs["df"] += g
                            detail += f"（积分 +{g}）"
                        elif evt["type"] == "gain_item":
                            it = random.choice(evt["item_list"])
                            gs["storehouse"].append(it)
                            detail += f"（获得 {it}）"
                        elif evt["type"] == "gain_rare_item":
                            it = random.choice(evt["item_list"])
                            gs["storehouse"].append(it)
                            gs["explore_rare_once_flag"] = 1
                            detail += f"（获得稀有道具 {it}）"
                        elif evt["type"] == "gain_hn":
                            lo, hi = evt["val_range"]
                            g = random.randint(lo, hi)
                            current_pet["hn"] += g
                            detail += f"（开心 +{g}）"
                        elif evt["type"] == "lose_health":
                            lo, hi = evt["val_range"]
                            ls = random.randint(lo, hi)
                            current_pet["health"] -= ls
                            detail += f"（健康 -{ls}）"
                        elif evt["type"] == "lose_cl":
                            lo, hi = evt["val_range"]
                            ls = random.randint(lo, hi)
                            current_pet["cl"] -= ls
                            detail += f"（清洁 -{ls}）"
                        current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                        current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                        current_pet["health"] = max(0, min(current_pet["health"], 150))
                        # 探索顺手捡到的进化材料
                        if random.random() < 0.30:
                            gs["storehouse"].append(STAR_DUST)
                            detail += "（顺手捡到 星尘）"
                        if get_rare and random.random() < 0.35:
                            gs["storehouse"].append(STAR_CRYSTAL)
                            detail += "（宝箱里还有 星尘结晶）"
                        flash(detail)
                st.rerun()
info_col, task_col = st.columns([1.15, 1], gap="large")
with info_col:
    section("bell", "小屋广播")
    render(messages_block(out_msgs, gs))
with task_col:
    section("task", "今日任务")
    render(tasks_block(gs))
    section("task", "本周任务")
    render(week_block(gs))
    week_prog = week_progress(gs)
    week_ready = [t for t in WEEK_TASK_LIST
                  if week_prog[t["id"]] >= t["target"] and t["id"] not in gs["week_done"]]
    if week_ready:
        if st.button(f"领取周任务奖励（+{sum(t['reward'] for t in week_ready)} 积分）",
                     type="primary", width="stretch"):
            total_r = 0
            for t in week_ready:
                gs["df"] += t["reward"]
                total_r += t["reward"]
                gs["week_done"].append(t["id"])
                add_log(f"完成周任务 {t['name']}，+{t['reward']}", gs["game_log"])
            flash(f"周任务奖励已发放：积分 +{total_r}")
            st.rerun()
    else:
        st.caption("周任务每周一重置，达标后在这里领取奖励。")
tab_shop, tab_fun, tab_star, tab_dex, tab_pet, tab_log = st.tabs(
    ["商店 · 仓库", "彩票 · 医院", "星辉 · 进化", "图鉴", "宠物管理", "日志 · 设置"]
)
with tab_shop:
    section("shop", "商店")
    sd_shop = season_of()
    season_item = sd_shop["shop"]
    shop_list = shop_things + [season_item]
    st.caption(
        f"{sd_shop['name']}限定：{season_item}（还剩 {sd_shop['left_days']} 天换季，"
        f"下一季 {sd_shop['next']} 会换新商品）"
    )
    buy_item = st.selectbox("选购商品", shop_list)
    render(item_card(buy_item))
    if buy_item == season_item:
        st.caption(f"★ 本季限定商品 · {shop_desc.get(season_item, '')}")
    if st.button("购买", type="primary"):
        tsk = next(x for x in daily_task_list if x["action"] == "shop")
        if tsk["id"] not in gs["task_finished"]:
            gs["task_finished"].append(tsk["id"])
            gs["df"] += tsk["reward"]
            gs["total_task"] += 1
        price = price_dict[buy_item]
        if gs["df"] >= price:
            gs["df"] -= price
            gs["storehouse"].append(buy_item)
            if buy_item in DEX_SEASON_ITEMS:
                dex_add(gs, [f"item|{buy_item}"], out_msgs)
            add_log(f"商店购买 {buy_item}", gs["game_log"])
            flash(f"购买成功：{buy_item}（积分 -{price}）")
            st.rerun()
        else:
            st.warning("积分不足！")
    st.divider()
    section("paint", "皮肤")
    st.caption(
        f"皮肤只改外观、不加属性。购买时按当前宠物【{current_pet['name']}·{pet_species}】自动记账，"
        f"买完到仓库「穿戴」，立绘会换成专属配色与光效。售价 {SKIN_PRICE} 积分。"
    )
    for k in SKIN_ORDER:
        st.caption(f"· {k}：{SKIN_THEMES[k]['desc']}")
    skin_pick = st.selectbox("选择皮肤主题", SKIN_ORDER, key="skin_buy")
    skin_item_name = f"皮肤·{skin_pick}·{pet_species}"
    st.caption(f"本次将购买：{skin_item_name}")
    st.image(room_svg(pet_species, pet_mood(current_pet), is_star, skin_pick), width=420)
    st.caption("预览：穿上后立绘和整间小屋都会换成这套主题配色")
    if st.button(f"购买皮肤（{SKIN_PRICE} 积分）", type="primary", width="stretch"):
        if gs["df"] < SKIN_PRICE:
            st.warning("积分不足！")
        else:
            gs["df"] -= SKIN_PRICE
            gs["storehouse"].append(skin_item_name)
            add_log(f"商店购买 {skin_item_name}", gs["game_log"])
            flash(f"购买成功：{skin_item_name}，去仓库穿戴")
            save_game(gs)
            st.rerun()
    st.divider()
    section("box", "仓库")
    render(inventory_block(gs["storehouse"]))
    skin_items = [it for it in dict.fromkeys(gs["storehouse"]) if it.startswith("皮肤·")]
    if skin_items:
        st.divider()
        st.caption("皮肤：穿戴后立绘立刻换装，脱下会退回仓库")
        for s_item in skin_items:
            parts = s_item.split("·")
            if len(parts) != 3:
                continue
            th, sp_of_item = parts[1], parts[2]
            worn = (species_of(current_pet) == sp_of_item
                    and skin_theme(current_pet) == th)
            cnt = gs["storehouse"].count(s_item)
            st.markdown(f"**{s_item}** ×{cnt}" + ("　·　当前已穿戴" if worn else ""))
            c_w, c_u = st.columns(2)
            with c_w:
                if st.button("穿戴", key=f"wear_{s_item}", width="stretch"):
                    if species_of(current_pet) != sp_of_item:
                        st.warning(f"这是 {sp_of_item} 的皮肤，请先切到 {sp_of_item} 宠物")
                    elif worn:
                        st.info("这件已经穿在身上了")
                    else:
                        gs["storehouse"].remove(s_item)
                        old = skin_theme(current_pet)
                        if old:
                            gs["storehouse"].append(f"皮肤·{old}·{sp_of_item}")
                        current_pet["skin"] = th
                        add_log(f"{current_pet['name']} 换上 {s_item}", gs["game_log"])
                        flash(f"{current_pet['name']} 换上了 {th} 皮肤")
                        save_game(gs)
                        st.rerun()
            with c_u:
                if st.button("脱下", key=f"unwear_{s_item}", width="stretch"):
                    if not worn:
                        st.info("当前没穿这件")
                    else:
                        gs["storehouse"].append(s_item)
                        current_pet["skin"] = "normal"
                        add_log(f"{current_pet['name']} 脱下 {s_item}", gs["game_log"])
                        flash(f"{current_pet['name']} 恢复原色")
                        save_game(gs)
                        st.rerun()
    st.caption("点击上方操作栏的【喂食】按钮即可投喂道具。")
    st.divider()
    section("info", "物品说明查询")
    query_item = st.selectbox("选择要查询的道具", shop_things, key="query_item")
    render(item_card(query_item))
    st.caption(f"用途：{shop_desc.get(query_item, '暂无说明')}")
    owned = gs["storehouse"].count(query_item)
    st.caption(f"仓库里目前有 {owned} 个 · 商店售价 {price_dict.get(query_item, 0)} 积分")
# ---------- 彩票医院 ----------
with tab_fun:
    section("ticket", "彩票店")
    lot_options = ["普通彩票（15 积分）", "中级彩票（40 积分）", "高级彩票（100 积分）"]
    lot_sel = st.radio("彩票类型", lot_options)
    lot_idx = lot_options.index(lot_sel)
    st.caption(f"中奖概率：大奖 {LOT_BIG_P}% · 高级奖 {LOT_MID_P}% · 不中奖 {LOT_NONE_P}%")
    if st.button("购买彩票", type="primary"):
        tsk = next(x for x in daily_task_list if x["action"] == "lottery")
        if tsk["id"] not in gs["task_finished"]:
            gs["task_finished"].append(tsk["id"])
            gs["df"] += tsk["reward"]
            gs["total_task"] += 1
        win_big = False
        res_text = ""
        # 概率固定：大奖 5%、高级奖 30%、不中奖 65%
        cost = [15, 40, 100][lot_idx]
        small_amt = [20, 60, 150][lot_idx]
        big_amt = [50, 120, 300][lot_idx]
        big_p = LOT_BIG_P
        if gs["df"] >= cost:
            gs["df"] -= cost
            r = random.randint(1, 100)
            if r <= big_p:
                gs["df"] += big_amt
                res_text = f"中大奖，积分 +{big_amt}"
                win_big = True
            elif r <= big_p + LOT_MID_P:
                gs["df"] += small_amt
                res_text = f"高级奖，积分 +{small_amt}"
            else:
                res_text = "没有中奖"
        else:
            res_text = "积分不足"
        if win_big:
            gs["big_win_flag"] = 1
            add_log("彩票中大奖", gs["game_log"])
        add_log(f"彩票结果:{res_text}", gs["game_log"])
        if "积分不足" not in res_text:
            gs["total_lottery"] = int(gs.get("total_lottery", 0)) + 1
            lot_name = ["普通", "中级", "高级"][lot_idx]
            gs.setdefault("lottery_history", []).append(
                f"{datetime.now().strftime('%m-%d %H:%M')} · {lot_name}彩票 · {res_text}"
            )
            gs["lottery_history"] = gs["lottery_history"][-5:]
        flash(f"彩票结果：{res_text}")
        st.rerun()
    hist = gs.get("lottery_history", [])
    if hist:
        st.caption("最近 5 次战果")
        for h in reversed(hist):
            st.caption(f"· {h}")
    else:
        st.caption("还没有买过彩票，历史记录会出现在这里。")
    st.divider()
    section("hospital", "宠物医院")
    h_options = ["基础治疗（30 积分 · 健康 +40）",
                 "深度治疗（80 积分 · 健康 +100）",
                 "ICU 急救（150 积分 · 健康拉满）"]
    h_sel = st.radio("治疗项目", h_options)
    h_idx = h_options.index(h_sel)
    if st.button("执行治疗", type="primary"):
        healed = False
        if h_idx == 0:
            c, h = 30, 40
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] += h
                healed = True
        elif h_idx == 1:
            c, h = 80, 100
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] += h
                healed = True
        else:
            c = 150
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] = 150.0
                healed = True
        current_pet["health"] = max(0, min(current_pet["health"], 150))
        add_log(f"医院治疗，health={current_pet['health']:.1f}", gs["game_log"])
        if healed:
            flash(f"治疗完成，当前健康值 {current_pet['health']:.1f}")
        else:
            flash("积分不足，治疗取消")
        st.rerun()
with tab_star:
    section("gem", "星辉等级")
    st.caption("星辉不再是“觉醒就拥有全部”，而是 1~10 级逐级增强：衰减更低、经验更多、护体更早生效。")
    if not is_star:
        st.warning("当前宠物还不是星辉形态。10 级后使用「宠物强化剂」觉醒，等级从 Lv.1 开始。")
    else:
        slv = max(1, int(current_pet.get("star_lv", 1) or 1))
        st.markdown(f"**{current_pet['name']}** · 星辉 Lv.**{slv}** / {STAR_MAX_LV}")
        st.caption(bonus_summary(current_pet))
        st.progress(min(1.0, slv / STAR_MAX_LV))
        if slv >= STAR_MAX_LV:
            st.success("星辉已满级 Lv.10：衰减 ×0.60、经验 ×1.30、健康回复 2 倍、护体常驻。")
        else:
            dust_need, df_need = star_up_cost(slv)
            have_dust = gs["storehouse"].count(STAR_DUST)
            st.caption(
                f"升到 Lv.{slv + 1} 需要：星尘 ×{dust_need}（现有 {have_dust}）、积分 {df_need}。"
                f"星尘可从探索稀有宝箱拾得，也可在商店购买。"
            )
            if st.button(f"升级星辉 → Lv.{slv + 1}", type="primary", width="stretch"):
                if have_dust < dust_need:
                    st.warning(f"星尘不足，还差 {dust_need - have_dust} 个")
                elif gs["df"] < df_need:
                    st.warning(f"积分不足，需要 {df_need} 积分")
                else:
                    for _ in range(dust_need):
                        gs["storehouse"].remove(STAR_DUST)
                    gs["df"] -= df_need
                    current_pet["star_lv"] = slv + 1
                    add_log(f"{current_pet['name']} 星辉升至 Lv.{slv + 1}", gs["game_log"])
                    flash(f"星辉升至 Lv.{slv + 1}：{bonus_summary(current_pet)}")
                    save_game(gs)
                    st.rerun()
    st.divider()
    section("skill", "星辉技能")
    st.caption("只有星辉形态的宠物才能释放技能，技能有独立冷却时间；数值随星辉等级提高。")
    sl_a = max(1, int(bonus["star_lv"]))
    skill_options = [
        f"星沐（40 分钟 · 开心/饱腹/清洁 +{30 + 2 * (sl_a - 1)}）",
        f"星愈（60 分钟 · 健康 +{60 + 4 * (sl_a - 1)}）",
        f"星满（50 分钟 · 全属性 +{20 + (sl_a - 1)}）",
        f"星启（120 分钟 · 好事 {3 + sl_a // 4} 次）",
    ]
    skill_sel = st.radio("技能", skill_options)
    skill_idx = skill_options.index(skill_sel)
    if st.button("释放技能", type="primary"):
        if not is_star:
            st.warning("当前宠物不是星辉形态！")
        else:
            now_b = datetime.now()
            if skill_idx == 0:
                if now_b >= gs["star_skill_cd"]["star_mu"]:
                    gs["star_skill_cd"]["star_mu"] = now_b + timedelta(minutes=40)
                    gs["total_star_skill_use"] += 1
                    mu_amt = 30 + 2 * (bonus["star_lv"] - 1)
                    current_pet["hn"] += mu_amt
                    current_pet["ha"] += mu_amt
                    current_pet["cl"] += mu_amt
                    current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                    current_pet["ha"] = max(0, min(current_pet["ha"], 150))
                    current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                    add_log("释放星辉技能【星沐】", gs["game_log"])
                    flash(f"释放星辉技能【星沐】：开心 / 饱腹 / 清洁各 +{mu_amt}")
                    st.rerun()
                else:
                    rem = gs["star_skill_cd"]["star_mu"] - now_b
                    st.warning(f"冷却剩余 {rem.total_seconds() / 60:.1f} 分钟")
            elif skill_idx == 1:
                if now_b >= gs["star_skill_cd"]["star_heal"]:
                    gs["star_skill_cd"]["star_heal"] = now_b + timedelta(minutes=60)
                    gs["total_star_skill_use"] += 1
                    heal_amt = 60 + 4 * (bonus["star_lv"] - 1)
                    current_pet["health"] += heal_amt
                    current_pet["health"] = max(0, min(current_pet["health"], 150))
                    add_log("释放星辉技能【星愈】", gs["game_log"])
                    flash(f"释放星辉技能【星愈】：健康 +{heal_amt}")
                    st.rerun()
                else:
                    rem = gs["star_skill_cd"]["star_heal"] - now_b
                    st.warning(f"冷却剩余 {rem.total_seconds() / 60:.1f} 分钟")
            elif skill_idx == 2:
                if now_b >= gs["star_skill_cd"]["star_full"]:
                    gs["star_skill_cd"]["star_full"] = now_b + timedelta(minutes=50)
                    gs["total_star_skill_use"] += 1
                    full_amt = 20 + (bonus["star_lv"] - 1)
                    current_pet["hn"] += full_amt
                    current_pet["ha"] += full_amt
                    current_pet["cl"] += full_amt
                    current_pet["health"] += full_amt
                    current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                    current_pet["ha"] = max(0, min(current_pet["ha"], 150))
                    current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                    current_pet["health"] = max(0, min(current_pet["health"], 150))
                    add_log("释放星辉技能【星满】", gs["game_log"])
                    flash(f"释放星辉技能【星满】：全属性 +{full_amt}")
                    st.rerun()
                else:
                    rem = gs["star_skill_cd"]["star_full"] - now_b
                    st.warning(f"冷却剩余 {rem.total_seconds() / 60:.1f} 分钟")
            else:
                if now_b >= gs["star_skill_cd"]["star_goodluck"]:
                    gs["star_skill_cd"]["star_goodluck"] = now_b + timedelta(minutes=120)
                    gs["total_star_skill_use"] += 1
                    gs["star_skill_cd"]["goodluck_stack"] = 3 + bonus["star_lv"] // 4
                    add_log("释放星辉技能【星启】", gs["game_log"])
                    flash(f"释放星辉技能【星启】：接下来 {gs['star_skill_cd']['goodluck_stack']} 次随机事件更偏向好事")
                    st.rerun()
                else:
                    rem = gs["star_skill_cd"]["star_goodluck"] - now_b
                    st.warning(f"冷却剩余 {rem.total_seconds() / 60:.1f} 分钟")
with tab_dex:
    section("trophy", "图鉴")
    dex_set = set(gs.get("dex", []))
    got_n = len([k for k in DEX_ALL_KEYS if k in dex_set])
    st.caption(
        f"已点亮 {got_n}/{DEX_TOTAL} 格 · 点亮即 +5 积分，成组另有奖励 · "
        "只要曾经拥有就会记录，不需要一直留着宠物"
    )
    st.progress(min(1.0, got_n / DEX_TOTAL))
    for cat in PET_CATEGORIES:
        cat_pets = [sp for sp in cat["pets"] if sp in PET_SPECIES]
        cat_lit = len([1 for sp in cat_pets for k in ("normal", "star")
                       if f"{sp}|{k}" in dex_set])
        render(
            f'<div class="dex-cat dex-{cat["key"]}">'
            f'<span class="dex-cat-name">{cat["name"]}</span>'
            f'<span class="dex-cat-desc">{cat["desc"]} · {len(cat_pets)} 种 · '
            f'点亮 {cat_lit}/{len(cat_pets) * 2}</span></div>'
        )
        for row_start in range(0, len(cat_pets), 6):
            cols = st.columns(6)
            for c, sp in zip(cols, cat_pets[row_start:row_start + 6]):
                with c:
                    for skin in ("normal", "star"):
                        key = f"{sp}|{skin}"
                        if key in dex_set:
                            st.image(pet_svg(sp, "happy", skin == "star"), width=64)
                        else:
                            st.markdown('<div class="dex-lock">?</div>', unsafe_allow_html=True)
                        st.caption(f"{sp}·{'星辉' if skin == 'star' else '普通'}")
    st.caption("限定区（四季商品，买过或拿到过即点亮）")
    scols = st.columns(len(DEX_SEASON_ITEMS))
    for c, it in zip(scols, DEX_SEASON_ITEMS):
        with c:
            key = f"item|{it}"
            if key in dex_set:
                st.markdown(
                    f'<div class="dex-item on">{icon(_ITEM_ICON.get(it, "box"), 26, "#9A6A1E")}'
                    f'<span>{it}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="dex-lock">?</div>', unsafe_allow_html=True)
            st.caption(it if key in dex_set else "未点亮")
    st.divider()
    section("paw", "进化方向（三选一）")
    st.caption("三个方向与五种元素全部列在这里；未进化时点「进化」，进化之后仍可花积分更换。")
    cur_branch = current_pet.get("evo_branch") or ""
    cur_elem = current_pet.get("element") or ""
    for name in EVO_ORDER:
        info = EVO_BRANCHES[name]
        now_mark = "【当前】" if name == cur_branch else ""
        st.caption(
            f"{now_mark}{name}（{info['tag']}）：{info['desc']}"
            f"　优：{info['pro']}　代价：{info['con']}"
        )
    branch_default = EVO_ORDER.index(cur_branch) if cur_branch in EVO_ORDER else 0
    branch_pick = st.radio("选择进化方向", EVO_ORDER, index=branch_default,
                           horizontal=True, key="dex_branch")
    st.divider()
    section("element", "五行元素（五选一）")
    for k in ELEMENT_ORDER:
        info = ELEMENTS[k]
        now_mark = "【当前】" if k == cur_elem else ""
        st.caption(f"{now_mark}{k}·{info['tag']}：{info['pro']}　代价：{info['con']}")
    elem_default = ELEMENT_ORDER.index(cur_elem) if cur_elem in ELEMENT_ORDER else 0
    elem_pick = st.radio("选择五行元素", ELEMENT_ORDER, index=elem_default,
                         horizontal=True, key="dex_elem")
    evo_lv = int(current_pet.get("evo_lv", 0) or 0)
    have_c = gs["storehouse"].count(STAR_CRYSTAL)
    if not is_star:
        st.caption("当前宠物还未觉醒星辉，进化暂不开放（先升到 10 级并使用宠物强化剂）。")
    elif evo_lv == 0:
        gate, cc = EVO_LV_GATE[1], EVO_LV_COST[1]
        st.caption(f"进化到 1 阶：需要 Lv.{gate}、星尘结晶 ×{cc}（现有 {have_c}）")
        if st.button(f"进化 · {branch_pick} · {elem_pick}元素", type="primary", width="stretch"):
            if current_pet["lv"] < gate:
                st.warning(f"宠物等级不足，需要 Lv.{gate}")
            elif have_c < cc:
                st.warning(f"星尘结晶不足，还需要 {cc - have_c} 枚")
            else:
                for _ in range(cc):
                    gs["storehouse"].remove(STAR_CRYSTAL)
                current_pet["evo_branch"] = branch_pick
                current_pet["element"] = elem_pick
                current_pet["evo_lv"] = 1
                add_log(f"{current_pet['name']} 进化为【{branch_pick}·{elem_pick}】1 阶", gs["game_log"])
                flash(f"进化成功：【{current_pet['name']}】{branch_pick}·{elem_pick}元素 1 阶")
                save_game(gs)
                st.rerun()
    else:
        st.caption(f"当前：{cur_branch} · {cur_elem}元素 · {evo_lv}/{EVO_MAX_LV} 阶")
        if evo_lv < EVO_MAX_LV:
            nxt = evo_lv + 1
            gate, cc = EVO_LV_GATE[nxt], EVO_LV_COST[nxt]
            st.caption(f"升到 {nxt} 阶：需要 Lv.{gate}、星尘结晶 ×{cc}（现有 {have_c}）")
            if st.button(f"升阶 → {nxt} 阶", type="primary", width="stretch"):
                if current_pet["lv"] < gate:
                    st.warning(f"宠物等级不足，需要 Lv.{gate}")
                elif have_c < cc:
                    st.warning(f"星尘结晶不足，还需要 {cc - have_c} 枚")
                else:
                    for _ in range(cc):
                        gs["storehouse"].remove(STAR_CRYSTAL)
                    current_pet["evo_lv"] = nxt
                    add_log(f"{current_pet['name']} 进化阶数升至 {nxt}", gs["game_log"])
                    flash(f"进化阶数升至 {nxt}/{EVO_MAX_LV}")
                    save_game(gs)
                    st.rerun()
        else:
            st.success("已是 5 阶满阶；方向与元素仍可更换。")
        if branch_pick != cur_branch:
            if st.button(f"更换方向 → {branch_pick}（-{ELEM_RESET_COST} 积分）", width="stretch"):
                if gs["df"] < ELEM_RESET_COST:
                    st.warning("积分不足")
                else:
                    gs["df"] -= ELEM_RESET_COST
                    current_pet["evo_branch"] = branch_pick
                    add_log(f"{current_pet['name']} 方向更换 {cur_branch} → {branch_pick}", gs["game_log"])
                    flash(f"方向已更换为 {branch_pick}（阶数保持 {evo_lv}）")
                    save_game(gs)
                    st.rerun()
        if elem_pick != cur_elem:
            if st.button(f"更换元素 → {elem_pick}（-{ELEM_RESET_COST} 积分）", width="stretch"):
                if gs["df"] < ELEM_RESET_COST:
                    st.warning("积分不足")
                else:
                    gs["df"] -= ELEM_RESET_COST
                    current_pet["element"] = elem_pick
                    add_log(f"{current_pet['name']} 元素更换 {cur_elem} → {elem_pick}", gs["game_log"])
                    flash(f"元素已更换为 {elem_pick}")
                    save_game(gs)
                    st.rerun()

    ready = dex_ready_groups(gs)
    st.divider()
    if ready:
        names = "、".join(g["name"] for g in ready)
        total_r = sum(g["reward"] for g in ready)
        st.caption(f"可领取：{names}")
        if st.button(f"领取图鉴组奖励（+{total_r} 积分）", type="primary", width="stretch"):
            for g in ready:
                dex_claim(gs, g["gid"], out_msgs)
            flash(f"图鉴奖励已发放 {len(ready)} 组，积分 +{total_r}")
            st.rerun()
    else:
        st.caption(
            f"组奖励：{len(PET_SPECIES)} 组双皮肤各 +30 · 集齐全物种双皮肤 +100 · "
            "集齐四季限定 +80 · 满册 +200"
        )
    st.caption("图鉴点亮来源：领养（普通）、星辉觉醒（星辉）、购买或获得季节限定商品。")
    st.divider()
    section("element", "进化方向（全部显示）")
    st.caption("三条方向都列在这里，进化操作在「星辉 · 进化」页完成；每阶增益更大，副作用固定。")
    for name in EVO_ORDER:
        info = EVO_BRANCHES[name]
        st.markdown(f"**{info['name']}（{info['tag']}）**  {info['desc']}")
        st.caption(f"　主增益：{info['pro']}　｜　代价：{info['con']}")
        st.caption("　" + "　".join(
            f"{lv} 阶：需 Lv.{EVO_LV_GATE[lv]} + 结晶 {EVO_LV_COST[lv]}"
            for lv in range(1, EVO_MAX_LV + 1)))
    st.divider()
    section("element", "五行元素（全部显示）")
    st.caption("进化时选一种元素，优点与代价同时生效；30 积分可重塑。")
    for k in ELEMENT_ORDER:
        el = ELEMENTS[k]
        st.markdown(f"**{el['name']}（{el['tag']}）**")
        st.caption(f"　优点：{el['pro']}　｜　代价：{el['con']}")
    st.divider()
    section("paw", "我的宠物进化状态")
    for p in gs["pet_list"]:
        nm = _short_name(p.get("name", "?"))
        if p.get("is_star"):
            head = f"星辉 Lv.{int(p.get('star_lv', 1) or 1)}"
            if p.get("evo_branch"):
                body = (f"{p['evo_branch']} · {p.get('element') or '无'}元素 · "
                        f"{int(p.get('evo_lv', 0))}/{EVO_MAX_LV} 阶")
            else:
                body = "尚未进化（25 级 + 星尘结晶可进化）"
            st.markdown(f"**{nm}**（{species_of(p)}）：{head}　｜　{body}")
        else:
            st.caption(f"{nm}（{species_of(p)}）：普通形态，星辉觉醒后才能进化")
with tab_pet:
    section("paw", "切换宠物")
    pet_names = [
        f"{i}. {p['name']}{'（星辉）' if p.get('is_star', False) else ''}"
        for i, p in enumerate(gs["pet_list"])
    ]
    sel_idx = st.selectbox(
        "选择要切换的宠物（3 分钟冷却）",
        options=list(range(len(pet_names))),
        index=min(gs["current_pet_idx"], len(pet_names) - 1),
        format_func=lambda x: pet_names[x],
    )
    sel_pet = gs["pet_list"][sel_idx]
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image(pet_art(sel_pet), width=76)
    with col_b:
        st.markdown(f"**{sel_pet['name']}**")
        st.caption(
            f"{PET_LABEL.get(species_of(sel_pet), '')} · Lv.{sel_pet['lv']} · "
            f"开心 {sel_pet['hn']:.1f} · 饱腹 {sel_pet['ha']:.1f}"
        )
    if st.button("确认切换", type="primary"):
        now_b = datetime.now()
        if now_b - gs["last_switch_pet_time"] >= timedelta(minutes=3):
            gs["current_pet_idx"] = sel_idx
            gs["last_switch_pet_time"] = now_b
            add_log(f"切换宠物至 {gs['pet_list'][sel_idx]['name']}", gs["game_log"])
            flash(f"已切换到【{gs['pet_list'][sel_idx]['name']}】")
            st.rerun()
        else:
            st.warning("切换宠物冷却中")
    st.divider()
    section("paw", "领养新宠物")
    new_pet_sel = st.selectbox(
        "领养新宠物（80 积分）", PET_SPECIES,
        format_func=lambda sp: f"{PET_CATEGORY_OF.get(sp, '')} · {PET_LABEL.get(sp, sp)}",
    )
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image(pet_svg(new_pet_sel, "happy", False), width=76)
    with col_b:
        st.markdown(f"**{new_pet_sel}**")
        st.caption("等级 1 · 初始属性 100")
    if st.button("领养", type="primary"):
        cost = 80
        if gs["df"] >= cost:
            gs["df"] -= cost
            np = {"name": new_pet_sel, "species": new_pet_sel, "lv": 1,
                  "hn": 100.0, "ha": 100.0, "cl": 100.0, "health": 150.0,
                  "exp": 0.0, "is_star": False,
                  "star_lv": 0, "evo_branch": "", "evo_lv": 0, "element": ""}
            gs["pet_list"].append(np)
            dex_add(gs, [f"{new_pet_sel}|normal"], out_msgs)
            add_log(f"领养新宠物 {new_pet_sel}", gs["game_log"])
            flash(f"领养新宠物：【{new_pet_sel}】，花费 80 积分")
            st.rerun()
        else:
            st.warning("积分不足 80！")
    st.divider()
    section("paw", "改名与存档")
    new_name = st.text_input("给当前宠物改名", value=current_pet["name"])
    st.caption(f"改名消耗 {RENAME_COST} 积分（改名后自动写入存档）")
    if st.button("确认改名", type="primary"):
        old = current_pet["name"]
        new_name_clean = strip_emoji(new_name).strip()
        if not new_name_clean:
            st.warning("名字不能为空")
        elif new_name_clean == old:
            st.info("名字没有变化，不扣积分")
        elif gs["df"] < RENAME_COST:
            st.warning(f"积分不足，改名需要 {RENAME_COST} 积分")
        else:
            new_name_clean = new_name_clean[:18]
            gs["df"] -= RENAME_COST
            current_pet["name"] = new_name_clean
            add_log(f"改名 {old} -> {new_name_clean}（-{RENAME_COST} 积分）", gs["game_log"])
            save_game(gs)
            flash(f"改名成功：{old} -> {new_name_clean}（积分 -{RENAME_COST}）")
            st.rerun()
    if st.button("手动存档"):
        ok, msg = save_game(gs)
        st.success(msg if ok else msg)
    st.caption(f"存档位置：{SAVE_PATH}")
with tab_log:
    section("log", "游戏日志")
    render(log_block(gs["game_log"]))
    st.divider()
    section("gear", "设置")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("切换随机事件开关"):
            gs["rand_event_switch"] = 1 - gs["rand_event_switch"]
            st.rerun()
    with col_b:
        if st.button("切换自动存档开关"):
            gs["auto_save_switch"] = 1 - gs["auto_save_switch"]
            st.rerun()
    next_evt = gs.get("last_rand_event_time", datetime.now()) + RAND_EVENT_INTERVAL
    if gs["rand_event_switch"] == 1:
        left = (next_evt - datetime.now()).total_seconds()
        if left > 0:
            st.caption(f"随机事件每 {RAND_EVENT_INTERVAL.seconds // 3600} 小时最多触发一次"
                       f"，下一次约 {fmt_wait(left)} 后")
        else:
            st.caption(f"随机事件每 {RAND_EVENT_INTERVAL.seconds // 3600} 小时最多触发一次"
                       "，下一次触发已就绪（刷新页面即可能触发）")
    else:
        st.caption("随机事件当前已关闭，历史触发节奏不受影响")
    st.divider()
    section("star", "季节")
    sd_tab = season_of()
    st.markdown(f"**{sd_tab['name']}**（第 {sd_tab['day_in_season']}/{SEASON_DAYS} 天）· {sd_tab['note']}")
    st.caption(
        f"衰减系数：饱腹 ×{sd_tab['ha']}、清洁 ×{sd_tab['cl']}、开心 ×{sd_tab['hn']}　|　"
        f"本季限定商品：{sd_tab['shop']}　|　剩 {sd_tab['left_days']} 天后进入{sd_tab['next']}季"
    )
    st.divider()
    section("bell", "今日事件")
    todays = gs.get("today_event_log", [])
    if todays:
        for e in reversed(todays):
            st.caption(f"· {e}")
    else:
        st.caption("今天还没有触发随机事件（每 2 小时最多一次）。")
    st.divider()
    section("info", "帮助 · 规则说明")
    with st.expander("展开查看全部规则", expanded=False):
        st.markdown(
            "- **经验**：投喂按饱腹增量的一半折算经验（星辉 ×1.25，星辉小鸡 ×1.4）；"
            "经验果直接 +35。升级所需经验 = 当前等级 × 50。\n"
            "- **衰减**：饱腹每分钟约 -0.5、清洁 -0.03；开心低于 75 / 清洁低于 60 时开心额外下降。"
            "星辉整体衰减 ×0.6，星辉机器人 ×0.4，小羊清洁半速。\n"
            "- **心情标签**：开心 ≥130「超开心」，衰减 ×0.85、随机事件更偏好事；"
            "开心 <30「郁闷」，衰减 ×1.15、更容易踩坑。\n"
            "- **健康**：低于 125/100/50 逐档加速下降；健康 30~50 每分钟缓慢掉经验，<30 掉得更快"
            "（星辉不受 <30 惩罚）。四项均 ≥80 时健康自动回升。\n"
            "- **冷却**：玩耍 / 洗澡各 2 小时，探索 30 分钟，切换宠物 3 分钟，"
            "随机事件 2 小时最多一次；星辉技能各自独立冷却。\n"
            "- **签到**：连续签到第 1/2/3… 天分别 10/15/20…（上限 30），断签重置为 10。\n"
            "- **周任务**：每周重置，达标后在「本周任务」下方领取。\n"
            "- **彩票**：普通 15 / 中级 40 / 高级 100 积分；概率固定为大奖 5%、高级奖 30%、"
            "不中奖 65%，中奖金额 20~300 积分不等；最近 5 次结果可在彩票店回看。\n"
            "- **季节**：每 7 天循环 春→夏→秋→冬。春季开心衰减 ×0.95；夏季清洁衰减 ×1.5；"
            "秋季饱腹衰减 ×0.8；冬季饱腹 ×1.5、开心 ×1.1。每季有对应专属随机事件和一件"
            "限定商品，换季后商品会轮换。\n"
            "- **星辉**：10 级后使用宠物强化剂觉醒，觉醒即为星辉 Lv.1；星辉最高 10 级，"
            "每级消耗「星尘」并需要积分，等级越高衰减越低、经验越多、健康回复越强，"
            "4 级起健康低于 30 时获得护体（不再快速掉经验）。\n"
            "- **进化**：宠物 25 级、持有「星尘结晶」时可选择进化方向（战意 / 守护 / 灵能），"
            "每个方向 5 阶，门槛依次为 25/30/35/40/45 级、材料 1~5 枚；主增益随阶数递增，"
            "副作用固定——战意衰减 ×1.15，守护经验 -10%，灵能饱腹衰减 ×1.25。"
            "方向与元素在「星辉 · 进化」页选择，图鉴页可以查看全部方向与元素说明，"
            "进化后还可以花 30 积分更换元素。\n"
            "- **五行元素**：金木水火土各有优点与代价：金 经验 +12%/开心衰减 +12%；"
            "木 健康回复 +25%/清洁衰减 +15%；水 清洁衰减 -25%/饱腹衰减 +12%；"
            "火 开心衰减 -20%/健康流失 +10%；土 饱腹衰减 -20%/开心衰减 +15%。\n"
            "- **皮肤**：商店「皮肤」100 积分，购买时自动按当前宠物的物种记账（皮肤·主题·物种），"
            "在仓库点「穿戴」即可换装，立绘会换成专属配色与光效，整间小屋的墙纸、地板、地毯、"
            "木色家具与窗户天空也会同步换成该主题的配色（夜行主题是夜空带星），脱下退回仓库。"
            "旧的「星光皮肤券」仍可给任意宠物换上星辉外观。\n"
            "- **宠物特性**：一共 40 只可领养，图鉴分机械类 / 萌宠类 / 神话类 / 游戏类 / 美食类 五类。"
            "猫吃鲜鱼额外回饱腹、星辉猫玩耍 +30 开心；"
            "机器人吃电池才回饱腹（星辉 +20）且清洁衰减 ×0.7；小羊清洁衰减减半；"
            "小鸡星辉喂食经验 ×1.1；豹子星辉积分 ×1.25；兔子探索稀有率 ×1.18（星辉 ×1.35）；"
            "仓鼠饱腹衰减 -10%；狐狸探索稀有率 +3%；企鹅清洁衰减 -10%；"
            "青蛙心情衰减 -8%；小熊健康回复 +15%；"
            "机械蜂清洁衰减 ×0.85；小鹿心情衰减 -5%；小龙健康回复 +10%；"
            "史莱姆饱腹衰减 -10%；布丁心情衰减 -5%；"
            "机械鼠清洁衰减 ×0.85；机甲兔心情衰减 -5%；小鸭清洁衰减 -10%；"
            "熊猫心情衰减 -10%；小狼饱腹衰减 -8%；小马饱腹衰减 -12%；"
            "独角兽心情衰减 -7%；麒麟健康回复 +12%；豆豆心情衰减 -6%；"
            "蘑菇仔清洁衰减 -8%；甜甜圈心情衰减 -5%；饭团饱腹衰减 -10%；"
            "机甲龟清洁衰减 -10%；机械狮心情衰减 -6%；小刺猬饱腹衰减 -7%；"
            "小猪饱腹衰减 -10%；小松鼠心情衰减 -5%；凤凰健康回复 +15%；"
            "貔貅心情衰减 -8%；方块仔清洁衰减 -10%；炸弹仔心情衰减 -8%；"
            "小笼包饱腹衰减 -8%；冰淇淋心情衰减 -6%。\n"
            "- **图鉴**：84 格（40 物种 × 普通/星辉 + 4 件季节限定），按五类分栏展示。"
            "点亮即 +5 积分，双皮肤齐 +30，四十物种齐 +100，四季限定齐 +80，满册 +200。曾拥有即点亮。\n"
        )
    st.divider()
    section("trophy", "成就")
    render(achievements_block(gs))
    st.divider()
    section("paw", "全部宠物一览")
    for idx, p in enumerate(gs["pet_list"]):
        c_img, c_txt = st.columns([1, 5])
        with c_img:
            st.image(pet_art(p), width=72)
        with c_txt:
            star_mark = ""
            if p.get("is_star", False):
                star_mark = f" · 星辉 Lv.{int(p.get('star_lv', 1) or 1)}"
                if p.get("evo_branch"):
                    star_mark += f" · {p['evo_branch']}·{p.get('element') or '无'} {int(p.get('evo_lv', 0))}/5"
            st.markdown(
                f"**{p['name']}**（{species_of(p)}） · Lv.{p['lv']}{star_mark}"
            )
            st.caption(
                f"开心 {p['hn']:.1f} · 饱腹 {p['ha']:.1f} · "
                f"清洁 {p['cl']:.1f} · 健康 {p['health']:.1f}"
            )
st.divider()
st.caption("提示：关闭终端窗口会停止游戏，仅关闭网页标签程序仍在后台运行；存档文件 player_pet.txt 保存在程序同级目录")