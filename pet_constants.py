# -*- coding: utf-8 -*-
"""pet_constants（从单文件 pet_web.py 拆出，逻辑未改）。"""
import hashlib
import re
from datetime import date, datetime, timedelta
import random

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


random_event_list = [
    {"name": "捡到积分", "type": "gain_df",
        "msg": "出门散步，在路边捡到了一些积分！", "val_range": (15, 40)},
    {"name": "捡到药品", "type": "gain_item", "msg": "草丛里发现了一瓶药品！", "item": "药品"},
    {"name": "捡到急救针", "type": "gain_item", "msg": "运气不错，捡到一支急救针！", "item": "急救针"},
    {"name": "捡到全能营养膏", "type": "gain_item",
        "msg": "发现一支未拆封的全能营养膏！", "item": "全能营养膏"},
    {"name": "宠物突然生病", "type": "lose_health",
        "msg": "宠物突然不舒服，健康下降！", "val_range": (15, 30)},
    {"name": "偶遇好心人", "type": "gain_df",
        "msg": "好心人送给你一些积分！", "val_range": (20, 50)},
    {"name": "宠物开心蹦跶", "type": "gain_hn",
        "msg": "宠物看到蝴蝶，开心值上升！", "val_range": (10, 25)},
    {"name": "宠物饿了", "type": "lose_ha",
        "msg": "宠物肚子饿了，饱腹下降！", "val_range": (10, 20)},
    {"name": "下雨弄脏了", "type": "lose_cl",
        "msg": "下雨踩泥坑，清洁值下降！", "val_range": (10, 25)},
    {"name": "无事发生", "type": "none", "msg": "平平淡淡的一天，没有特殊事情。"}
]

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
    {"aid": 1, "title": "初次相伴", "desc": "解锁你的第一只宠物", "cond": "first_pet", "reward": {'df': 20}},
    {"aid": 2, "title": "勤劳铲屎官", "desc": "累计完成10次每日任务", "cond": "task10", "reward": {'df': 30}},
    {"aid": 3, "title": "幸运之星", "desc": "彩票中一次大奖", "cond": "lottery_win", "reward": {'df': 50}},
    {"aid": 4, "title": "喂养达人", "desc": "累计投喂20次", "cond": "feed20", "reward": {'df': 30}},
    {"aid": 5, "title": "成长伙伴", "desc": "宠物升到5级", "cond": "lv5", "reward": {'df': 40}},
    {"aid": 6, "title": "初探秘境", "desc": "累计完成10次探索", "cond": "explore10", "reward": {'df': 30}},
    {"aid": 7, "title": "寻踪不倦", "desc": "累计完成100次探索", "cond": "explore100", "reward": {'df': 80}},
    {"aid": 8, "title": "秘境欧皇", "desc": "探索时拿到稀有宝箱奖励", "cond": "explore_rare_once", "reward": {'df': 60, 'items': [['星尘结晶', 1]]}},
    {"aid": 9, "title": "星辉觉醒", "desc": "将一只宠物转化为星辉形态", "cond": "star_awake", "reward": {'df': 60}},
    {"aid": 10, "title": "群星同行", "desc": "拥有3只星辉宠物", "cond": "star_3pet", "reward": {'df': 80}},
    {"aid": 11, "title": "星途无尽", "desc": "使用星辉宠物完成50次探索", "cond": "star_explore50", "reward": {'df': 100}},
    {"aid": 12, "title": "星能掌控者", "desc": "累计释放星辉技能50次", "cond": "star_skill50", "reward": {'df': 100, 'items': [['宠物强化剂', 1]]}},
    {"aid": 13, "title": "图鉴初成", "desc": "点亮 7 格图鉴", "cond": "dex7", "reward": {'df': 40}},
    {"aid": 14, "title": "五行归一", "desc": "任意宠物进化到 5 阶", "cond": "evo5", "reward": {'df': 100, 'items': [['星尘', 3]]}},
    {"aid": 15, "title": "收集起步", "desc": "图鉴点亮 25%", "cond": "dex_quarter", "reward": {'df': 40}},
    {"aid": 16, "title": "半册在手", "desc": "图鉴点亮 50%", "cond": "dex_half", "reward": {'df': 60}},
    {"aid": 17, "title": "博物学家", "desc": "图鉴点亮 75%", "cond": "dex_3q", "reward": {'df': 80}},
    {"aid": 18, "title": "图鉴大成", "desc": "图鉴满册", "cond": "dex_full", "reward": {'df': 150, 'items': [['星尘', 3]]}},
    {"aid": 19, "title": "异色猎手", "desc": "收集 5 只异色宠物", "cond": "shiny5", "reward": {'df': 60}},
    {"aid": 20, "title": "彩虹收藏", "desc": "收集 20 只异色宠物", "cond": "shiny20", "reward": {'df': 100, 'items': [['星尘结晶', 1]]}},
    {"aid": 21, "title": "半百之约", "desc": "任意宠物升到 50 级", "cond": "lv50", "reward": {'df': 80}},
    {"aid": 22, "title": "形影不离", "desc": "任意宠物亲密度达到满档", "cond": "bond_full", "reward": {'df': 60}},
    {"aid": 23, "title": "星辉顶点", "desc": "任意宠物星辉升到 10 级", "cond": "star10", "reward": {'df': 100}},
    {"aid": 24, "title": "手气不错", "desc": "彩票累计中奖 500 积分", "cond": "lotwin500", "reward": {'df': 60}},
    {"aid": 25, "title": "再接再厉", "desc": "连续 3 次彩票不中", "cond": "lot3miss", "reward": {'df': 40}},
    {"aid": 26, "title": "二手商贩", "desc": "变卖累计收入 1000 积分", "cond": "sell1000", "reward": {'df': 80}},
    {"aid": 27, "title": "合成大师", "desc": "累计合成 50 次", "cond": "craft50", "reward": {'df': 60}},
    {"aid": 28, "title": "大胃王", "desc": "累计投喂 200 次", "cond": "feed200", "reward": {'df': 50}},
    {"aid": 29, "title": "撸宠专家", "desc": "累计抚摸 100 次", "cond": "touch100", "reward": {'df': 50}},
    {"aid": 30, "title": "玩耍一百", "desc": "累计玩耍 100 次", "cond": "play100", "reward": {'df': 50}},
]

def add_log(msg, log_list, max_len=12):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_list.append(f"[{t}] {msg}")
    if len(log_list) > max_len:
        log_list.pop(0)
    return log_list


# ===================== 道具表（唯一真源） =====================
# 价格、文案、喂食效果、是否算投喂任务、是否上架，全部从这张表派生；
# 加一件新道具只需要在这里加一行（商店、仓库、说明查询会自动跟上）。
ITEMS = {
    "面包": {"price": 10, "desc": "增加 10 点饱腹值", "eff": {"ha": 10}},
    "电池": {"price": 15, "desc": "增加机器人的饱腹值，给其他宠物会倒扣",
             "eff": {}, "special": "battery"},
    "鲜鱼": {"price": 12, "desc": "给猫吃会额外增加 5 点饱腹值",
             "eff": {"ha": 10}, "special": "fish"},
    "护发素": {"price": 20, "desc": "增加 15 点宠物开心值", "eff": {"hn": 15}},
    "玩具": {"price": 25, "desc": "增加 20 点宠物开心值", "eff": {"hn": 20}},
    "葡萄": {"price": 18, "desc": "增加 30 点饱食度", "eff": {"ha": 30}},
    "肥皂": {"price": 22, "desc": "洗澡时使用，本次洗澡额外 +40 清洁值",
             "eff": {}, "special": "soap", "feed": False},
    "零食": {"price": 15, "desc": "增加 25 点开心值", "eff": {"hn": 25}},
    "药品": {"price": 30, "desc": "恢复 40 点健康值", "eff": {"health": 40}},
    "急救针": {"price": 40, "desc": "紧急施救，直接把健康拉到 50（救急专用）",
               "eff": {}, "special": "heal_to_50"},
    "全能营养膏": {"price": 45, "desc": "饱腹 +25，开心 +25，健康 +25",
                   "eff": {"ha": 25, "hn": 25, "health": 25}},
    "高级营养液": {"price": 60, "desc": "饱腹 +40，开心 +40，健康 +40",
                   "eff": {"ha": 40, "hn": 40, "health": 40}},
    "幸运徽章": {"price": 80, "desc": "携带后，全局随机事件好事概率小幅提升（被动）",
                 "eff": {}, "special": "lucky", "feed": False},
    "宠物强化剂": {"price": 120,
                   "desc": "蕴含星辉之力的神秘药剂，宠物等级达到 10 级，消耗本品，"
                           "将宠物转化为【星辉状态】，解锁大量额外增益。",
                   "eff": {}, "special": "star_potion", "feed": False},
    "除臭喷雾": {"price": 26, "desc": "清洁 +45，且不会占用洗澡冷却（不产生经验）",
                 "eff": {"cl": 45}, "exp": 0, "feed": False},
    "小零食礼包": {"price": 34, "desc": "打开随机获得 2 份零食类道具，开心值靠零食慢慢补",
                   "eff": {}, "special": "snack_pack", "exp": 0, "feed": False},
    "经验果": {"price": 45, "desc": "直接增加 35 点经验，不占饱腹、不触发投喂任务",
               "eff": {}, "special": "exp_fruit", "exp": 0, "feed": False},
    "星尘": {"price": 40,
             "desc": "星辉升级材料。星辉 1~10 级每升一级都要消耗，探索稀有宝箱也会掉。",
             "eff": {}, "special": "material", "feed": False},
    "星尘结晶": {"price": 150,
                 "desc": "进化的钥匙。宠物 25 级后可用来选择进化方向与五行元素，"
                         "之后每阶也各需数枚。",
                 "eff": {}, "special": "material", "feed": False},
    "星光皮肤券": {"price": 100, "desc": "给宠物换上星辉皮肤（纯外观，不加任何属性）。"
                                        "再次使用可切回普通外观。",
                   "eff": {}, "special": "skin_ticket", "feed": False},
    # ---- 2026-11 新增：10 件道具 ----
    "时间秒表": {"price": 25,
                 "desc": "拧一下就把玩耍 / 洗澡 / 探索的冷却全部清零，立刻就能再玩一轮",
                 "eff": {}, "special": "cooldown_reset", "exp": 0, "feed": False},
    "保温饭盒": {"price": 30, "desc": "饱腹 +45，健康 +10，热乎的饭最养人",
                 "eff": {"ha": 45, "health": 10}},
    "猫薄荷香囊": {"price": 32, "desc": "开心 +50；猫闻到会额外再 +20",
                   "eff": {"hn": 50}, "special": "catnip"},
    "泡泡浴球": {"price": 26, "desc": "清洁 +60，洗完一身泡泡香（不产生经验）",
                 "eff": {"cl": 60}, "exp": 0, "feed": False},
    "彩虹糖罐": {"price": 40, "desc": "开心 +30，饱腹 +15，甜到冒彩虹",
                 "eff": {"hn": 30, "ha": 15}},
    "成长沙漏": {"price": 55, "desc": "经验 +80，不占饱腹、不触发投喂任务",
                 "eff": {}, "exp": 80, "feed": False,
                 "use_msg": "经验 +80（不影响饱腹）"},
    "温泉蛋": {"price": 24, "desc": "健康 +30，清洁 +20，泡完温泉再来一颗",
               "eff": {"health": 30, "cl": 20}},
    "磨牙棒": {"price": 28, "desc": "开心 +35；狗啃起来额外 +15",
               "eff": {"hn": 35}, "special": "chew"},
    "月亮抱枕": {"price": 35, "desc": "开心 +40，健康 +10，抱着睡一整晚",
                 "eff": {"hn": 40, "health": 10}},
    "星星许愿瓶": {"price": 65, "desc": "摇一摇随机得到 30~120 积分，纯看运气",
                   "eff": {}, "special": "wish_coin", "exp": 0, "feed": False},
    # 季节限定：只在当季商店出现，所以 shop=False
    "春日花束": {"price": 28, "desc": "春季限定 · 开心 +30，花瓣带一点青草香",
                 "eff": {"hn": 30}, "shop": False},
    "冰镇西瓜": {"price": 26, "desc": "夏季限定 · 饱腹 +25、清洁 +10，解暑又解饿",
                 "eff": {"ha": 25, "cl": 10}, "shop": False},
    "丰收南瓜派": {"price": 28, "desc": "秋季限定 · 饱腹 +30、健康 +10，秋收的味道",
                   "eff": {"ha": 30, "health": 10}, "shop": False},
    "姜茶": {"price": 30, "desc": "冬季限定 · 健康 +20、开心 +10，寒冬里最暖的一杯",
             "eff": {"health": 20, "hn": 10}, "shop": False},
    # 节日限定：只在对应节日窗口出现在商店，shop=False + limited=True
    "年夜饭拼盘": {"price": 38, "desc": "春节限定 · 饱腹 +30、开心 +25、健康 +10，一桌热气",
                   "eff": {"ha": 30, "hn": 25, "health": 10}, "shop": False,
                   "limited": True},
    "蛋黄月饼": {"price": 36, "desc": "中秋限定 · 开心 +30、健康 +15，咸蛋黄流心",
                 "eff": {"hn": 30, "health": 15}, "shop": False, "limited": True},
    "南瓜灯糖袋": {"price": 34, "desc": "万圣限定 · 开心 +35、饱腹 +10，糖比惊吓多",
                   "eff": {"hn": 35, "ha": 10}, "shop": False, "limited": True},
    "圣诞姜饼屋": {"price": 40, "desc": "圣诞限定 · 开心 +40、健康 +20，姜饼还带着烤箱的余温",
                   "eff": {"hn": 40, "health": 20}, "shop": False, "limited": True},
}

shop_things = [k for k, v in ITEMS.items() if v.get("shop", True)]
price_dict = {k: v["price"] for k, v in ITEMS.items()}
shop_desc = {k: v["desc"] for k, v in ITEMS.items()}
FEED_SKIP = {k for k, v in ITEMS.items() if not v.get("feed", True)}


# ===================== 天气系统 =====================
# 按「日期 + 季节」算出一个稳定的天气，同一天全天不变，换天就换。
WEATHER_ORDER = ["晴", "雨", "雪", "雷"]
WEATHER_INFO = {
    "晴": {"name": "晴", "desc": "阳光正好，四平八稳", "icon": "☀",
           "ha": 1.0, "cl": 1.0, "hn": 0.95,
           "sky": "#BFE8FA", "cloud": "#FFFDF2", "tint": None,
           "tip": "晴天的衰减最温和，适合出门探索"},
    "雨": {"name": "雨", "desc": "潮气重，清洁掉得快", "icon": "☂",
           "ha": 1.0, "cl": 1.35, "hn": 1.0,
           "sky": "#8FAEC4", "cloud": "#C9D6E2", "tint": "#4E6C86",
           "tip": "雨天清洁 ×1.35，记得多洗澡或备点肥皂"},
    "雪": {"name": "雪", "desc": "天寒地冻，饱腹掉得快", "icon": "❄",
           "ha": 1.35, "cl": 1.05, "hn": 1.05,
           "sky": "#D5E3EF", "cloud": "#F3F8FC", "tint": "#8FA6BC",
           "tip": "雪天饱腹 ×1.35，出门前先喂饱"},
    "雷": {"name": "雷", "desc": "雷雨交加，心情掉得快", "icon": "⚡",
           "ha": 1.05, "cl": 1.15, "hn": 1.25,
           "sky": "#3A3F5E", "cloud": "#5B6288", "tint": "#2A2E44",
           "tip": "雷天心情 ×1.25，多摸摸头安抚一下"},
}
# 季节权重：夏天没有雪，冬天很少打雷
WEATHER_WEIGHTS = {
    "春": {"晴": 5, "雨": 3, "雪": 1, "雷": 1},
    "夏": {"晴": 4, "雨": 3, "雪": 0, "雷": 3},
    "秋": {"晴": 5, "雨": 2, "雪": 1, "雷": 1},
    "冬": {"晴": 3, "雨": 1, "雪": 5, "雷": 0},
}
# 天气专属随机事件，会插进当天的随机事件池
WEATHER_EVENTS = {
    "晴": [
        {"name": "晒被子", "type": "gain_hn", "val_range": (10, 20),
         "msg": "大晴天，宠物趴在窗台上晒得暖洋洋！"},
    ],
    "雨": [
        {"name": "踩水坑", "type": "lose_cl", "val_range": (10, 20),
         "msg": "雨天出门踩了水坑，宠物溅了一身泥！"},
        {"name": "听雨", "type": "gain_hn", "val_range": (8, 16),
         "msg": "雨声嘀嗒，宠物窝在毯子里听得很安心。"},
    ],
    "雪": [
        {"name": "扑雪花", "type": "gain_hn", "val_range": (15, 25),
         "msg": "下雪了！宠物扒着窗户，眼睛跟着雪花转。"},
        {"name": "冻手冻脚", "type": "lose_ha", "val_range": (10, 20),
         "msg": "雪天太冷，热量消耗快，饱腹下降！"},
    ],
    "雷": [
        {"name": "被雷声吓到", "type": "lose_hn", "val_range": (10, 20),
         "msg": "一个响雷，宠物吓得躲进了床底！"},
        {"name": "雷雨许愿", "type": "gain_df", "val_range": (20, 40),
         "msg": "雷雨里许了个愿，居然在门口捡到一袋积分！"},
    ],
}


def _stable_seed(text):
    """进程无关的稳定种子（str 的 hash 每个进程都不一样，所以走 sha1）。"""
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:10], 16)


def weather_of(day=None):
    """按日期 + 季节算出天气，返回 WEATHER_INFO 的副本（附加 key / 种子）。"""
    d = day or date.today()
    season_key = season_of(d)["key"]
    weights = WEATHER_WEIGHTS.get(season_key, WEATHER_WEIGHTS["春"])
    seed = _stable_seed(f"weather|{d.isoformat()}|{season_key}")
    pick = random.Random(seed).choices(WEATHER_ORDER,
                                       weights=[weights[k] for k in WEATHER_ORDER],
                                       k=1)[0]
    info = dict(WEATHER_INFO[pick])
    info["key"] = pick
    info["season"] = season_key
    info["seed"] = seed
    return info


# ===================== 节日限定 =====================
# 公历近似窗口（春节按 1/15~2/20，中秋按 9/10~10/10，万圣按 10/20~11/2），
# 一年只在这几段里出现，过完就下架，明年同一时间再来。
FESTIVALS = [
    {"key": "spring", "name": "春节", "item": "年夜饭拼盘", "price": 38,
     "start": (1, 15), "end": (2, 20), "color": "#D9534F", "icon": "🏮",
     "event": {"name": "年夜饭", "type": "gain_item", "item": "年夜饭拼盘",
               "msg": "邻居端来一盘年夜饭，热气腾腾，宠物馋得直转圈！"},
     "desc": "春节限定"},
    {"key": "midautumn", "name": "中秋", "item": "蛋黄月饼", "price": 36,
     "start": (9, 10), "end": (10, 10), "color": "#E8A83B", "icon": "🥮",
     "event": {"name": "一起赏月", "type": "gain_hn", "val_range": (20, 35),
               "msg": "月亮圆了，抱着宠物坐在窗边看了会儿月亮。"},
     "desc": "中秋限定"},
    {"key": "halloween", "name": "万圣", "item": "南瓜灯糖袋", "price": 34,
     "start": (10, 20), "end": (11, 2), "color": "#8A5A1C", "icon": "🎃",
     "event": {"name": "讨糖", "type": "gain_item", "item": "南瓜灯糖袋",
               "msg": "敲门喊了句「不给糖就捣蛋」，讨到一袋糖果！"},
     "desc": "万圣限定"},
    {"key": "christmas", "name": "圣诞", "item": "圣诞姜饼屋", "price": 40,
     "start": (12, 20), "end": (12, 26), "color": "#2E7D5B", "icon": "🎄",
     "event": {"name": "平安夜", "type": "gain_item", "item": "圣诞姜饼屋",
               "msg": "窗外的雪落了整夜，门口的姜饼屋还热着，宠物守着一棵小树不肯走。"},
     "desc": "圣诞限定"},
]
FESTIVAL_ITEMS = [f["item"] for f in FESTIVALS]


def festival_of(day=None):
    """今天在节日窗口里就返回该节日信息，否则 None。"""
    d = day or date.today()
    for f in FESTIVALS:
        sm, sd = f["start"]
        em, ed = f["end"]
        if (d.month, d.day) >= (sm, sd) and (d.month, d.day) <= (em, ed):
            out = dict(f)
            out["left_days"] = (date(d.year, em, ed) - d).days + 1
            return out
    return None


# ===================== 小屋装修 =====================
# 皮肤 = 整套换；装修 = 分部位自由搭，两条线互不影响。
DECOR_SLOTS = [
    {"key": "wall", "name": "墙纸", "note": "墙面底色与竖条纹"},
    {"key": "rug", "name": "地毯", "note": "房间中央那块地毯"},
    {"key": "art", "name": "挂画", "note": "墙上新挂的一幅画"},
    {"key": "window", "name": "窗景", "note": "窗外的风景"},
]
DECOR_ITEMS = {
    "wall": [
        {"id": "wall_sakura", "name": "樱花墙纸", "price": 55,
         "desc": "浅粉底配樱花瓣，像春天停在墙上一整天",
         "pal": {"wall": "#FBE3EC", "wall2": "#F3C9DA", "skirt": "#D79AAE"}},
        {"id": "wall_sky", "name": "晴空墙纸", "price": 55,
         "desc": "浅浅的蓝，配云朵条纹",
         "pal": {"wall": "#DCEBF7", "wall2": "#C4DDEE", "skirt": "#8FAEC4"}},
        {"id": "wall_forest", "name": "森林墙纸", "price": 55,
         "desc": "草木绿 + 竖向树影",
         "pal": {"wall": "#E3F0DA", "wall2": "#CBE1BC", "skirt": "#8FAE7E"}},
        {"id": "wall_night", "name": "星夜墙纸", "price": 70,
         "desc": "深蓝夜空墙纸，白天也有点夜色",
         "pal": {"wall": "#22203E", "wall2": "#2E2B54", "skirt": "#3E3A6A"}},
    ],
    "rug": [
        {"id": "rug_check", "name": "格纹地毯", "price": 45,
         "desc": "红白格纹，乡村感很足",
         "pal": {"rug1": "#C97B6E", "rug2": "#F6E5C2", "rug3": "#A85F53"}},
        {"id": "rug_sky", "name": "云朵地毯", "price": 45,
         "desc": "像一小片天空铺在木地板上",
         "pal": {"rug1": "#B7D8E6", "rug2": "#EAF4FA", "rug3": "#88B6CA"}},
        {"id": "rug_leaf", "name": "落叶地毯", "price": 45,
         "desc": "秋日落叶堆成的一圈",
         "pal": {"rug1": "#D8A45C", "rug2": "#F3D9A6", "rug3": "#B27B3C"}},
    ],
    "art": [
        {"id": "art_fish", "name": "小鱼挂画", "price": 40,
         "desc": "一幅画着橘猫和小鱼的画",
         "pal": {"frame": "#8A5A1C", "bg": "#FFF3D6", "ink": "#C9702C"}},
        {"id": "art_moon", "name": "月亮挂画", "price": 40,
         "desc": "深蓝底上一轮黄月亮",
         "pal": {"frame": "#5B4A94", "bg": "#2E2B54", "ink": "#FFE066"}},
        {"id": "art_fest", "name": "节日挂画", "price": 0,
         "desc": "节日任务链的纪念品，红底金边",
         "pal": {"frame": "#8A2B1C", "bg": "#C0392B", "ink": "#FFD86B"}},
        {"id": "art_flower", "name": "小花挂画", "price": 40,
         "desc": "奶油底 + 一朵粉花",
         "pal": {"frame": "#B4803B", "bg": "#FFF8E7", "ink": "#E08A97"}},
    ],
    "window": [
        {"id": "win_garden", "name": "花园窗景", "price": 50,
         "desc": "窗外是草地和云，默认就是它",
         "pal": {"sky": "#BFE8FA", "cloud": "#FFFDF2", "ground": "#A8CE96"}},
        {"id": "win_sea", "name": "海边窗景", "price": 50,
         "desc": "窗外换成海面和一层层浪",
         "pal": {"sky": "#9ED6EE", "cloud": "#FFFFFF", "ground": "#4E9EC4"}},
        {"id": "win_snow", "name": "雪原窗景", "price": 50,
         "desc": "窗外一片白，远山带松树",
         "pal": {"sky": "#E6EFF8", "cloud": "#FFFFFF", "ground": "#F3F8FC"}},
        {"id": "win_star", "name": "星空窗景", "price": 60,
         "desc": "窗外是星空与月牙",
         "pal": {"sky": "#1E2348", "cloud": "#3A4A86", "ground": "#2A3160"}},
    ],
}
DECOR_BY_ID = {it["id"]: dict(it, slot=slot)
               for slot, its in DECOR_ITEMS.items() for it in its}


_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u2600-\u26FF]"
)


# ===================== 目标 / 留存 相关配置 =====================
PET_MAX = 6                 # 宠物栏位上限（超出要先放生）
RELEASE_REFUND = 30         # 放生返还积分
ADOPT_COST = 80

# 每日任务池：每天按日期当种子抽 3 条，所以同一天所有人看到的是同一组，
# 换一天就换一组；id 是稳定的，进度记在 task_finished 里。
DAILY_TASK_POOL = [
    {"id": 1, "name": "陪宠物玩耍", "desc": "和宠物玩耍一次", "action": "play", "reward": 10},
    {"id": 2, "name": "给宠物洗澡", "desc": "给宠物洗一次澡", "action": "bath", "reward": 10},
    {"id": 3, "name": "投喂食物", "desc": "给宠物投喂任意食物", "action": "feed", "reward": 10},
    {"id": 4, "name": "逛一次商店", "desc": "进商店买任意一件东西", "action": "shop", "reward": 10},
    {"id": 5, "name": "买一张彩票", "desc": "在彩票店买任意一张彩票", "action": "lottery", "reward": 12},
    {"id": 6, "name": "出门探索", "desc": "完成一次探索（任意路线）", "action": "explore", "reward": 15},
    {"id": 7, "name": "去趟医院", "desc": "给宠物做一次治疗", "action": "heal", "reward": 10},
    {"id": 8, "name": "整理背包", "desc": "在仓库里合成任意一件道具", "action": "craft", "reward": 10},
    {"id": 9, "name": "星辉一闪", "desc": "释放一次星辉技能", "action": "star_skill", "reward": 12},
    {"id": 10, "name": "今日签到", "desc": "今天登录并签到（自动完成）", "action": "sign", "reward": 8},
]

# 每日限时挑战：每天从池子里抽 1 条，带倒计时，超时就作废
DAILY_CHALLENGES = [
    {"key": "explore3", "name": "三连探索", "metric": "total_explore", "target": 3,
     "minutes": 30, "reward": 50, "desc": "30 分钟内完成 3 次探索"},
    {"key": "feed5", "name": "喂饱小馋猫", "metric": "total_feed", "target": 5,
     "minutes": 60, "reward": 45, "desc": "60 分钟内投喂 5 次"},
    {"key": "play2", "name": "开心加倍", "metric": "total_play", "target": 2,
     "minutes": 90, "reward": 40, "desc": "90 分钟内陪它玩 2 次"},
    {"key": "touch8", "name": "亲密接触", "metric": "total_pet_touch", "target": 8,
     "minutes": 60, "reward": 35, "desc": "60 分钟内摸头 / 逗猫棒 8 次"},
    {"key": "bath1", "name": "洗香香", "metric": "total_bath", "target": 1,
     "minutes": 120, "reward": 35, "desc": "2 小时内给它洗一次澡"},
    {"key": "explore6", "name": "远行者", "metric": "total_explore", "target": 6,
     "minutes": 90, "reward": 60, "desc": "90 分钟内完成 6 次探索"},
]



# 月度目标：按“总量 - 月初起点”算进度，跨月自动重置
MONTH_TASK_LIST = [
    {"id": "m1", "name": "月度铲屎官", "desc": "本月累计投喂 60 次",
     "metric": "feed", "target": 60, "reward": 150},
    {"id": "m2", "name": "月度探险队", "desc": "本月累计探索 30 次",
     "metric": "explore", "target": 30, "reward": 200},
    {"id": "m3", "name": "月度收藏家", "desc": "本月点亮 8 格新图鉴",
     "metric": "dex", "target": 8, "reward": 250},
    {"id": "m4", "name": "四季尝鲜", "desc": "图鉴里点亮全部四季限定商品",
     "metric": "season_item", "target": 4, "reward": 300},
]

# 称号：解锁对应成就后自动获得，展示在宠物面板上
TITLES = {
    1: "初遇之缘",
    2: "铲屎小能手",
    3: "幸运儿",
    4: "喂养达人",
    5: "成长见证者",
    6: "秘境旅人",
    7: "寻踪者",
    8: "欧皇体质",
    9: "星辉初现",
    10: "群星同行",
    11: "星轨行者",
    12: "星能掌控者",
    13: "图鉴猎人",
    14: "五行归一者",
    15: "初入图鉴",
    16: "半个博物学家",
    17: "博物学家",
    18: "图鉴大成者",
    19: "异色猎手",
    20: "彩虹收藏家",
    21: "半百老友",
    22: "形影不离的人",
    23: "星辉顶点",
    24: "手气王",
    25: "愈挫愈勇",
    26: "二手商贩",
    27: "合成大师",
    28: "大胃王",
    29: "撸宠专家",
    30: "玩耍一百",
}

# 合成台：仓库越堆越多时把低级材料换高级的
CRAFT_RECIPES = [
    {"id": "c1", "out": "星尘结晶", "need": {"星尘": 5},
     "desc": "5 个星尘 → 1 个星尘结晶（进化材料不用再攒积分买）"},
    {"id": "c2", "out": "葡萄", "need": {"面包": 2},
     "desc": "2 个面包 → 1 个葡萄（把吃不完的饱腹换开心）"},
    {"id": "c3", "out": "高级营养液", "need": {"药品": 2, "面包": 2},
     "desc": "2 药品 + 2 面包 → 1 瓶高级营养液"},
    {"id": "c4", "out": "急救针", "need": {"药品": 3},
     "desc": "3 个药品 → 1 支急救针（先把健康拉到 50 再喂药）"},
]

# ===================== 第二批扩展：变卖 / 亲密 / 口味 / 异色 =====================
# 变卖：按商店原价的一半回收，最低 1 积分（季节限定也照此价回收）
SELL_RATE = 0.5

# 抚摸互动：每个自然日的次数上限（摸摸头算 1 次，逗猫棒算 2 次）
SICK_HEALTH = 10            # 健康低于这个值进入生病：不能玩耍 / 探索
TOUCH_DAILY = 10

# 探索遇到异色花粉的概率（远低于稀有宝箱，长期收集目标）
SHINY_RATE = 0.01
SHINY_ITEM = "异色花粉"

BOND_MAX = 100
# 亲密度 5 档：解锁专属台词 + 立绘小动作，展示在宠物面板
BOND_TIERS = [
    {"min": 0, "name": "陌生", "line": "它还在偷偷观察你。", "act": ""},
    {"min": 20, "name": "熟络", "line": "看到你会轻轻摇两下尾巴。", "act": "尾巴摇了两下"},
    {"min": 40, "name": "亲近", "line": "你一坐下，它就会凑过来。", "act": "蹭了蹭你的手"},
    {"min": 60, "name": "依赖", "line": "你走到哪儿，它就跟到哪儿。", "act": "原地转了个圈"},
    {"min": 80, "name": "形影不离", "line": "你离开一会儿，它就开始到处找你。", "act": "扑到你身上撒娇"},
]

# 每个物种 1 个最爱、1 个嫌弃：爱吃效果翻倍并加亲密度，嫌弃效果减半还掉开心
TASTE = {
    "猫": {"love": "鲜鱼", "hate": "姜茶"},
    "狗": {"love": "面包", "hate": "肥皂"},
    "机器人": {"love": "电池", "hate": "鲜鱼"},
    "小羊": {"love": "春日花束", "hate": "冰镇西瓜"},
    "小鸡": {"love": "面包", "hate": "姜茶"},
    "豹子": {"love": "葡萄", "hate": "面包"},
    "兔子": {"love": "葡萄", "hate": "鲜鱼"},
    "仓鼠": {"love": "面包", "hate": "鲜鱼"},
    "狐狸": {"love": "鲜鱼", "hate": "肥皂"},
    "企鹅": {"love": "鲜鱼", "hate": "姜茶"},
    "青蛙": {"love": "冰镇西瓜", "hate": "面包"},
    "小熊": {"love": "葡萄", "hate": "冰镇西瓜"},
    "机械蜂": {"love": "电池", "hate": "春日花束"},
    "小鹿": {"love": "春日花束", "hate": "鲜鱼"},
    "小龙": {"love": "丰收南瓜派", "hate": "姜茶"},
    "史莱姆": {"love": "冰镇西瓜", "hate": "面包"},
    "布丁": {"love": "葡萄", "hate": "除臭喷雾"},
    "机械鼠": {"love": "电池", "hate": "鲜鱼"},
    "机甲兔": {"love": "电池", "hate": "面包"},
    "小鸭": {"love": "面包", "hate": "鲜鱼"},
    "熊猫": {"love": "春日花束", "hate": "鲜鱼"},
    "小狼": {"love": "鲜鱼", "hate": "葡萄"},
    "小马": {"love": "葡萄", "hate": "肥皂"},
    "独角兽": {"love": "春日花束", "hate": "除臭喷雾"},
    "麒麟": {"love": "春日花束", "hate": "姜茶"},
    "豆豆": {"love": "零食", "hate": "肥皂"},
    "蘑菇仔": {"love": "姜茶", "hate": "冰镇西瓜"},
    "甜甜圈": {"love": "葡萄", "hate": "姜茶"},
    "饭团": {"love": "鲜鱼", "hate": "冰镇西瓜"},
    "机甲龟": {"love": "电池", "hate": "春日花束"},
    "机械狮": {"love": "电池", "hate": "葡萄"},
    "小刺猬": {"love": "葡萄", "hate": "鲜鱼"},
    "小猪": {"love": "面包", "hate": "姜茶"},
    "小松鼠": {"love": "面包", "hate": "鲜鱼"},
    "凤凰": {"love": "姜茶", "hate": "冰镇西瓜"},
    "貔貅": {"love": "高级营养液", "hate": "肥皂"},
    "方块仔": {"love": "经验果", "hate": "面包"},
    "炸弹仔": {"love": "姜茶", "hate": "冰镇西瓜"},
    "小笼包": {"love": "面包", "hate": "鲜鱼"},
    "冰淇淋": {"love": "冰镇西瓜", "hate": "姜茶"},
}

# 调参面板用的一层可变系数，默认值等于现在的正式数值；改完随时能改回去
TUNE = {
    "play_cd_h": 2.0,
    "bath_cd_h": 2.0,
    "explore_cd_min": 30,
    "decay_mul": 1.0,
    "rare_cap": 0.60,
    "big_p": 5,
    "mid_p": 30,
}
TUNE_DEFAULTS = dict(TUNE)

# ===================== 40 只小传 =====================
# intro：图鉴点亮就能读；quote：口头禅；deep：亲密度到「亲近」以上才解锁
BIO = {
    "猫": {"intro": "白天睡满十八小时，夜里负责巡视整间小屋。",
          "quote": "「摸头可以，别摸肚子。」",
          "deep": "它把最暖和的那块地毯留给你坐，自己挪到边上——这是猫的体贴。"},
    "狗": {"intro": "你一开门它就在门口打转，尾巴快摇成螺旋桨。",
          "quote": "「今天出门吗？出门吗？出门吗？」",
          "deep": "它记不住昨天吃了什么，但记得你每次回家的时间。"},
    "机器人": {"intro": "出厂设定是保姆型，结果第一件事是给你递电池。",
          "quote": "「电量 87%，还能再陪你 6 小时。」",
          "deep": "它偷偷把你的名字写进了系统启动日志的第一行。"},
    "小羊": {"intro": "羊毛蓬松，走两步就要停下来蹭蹭墙。",
          "quote": "「咩——今天风是甜的。」",
          "deep": "它把掉的毛攒起来，说等冬天给你织条围巾。"},
    "小鸡": {"intro": "走路一点一点，啄米的速度却快得看不清。",
          "quote": "「叽！先吃，吃完再说。」",
          "deep": "它会在你手心里蹲着睡，翅膀盖住你的指尖。"},
    "豹子": {"intro": "安静、体面，走路不带一点声音。",
          "quote": "「别跟着我，我自己会回来。」",
          "deep": "它把抓到的第一只蝴蝶放在你枕边，当作礼物。"},
    "兔子": {"intro": "耳朵比身体还忙，听到一点动静就立起来。",
          "quote": "「不是害怕，只是耳朵想动。」",
          "deep": "它开始在你脚边打滚，那是兔子最没防备的样子。"},
    "仓鼠": {"intro": "两颊永远鼓鼓的，像随身带了个仓库。",
          "quote": "「这是存粮，不是零食。」",
          "deep": "它分了你半颗瓜子，那是仓鼠能给出的最大方。"},
    "狐狸": {"intro": "尾巴蓬松，眼神总像在算计什么。",
          "quote": "「我没偷看，我只是刚好路过。」",
          "deep": "它把藏起来的宝贝全搬出来，一件件摆给你看。"},
    "企鹅": {"intro": "走路左右摇摆，站定了又特别笔挺。",
          "quote": "「冷？还好，脂肪够厚。」",
          "deep": "它把最中间的位置让给你，自己站到风口。"},
    "青蛙": {"intro": "一天到晚趴在窗台上，只在下雨时特别兴奋。",
          "quote": "「呱，今天要下雨。」",
          "deep": "下雨天它会跳到你手背上，等着一起听雨。"},
    "小熊": {"intro": "抱起来沉沉的，体温比房间还暖。",
          "quote": "「蜂蜜呢？就一点点。」",
          "deep": "它睡觉时会把你的一只袖子攥在爪子里。"},
    "机械蜂": {"intro": "翅膀嗡嗡响，巡逻路线从不重复。",
          "quote": "「检测完毕，一切正常。」",
          "deep": "它学会了在你回家前把灯先打开。"},
    "小鹿": {"intro": "腿细，胆子更细，一惊就往后退半步。",
          "quote": "「那个……可以靠近一点吗？」",
          "deep": "它终于肯把头搁在你膝盖上，睫毛一颤一颤。"},
    "小龙": {"intro": "体型不大，气势十足，打喷嚏会冒小火星。",
          "quote": "「本龙今天心情不错。」",
          "deep": "它把最亮的一片鳞擦干净，说要送你。"},
    "史莱姆": {"intro": "半透明的一团，开心时会轻轻发抖。",
          "quote": "「啵。」",
          "deep": "它把自己分成两半，一半贴在你手心里。"},
    "布丁": {"intro": "晃晃悠悠，走快了会自己晃倒。",
          "quote": "「别摇我，要散架了。」",
          "deep": "它愿意让你戳一下最软的地方，只给你。"},
    "机械鼠": {"intro": "轮子小，跑得却比谁都快。",
          "quote": "「叽——导航中，请稍候。」",
          "deep": "它把巡逻地图偷偷存成了你的房间形状。"},
    "机甲兔": {"intro": "耳朵是天线，听得到隔壁房间的动静。",
          "quote": "「信号良好，心跳正常。」",
          "deep": "它把你的脚步声单独建了一个识别档案。"},
    "小鸭": {"intro": "走到哪都要跟着，像有个隐形的绳。",
          "quote": "「嘎，等等我！」",
          "deep": "它学会了在你坐下之前先占好位置，留一半给你。"},
    "熊猫": {"intro": "一天吃四顿，睡三次，工作量为零。",
          "quote": "「竹子呢？没有竹子就躺着了。」",
          "deep": "它把最舒服的那块竹席让给你，自己睡地板。"},
    "小狼": {"intro": "看着凶，其实怕打雷，雷天会往你身后躲。",
          "quote": "「我不怕，只是站得靠后一点。」",
          "deep": "它开始在你门口守着睡，说是值班。"},
    "小马": {"intro": "喜欢奔跑，房间太小，只能原地踱步。",
          "quote": "「有风吗？我想跑起来。」",
          "deep": "它把跑得最快的一次留给你看，只跑给你看。"},
    "独角兽": {"intro": "角上有一点光，走过的地方会留下很淡的亮。",
          "quote": "「许愿吗？我听着。」",
          "deep": "它低下头，让你摸那支角——传说只有信任的人才碰得到。"},
    "麒麟": {"intro": "脚步很轻，走过的地板会短暂变暖。",
          "quote": "「此处有福。」",
          "deep": "它在你生病那晚一直守在床边，一步没离开。"},
    "豆豆": {"intro": "一颗会走路的豆子，最爱滚来滚去。",
          "quote": "「滚一圈给你看？」",
          "deep": "它滚到你脚边停住，说这里最舒服。"},
    "蘑菇仔": {"intro": "伞盖会随心情变色，阴天是灰的，晴天是橘的。",
          "quote": "「别踩我，我还在长。」",
          "deep": "它把伞盖倾向你这边，替你挡了一点点雨。"},
    "甜甜圈": {"intro": "身上的糖霜会掉，掉完会有点委屈。",
          "quote": "「糖霜……又掉了。」",
          "deep": "它允许你舔一口糖霜，然后自己红了半天。"},
    "饭团": {"intro": "安静、圆润，是房间里最像抱枕的东西。",
          "quote": "「海苔要掉了，扶一下。」",
          "deep": "它把自己摆成刚好能靠的形状，等你躺下。"},
    "机甲龟": {"intro": "壳是合金的，走路慢，但从不迟到。",
          "quote": "「稳住，就到了。」",
          "deep": "它把壳上的划痕一条条讲给你听，都是它走过的路。"},
    "机械狮": {"intro": "鬃毛是散热片，发怒时整片会亮起来。",
          "quote": "「本王在此，退后。」",
          "deep": "它趴下来把下巴搁在你手上，鬃毛的温度慢慢降下来。"},
    "小刺猬": {"intro": "遇事先缩成球，确认安全才慢慢展开。",
          "quote": "「别急，我先看看。」",
          "deep": "它第一次在你面前露出软肚子，刺全收了起来。"},
    "小猪": {"intro": "吃得多，睡得更香，梦里都在嚼东西。",
          "quote": "「还有吗？还有吧？」",
          "deep": "它把食盆推到你面前，意思是分你一半。"},
    "小松鼠": {"intro": "到处藏东西，藏完就忘，秋天满屋子翻。",
          "quote": "「我藏哪了？你看见了吗？」",
          "deep": "它把最好的那颗果子塞进你口袋，不让你还。"},
    "凤凰": {"intro": "羽毛会随着温度变色，冷的时候偏蓝，暖的时候偏金。",
          "quote": "「烧尽一次，还会回来。」",
          "deep": "它留下了一根不会熄灭的尾羽，放在你窗台上。"},
    "貔貅": {"intro": "只进不出，仓库里的每件东西它都记得。",
          "quote": "「这个，归我了。」",
          "deep": "它把攒了很久的宝贝倒出来，一件件塞给你。"},
    "方块仔": {"intro": "行动是格子式的，一步一格，绝不斜走。",
          "quote": "「一格，再一格。」",
          "deep": "它把路线改成绕着你走，说是画个圈保护你。"},
    "炸弹仔": {"intro": "脾气一点就着，但炸完会立刻道歉。",
          "quote": "「别点我！……对不起。」",
          "deep": "它学会了在你面前把引线收起来，只留个笑脸。"},
    "小笼包": {"intro": "热气腾腾，一急就会自己揭盖。",
          "quote": "「趁热，趁热！」",
          "deep": "它把最完整的那只留给你，自己吃破皮的那些。"},
    "冰淇淋": {"intro": "天一热就开始化，一冷又硬得咬不动。",
          "quote": "「快点，我要化了。」",
          "deep": "它愿意在你手心里多待一会儿，哪怕化掉一点点。"},
}


# ===================== 性格 / 主动技能 =====================
# 性格只做轻微手感差异，不改核心数值。
PERSONALITIES = {
    "lively": {"name": "活泼", "decay": 1.06, "exp": 1.03,
               "line": "一有动静就凑过来，睡觉也要贴着你的手。"},
    "quiet": {"name": "安静", "decay": 0.92, "exp": 1.0,
              "line": "大部分时间在窗边发呆，偶尔抬头看你一眼。"},
    "greedy": {"name": "贪吃", "decay": 1.03, "exp": 1.0, "feed": 1.10,
               "line": "听见袋子的声音就会从房间另一头冲过来。"},
    "shy": {"name": "认生", "decay": 0.95, "exp": 1.0, "bond": 1.2,
            "line": "先躲起来观察你半天，确认安全才肯靠近。"},
}
PERSONALITY_KEYS = tuple(PERSONALITIES)

# 主动技能：按物种特性给效果，冷却 45 分钟、消耗 3 点亲密度。
_ACTIVE_BY_CATEGORY = {
    "机械": {"key": "overclock", "name": "超频", "desc": "齿轮狂转，直接产出 40 积分",
             "cd": 45, "bond": 3},
    "萌宠": {"key": "dig", "name": "挖洞", "desc": "刨出一件仓库里没有的东西",
             "cd": 45, "bond": 3},
    "水生": {"key": "tide", "name": "唤潮", "desc": "四项状态各 +8",
             "cd": 45, "bond": 3},
    "奇幻": {"key": "heal", "name": "自愈", "desc": "健康 +25",
             "cd": 45, "bond": 3},
    "神话": {"key": "charm", "name": "魅惑", "desc": "开心 +25、亲密度 +2",
             "cd": 45, "bond": 3},
}
ACTIVE_SKILLS = {
    "兔子": {"key": "dig", "name": "挖洞", "desc": "兔子最懂土里的东西，直接带走一件稀有道具",
               "cd": 40, "bond": 3},
    "猫": {"key": "charm", "name": "撒娇", "desc": "翻个肚皮，开心 +25、亲密度 +2",
            "cd": 40, "bond": 3},
    "机器人": {"key": "overclock", "name": "超频", "desc": "齿轮狂转，直接产出 45 积分",
              "cd": 40, "bond": 3},
    "独角兽": {"key": "heal", "name": "圣光", "desc": "角尖亮一下，健康 +30",
                "cd": 50, "bond": 3},
}


def active_skill_of(species):
    """给一个物种挑主动技能：特例优先，否则按类别默认。"""
    if species in ACTIVE_SKILLS:
        return dict(ACTIVE_SKILLS[species])
    for cat in PET_CATEGORIES:
        if species in cat["pets"]:
            return dict(_ACTIVE_BY_CATEGORY.get(cat["name"], _ACTIVE_BY_CATEGORY["萌宠"]))
    return dict(_ACTIVE_BY_CATEGORY["萌宠"])


# ===================== 主线章节 =====================
# chapter: 达到第几章；sections: 该章额外解锁的分区 tag。
CHAPTERS = [
    {"id": 1, "name": "初来乍到", "desc": "完成 3 步新手引导",
     "sections": ("shop", "pet"), "reward": {"df": 30}},
    {"id": 2, "name": "第一颗星", "desc": "任意宠物 Lv10 并觉醒星辉",
     "sections": ("star", "dex"), "reward": {"item": "星尘", "n": 3}},
    {"id": 3, "name": "小有所成", "desc": "图鉴 30 格 + 星辉 5 阶",
     "sections": ("decor", "ach"),
     "reward": {"decor": "art_fest"}},
    {"id": 4, "name": "四季流转", "desc": "经历 40 次季节更替",
     "sections": ("fun", "svc"), "reward": {"df": 80}},
    {"id": 5, "name": "满屋欢声", "desc": "拥有 5 只宠物 或 图鉴点亮一半",
     "sections": (), "reward": {"df": 150}},
]
# 一直开放的分区
ALWAYS_SECTIONS = ("shop", "pet", "log", "help")
