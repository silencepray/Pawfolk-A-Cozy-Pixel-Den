# -*- coding: utf-8 -*-
"""pet_svg（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
import colorsys
import math
from pet_constants import *
import streamlit as st
from pet_progress import *
from pet_progress import (_ICON_BODY, _ITEM_ICON)

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


SHINY_HUE = 188          # 异色把全身色相拉到冰蓝紫一侧，和星辉的紫色区分开
SHINY_SAT = 1.35


def _shiny_color(val, hue=SHINY_HUE, sat=SHINY_SAT):
    """单色异色化：色相统一、提饱和；接近白色的浅色额外压一点明度，
    否则白毛宠物的异色会跟原色分不出来。"""
    h = val.lstrip("#")
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return val
    _, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    ss = min(1.0, ss * sat)
    if vv > 0.86 and ss < 0.28:      # 白/米白：给一层淡青，并压到 0.90 明度
        ss = 0.34
        vv = min(vv, 0.90)
    r2, g2, b2 = colorsys.hsv_to_rgb(hue / 360.0, ss, vv)
    return "#%02X%02X%02X" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))


def _shiny_pal(pal):
    """异色变体：整身色相统一挪位，明暗关系保持不变。"""
    out = dict(pal)
    for key, val in list(pal.items()):
        if isinstance(val, str) and val.startswith("#") and len(val) == 7:
            out[key] = _shiny_color(val)
    return out


def _pet_group(species, mood="happy", star=False, skin="", shiny=False):
    """返回 240×240 坐标系里的宠物本体（立绘与房间共用）。"""
    sp = species if species in PET_SPECIES else "猫"
    if mood not in ("happy", "sad", "sick"):
        mood = "happy"
    pal = dict(_STAR_SKIN[sp] if star else _PET_SKIN[sp])
    pal = _theme_pal(pal, skin)
    if shiny:
        pal = _shiny_pal(pal)
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
    if shiny:
        # 异色闪粉：几颗高亮像素 + 边框外的光点，和普通颜色一眼能分开
        for (x, y) in ((20, 18), (6, 16), (22, 8), (4, 22)):
            s.append(_r(x, y, 1, 1, "#FFF1FF", .95))
        s.append(_r(21, 17, 0.6, 0.6, "#B98BFF"))
        s.append(_r(5, 15, 0.6, 0.6, "#B98BFF"))
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


_CACHE = None  # 由 _cached 装饰器填充


@st.cache_data(max_entries=200, show_spinner=False)
def growth_stage(pet):
    """成长阶段：Lv1~9 幼体、10~39 成年、40+ 成熟。"""
    try:
        lv = int(pet.get("lv", pet.get("level", 1)) or 1)
    except (TypeError, ValueError):
        lv = 1
    if lv >= 40:
        return "mature"
    if lv >= 10:
        return "adult"
    return "baby"


STAGE_LABEL = {"baby": "幼体", "adult": "成年", "mature": "成熟期"}


def pet_svg(species, mood="happy", star=False, skin="", shiny=False, stage="adult"):
    sp = species if species in PET_SPECIES else "猫"
    if mood not in ("happy", "sad", "sick"):
        mood = "happy"
    th = SKIN_THEMES.get(skin or "")
    if th:
        bg1, bg2 = th["bg"]
    elif shiny:
        bg1, bg2 = ("#E4F3FB", "#C9E6F5") if not star else ("#1B2A46", "#243A5E")
    else:
        bg1, bg2 = (_STAR_BG if star else _PET_BG[sp])
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
    # 三档形态：幼体缩小 + 奶嘴；成年原样；成熟放大 + 小皇冠 / 围巾
    _tf = {"baby": 'translate(36 48) scale(0.70)',
           "mature": 'translate(-9.6 -19.2) scale(1.08)'}.get(stage, "")
    if _tf:
        parts.append(f'<g transform="{_tf}">')
    if th:
        parts.append(_pet_group(sp, mood, star, skin, shiny))
        parts.append(_r(9, 26, 2, 1, th["glow"]))
        parts.append(_r(9, 27, 1, 1, th["glow"]))
    else:
        parts.append(_pet_group(sp, mood, star, shiny=shiny))
    if stage == "baby":
        # 奶嘴 + 头顶小尖帽
        parts.append(_r(17, 17, 2, 1, "#FFD1E0"))
        parts.append(_r(18, 18, 1, 1, "#FF8FB1"))
        parts.append(_r(13, 2, 4, 1, "#8DD3C7"))
        parts.append(_r(14, 1, 2, 1, "#8DD3C7"))
    elif stage == "mature":
        # 小皇冠 + 围巾 + 两点星屑
        for x, y in ((13, 2), (15, 1), (17, 2)):
            parts.append(_r(x, y, 1, 1, "#FFD84D"))
        parts.append(_r(13, 3, 5, 1, "#FFD84D"))
        parts.append(_r(9, 18, 12, 1, "#E2574C"))
        parts.append(_r(18, 19, 2, 2, "#E2574C"))
        parts.append(_r(4, 9, 1, 1, "#FFF3B0"))
        parts.append(_r(25, 14, 1, 1, "#FFF3B0"))
    if _tf:
        parts.append("</g>")
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
    return pet_svg(species_of(pet), pet_mood(pet), star_art(pet), skin_theme(pet),
                   bool(pet.get("shiny", False)), growth_stage(pet))

