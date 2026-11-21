# -*- coding: utf-8 -*-
"""pet_room（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
from datetime import date, datetime, timedelta
import math
from pet_constants import *
import streamlit as st
from pet_progress import *
from pet_svg import *
from pet_svg import (_r, _mx, _blob, _outline, _eyes, _mouth, _cheeks, _mood_prop, _star_deco, _legs, _PET_BODY, _PET_SKIN, _STAR_SKIN, _PET_BG, _pet_group, _frame, _theme_pal, _to_hue)
from pet_progress import (_ICON_BODY, _ITEM_ICON)


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


_CACHE = None  # 由 _cached 装饰器填充


@st.cache_data(max_entries=200, show_spinner=False)
def room_svg(species, mood="happy", star=False, skin="", extras=None, shiny=False,
             decor=None, weather=None, stage="adult"):
    """像素风小屋场景：普通白天房间 / 星辉夜晚房间 / 主题皮肤房间。

    extras 是同屋的其它宠物（最多 3 只），每项形如
    {"species": "狗", "mood": "happy", "star": False, "skin": "", "shiny": False}，
    站位由本函数按固定三个位置分配，不重叠在主角身上。
    decor 是装修覆盖表 {"wall": 调色, "rug": 调色, "art": 调色, "window": 调色}；
    weather 是天气 key（晴/雨/雪/雷），会往房间上叠雨丝、飘雪、雷光。
    """
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

    _decor_raw = decor or {}

    def _pal(slot):
        """装修槽位既能传家具 dict（含 pal），也能直接传调色 dict。"""
        item = _decor_raw.get(slot) or {}
        return item.get("pal") or (item if ("rug1" in item or "wall2" in item
                                            or "sky" in item or "frame" in item)
                                   else None)

    def _item_id(slot):
        return (_decor_raw.get(slot) or {}).get("id", "")

    decor = {k: _pal(k) for k in ("wall", "rug", "art", "window")}
    win_pal = decor.get("window")
    art_pal = decor.get("art")
    if decor.get("wall"):
        wall, wall2, skirt = (decor["wall"]["wall"], decor["wall"]["wall2"],
                              decor["wall"]["skirt"])

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
    win_id = _item_id("window")
    sky_c = win_pal["sky"] if win_pal else sky
    cloud_c = win_pal["cloud"] if win_pal else cloud
    ground_c = win_pal["ground"] if win_pal else "#A8CE96"
    wx = WEATHER_INFO.get(weather or "") or {}
    rainy = weather in ("雨", "雷")
    snowy = weather == "雪"
    if rainy:
        sky_c, cloud_c = "#7E97B2", "#AEC0D2"
    elif snowy:
        sky_c, cloud_c = "#D5E3EF", "#F3F8FC"
    p.append(_qr(5, 2, 14, 12, frame))
    p.append(_qr(6, 3, 12, 10, sky_c))
    if rainy:
        # 窗外下雨：屋檐压暗 + 斜雨丝 + 乌云
        p.append(_qr(6, 3, 12, 3, "#6E879F", .9))
        for i in range(22):
            x = 6 + (i * 0.53) % 11.4
            y = 3.4 + (i * 1.37) % 8.2
            p.append(_qr(x, y, 0.18, 1.5, "#BFD8EC", .75))
        p.append(_qr(6, 12, 12, 1, "#6E879F"))
    elif snowy:
        p.append(_qr(6, 10, 12, 3, "#FFFFFF"))
        p.append(_qr(6, 12.4, 12, 0.6, "#DCE8F2"))
        for (x, y) in ((7, 5), (9.4, 6.6), (12, 4.4), (15, 7.4), (8, 9),
                       (13.6, 9.6), (16.4, 5.6), (11, 8.2)):
            p.append(_qr(x, y, 0.5, 0.5, "#FFFFFF", .95))
        p.append(_qr(7.2, 8.6, 0.9, 3.4, "#5E9A5C"))
        p.append(_qr(7, 8, 1.3, 1, "#6FA96B"))
        p.append(_qr(15.6, 9.2, 0.8, 3, "#5E9A5C"))
        p.append(_qr(15.4, 8.6, 1.2, 1, "#6FA96B"))
    elif night or win_id == "win_star":
        for (x, y) in ((7, 4), (10, 6), (14, 4), (16, 9), (9, 10), (13, 11)):
            p.append(_qr(x, y, 1, 1, "#FFE066", .9))
        p.append(_qr(13, 4, 2, 2, "#FFF3B0"))
        p.append(_qr(13, 3.4, 1, 1, "#FFF3B0"))
        p.append(_qr(12.6, 4.6, 1, 1, "#FFF3B0"))
    elif win_id == "win_sea":
        p.append(_qr(15, 3.5, 2, 2, "#FFF3B0"))
        p.append(_qr(7, 5, 3, 1, cloud_c, .95))
        p.append(_qr(8, 4, 2, 1, cloud_c, .95))
        p.append(_qr(6, 9, 12, 4, ground_c))
        p.append(_qr(6, 9.4, 12, 0.6, "#7FC0D8", .9))
        p.append(_qr(6, 11, 12, 0.6, "#7FC0D8", .9))
        p.append(_qr(10, 10.4, 3, 0.5, "#CDEBF6", .85))
        p.append(_qr(14, 12, 2.4, 0.5, "#CDEBF6", .85))
    elif win_id == "win_snow":
        p.append(_qr(6, 10, 12, 3, "#F3F8FC"))
        p.append(_qr(6, 9.6, 12, 0.8, "#E6EFF8"))
        p.append(_qr(7.4, 8.4, 0.9, 3.6, "#5E9A5C"))
        p.append(_qr(7.2, 7.8, 1.3, 1, "#6FA96B"))
        p.append(_qr(15.4, 9, 0.9, 3, "#5E9A5C"))
        p.append(_qr(15.2, 8.4, 1.3, 1, "#6FA96B"))
        p.append(_qr(11, 4.4, 5, 1.2, "#FFFFFF", .7))
    else:
        p.append(_qr(15, 3.5, 2, 2, "#FFF3B0"))
        p.append(_qr(7, 5, 3, 1, cloud_c, .95))
        p.append(_qr(8, 4, 2, 1, cloud_c, .95))
        p.append(_qr(12, 8, 3, 1, cloud_c, .8))
        p.append(_qr(7, 10, 12, 3, ground_c))
        p.append(_qr(7, 9.4, 2, 1, ground_c))
        p.append(_qr(16, 9.6, 3, 1, ground_c))
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
    if not night and weather in (None, "晴"):
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

    # ---------- 挂画（装修） ----------
    if art_pal:
        af, ab, ai = art_pal["frame"], art_pal["bg"], art_pal["ink"]
        p.append(_qr(33.4, 4, 5.6, 5.8, af))
        p.append(_qr(33.8, 4.4, 4.8, 5, ab))
        ay = _item_id("art")
        if ay == "art_moon":
            p.append(_qr(35.4, 5.4, 1.8, 1.8, ai))
            p.append(_qr(35.6, 5.6, 0.6, 0.6, ab))
            p.append(_qr(35.4, 7.6, 2, 0.4, "#5B4A94"))
        elif ay == "art_flower":
            p.append(_qr(35.4, 5.8, 1.4, 1.4, ai))
            p.append(_qr(35.2, 5.4, 0.8, 0.8, ai))
            p.append(_qr(36.2, 5.4, 0.8, 0.8, ai))
            p.append(_qr(35.9, 6.6, 0.4, 2, "#6FA96B"))
        else:
            p.append(_qr(34.6, 6.4, 3.2, 1.2, ai))
            p.append(_qr(34.2, 6.2, 1.2, 1.2, ai))
            p.append(_qr(35.8, 6.6, 0.4, 0.4, ab))
            p.append(_qr(37.4, 6.6, 1, 1, ai))
            p.append(_qr(37.8, 6.2, 0.8, 0.8, ai))
        p.append(_qr(33.4, 9.6, 5.6, 0.5, "#00000000" if False else af, .35))

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
    if decor.get("rug"):
        rug1, rug2, rug3 = (decor["rug"]["rug1"], decor["rug"]["rug2"],
                            decor["rug"]["rug3"])
    elif rm:
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

    # ---------- 同屋的其它宠物（最多 3 只，站在左右两侧） ----------
    _slots = ((4.6, 25.0, 0.56), (10.4, 24.7, 0.58), (35.2, 26.4, 0.60))
    for _e, (_sx, _feet, _sc) in zip((extras or [])[:3], _slots):
        _esp = _e.get("species") or "猫"
        if _esp not in PET_SPECIES:
            _esp = "猫"
        _esc = _sc * {"baby": 0.82, "mature": 1.06}.get(_e.get("stage") or "adult", 1.0)
        p.append(_rz(_sx, _feet - 0.6, 5.0 * _esc, 0.7, "#000000", .15))
        _epet = _pet_group(_esp, _e.get("mood") or "happy",
                           bool(_e.get("star")), _e.get("skin") or "",
                           bool(_e.get("shiny")))
        _tx = int(round(_sx * 20 - 120 * _esc))
        _ty = int(round(_feet * 20 - 205 * _esc))
        p.append(
            f'<g transform="translate({_tx} {_ty}) scale({_esc})">{_epet}</g>')

    # ---------- 当前宠物 ----------
    if star:
        p.append(_rz(25, 24, 11, 4.6, "#6C5CE7", .3))
        p.append(_rz(25, 24, 6.4, 2.8, "#8F7CFF", .28))
    p.append(_rz(25, 26.4, 8.4, 1.2, "#000000", .18))
    _ms = 1.5 * {"baby": 0.78, "mature": 1.08}.get(stage, 1.0)
    _mtx = int(round(330 + 120 * (1.5 - _ms)))
    _mty = int(round(233 + 205 * (1.5 - _ms)))
    p.append(f'<g transform="translate({_mtx} {_mty}) scale({_ms:.3f})">'
             f'{_pet_group(sp, mood, star, skin, shiny)}</g>')

    if star:
        for (x, y) in ((4, 3), (18, 2), (36, 2), (56, 4), (6, 20), (50, 22), (57, 18)):
            p.append(_qr(x, y, 0.6, 1.8, "#FFD54A", .95))
            p.append(_qr(x - 0.6, y + 0.6, 1.8, 0.6, "#FFD54A", .95))

    # ---------- 天气层 ----------
    wkey = weather if weather in ("晴", "雨", "雪", "雷") else ""
    if wkey in ("雨", "雪", "雷"):
        tint = WEATHER_INFO[wkey]["tint"]
        p.append(f'<rect x="0" y="0" width="1200" height="620" fill="{tint}" '
                 f'opacity="{0.16 if wkey == "雷" else 0.10}"/>')
    if wkey == "雨":
        for i in range(34):
            x = (i * 149) % 1160
            y = (i * 97) % 540
            p.append(f'<polygon points="{x},{y} {x + 5},{y + 30} {x + 11},{y + 30} '
                     f'{x + 6},{y}" fill="#A8CCE6" opacity=".7"/>')
        for i in range(18):
            x = (i * 211) % 1140
            y = (i * 173) % 520
            p.append(f'<rect x="{x}" y="{y}" width="6" height="10" fill="#CDE2F2" '
                     f'opacity=".5"/>')
        p.append(_qr(0, 0, 60, 2, "#5E7B96", .25))
    if wkey == "雪":
        for i in range(60):
            x = (i * 173) % 1180
            y = (i * 61) % 590
            sz = 5 if i % 5 else 7
            p.append(f'<rect x="{x}" y="{y}" width="{sz}" height="{sz}" '
                     f'fill="#FFFFFF" opacity=".85"/>')
        for i in range(12):
            x = (i * 263) % 1160
            y = (i * 149) % 570
            p.append(f'<rect x="{x}" y="{y}" width="9" height="9" fill="#FFFFFF" '
                     f'opacity=".95"/>')
    if wkey == "雷":
        # 闪电只出现在窗外，室内是整体压暗 + 一层冷光
        p.append('<polygon points="230,60 268,190 244,190 282,320 208,168 236,168" '
                 'fill="#FFF6C2" opacity=".95"/>')
        p.append('<polygon points="214,60 230,60 268,190 244,190 282,320 208,168 236,168" '
                 'fill="#FFE066" opacity=".8"/>')
        p.append('<ellipse cx="300" cy="160" rx="240" ry="150" fill="#FFF3B0" '
                 'opacity=".14"/>')
        p.append(_qr(0, 0, 60, 3, "#2A2E44", .28))
    if wkey == "晴":
        p.append('<polygon points="300,100 420,100 560,360 400,360" fill="#FFF7D8" '
                 'opacity=".10"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 620" '
            'preserveAspectRatio="xMidYMid slice" '
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
@media (max-width: 760px) {
    .block-container {padding:.7rem .5rem 2rem;}
    .game-hud {gap:8px;}
    .hud-title {font-size:1.25rem;}
    .st-key-dock [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important; gap:.45rem;}
    .st-key-dock [data-testid="stColumn"] {
        flex:1 1 46% !important; width:46% !important;
        min-width:46% !important; max-width:48% !important;
    }
    .st-key-dock button, .st-key-dock [data-testid="stPopover"] button {
        font-size:.9rem; padding:.35rem .2rem;
    }
    .st-key-scene svg {max-width:100%;}
}
.block-container {padding:1.3rem 1.1rem 2.6rem; max-width:1280px;}

html, body, [class*="css"] {
    font-family:"Zpix","Fusion Pixel","Cascadia Mono","SimHei","黑体",
                "Microsoft YaHei",monospace;
    letter-spacing:.3px;
    -webkit-font-smoothing:none;
}
/* 功能分区：像素风胶囊 */
[class*="st-key-main_section"] [role="radiogroup"] {gap:6px;}
[class*="st-key-main_section"] button {border-radius:0 !important; border:2px solid #C9702C !important;
    background:#FFF3D6 !important; color:#3B2A18 !important; font-weight:700;}
[class*="st-key-main_section"] button[aria-checked="true"] {background:#FFC94D !important;
    box-shadow:3px 3px 0 #3B2A18;}

/* 存档槽缩略头像：小尺寸像素宠物 */
.slot-thumb {display:flex; align-items:flex-start;}
.slot-thumb svg {width:56px !important; height:auto !important; max-width:56px;}
.slot-thumb img {width:56px !important; height:auto; image-rendering:pixelated;}

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
.bond-box {margin:6px 0 2px; padding:8px 10px; border-radius:10px;
    background:#FFF4DB; border:2px dashed #E7CB92;}
.bond-top {display:block; font-size:.72rem; font-weight:900; color:#7A5B33;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.bond-pct {display:none;}
.bond-bar {height:8px; margin:5px 0 4px; background:#F0DFC0; border:1px solid #DCC196;}
.bond-bar i {display:block; height:100%; background:#E8A15C;}
.bond-line {font-size:.72rem; color:#4A3218; font-weight:700; line-height:1.35;}
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
/* dock 里任何 popover 触发按钮（不限 key 前缀）都跟四个大按钮同款 */
.st-key-dock [data-testid="stPopover"] {width:100%;}
.st-key-dock [data-testid="stPopover"] button {
    width:100%; min-height:78px; padding:8px 4px; border-radius:0;
    background:var(--cream); border:3px solid var(--ink);
    box-shadow:5px 5px 0 var(--wood); color:#2B1D10; font-weight:900;
    font-size:.88rem; display:flex; flex-direction:column; align-items:center;
    justify-content:center; gap:2px; transition:none;}
.st-key-dock [data-testid="stPopover"] button:hover {
    background:var(--cream2); border-color:var(--ink);
    box-shadow:6px 6px 0 var(--gold2);}
.st-key-dock [data-testid="stPopover"] button:active {
    transform:translate(5px,5px); box-shadow:0 0 0 var(--wood);}
.st-key-dock [data-testid="stPopover"] button > div {
    flex-direction:column; align-items:center; justify-content:center; gap:2px !important;}
.st-key-dock [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
    font-size:26px; width:26px; height:26px; color:#8A5A1C;}
.st-key-dock [data-testid="stPopover"] button p {
    font-size:.86rem; font-weight:900; margin:0; line-height:1.2;}
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
/* HUD 里的天气 / 节日小牌子 */
.weather-chip {
    display:inline-block; margin-left:6px; padding:2px 9px; white-space:nowrap;
    border:2px solid #8A6A44; border-radius:0; color:#FFFDF2;
    font-weight:900; font-size:.78rem; text-shadow:1px 1px 0 rgba(0,0,0,.35);
    vertical-align:middle;
}
.fest-chip {color:#FFF7E0;}
.fest-banner {
    margin:6px 0 2px; padding:8px 12px; background:#FFF2DC;
    border:3px solid #D9534F; border-radius:0; box-shadow:4px 4px 0 #C48A5A;
    color:#8A3A2A; font-weight:900;
}
/* 音效播放器占位：整块压成 1px，不占版面 */
div[class*="st-key-sfxplayer_"] {height:1px !important; min-height:1px !important;
    overflow:hidden !important; margin:0 !important; padding:0 !important;
    opacity:0.01;}
div[class*="st-key-sfxplayer_"] [data-testid="stAudio"] {height:1px;}
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
    border:2.5px solid #E8B48C; border-radius:16px; background:var(--cream);
    flex-wrap:wrap; min-width:0; box-shadow:4px 4px 0 #EFC9A6;
}
.pe-item-ico {width:56px; height:56px; flex:none; border-radius:12px;
    background:#FFE9BE; color:#5A3A10; border:2.5px solid #E8B48C;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
    box-shadow:2px 2px 0 #EFC9A6;}
.pe-item > div:not(.pe-item-ico):not(.pe-item-price) {min-width:0; flex:1 1 auto;}
.pe-item-name {font-weight:900; color:#2B1D10; font-size:.98rem; line-height:1.35;
    word-wrap:break-word; overflow-wrap:anywhere;}
.pe-item-desc {font-size:.8rem; color:#4A3218; font-weight:700; margin-top:2px;
    line-height:1.45; word-wrap:break-word; overflow-wrap:anywhere;}
.pe-item-price {margin-left:auto; display:flex; align-items:center; gap:4px;
    font-weight:900; color:#B8690E; white-space:nowrap; flex:0 0 auto;}

/* ================= 商店货架（暖粉小店） ================= */
.shop-card {
    text-align:center; padding:10px 6px; border:2.5px solid #E8B48C;
    background:#FFF9F1; border-radius:14px; box-shadow:3px 3px 0 #EFC9A6;
    margin-bottom:6px;
}
.shop-card.active {border-color:#E87AA8; background:#FFF0F6; box-shadow:3px 3px 0 #F2C4D8;}
.shop-card-ico {
    width:44px; height:44px; margin:0 auto 6px; background:#FFE9BE;
    border:2px solid #E8B48C; border-radius:12px;
    display:flex; align-items:center; justify-content:center;
}
.shop-card-name {font-weight:900; color:#3B2A18; font-size:.82rem; line-height:1.25; min-height:2em;}
.shop-card-price {margin-top:4px; font-weight:900; color:#B8690E; display:flex; justify-content:center; gap:4px; align-items:center;}
.shop-detail {margin:10px 0 6px; padding:12px; border:2.5px solid #E8B48C;
    border-radius:16px; background:#FFFDF8;}

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
.pe-ach-rw {display:inline-block; margin-top:3px; padding:1px 7px; border-radius:8px;
    background:#FFF3D0; border:1px solid #E6C88C; font-size:.72rem; font-weight:900;
    color:#8A5A14;}
.pe-ach.locked .pe-ach-rw {background:#F0E2C6; border-color:#DCC49A; color:#6B5222;}
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

/* ================= 热点导航 + 分区横幅 ================= */
.hotspot-title {margin:10px 0 6px; font-weight:900; color:#4A3218; font-size:.92rem;}
.sec-banner {display:flex; align-items:center; gap:12px; margin:8px 0 12px;
  padding:12px 16px; border:3px solid #6B4423; border-radius:16px;
  box-shadow:5px 5px 0 rgba(107,68,35,.25); color:#fff;}
.sec-banner-ico {width:44px; height:44px; flex:none; display:flex; align-items:center;
  justify-content:center; background:rgba(255,255,255,.22); border-radius:12px;
  border:2px solid rgba(255,255,255,.5);}
.sec-banner-title {font-weight:900; font-size:1.15rem; line-height:1.2;}
.sec-banner-sub {font-size:.82rem; opacity:.92; margin-top:2px; font-weight:700;}
.sec-shop {background:linear-gradient(135deg,#F0A2C4,#E87AA8);}
.sec-fun {background:linear-gradient(135deg,#B7A8D8,#8A6AC0);}
.sec-star {background:linear-gradient(135deg,#8A6AC0,#5A449A);}
.sec-decor {background:linear-gradient(135deg,#E8B06A,#D98A3A);}
.sec-dex {background:linear-gradient(135deg,#C9A86B,#A97F3F);}
.sec-pet {background:linear-gradient(135deg,#F2A6A6,#E0707E);}
.sec-help {background:linear-gradient(135deg,#9CC4E0,#6FA3C4);}
.sec-ach {background:linear-gradient(135deg,#D9A93A,#B8861F);}
.sec-svc {background:linear-gradient(135deg,#7FA8B8,#5A8296);}
.sec-log {background:linear-gradient(135deg,#9CC47A,#6FA052);}

/* 旧顶部分区标签条隐藏（状态仍由该 widget 绑定，导航收进底部圆形菜单） */
.st-key-main_section { display:none !important; }

/* ================= 底部圆形导航 ================= */
.st-key-nav_out button, .st-key-nav_shop button, .st-key-nav_bag button,
.st-key-nav_more button {
    background:#FFF3D8; border:3px solid #B58A4E; border-radius:18px;
    font-weight:900; color:#4A3218; box-shadow:3px 3px 0 #EFC9A6;
    min-height:64px; padding:10px 6px;
}
.st-key-nav_shop button[kind="primary"], .st-key-nav_bag button[kind="primary"] {
    background:#F6C98B; border-color:#8A5A14;
}
/* 底部导航固定悬浮在广场右下角 */
.st-key-plaza_nav { position:fixed; right:18px; bottom:18px; z-index:30; width:330px; }
.st-key-plaza_nav [data-testid="stHorizontalBlock"] { gap:10px; }
.st-key-plaza_nav button { min-height:72px; border-radius:22px; }
/* 给固定导航留出底部空间，避免遮住下方面板 */
.stMainBlockContainer { padding-bottom:120px; }

/* ===== 首页主场景全屏（弹层打开时 :not(:has(...)) 自动不生效） ===== */
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) {
    max-width:100% !important; padding:0 !important;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-scene_wrap {
    position:fixed; inset:0; z-index:0; margin:0 !important; padding:0 !important;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-scene {
    margin:0 !important; padding:0 !important; height:100vh;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .pet-stage {
    width:100vw !important; height:100vh !important;
    border:0 !important; border-radius:0 !important; box-shadow:none !important;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .pet-stage svg {
    width:100% !important; height:100% !important;
}
/* 背景音乐开关：顶部居中偏左，避开左右两张卡片 */
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-bgm_bar {
    position:fixed; top:10px; left:280px; z-index:30; max-width:220px;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-bgm_bar [data-testid="stExpander"] {
    background:rgba(255,246,224,.92); border:2px solid #B58A4E; border-radius:14px;
    box-shadow:3px 3px 0 rgba(120,80,30,.2);
}
/* 天气说明：底部居中悬浮，避开左右两侧卡片与导航 */
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-weather_line {
    position:fixed; left:50%; transform:translateX(-50%); bottom:96px; z-index:6; max-width:38%;
}
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-weather_line [data-testid="stCaptionContainer"] {
    background:rgba(255,246,224,.85); border-radius:10px; padding:4px 10px; white-space:nowrap;
}
/* 首页全屏时隐藏终端提示条（弹层内仍保留） */
.stMainBlockContainer:has(.st-key-plaza_nav):not(:has(.st-key-panel_overlay)) .st-key-footer_note {
    display:none;
}

/* 分区弹出覆盖层 */
.st-key-panel_overlay { position:fixed; inset:0; z-index:40; overflow-y:auto;
    background:rgba(43,29,16,.55); padding:20px; }
.st-key-panel_overlay > div { background:var(--cream); border:4px solid var(--ink);
    border-radius:20px; padding:16px; max-width:1100px; margin:0 auto; }
.st-key-panel_overlay .st-key-panel_close button {
    background:#F6C98B; border:3px solid #8A5A14; border-radius:14px; font-weight:900;
}
/* 覆盖层打开时收起「更多」残留菜单（PopoverBody 为 body 下的浮动门户） */
.stMainBlockContainer:has(.st-key-panel_overlay) [data-testid="stPopoverBody"],
body:has(.st-key-panel_overlay) [data-testid="stPopoverBody"] { display:none !important; }

/* ================= 广场悬浮圆角卡片 ================= */
.st-key-scene { position:relative; }
/* markdown 渲染出的内层容器不要成为定位父级，保证卡片相对舞台四角定位 */
.st-key-scene .stElementContainer { position:static !important; }
.float-card {
    position:absolute; z-index:5;
    background:rgba(255,246,224,.95); border:3px solid #B58A4E; border-radius:20px;
    box-shadow:4px 5px 0 rgba(120,80,30,.22); padding:10px 14px; color:#3B2A18;
}
.float-tl { top:14px; left:14px; max-width:52%; }
.float-tl-inner { display:flex; gap:10px; align-items:center; }
.float-avatar { width:54px; height:54px; flex:none; border-radius:50%; overflow:hidden;
    background:#FFE9BE; border:3px solid #B58A4E; }
.float-avatar svg { width:100%; height:100%; display:block; }
.float-title { font-size:1.2rem; font-weight:900; letter-spacing:1px; color:#3B2A18;
    text-shadow:2px 2px 0 #FFC94D; }
.float-sub { font-size:.74rem; font-weight:700; color:#5A3E1E; margin-top:2px; }
.float-money { display:flex; gap:8px; margin-top:6px; flex-wrap:wrap; }
.float-money .money-pill { padding:3px 10px; font-size:.85rem; box-shadow:3px 3px 0 var(--wood); }
.float-tr { top:14px; right:14px; width:42%; }
.float-card-title { font-size:.9rem; font-weight:900; color:#8A5A14; margin-bottom:6px; }
.float-task { display:flex; align-items:center; gap:8px; font-weight:800; font-size:.82rem; padding:3px 0; }
.float-task.done { opacity:.55; }
.ft-name { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ft-rew { color:#B8690E; font-weight:900; }
.float-bl { bottom:14px; left:14px; width:26%; }
.float-stat { display:flex; align-items:center; gap:8px; padding:3px 0; font-weight:900; }
.fs-ico { width:26px; height:26px; border-radius:50%; display:flex; align-items:center;
    justify-content:center; border:2px solid; flex:none; }
.fs-label { font-size:.85rem; }
.fs-val { margin-left:auto; font-size:1rem; font-variant-numeric:tabular-nums; }

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
@media (max-width:500px){
    .st-key-scene_wrap, .st-key-scene {position:static !important; height:auto !important;}
    .float-card {position:static; margin:8px 0; max-width:100% !important; width:100% !important;}
    .st-key-plaza_nav {position:static; width:100%; margin-top:10px;}
    .st-key-bgm_bar, .st-key-weather_line {position:static !important; max-width:100% !important; transform:none !important;}
    .st-key-footer_note {display:block !important;}
}
</style>
"""
