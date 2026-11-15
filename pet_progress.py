# -*- coding: utf-8 -*-
"""pet_progress（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
from datetime import date, datetime, timedelta
import random
from pet_constants import *
from pet_constants import _EMOJI_RE

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
DEX_FESTIVAL_ITEMS = ["年夜饭拼盘", "蛋黄月饼", "南瓜灯糖袋", "圣诞姜饼屋"]
# 限定商品：四季 4 件 + 节日 3 件，图鉴里单独一块
DEX_LIMITED_ITEMS = DEX_SEASON_ITEMS + DEX_FESTIVAL_ITEMS
DEX_SEASON_KEYS = [f"item|{i}" for i in DEX_SEASON_ITEMS]
DEX_LIMITED_KEYS = [f"item|{i}" for i in DEX_LIMITED_ITEMS]
DEX_ALL_KEYS = DEX_SKIN_KEYS + DEX_LIMITED_KEYS
DEX_TOTAL = len(DEX_ALL_KEYS)
DEX_GROUPS = [
    {"gid": f"pair_{sp}", "name": f"{sp} · 双皮肤", "reward": 30,
     "keys": [f"{sp}|normal", f"{sp}|star"]}
    for sp in PET_SPECIES
] + [
    {"gid": "all_species", "name": "集齐全物种双皮肤", "reward": 100, "keys": DEX_SKIN_KEYS},
    {"gid": "all_season", "name": "集齐四季限定", "reward": 80, "keys": DEX_SEASON_KEYS},
    {"gid": "all_festival", "name": "集齐节日限定", "reward": 90, "keys": DEX_LIMITED_KEYS[4:]},
    {"gid": "all_dex", "name": "图鉴满册", "reward": 200, "keys": DEX_ALL_KEYS},
]


def dex_label(key):
    if key.startswith("item|"):
        return key.split("|", 1)[1]
    sp, skin = key.split("|")
    return f"{sp} · {'星辉' if skin == 'star' else ('异色' if skin == 'shiny' else '普通')}"


# 异色（第三态）：只做收藏展示与点亮记录，不计入 DEX_TOTAL，
# 以免影响图鉴完成度、成就和月度目标的历史口径。


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


# ===================== 物种特性表（唯一真源） =====================
# cl/ha/hn/mood 是衰减乘数；mood 参与 cl/ha/hn 的合成，mood_direct 只作用于
# 心情本身的衰减（和原实现的分先后顺序保持一致）；cl_star 只在星辉形态生效。
SPECIES_TRAITS = {
    "小羊": {"cl": 0.5},
    "企鹅": {"cl": 0.9},
    "机器人": {"cl_star": 0.7},
    "机械蜂": {"cl": 0.85},
    "青蛙": {"mood": 0.92},
    "小鹿": {"mood": 0.95},
    "仓鼠": {"ha": 0.9},
    "史莱姆": {"ha": 0.9},
    "布丁": {"mood_direct": 0.95},
    "小鸭": {"cl": 0.9},
    "机械鼠": {"cl": 0.85},
    "蘑菇仔": {"cl": 0.92},
    "熊猫": {"hn": 0.9},
    "小狼": {"ha": 0.92},
    "小马": {"ha": 0.88},
    "饭团": {"ha": 0.9},
    "机甲兔": {"mood_direct": 0.95},
    "独角兽": {"mood_direct": 0.93},
    "豆豆": {"hn": 0.94},
    "甜甜圈": {"hn": 0.95},
    "机甲龟": {"cl": 0.9},
    "方块仔": {"cl": 0.9},
    "机械狮": {"mood_direct": 0.94},
    "炸弹仔": {"mood_direct": 0.92},
    "冰淇淋": {"mood_direct": 0.94},
    "小刺猬": {"ha": 0.93},
    "小猪": {"ha": 0.9},
    "小松鼠": {"hn": 0.95},
    "貔貅": {"hn": 0.92},
    "小笼包": {"ha": 0.92},
    "小熊": {"heal": 1.15},
    "小龙": {"heal": 1.1},
    "麒麟": {"heal": 1.12},
    "凤凰": {"heal": 1.15},
}


def species_mods(species, is_star=False):
    """取某物种的衰减/恢复乘数，未列出的物种全为 1.0。"""
    t = SPECIES_TRAITS.get(species, {})
    mood = t.get("mood", 1.0)
    return {
        "cl": t.get("cl", 1.0) * (t.get("cl_star", 1.0) if is_star else 1.0),
        "ha": t.get("ha", 1.0),
        "hn": t.get("hn", 1.0),
        "mood": mood,
        "mood_direct": mood * t.get("mood_direct", 1.0),
        "heal": t.get("heal", 1.0),
    }


# 写死在逻辑里的特例（猫吃鱼、机器人吃电池之类），一并交给帮助页自动拼
SPECIES_NOTES = {
    "猫": "吃鲜鱼额外回饱腹，星辉猫玩耍再 +30 开心",
    "机器人": "吃电池才回饱腹（星辉 +20）",
    "小鸡": "星辉形态喂食经验 ×1.1",
    "豹子": "星辉形态积分 ×1.25",
    "兔子": "探索稀有率 ×1.18（星辉 ×1.35）",
    "狐狸": "探索稀有率 +3%",
}

_TRAIT_LABEL = (
    ("ha", "饱腹衰减 ×{v}"),
    ("hn", "心情衰减 ×{v}"),
    ("mood", "三项衰减 ×{v}"),
    ("mood_direct", "心情衰减 ×{v}"),
    ("cl", "清洁衰减 ×{v}"),
    ("cl_star", "星辉清洁 ×{v}"),
    ("heal", "健康回复 ×{v}"),
)


def species_trait_lines():
    """把 TASTE + SPECIES_TRAITS + SPECIES_NOTES 拼成"一物种一行"的说明。

    帮助页直接读这里，改数值/加物种不用再改文案。
    """
    from pet_constants import TASTE
    lines = []
    for sp, taste in TASTE.items():
        bits = [f"爱 {taste['love']}", f"嫌 {taste['hate']}"]
        t = SPECIES_TRAITS.get(sp, {})
        for key, tpl in _TRAIT_LABEL:
            if key in t:
                bits.append(tpl.format(v=t[key]))
        note = SPECIES_NOTES.get(sp)
        if note:
            bits.append(note)
        lines.append(f"- **{sp}**：" + " · ".join(bits))
    return lines


def _lottery_is_miss(x):
    """彩票记录兼容新旧两种形态：dict 取 level；现行档/老档都是纯文本，按结果文案判断。"""
    if isinstance(x, dict):
        return str(x.get("level", "")) in ("none", "未中奖")
    if isinstance(x, str):
        return ("没有中奖" in x) or ("未中奖" in x)
    return False


# ===================== 成就条件表 =====================
# 每个成就的 cond 对应一个判定函数，加成就只需在 achievement_list 里加数据 + 这里加一行
_ACH_CONDS = {
    "first_pet": lambda gs, pet, stars: bool(gs["first_pet_flag"]),
    "task10": lambda gs, pet, stars: gs["total_task"] >= 10,
    "lottery_win": lambda gs, pet, stars: gs["big_win_flag"] == 1,
    "feed20": lambda gs, pet, stars: gs["total_feed"] >= 20,
    "lv5": lambda gs, pet, stars: pet["lv"] >= 5,
    "explore10": lambda gs, pet, stars: gs["total_explore"] >= 10,
    "explore100": lambda gs, pet, stars: gs["total_explore"] >= 100,
    "explore_rare_once": lambda gs, pet, stars: gs["explore_rare_once_flag"] == 1,
    "star_awake": lambda gs, pet, stars: stars >= 1,
    "star_3pet": lambda gs, pet, stars: stars >= 3,
    "star_explore50": lambda gs, pet, stars: gs["total_star_explore"] >= 50,
    "star_skill50": lambda gs, pet, stars: gs["total_star_skill_use"] >= 50,
    "dex7": lambda gs, pet, stars: len(gs.get("dex", [])) >= 7,
    "dex_quarter": lambda gs, pet, stars: len(gs.get("dex", [])) >= DEX_TOTAL * 0.25,
    "dex_half": lambda gs, pet, stars: len(gs.get("dex", [])) >= DEX_TOTAL * 0.5,
    "dex_3q": lambda gs, pet, stars: len(gs.get("dex", [])) >= DEX_TOTAL * 0.75,
    "dex_full": lambda gs, pet, stars: len([k for k in DEX_ALL_KEYS
                                            if k in set(gs.get("dex", []))]) >= DEX_TOTAL,
    "shiny5": lambda gs, pet, stars: len([k for k in gs.get("dex", [])
                                          if str(k).endswith("|shiny")]) >= 5,
    "shiny20": lambda gs, pet, stars: len([k for k in gs.get("dex", [])
                                           if str(k).endswith("|shiny")]) >= 20,
    "lv50": lambda gs, pet, stars: int(pet.get("lv", 0) or 0) >= 50,
    "bond_full": lambda gs, pet, stars: max([float(x.get("bond", 0) or 0)
                                             for x in gs.get("pet_list", [])
                                             if isinstance(x, dict)] or [0])
                                           >= float(BOND_MAX),
    "star10": lambda gs, pet, stars: max([int(x.get("star_lv", 0) or 0)
                                          for x in gs.get("pet_list", [])
                                          if isinstance(x, dict)] or [0])
                                        >= STAR_MAX_LV,
    "lotwin500": lambda gs, pet, stars: int(gs.get("total_lottery_win", 0) or 0) >= 500,
    "lot3miss": lambda gs, pet, stars: len(gs.get("lottery_history", [])[-3:]) >= 3 and
                                       all(_lottery_is_miss(x)
                                           for x in gs.get("lottery_history", [])[-3:]),
    "sell1000": lambda gs, pet, stars: int(gs.get("total_sell_df", 0) or 0) >= 1000,
    "craft50": lambda gs, pet, stars: int(gs.get("total_craft", 0) or 0) >= 50,
    "feed200": lambda gs, pet, stars: int(gs.get("total_feed", 0) or 0) >= 200,
    "touch100": lambda gs, pet, stars: int(gs.get("total_pet_touch", 0) or 0) >= 100,
    "play100": lambda gs, pet, stars: int(gs.get("total_play", 0) or 0) >= 100,
    "evo5": lambda gs, pet, stars: any(
        int(p.get("evo_lv", 0) or 0) >= EVO_MAX_LV
        for p in gs.get("pet_list", []) if isinstance(p, dict)),
}


def unlocked_achievements(gs, current_pet, star_count):
    """按 achievement_list 里的 cond 批量判定，返回已达成但可能尚未解锁的 aid。"""
    return [a["aid"] for a in achievement_list
            if _ACH_CONDS.get(a.get("cond"), lambda *_: False)(gs, current_pet, star_count)]

RARE_RATE_CAP = 0.60        # 稀有率硬上限，避免一只宠物把玩法叠成必中


def explore_rare_rate(cfg, species, is_star, bonus_rare, cap=None):
    """探索稀有率：基础 + 物种天赋 + 灵能加成，最后封顶。

    cap 不给时读调参表里的 rare_cap（再没有就用 RARE_RATE_CAP），
    调用方也可以直接传一个更严的上限，方便在面板上做展示/封顶预览。
    """
    rate = cfg["rare_rate"]
    if species == "兔子":
        rate *= 1.35 if is_star else 1.18
    if species == "狐狸":
        rate += 0.03        # 狐狸鼻子灵，容易嗅到稀有事件
    rate += bonus_rare
    if cap is None:
        try:
            cap = float(TUNE["rare_cap"])
        except (KeyError, TypeError, ValueError):
            cap = RARE_RATE_CAP
    return min(float(cap), max(0.0, rate))


import random as _random

# ===================== 每日任务（3 选于池） =====================
def pick_daily_tasks(day):
    """用日期当种子抽 3 条，同一天固定同一组，换天就换。"""
    rng = _random.Random(int(day.strftime("%Y%m%d")))
    ids = rng.sample([t["id"] for t in DAILY_TASK_POOL], 3)
    return sorted(ids)


def tasks_today(gs):
    """今天真正生效的三条任务（老存档没存 task_pool 时按当天现抽）。"""
    ids = gs.get("task_pool") or pick_daily_tasks(gs.get("task_day") or date.today())
    return [t for t in DAILY_TASK_POOL if t["id"] in ids]


def complete_task(gs, action, out_msgs=None):
    """把今天抽到的、动作匹配的任务标记完成并发奖励；没抽到就静默跳过。"""
    if out_msgs is None:
        out_msgs = []
    for t in tasks_today(gs):
        if t["action"] == action and t["id"] not in gs["task_finished"]:
            gs["task_finished"].append(t["id"])
            gs["df"] += t["reward"]
            gs["total_task"] = int(gs.get("total_task", 0)) + 1
            add_log(f"完成每日任务 {t['name']}，+{t['reward']}", gs["game_log"])
            out_msgs.append(f"今日任务完成：{t['name']}（积分 +{t['reward']}）")
            return t
    return None


# ===================== 月度目标 =====================
MONTH_METRICS = {
    "feed": lambda gs: gs["total_feed"],
    "explore": lambda gs: gs["total_explore"],
    "dex": lambda gs: len(gs.get("dex", [])),
    "season_item": lambda gs: len(
        [1 for it in DEX_SEASON_ITEMS if f"item|{it}" in gs.get("dex", [])]),
}


def month_key_of(day):
    return day.strftime("%Y-%m")


def month_progress(gs):
    base = gs.get("month_base") or {}
    out = {}
    for t in MONTH_TASK_LIST:
        cur = MONTH_METRICS[t["metric"]](gs)
        if t["metric"] == "season_item":
            out[t["id"]] = cur                 # 季节限定是“集齐”型，不看增量
        else:
            b = int(base.get(t["metric"], cur))
            out[t["id"]] = max(0, cur - b)
    return out


def month_ready(gs):
    prog = month_progress(gs)
    done = gs.get("month_done") or []
    return [t for t in MONTH_TASK_LIST
            if prog[t["id"]] >= t["target"] and t["id"] not in done]


# ===================== 称号 =====================
def current_title(gs):
    """已解锁成就里等级最高（aid 最大）的那个称号。"""
    got = set(gs.get("unlock_ach") or [])
    for aid in sorted(TITLES.keys(), reverse=True):
        if aid in got:
            return TITLES[aid]
    return "刚搬进小屋的人"


# ===================== 合成台 =====================
def recipe_by_id(rid):
    return next((r for r in CRAFT_RECIPES if r["id"] == rid), None)


def can_craft(gs, recipe):
    for item, n in recipe["need"].items():
        if gs["storehouse"].count(item) < n:
            return False
    return True


def craft(gs, rid, out_msgs=None):
    """消耗配方材料换成品，返回 (是否成功, 提示)。"""
    if out_msgs is None:
        out_msgs = []
    r = recipe_by_id(rid)
    if not r:
        return False, "没有这个配方"
    if not can_craft(gs, r):
        lack = "、".join(f"{k}×{v}" for k, v in r["need"].items()
                       if gs["storehouse"].count(k) < v)
        return False, f"材料不够：{lack}"
    for item, n in r["need"].items():
        for _ in range(n):
            gs["storehouse"].remove(item)
    gs["storehouse"].append(r["out"])
    add_log(f"合成 {r['out']}", gs["game_log"])
    complete_task(gs, "craft", out_msgs)
    return True, f"合成成功：{r['out']}（消耗 " + "、".join(
        f"{k}×{v}" for k, v in r["need"].items()) + "）"


# ===================== 每日限时挑战 =====================
def _challenge_seed(day):
    import hashlib
    return int(hashlib.sha1(str(day).encode("utf-8")).hexdigest()[:8], 16)


def _challenge_of(key):
    for c in DAILY_CHALLENGES:
        if c["key"] == key:
            return c
    return DAILY_CHALLENGES[0]


def challenge_today(gs, now=None):
    """当天抽 1 条限时挑战；换天自动重抽并重置进度基线。"""
    now = now or datetime.now()
    today = now.date()
    if gs.get("challenge_day") == today and gs.get("challenge_key"):
        return _challenge_of(gs["challenge_key"])
    idx = _challenge_seed(today) % len(DAILY_CHALLENGES)
    c = DAILY_CHALLENGES[idx]
    gs["challenge_day"] = today
    gs["challenge_key"] = c["key"]
    gs["challenge_base"] = {m: int(gs.get(m, 0) or 0) for m in
                            {x["metric"] for x in DAILY_CHALLENGES}}
    gs["challenge_end"] = now + timedelta(minutes=c["minutes"])
    gs["challenge_done"] = 0
    gs["challenge_result"] = ""
    return c


def challenge_progress(gs):
    """返回 (已完成进度, 目标, 剩余秒数, 是否已结算)。"""
    c = _challenge_of(gs.get("challenge_key") or "")
    base = (gs.get("challenge_base") or {}).get(c["metric"], 0)
    cur = max(0, int(gs.get(c["metric"], 0) or 0) - int(base))
    end = gs.get("challenge_end") or datetime.now()
    left = (end - datetime.now()).total_seconds()
    return min(cur, c["target"]), c["target"], left, bool(gs.get("challenge_done"))


def challenge_settle(gs, now=None):
    """达标就发奖；超时作废。返回真正发生变化时的提示。"""
    now = now or datetime.now()
    c = challenge_today(gs, now)
    if gs.get("challenge_done"):
        return []
    cur, target, left, _ = challenge_progress(gs)
    if cur >= target and left > 0:
        gs["challenge_done"] = 1
        gs["challenge_result"] = "win"
        gs["df"] = int(gs.get("df", 0)) + int(c["reward"])
        msg = f"限时挑战完成：【{c['name']}】+{c['reward']} 积分"
        add_log(msg, gs["game_log"])
        return [msg]
    if left <= 0:
        gs["challenge_done"] = 1
        gs["challenge_result"] = "miss"
        msg = f"限时挑战【{c['name']}】超时作废，明天再来"
        add_log(msg, gs["game_log"])
        return [msg]
    return []
