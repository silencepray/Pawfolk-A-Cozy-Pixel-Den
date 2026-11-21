# -*- coding: utf-8 -*-
"""操作场景 + 特效层：给每个动作一套自己的背景和道具，配一层纯 CSS 粒子动画。

设计约定：
- 画布和 room_svg 一样是 1200×620、60×30 的像素格（一格 20 单位），
  宠物固定画在 translate(330 233) scale(1.5)，所以换背景不会让宠物跳位。
- 粒子用 div + @keyframes，不依赖 JS（Streamlit 会把 script 丢掉）。
- strength 表示“这次做得有多到位”：洗澡用了肥皂是 2，长途探索是 3，
  数字越大粒子越多、光晕越强。
"""
import random
import streamlit as st

from pet_room import _qr, _rz, room_svg
from pet_svg import _pet_group
from pet_constants import PET_SPECIES

_MOODS = ("happy", "sad", "sick")

_CSS = """
<style>
.pet-stage{position:relative;overflow:hidden;border:4px solid #6B4423;
  box-shadow:8px 8px 0 #C08A57;background:#20182F;line-height:0}
.pet-stage svg{display:block;width:100%;height:auto;image-rendering:pixelated}
.ps-fx{position:absolute;inset:0;pointer-events:none;line-height:1}
.ps-p{position:absolute;opacity:0;font-weight:700;
  animation-name:ps-rise;animation-timing-function:cubic-bezier(.25,.7,.4,1);
  animation-iteration-count:infinite}
@keyframes ps-rise{
  0%{opacity:0;transform:translate(0,10px) scale(.55)}
  18%{opacity:1}
  70%{opacity:.85}
  100%{opacity:0;transform:translate(var(--dx,0px),-110px) scale(1.15)}}
.ps-twinkle{animation-name:ps-twinkle;animation-timing-function:ease-in-out}
@keyframes ps-twinkle{
  0%,100%{opacity:.15;transform:scale(.6) rotate(0deg)}
  50%{opacity:1;transform:scale(1.2) rotate(18deg)}}
.ps-bob{animation-name:ps-bob;animation-timing-function:ease-in-out}
@keyframes ps-bob{
  0%,100%{opacity:.7;transform:translateY(0) scale(1)}
  50%{opacity:1;transform:translateY(-14px) scale(1.08)}}
.ps-glow{position:absolute;left:50%;top:62%;width:46%;height:34%;
  transform:translate(-50%,-50%);border-radius:50%;pointer-events:none;
  animation:ps-pulse 2.4s ease-in-out infinite}
@keyframes ps-pulse{0%,100%{opacity:.25}50%{opacity:.6}}
</style>
"""

# 每个场景的粒子：(符号, 颜色, 动画类)
_PARTICLES = {
    "bath": (("○", "#BFE6F5", "ps-p"), ("•", "#FFFFFF", "ps-p")),
    "feed": (("♥", "#E98A9A", "ps-p"), ("~", "#FFF3D0", "ps-p")),
    "play": (("★", "#FFC94A", "ps-p"), ("●", "#FF9F6E", "ps-p")),
    "explore": (("✦", "#FFE066", "ps-twinkle"), ("✧", "#C9F0A8", "ps-twinkle")),
    "clinic": (("✚", "#8FD3A8", "ps-p"), ("♥", "#F3A6B0", "ps-p")),
    "craft": (("◆", "#F0B24A", "ps-p"), ("✧", "#FFE9A8", "ps-twinkle")),
    "star": (("✧", "#B79BFF", "ps-p"), ("★", "#FFE066", "ps-twinkle"),
             ("✦", "#FFFFFF", "ps-bob")),
    "garden": (("✿", "#F6A6C0", "ps-p"), ("·", "#CDEBAF", "ps-bob")),
    "plaza": (("✿", "#F6A6C0", "ps-p"), ("·", "#CDEBAF", "ps-bob"),
              ("✧", "#FFF3D0", "ps-twinkle")),
    "sec_shop": (("●", "#F6A6C0", "ps-p"), ("♥", "#FFD3E0", "ps-p")),
    "sec_fun": (("◆", "#FFD34E", "ps-p"), ("✚", "#8FD3A8", "ps-p")),
    "sec_decor": (("✿", "#F6A6C0", "ps-p"), ("◆", "#F0B24A", "ps-twinkle")),
    "sec_dex": (("✧", "#C9A86B", "ps-twinkle"), ("·", "#8FB6C4", "ps-bob")),
    "sec_pet": (("♥", "#E98A9A", "ps-p"), ("●", "#FFE066", "ps-bob")),
    "sec_help": (("✧", "#9CC4E0", "ps-twinkle"), ("·", "#FFF3D0", "ps-p")),
    "sec_ach": (("★", "#FFE066", "ps-twinkle"), ("◆", "#F0B24A", "ps-p")),
    "sec_svc": (("·", "#8FB6C4", "ps-bob"), ("✧", "#C9CDD6", "ps-twinkle")),
    "sec_log": (("·", "#9CC47A", "ps-bob"), ("✧", "#FFF3D0", "ps-p")),
}

# 场景主色，用于粒子层底光
_GLOW = {
    "bath": "#8FD3E8", "feed": "#E8C08A", "play": "#F5C8A8",
    "explore": "#7FA86B", "clinic": "#A8D8C0", "craft": "#C59A5C",
    "star": "#8A6AC0", "garden": "#9CC47A", "plaza": "#BFE3F7",
    "sec_shop": "#F0A2C4", "sec_fun": "#B7A8D8", "sec_decor": "#E8C8A0",
    "sec_dex": "#C9A86B", "sec_pet": "#F2A6A6", "sec_help": "#B7CFD8",
    "sec_ach": "#C9A24A", "sec_svc": "#9FBFCB", "sec_log": "#9CC47A",
}


def _tile_floor(p, y0, color, line, step=2):
    p.append(_qr(0, y0, 60, 31 - y0, color))
    for y in range(int(y0) + step, 31, step):
        p.append(_qr(0, y, 60, 0.35, line, .8))


def _pet(p, sp, mood, star, skin, dy=0, shadow=True, shiny=False):
    if shadow:
        p.append(_rz(25, 26.6 + dy, 8.4, 1.2, "#000000", .18))
    p.append(f'<g transform="translate(330 {233 + dy * 20}) scale(1.5)">'
             f'{_pet_group(sp, mood, star, skin, shiny)}</g>')


def _bath_svg(sp, mood, star, skin, strength, shiny=False):
    """浴室：瓷砖墙 + 浴缸 + 淋浴 + 泡泡。"""
    p = []
    p.append(_qr(0, 0, 60, 19, "#E8F6FC"))
    for x in range(0, 60, 4):
        p.append(_qr(x, 0, 0.5, 19, "#CBE6F2"))
    for y in range(0, 19, 4):
        p.append(_qr(0, y, 60, 0.5, "#CBE6F2"))
    p.append(_qr(0, 19, 60, 2, "#B7DCEA"))
    _tile_floor(p, 21, "#D6EAF3", "#BCDCEA", 3)
    # 镜子 + 毛巾架
    p.append(_qr(3, 2.5, 10, 9, "#8FB6C4"))
    p.append(_qr(3.6, 3.1, 8.8, 7.8, "#DCF2FA"))
    p.append(_qr(4.4, 3.8, 7, 5, "#FFE9C8", .25))
    p.append(_qr(47, 2, 0.6, 8, "#9EBDCB"))
    p.append(_qr(46, 8.4, 4, 1, "#9EBDCB"))
    # 浴缸（白瓷 + 水）
    p.append(_rz(30, 25.4, 17, 4.4, "#9EBDCB"))
    p.append(_rz(30, 24.8, 16.4, 4, "#EFFAFE"))
    p.append(_rz(30, 24.2, 15.4, 3.4, "#86CDE6"))
    p.append(_rz(30, 23.4, 13.8, 2.6, "#B7E4F4"))
    p.append(_qr(13.2, 24.6, 1.2, 10.6, "#E4F5FB"))
    p.append(_qr(45.6, 24.6, 1.2, 10.6, "#E4F5FB"))
    p.append(_qr(22, 30.6, 16, 1, "#9EBDCB"))
    # 泡沫堆：只在左边水面上，不糊住宠物
    for (x, y, rx, ry) in ((14.6, 22.4, 2.4, 1.2), (17.6, 21.8, 2, 1.1),
                           (12, 22.6, 1.8, 1), (20.4, 22.2, 1.6, 0.9)):
        p.append(_rz(x, y, rx, ry, "#FFFFFF", .95))
    # 橡胶鸭 + 小凳子 + 海绵
    p.append(_rz(51, 25.4, 2, 1.4, "#FFD34E"))
    p.append(_rz(50.2, 23.8, 1.1, 1.1, "#FFD34E"))
    p.append(_qr(51.1, 24.2, 1, 0.5, "#F2A03C"))
    p.append(_qr(50.9, 23.4, 0.5, 0.5, "#5C4425"))
    p.append(_qr(3, 23, 5, 1, "#C79A63"))
    p.append(_qr(3.4, 24, 0.8, 3, "#A9744A"))
    p.append(_qr(7, 24, 0.8, 3, "#A9744A"))
    p.append(_qr(3.2, 21.4, 4.4, 1.4, "#F7B6C2"))       # 海绵
    p.append(_qr(3.6, 21.8, 1.2, 0.6, "#FCE0E6"))
    if strength >= 2:                                    # 肥皂（用了肥皂才有）
        p.append(_qr(8.2, 23.4, 3, 1.3, "#F6E7A6"))
        p.append(_qr(8.5, 23.0, 2.4, 0.6, "#FFF6D2"))
        p.append(_qr(8.2, 24.7, 3, 0.3, "#E4D083", .5))
    # 淋浴头 + 水柱
    p.append(_qr(42.5, 3, 0.8, 6, "#B7CFD8"))
    p.append(_qr(40, 6.6, 6, 1.4, "#D6ECF4"))
    for x in (40.6, 42.2, 43.8, 45):
        p.append(_qr(x, 8, 0.5, 6, "#CFEBF7", .8))
    _pet(p, sp, mood, star, skin, dy=0.3, shiny=shiny)
    if strength >= 2:
        for (x, y, rx, ry) in ((15.4, 20.6, 2.6, 1.4), (18.6, 19.8, 2.2, 1.2),
                               (12.6, 20.2, 1.8, 1)):
            p.append(_rz(x, y, rx, ry, "#FFFFFF", .9))
    return _wrap(p, still=True)


def _feed_svg(sp, mood, star, skin, strength, shiny=False):
    """餐厅角：木地板 + 大食盆 + 餐桌 + 食物。"""
    p = []
    p.append(_qr(0, 0, 60, 19, "#FBEBD3"))
    for x in range(0, 60, 3):
        p.append(_qr(x, 0, 0.4, 19, "#F2DCB6", .8))
    p.append(_qr(0, 19, 60, 1.6, "#C79A63"))
    _tile_floor(p, 20.6, "#DDB180", "#C99A6A", 2)
    # 窗户（阳光）
    p.append(_qr(4, 3, 12, 9, "#9B6B3A"))
    p.append(_qr(4.6, 3.6, 10.8, 7.8, "#BFE8FA"))
    p.append(_qr(9.6, 3.6, 0.5, 7.8, "#9B6B3A"))
    p.append(_qr(4.6, 7.2, 10.8, 0.5, "#9B6B3A"))
    p.append('<polygon points="120 120 300 120 420 620 150 620" fill="#FFF7D8" opacity=".16"/>')
    # 餐桌 + 椅子
    p.append(_qr(44, 12, 14, 1.6, "#B9824E"))
    p.append(_qr(45, 13.6, 1.4, 9, "#A9744A"))
    p.append(_qr(55, 13.6, 1.4, 9, "#A9744A"))
    p.append(_qr(46, 9.6, 4, 2.4, "#F7F3E4"))
    p.append(_qr(51, 10.2, 2.6, 1.8, "#F2A6A6"))
    # 食物堆：面包 + 葡萄 + 蛋糕
    p.append(_qr(37.6, 17, 6, 2.2, "#E8B06A"))
    p.append(_qr(38, 16.6, 5.2, 0.8, "#F6C98B"))
    for (gx, gy) in ((39.6, 14.2), (40.8, 14.2), (42, 14.2),
                     (40.2, 13.4), (41.4, 13.4), (40.8, 12.6)):
        p.append(_qr(gx, gy, 1, 1, "#9C6FC0"))
    p.append(_qr(40.8, 12.2, 0.8, 0.6, "#7FA86B"))
    # 超大食盆（正对宠物）
    p.append(_rz(35, 27.6, 7.4, 2.6, "#EFE3CB"))
    p.append(_rz(35, 27.2, 6.6, 2.1, "#FFFDF6"))
    p.append(_rz(35, 27, 5.2, 1.5, "#E8A15C"))
    p.append(_qr(31.6, 25.6, 1.2, 0.8, "#E8A15C"))
    p.append(_qr(36.4, 25.6, 1.2, 0.8, "#E8A15C"))
    # 餐具：勺子 / 小碗
    p.append(_qr(43, 22, 0.8, 4.4, "#C9CDD6"))
    p.append(_rz(43.4, 21.4, 1.6, 1.1, "#E3E7EE"))
    p.append(_qr(6, 24, 4, 1.6, "#F6E9D2"))
    p.append(_qr(6.4, 24.4, 3.2, 0.8, "#F2C58A"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    if strength >= 2:
        p.append(_qr(24, 22, 4, 1, "#FFF3D8", .8))
        p.append(_qr(25, 21, 2, 1, "#FFF3D8", .7))
        for x in (9, 11, 13):
            p.append(_qr(x, 13.4, 1, 2, "#FFD9A0", .8))   # 热气
    return _wrap(p, still=True)


def _play_svg(sp, mood, star, skin, strength, shiny=False):
    """院子里：草地 + 栅栏 + 球 + 逗猫棒。"""
    p = []
    p.append(_qr(0, 0, 60, 13, "#CFEAFA"))
    p.append(_qr(3, 2, 10, 2, "#FFFFFF", .9))
    p.append(_qr(4.5, 1.4, 7, 1.4, "#FFFFFF", .9))
    p.append(_qr(40, 3, 11, 2, "#FFFFFF", .85))
    p.append(_qr(41.5, 2.4, 8, 1.4, "#FFFFFF", .85))
    p.append(_qr(17, 0.6, 4, 4, "#FFE066"))
    p.append(_rz(19, 2.6, 2.4, 2.4, "#FFD34E"))
    p.append(_qr(0, 13, 60, 18, "#A8D48F"))
    for x in range(0, 60, 2):
        p.append(_qr(x, 13 + (x % 4 == 0) * 0.6, 1.4, 0.6, "#8FC276", .7))
    # 栅栏
    for x in range(0, 60, 6):
        p.append(_qr(x, 9, 1.4, 5, "#F2E2C6"))
        p.append(_qr(x, 9, 1.4, 0.6, "#E0CBAA"))
    p.append(_qr(0, 10.4, 60, 1.2, "#EFDCBC"))
    # 大树
    p.append(_qr(50, 13, 4, 12, "#9B6B3A"))
    p.append(_rz(52, 11, 8, 4.4, "#7FB875"))
    p.append(_rz(48, 12.4, 5, 3, "#6FA96B"))
    p.append(_rz(55, 13, 4.4, 2.6, "#8CC47E"))
    # 大球 + 小皮球 + 逗猫棒
    p.append(_rz(13, 25.4, 4.4, 4.4, "#F2705C"))
    p.append(_rz(13, 24, 3.2, 2.4, "#FF9C86", .9))
    p.append(_rz(13, 26.6, 3.2, 1.2, "#E8F6FF", .35))
    # 小皮球（圆）
    p.append(_rz(7.5, 28.6, 1.6, 1.6, "#FFD34E"))
    p.append(_rz(7.2, 28, 0.8, 0.6, "#FFF0B8"))
    p.append(_qr(20, 20, 0.8, 8, "#C99A5A"))
    p.append(_qr(20.4, 19, 1.4, 1.6, "#F6A6C0"))
    p.append(_qr(20.4, 19, 1.4, 0.6, "#FFE4EE"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    if strength >= 2:
        for (x, y) in ((16, 19), (30, 18.6), (8, 20)):
            p.append(_qr(x, y, 1, 1, "#FFE066", .95))
    return _wrap(p, still=True)


def _explore_svg(sp, mood, star, skin, strength, shiny=False):
    """林间小路：天色 + 树影 + 萤火，长途更暗更亮。"""
    p = []
    p.append(_qr(0, 0, 60, 19, "#3E5A6E" if strength >= 3 else "#6E93A6"))
    p.append(_rz(46, 6, 6, 5, "#9CC8E0" if strength >= 3 else "#FFE9B0", .8))
    p.append(_qr(0, 19, 60, 12, "#4E6B44"))
    # 小路
    p.append(_rz(30, 27, 22, 4.6, "#B79A6A"))
    p.append(_rz(30, 25, 16, 3, "#CBAE7E"))
    p.append(_qr(26, 22, 8, 2, "#C2A472"))
    # 树（远近三层）
    for (x, sc, col) in ((4, 1, "#33503A"), (12, 0.78, "#3D5C42"),
                         (44, 0.9, "#33503A"), (54, 0.7, "#3D5C42")):
        p.append(_qr(x, 8 + (1 - sc) * 4, 3 * sc, 13 - (1 - sc) * 3, "#5C4130"))
        p.append(_rz(x + 1.5 * sc, 7 + (1 - sc) * 4, 7 * sc, 4.4 * sc, col))
        p.append(_rz(x + 1.5 * sc, 9 + (1 - sc) * 4, 6 * sc, 3 * sc, col))
    # 草丛与石头
    for x in (20, 24, 38, 41, 8):
        p.append(_qr(x, 21.4, 2.4, 1.4, "#5F8648"))
        p.append(_qr(x + 0.4, 20.6, 1, 1, "#6E9A52"))
    p.append(_rz(38, 24, 3, 1.8, "#7E8C7A"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    # 萤火（长途更多）
    n = 6 if strength < 3 else 14
    for i in range(n):
        x = 6 + (i * 7) % 50
        y = 12 + (i * 5) % 12
        p.append(_qr(x, y, 0.8, 0.8, "#FFE066", .95))
    return _wrap(p, still=True)


def _clinic_svg(sp, mood, star, skin, strength, shiny=False):
    """诊所：白墙 + 十字 + 检查台 + 吊瓶。"""
    p = []
    p.append(_qr(0, 0, 60, 19, "#F6FBFD"))
    for x in range(0, 60, 4):
        p.append(_qr(x, 0, 0.4, 19, "#E2EEF3", .9))
    p.append(_qr(0, 19, 60, 2, "#B7D8E2"))
    _tile_floor(p, 21, "#E6F1F5", "#D2E4EC", 2)
    # 十字标 + 心电图屏
    p.append(_qr(4, 3, 8, 8, "#FFFFFF"))
    p.append(_qr(7.2, 4, 1.6, 6, "#7FC79B"))
    p.append(_qr(5, 6.2, 6, 1.6, "#7FC79B"))
    p.append(_qr(44, 3, 11, 7, "#2C3A44"))
    p.append(_qr(44.6, 3.6, 9.8, 5.8, "#14202A"))
    for i, h in enumerate((1.4, 2.4, 1, 3, 1.6, 2.2)):
        p.append(_qr(45.4 + i * 1.5, 7 - h, 0.8, h, "#7CF0A8"))
    # 检查台
    p.append(_qr(14, 22, 20, 1.4, "#BFD8E2"))
    p.append(_qr(15, 23.4, 1.6, 7, "#9EBDCB"))
    p.append(_qr(31.4, 23.4, 1.6, 7, "#9EBDCB"))
    p.append(_qr(14, 21, 20, 1, "#E9F5FA"))
    # 吊瓶
    p.append(_qr(40, 8, 0.6, 12, "#B7CFD8"))
    p.append(_qr(38.6, 9.6, 3, 3.4, "#CFEBF7"))
    p.append(_qr(39, 10, 2.2, 2.6, "#E8F8FF"))
    p.append(_qr(39.8, 13, 0.5, 6, "#CFEBF7", .8))
    # 药柜
    p.append(_qr(48, 13, 9, 8, "#FFFFFF"))
    p.append(_qr(49, 14, 3.4, 2, "#F2A6A6"))
    p.append(_qr(49, 17, 3.4, 2, "#F6D08A"))
    _pet(p, sp, mood, star, skin, dy=-0.6, shadow=False, shiny=shiny)
    if strength >= 2:
        p.append(_rz(25, 22, 9, 2.6, "#B7F0CE", .35))
    return _wrap(p, still=True)


def _craft_svg(sp, mood, star, skin, strength, shiny=False):
    """工坊：木桌 + 铁砧 + 齿轮 + 火星。"""
    p = []
    p.append(_qr(0, 0, 60, 19, "#EAD9BE"))
    for x in range(0, 60, 5):
        p.append(_qr(x, 0, 0.4, 19, "#DEC9A6", .9))
    p.append(_qr(0, 19, 60, 2, "#8E6B44"))
    _tile_floor(p, 21, "#C49A6C", "#B4874F", 2)
    # 工具墙：锤子、钳子、锯
    p.append(_qr(6, 3, 1.2, 7, "#8A6A44"))
    p.append(_qr(4.6, 2.6, 4, 2, "#C9CDD6"))
    p.append(_qr(12, 3, 1, 7, "#8A6A44"))
    p.append(_qr(11.4, 3.4, 2.2, 2.4, "#A8AFBA"))
    p.append(_qr(18, 3.4, 6, 1.2, "#8FA6B8"))
    # 工作台
    p.append(_qr(30, 16, 26, 2, "#A9744A"))
    p.append(_qr(30, 18, 26, 1, "#8E6B44"))
    p.append(_qr(31, 19, 1.6, 8, "#8E6B44"))
    p.append(_qr(53, 19, 1.6, 8, "#8E6B44"))
    # 铁砧 + 齿轮 + 星尘袋
    p.append(_qr(36, 12, 7, 3.4, "#6B727C"))
    p.append(_qr(34.6, 14.4, 10, 1.6, "#565C66"))
    p.append(_qr(16, 24, 3, 1.2, "#6B727C"))
    p.append(_qr(16.6, 25.2, 1.6, 3, "#565C66"))
    p.append(_rz(48, 12.4, 3, 3, "#C9CDD6"))
    p.append(_rz(48, 12.4, 1.6, 1.6, "#9AA3AE"))
    for a in range(6):
        p.append(_qr(47.4 + (a % 3) * 1.6, 11.6 + (a // 3) * 1.6, 0.6, 0.6, "#8B939E"))
    p.append(_qr(8, 20.4, 4, 3.4, "#C9A26A"))
    p.append(_qr(8.6, 19.8, 3, 1, "#B98C55"))
    p.append(_qr(9, 21, 0.8, 0.8, "#FFE066"))
    p.append(_qr(10.4, 22, 0.6, 0.6, "#9FD4EA"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    if strength >= 2:
        for (x, y) in ((38, 10), (41, 11.4), (34, 11)):
            p.append(_qr(x, y, 0.8, 0.8, "#FFC94A", .95))
    return _wrap(p, still=True)


def _star_svg(sp, mood, star, skin, strength, shiny=False):
    """星辉祭坛：星空 + 法阵 + 光柱。"""
    p = []
    p.append(_qr(0, 0, 60, 31, "#1B1533"))
    for (x, y, s) in ((6, 3, 1.4), (17, 5, 1), (31, 2, 1.6), (44, 4, 1.2),
                      (53, 7, 1), (9, 12, 1.1), (38, 11, 1.3), (56, 15, 1)):
        p.append(_qr(x, y, s, s, "#FFE066", .95))
        p.append(_qr(x - s * 0.4, y + s * 0.4, s * 1.8, s * 0.3, "#FFE066", .8))
        p.append(_qr(x + s * 0.4, y - s * 0.4, s * 0.3, s * 1.8, "#FFE066", .8))
    # 地面 + 法阵
    p.append(_qr(0, 20, 60, 11, "#241C44"))
    for rx, col, op in ((20, "#6C5CE7", .35), (15, "#8F7CFF", .4), (10, "#C0B4FF", .5)):
        p.append(_rz(25, 25.4, rx, rx * 0.36, col, op))
    for i in range(12):
        ang = i * 30
        import math
        x = 25 + 15 * math.cos(math.radians(ang))
        y = 25.4 + 5.4 * math.sin(math.radians(ang))
        p.append(_qr(x, y, 1, 1, "#C0B4FF", .9))
    # 光柱
    p.append('<polygon points="330 40 690 40 760 620 260 620" fill="#B79BFF" opacity=".10"/>')
    p.append('<polygon points="400 60 620 60 660 620 360 620" fill="#D9CCFF" opacity=".10"/>')
    # 两侧水晶
    p.append(_qr(12, 14, 3, 8, "#9C8AE0"))
    p.append(_qr(12.6, 12.4, 1.8, 2, "#C0B4FF"))
    p.append(_qr(46, 15, 2.6, 7, "#9C8AE0"))
    p.append(_qr(46.6, 13.6, 1.4, 1.8, "#C0B4FF"))
    _pet(p, sp, mood, True, skin, shiny=shiny)
    if strength >= 2:
        p.append(_qr(24, 18, 2, 2, "#FFFFFF", .9))
        p.append(_qr(34, 19, 1.4, 1.4, "#FFFFFF", .8))
    return _wrap(p, still=True, glow="#8A6AC0")


def _garden_svg(sp, mood, star, skin, strength, shiny=False):
    """花园：花丛 + 蝴蝶（洗澡/玩耍之外的日常场景）。"""
    p = []
    p.append(_qr(0, 0, 60, 14, "#CFEAFA"))
    p.append(_qr(0, 14, 60, 17, "#B4DC96"))
    for x in range(0, 60, 3):
        p.append(_qr(x, 14.4 + (x % 6 == 0) * 0.6, 1.4, 0.5, "#9CCC7E", .8))
    for x in (6, 10, 16, 22, 30, 38, 44, 50, 56):
        p.append(_qr(x, 18, 0.5, 4, "#7FA86B"))
        p.append(_qr(x - 0.6, 17, 1.7, 1.4, "#F6A6C0"))
        p.append(_qr(x - 0.2, 17.4, 0.9, 0.7, "#FFE4EE"))
    for x in (26, 34, 42):
        p.append(_rz(x, 21, 3.4, 1.2, "#8FC276"))
    p.append(_qr(52, 10, 3, 10, "#9B6B3A"))
    p.append(_rz(53, 8.6, 6, 3, "#7FB875"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _shell(p, wall, wall2, skirt, floor, floor2, stripes=4):
    """分区场景通用墙地：0~19 墙、19~21 踢脚线、21~31 地板。"""
    p.append(_qr(0, 0, 60, 19, wall))
    for x in range(0, 60, stripes):
        p.append(_qr(x, 0, 1, 19, wall2, .6))
    p.append(_qr(0, 19, 60, 2, skirt))
    p.append(_qr(0, 21, 60, 10, floor))
    for y in range(22, 31, 2):
        p.append(_qr(0, y, 60, 1, floor2, .7))


def _sec_shop(sp, mood, star, skin, strength, shiny=False):
    """萌宠商店：左右货架 + 彩球 + 衣架 + 柜台。"""
    p = []
    _shell(p, "#FDEEF2", "#F7D9E2", "#E8A1B8", "#F2D9B8", "#E5C49A")
    p.append(_rz(30, 3.6, 15, 2.6, "#F7A8C4"))
    p.append(_rz(30, 3.2, 13.6, 2.1, "#FFE4EE"))
    for x in (24, 30, 36):
        p.append(_qr(x, 2.6, 1, 1, "#FFC94A", .95))
    # 左货架 + 彩球
    p.append(_qr(2, 6, 12, 13, "#C79A63"))
    p.append(_qr(2.6, 6.6, 10.8, 11.8, "#FFF3E4"))
    for sy in (9.6, 13.6, 17.6):
        p.append(_qr(2.6, sy, 10.8, 0.6, "#E8C8A0"))
    balls = [("#F2705C", "#FF9C86"), ("#FFD34E", "#FFE9A8"), ("#7CC6F2", "#B7E4F4"),
             ("#9CC47A", "#CDEBAF"), ("#C9A0E0", "#E2CFF2")]
    for row, sy in enumerate((8.4, 12.4, 16.4)):
        for i in range(5):
            c, hi = balls[(row + i) % 5]
            p.append(_rz(4.2 + i * 1.9, sy, 0.9, 0.9, c))
            p.append(_rz(4.0 + i * 1.9, sy - 0.3, 0.4, 0.3, hi, .9))
    # 右衣架
    p.append(_qr(46, 6, 12, 13, "#C79A63"))
    p.append(_qr(46.6, 6.6, 10.8, 11.8, "#FFF3E4"))
    p.append(_qr(47, 8, 9.6, 0.6, "#E8C8A0"))
    shirts = [("#F7B6C2", "#FFE4EE"), ("#7CC6F2", "#CFEBF7"), ("#FFD34E", "#FFF0B8"),
              ("#9CC47A", "#CDEBAF"), ("#C9A0E0", "#E2CFF2")]
    for row, sy in enumerate((9.4, 13.4, 17.4)):
        for i in range(3):
            c, hi = shirts[(row + i) % 5]
            x = 48 + i * 3.2
            p.append(_qr(x, sy, 2.4, 2.6, c))
            p.append(_qr(x - 0.4, sy, 0.7, 1, c))
            p.append(_qr(x + 2.1, sy, 0.7, 1, c))
            p.append(_qr(x + 0.5, sy + 0.6, 1.4, 0.8, hi, .8))
    # 柜台（低矮，不挡主角）
    p.append(_qr(22, 27.4, 16, 2, "#E8A15C"))
    p.append(_qr(22, 27, 16, 0.7, "#F6C98B"))
    _pet(p, sp, mood, star, skin, dy=0.4, shiny=shiny)
    return _wrap(p, still=True)


def _sec_fun(sp, mood, star, skin, strength, shiny=False):
    """彩票 · 医院：左摇号柜台，右诊所十字。"""
    p = []
    _shell(p, "#F3F0FA", "#E4DEF2", "#B7A8D8", "#E8DCE8", "#D8C8D8")
    p.append(_qr(3, 8, 13, 11, "#C99A5C"))
    p.append(_qr(3.6, 8.6, 11.8, 9.8, "#FFF3E4"))
    p.append(_rz(7, 6.4, 2.6, 2.6, "#7CC6F2"))
    p.append(_rz(7, 6.0, 1.6, 1.2, "#B7E4F4"))
    for i in range(3):
        p.append(_qr(5 + i * 3, 11, 2.2, 3, "#FFE066"))
    # 右诊所
    p.append(_qr(45, 3, 11, 8, "#FFFFFF"))
    p.append(_qr(48.2, 4, 1.6, 6, "#7FC79B"))
    p.append(_qr(46, 6.2, 6, 1.6, "#7FC79B"))
    p.append(_qr(47, 13, 9, 6, "#FFFFFF"))
    p.append(_qr(48, 14, 3, 2, "#F2A6A6"))
    p.append(_qr(52, 14, 3, 2, "#F6D08A"))
    p.append(_qr(20, 27.4, 20, 2, "#B7CFD8"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_decor(sp, mood, star, skin, strength, shiny=False):
    """小屋装修：色卡架 + 挂画 + 地毯卷 + 颜料罐。"""
    p = []
    _shell(p, "#F6F1E6", "#EBDFC8", "#C9A878", "#E3D0B0", "#D5BE96")
    p.append(_qr(3, 4, 12, 12, "#B9824E"))
    swatches = ["#F7B6C2", "#7CC6F2", "#FFD34E", "#9CC47A", "#C9A0E0", "#F2A6A6"]
    for i, c in enumerate(swatches):
        p.append(_qr(4 + (i % 3) * 3.6, 6 + (i // 3) * 4, 3, 3, c))
    for x in (46, 51.5):
        p.append(_qr(x, 4, 4.5, 6, "#8A6A44"))
        p.append(_qr(x + 0.5, 4.5, 3.5, 5, "#BFE8FA"))
    p.append(_rz(10, 27.6, 4, 1.4, "#F6A6C0"))
    for i, c in enumerate(("#7CC6F2", "#FFD34E", "#9CC47A")):
        p.append(_qr(46 + i * 3, 24, 2, 2.4, c))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_dex(sp, mood, star, skin, strength, shiny=False):
    """图鉴书房：双侧书架 + 中央相框。"""
    p = []
    _shell(p, "#EFE6D6", "#E2D4BC", "#A9744A", "#C49A6C", "#B4874F")
    book_cols = ["#F2A6A6", "#7CC6F2", "#FFD34E", "#9CC47A", "#C9A0E0", "#F6E7A6"]
    for bx in (2, 46):
        p.append(_qr(bx, 3, 12, 16, "#8E6B44"))
        for sy in (7, 11, 15):
            p.append(_qr(bx, sy, 12, 0.6, "#6B4423"))
        for row, sy in enumerate((4.6, 8.6, 12.6, 16.6)):
            for i in range(6):
                p.append(_qr(bx + 0.6 + i * 1.9, sy, 1.2, 2.6,
                             book_cols[(row + i) % 6]))
    p.append(_qr(24, 4, 12, 8, "#8A6A44"))
    p.append(_qr(24.6, 4.6, 10.8, 6.8, "#FFFDF2"))
    p.append(_rz(30, 8, 2.4, 2.2, "#F2C58A"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_pet(sp, mood, star, skin, strength, shiny=False):
    """宠物管理：沙发 + 站架名牌。"""
    p = []
    _shell(p, "#FBEBD3", "#F2DCB6", "#C79A63", "#DDB180", "#C99A6A")
    p.append(_qr(3, 17, 15, 6, "#F2A6A6"))
    p.append(_qr(3, 15.6, 15, 2, "#F7B6C2"))
    p.append(_qr(4, 23, 1.6, 4, "#C9727F"))
    p.append(_qr(15.4, 23, 1.6, 4, "#C9727F"))
    for x in (44, 50, 55.5):
        p.append(_qr(x, 16, 4, 1, "#B9824E"))
        p.append(_qr(x + 1.6, 17, 0.8, 6, "#A9744A"))
        p.append(_qr(x - 0.4, 14.4, 4.8, 1.4, "#FFF3E4"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_help(sp, mood, star, skin, strength, shiny=False):
    """帮助规则：告示板 + 大书讲台 + 台灯。"""
    p = []
    _shell(p, "#F3EFE4", "#E6DEC8", "#B98C55", "#D8C6A4", "#C8B48E")
    p.append(_qr(44, 3, 13, 9, "#8A6A44"))
    p.append(_qr(44.6, 3.6, 11.8, 7.8, "#FFF8E7"))
    for y in (5, 7.2, 9.4):
        p.append(_qr(46, y, 8, 0.8, "#C9B48A"))
    p.append(_qr(8, 18, 12, 1.6, "#B9824E"))
    p.append(_qr(12, 19.6, 1.6, 6, "#A9744A"))
    p.append(_qr(6.6, 15.4, 14.8, 3.4, "#FFFFFF"))
    p.append(_qr(7.2, 15.8, 13.6, 2.6, "#F2F6FA"))
    p.append(_qr(13.6, 15.4, 0.5, 3.4, "#C9CDD6"))
    p.append(_qr(4, 12, 0.8, 6, "#C99A5A"))
    p.append(_rz(4.4, 11, 1.8, 1.2, "#FFD34E"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_ach(sp, mood, star, skin, strength, shiny=False):
    """成就殿堂：深色金厅 + 奖杯架 + 勋章。"""
    p = []
    _shell(p, "#2A2138", "#352A48", "#4A3A5E", "#241B33", "#1B1528")
    for x in (3, 44):
        p.append(_qr(x, 6, 13, 1, "#6B5540"))
        p.append(_qr(x, 12, 13, 1, "#6B5540"))
    for x, y in ((6, 3.6), (11, 3.6), (47, 3.6), (52, 3.6)):
        p.append(_qr(x, y, 2.4, 2.6, "#FFD34E"))
        p.append(_qr(x + 0.6, y + 2.6, 1.2, 1, "#E8A15C"))
    p.append(_rz(30, 6.4, 3.4, 3.4, "#FFD34E"))
    p.append(_qr(29.2, 9.6, 1.6, 2.4, "#F2705C"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_svc(sp, mood, star, skin, strength, shiny=False):
    """数据服务：图表板 + 办公桌 + 打印机。"""
    p = []
    _shell(p, "#EAF1F5", "#D8E6EC", "#9FBFCB", "#CFDDE2", "#BCCFD8")
    p.append(_qr(4, 3, 13, 9, "#2C3A44"))
    p.append(_qr(4.6, 3.6, 11.8, 7.8, "#14202A"))
    for i, h in enumerate((1.4, 2.6, 1.8, 3.2, 2.2)):
        p.append(_qr(5.6 + i * 2.2, 9.4 - h, 1.2, h, "#7CC6F2"))
    p.append(_qr(38, 19, 18, 1.6, "#B9824E"))
    p.append(_qr(39, 20.6, 1.6, 7, "#A9744A"))
    p.append(_qr(52.4, 20.6, 1.6, 7, "#A9744A"))
    p.append(_qr(42, 15.6, 6, 3.4, "#C9CDD6"))
    p.append(_qr(43, 16.4, 4, 1, "#9AA3AE"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _sec_log(sp, mood, star, skin, strength, shiny=False):
    """日志设置：挂历 + 钟 + 书桌卷轴。"""
    p = []
    _shell(p, "#EFF6EA", "#DFEDD6", "#9CC47A", "#D6E2BE", "#C2D2A4")
    p.append(_qr(45, 3, 7, 8, "#FFFFFF"))
    p.append(_qr(45, 3, 7, 1.6, "#F2705C"))
    for r in range(2):
        for c in range(3):
            p.append(_qr(46 + c * 2, 5.4 + r * 2, 1.2, 1.2, "#C9CDD6"))
    p.append(_rz(56, 6.4, 2.6, 2.6, "#FFFFFF"))
    p.append(_qr(55.6, 5.6, 0.4, 1.6, "#4A3218"))
    p.append(_qr(4, 19, 16, 1.6, "#B9824E"))
    p.append(_qr(5, 20.6, 1.6, 7, "#A9744A"))
    p.append(_qr(17.4, 20.6, 1.6, 7, "#A9744A"))
    p.append(_qr(8, 16.4, 5, 2.4, "#FFF3D8"))
    p.append(_qr(8, 16.4, 0.6, 2.4, "#C99A5A"))
    p.append(_qr(12.4, 16.4, 0.6, 2.4, "#C99A5A"))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


def _plaza_svg(sp, mood, star, skin, strength, shiny=False):
    """小镇广场：左侧宠物店 + 气球，右侧喷泉长椅，绿树蝴蝶，主角居中。"""
    p = []
    # 天空 + 云 + 太阳
    p.append(_qr(0, 0, 60, 17, "#BFE3F7"))
    p.append(_rz(10, 3.4, 4, 1.6, "#FFFFFF", .9))
    p.append(_rz(13, 2.6, 3, 1.4, "#FFFFFF", .9))
    p.append(_rz(40, 4, 4.6, 1.8, "#FFFFFF", .85))
    p.append(_rz(44, 3, 3, 1.4, "#FFFFFF", .85))
    p.append(_rz(54, 3.4, 2.6, 2.6, "#FFE9A8"))
    # 地面石板路
    p.append(_qr(0, 17, 60, 14, "#EBD3B0"))
    for y in range(19, 31, 2):
        p.append(_qr(0, y, 60, 0.4, "#D8B98C", .7))
    for x in range(0, 60, 4):
        p.append(_qr(x, 17, 0.4, 14, "#D8B98C", .5))
    # 远景树
    for x, c in ((0, "#8FC276"), (58, "#7FB875")):
        p.append(_qr(x + 1, 9, 2, 8, "#9B6B3A"))
        p.append(_rz(x + 2, 8, 4, 3.4, c))
    # ---------- 左侧宠物店 ----------
    p.append(_qr(2, 5, 16, 19, "#F7C6CE"))
    p.append(_qr(2, 5, 16, 1.2, "#EFA8B8"))
    # 招牌
    p.append(_rz(10, 6.6, 6.4, 2.2, "#FFF3E0"))
    p.append(_qr(7.4, 6.2, 5.2, 0.5, "#E8B48C"))
    # 条纹雨棚
    for i in range(8):
        c = "#F2708A" if i % 2 == 0 else "#FFF3F5"
        p.append(_qr(2 + i * 2, 9.6, 2, 1.8, c))
    p.append(_qr(2, 11.4, 16, 0.6, "#D98A9A"))
    # 门窗 + 货架
    p.append(_qr(3.4, 13.4, 4, 5.4, "#BFE8FA"))
    p.append(_qr(3.8, 14.2, 3.2, 0.5, "#FFF"))
    p.append(_qr(3.8, 15.8, 3.2, 0.5, "#FFF"))
    p.append(_qr(8.4, 13.4, 4.4, 10.6, "#B9824E"))
    p.append(_qr(9, 14.2, 3.2, 9, "#8A5A2E"))
    p.append(_qr(13.6, 13.4, 3.4, 5.4, "#BFE8FA"))
    # 花盆
    p.append(_qr(3, 23.4, 2.4, 1.6, "#C9824A"))
    p.append(_qr(3.3, 22.6, 1.8, 1, "#7FB875"))
    # 气球串
    balloons = [("#F6A6C0", 15, 2.6), ("#FFB26B", 13.4, 3.6),
                ("#FFE066", 16.6, 3.8), ("#7CC6F2", 15, 4.6)]
    for c, bx, by in balloons:
        p.append(_qr(bx, by + 1.6, 0.2, 3.4, "#8A6A44", .7))
        p.append(_rz(bx, by, 1.3, 1.3, c))
    # ---------- 右侧喷泉 ----------
    p.append(_rz(47, 25.4, 9, 2.6, "#D8DEE6"))
    p.append(_rz(47, 24.8, 7.6, 2, "#9FD8EE"))
    p.append(_qr(50.4, 17, 3.2, 7.4, "#C4CCD6"))
    p.append(_rz(52, 16.4, 4.4, 1.6, "#D8DEE6"))
    p.append(_rz(52, 13.4, 2.6, 1.2, "#E6ECF2"))
    for dx in (-2.4, 0, 2.4):
        p.append(_qr(52 + dx, 14.6, 0.4, 5, "#BFE6F5", .8))
    # 长椅
    p.append(_qr(49, 21.6, 9, 1, "#B9824E"))
    p.append(_qr(49, 20.2, 9, 0.8, "#C99A63"))
    p.append(_qr(50, 22.6, 1, 3, "#8A6A44"))
    p.append(_qr(56, 22.6, 1, 3, "#8A6A44"))
    # 蝴蝶
    for bx, by, bc in ((24, 8, "#F6A6C0"), (38, 9, "#C9A0E0"),
                       (30, 12, "#FFE066"), (55, 12, "#F2A6A6")):
        p.append(_qr(bx, by, 0.8, 0.5, bc))
        p.append(_qr(bx + 0.8, by, 0.8, 0.5, bc))
    _pet(p, sp, mood, star, skin, shiny=shiny)
    return _wrap(p, still=True)


_BUILDERS = {
    "bath": _bath_svg,
    "feed": _feed_svg,
    "play": _play_svg,
    "explore": _explore_svg,
    "clinic": _clinic_svg,
    "craft": _craft_svg,
    "star": _star_svg,
    "garden": _garden_svg,
    "plaza": _plaza_svg,
    "sec_shop": _sec_shop,
    "sec_fun": _sec_fun,
    "sec_star": _star_svg,
    "sec_decor": _sec_decor,
    "sec_dex": _sec_dex,
    "sec_pet": _sec_pet,
    "sec_help": _sec_help,
    "sec_ach": _sec_ach,
    "sec_svc": _sec_svc,
    "sec_log": _sec_log,
}

SCENE_LABELS = {
    "room": "小屋",
    "bath": "浴室",
    "feed": "餐厅",
    "play": "院子",
    "explore": "林间小路",
    "clinic": "宠物医院",
    "craft": "工坊",
    "star": "星辉祭坛",
    "garden": "花园",
    "plaza": "小镇广场",
    "sec_shop": "萌宠商店",
    "sec_fun": "彩票 · 医院",
    "sec_star": "星辉祭坛",
    "sec_decor": "装修工坊",
    "sec_dex": "图鉴书房",
    "sec_pet": "宠物客厅",
    "sec_help": "规则书房",
    "sec_ach": "成就殿堂",
    "sec_svc": "数据服务台",
    "sec_log": "日志设置室",
}


def _wrap(body, still=False, glow=None):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 620" '
            'preserveAspectRatio="xMidYMid slice" '
            'width="1200" height="620" shape-rendering="crispEdges">'
            + "".join(body) + "</svg>")


def _particles(scene, strength):
    """按场景 + 强度撒粒子；强度越高越多。"""
    kinds = _PARTICLES.get(scene)
    if not kinds:
        return ""
    random.seed(f"{scene}-{strength}")
    n = {1: 7, 2: 12, 3: 20}.get(int(strength), 7)
    out = []
    for i in range(n):
        sym, color, anim = kinds[i % len(kinds)]
        left = random.randint(6, 92)
        bottom = random.randint(4, 66)
        delay = round(random.uniform(0, 2.6), 2)
        dur = round(random.uniform(2.4, 4.2), 2)
        size = random.choice([12, 15, 18, 22])
        dx = random.randint(-26, 26)
        out.append(
            f'<span class="ps-p {anim}" style="left:{left}%;bottom:{bottom}%;'
            f'font-size:{size}px;color:{color};animation-duration:{dur}s;'
            f'animation-delay:{delay}s;--dx:{dx}px">{sym}</span>'
        )
    return "".join(out)


_CACHE = None  # 由 _cached 装饰器填充


@st.cache_data(max_entries=200, show_spinner=False)
def scene_html(scene, species, mood="happy", star=False, skin="", strength=1,
               shiny=False, extras=None, decor=None, weather=None):
    """返回可直接 render() 的场景 HTML（含粒子层）。

    extras 只在「小屋」场景生效：其它宠物按固定站位画进房间。
    """
    sp = species if species in PET_SPECIES else "猫"
    if mood not in _MOODS:
        mood = "happy"
    strength = int(strength) if int(strength) in (1, 2, 3) else 1
    if scene not in _BUILDERS:
        svg = room_svg(sp, mood, star, skin, extras=extras, shiny=shiny,
                       decor=decor, weather=weather)
        body = f'<div class="pet-stage">{svg}</div>'
        return _CSS + body
    svg = _BUILDERS[scene](sp, mood, star, skin, strength, shiny=shiny)
    glow = _GLOW.get(scene, "#E8C08A")
    glow_html = (
        f'<div class="ps-glow" style="background:radial-gradient('
        f'circle,rgba(255,255,255,.55),{glow}55,transparent 70%)"></div>'
        if strength >= 2 else ""
    )
    return (_CSS
            + f'<div class="pet-stage">{svg}'
              f'<div class="ps-fx">{glow_html}{_particles(scene, strength)}</div>'
              '</div>')
