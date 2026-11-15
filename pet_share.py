# -*- coding: utf-8 -*-
"""分享卡片：把宠物、等级、星辉/进化、图鉴进度画成一张 PNG，方便直接发出去。

宠物立绘本身是 pet_svg() 生成的纯 <rect> 拼图（像素画），这里按矩形逐个
alpha 合成到 PIL 图上，所以不需要 cairosvg 之类的 SVG 渲染依赖。
"""
import io
import re
from datetime import date

from PIL import Image, ImageDraw, ImageFont

from pet_svg import pet_svg
from pet_constants import PET_CATEGORY_OF, season_of
from pet_progress import species_of, current_title
from pet_state import bond_tier

_FONT_CANDIDATES = (
    (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"),
    (r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simhei.ttf"),
    (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"),
)
_RECT_RE = re.compile(r"<rect\s+([^/>]*)/>", re.I)
_ATTR_RE = re.compile(r'([a-zA-Z:-]+)="([^"]*)"')


def _font(size, bold=False):
    for pair in _FONT_CANDIDATES:
        path = pair[0] if bold else pair[1]
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hex_to_rgb(color):
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def pet_image(species, mood="happy", is_star=False, scale=2, skip_bg=True,
              shiny=False):
    """把 pet_svg 输出的矩形逐个画到 PIL 图上，返回 RGBA 立绘。

    skip_bg=True 时丢掉铺满画布的底色层，卡片里就能直接压在圆底上。
    shiny=True 走异色配色，和房间里看到的立绘保持一致。
    """
    svg = pet_svg(species, mood, is_star, shiny=shiny)
    side = 240 * scale
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for tag in _RECT_RE.findall(svg):
        attrs = dict(_ATTR_RE.findall(tag))
        try:
            x = float(attrs.get("x", 0)) * scale
            y = float(attrs.get("y", 0)) * scale
            w = float(attrs.get("width", 1)) * scale
            h = float(attrs.get("height", 1)) * scale
        except ValueError:
            continue
        fill = attrs.get("fill", "#000000")
        if not fill.startswith("#"):
            continue
        try:
            rgb = _hex_to_rgb(fill)
            alpha = int(round(255 * float(attrs.get("opacity", 1))))
        except ValueError:
            continue
        if w <= 0 or h <= 0:
            continue
        if skip_bg and (w >= 180 or h >= 180):
            continue
        draw.rectangle([x, y, x + w, y + h], fill=rgb + (max(0, min(255, alpha)),))
    return img


def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def share_card(gs, pet, out_path=None):
    """渲染 720×1000 的分享卡片，返回 PNG 字节；给路径则同时落盘。"""
    W, H = 720, 1000
    sp = species_of(pet)
    cat = PET_CATEGORY_OF.get(sp, "萌宠")
    title = current_title(gs)
    got_dex = len(gs.get("dex", []))

    # 背景：竖向暖色渐变
    img = Image.new("RGB", (W, H), "#FDF6E8")
    draw = ImageDraw.Draw(img)
    top, bottom = (253, 246, 232), (245, 220, 176)
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)],
                  fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    _rounded(draw, (36, 36, W - 36, H - 36), 36, (255, 252, 245), (232, 208, 168), 3)

    f_small = _font(22)
    f_mid = _font(28)
    f_big = _font(46, bold=True)
    f_tag = _font(24, bold=True)

    draw.text((W // 2, 74), "毛孩子的小屋", font=f_small, fill="#8A6A3E", anchor="mm")
    draw.text((W // 2, 108), "MY LITTLE PET", font=_font(16), fill="#BFA57F", anchor="mm")

    # 立绘：保留像素画自带的底色块，四角磨圆当头像砖贴上去
    draw.ellipse((W // 2 - 208, 128, W // 2 + 208, 552), fill="#FFF0D6")
    art = pet_image(sp, "happy", bool(pet.get("is_star")), scale=2, skip_bg=False,
                    shiny=bool(pet.get("shiny")))
    art = art.resize((392, 392), Image.LANCZOS)
    mask = Image.new("L", art.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, art.size[0] - 1, art.size[1] - 1),
                                           radius=26, fill=255)
    img.paste(art, (W // 2 - 196, 136), mask)

    name = str(pet["name"])
    if len(name) > 12:
        name = name[:12] + "…"
    draw.text((W // 2, 566), name, font=f_big, fill="#5C4425", anchor="mm")
    sub = f"{cat}类 · {sp} · Lv.{pet['lv']}"
    if pet.get("shiny"):
        sub = f"异色 · {sub}"
    draw.text((W // 2, 612), sub, font=f_mid, fill="#8A6A3E", anchor="mm")

    # 称号药丸
    pill = f"称号 · {title}"
    pw = draw.textlength(pill, font=f_tag) + 44
    _rounded(draw, (W // 2 - pw / 2, 640, W // 2 + pw / 2, 684), 22, "#FFE9C0", "#E0BE84", 2)
    draw.text((W // 2, 662), pill, font=f_tag, fill="#8A5A14", anchor="mm")

    # 属性四宫格
    stats = [("心情", pet["hn"], "#C08A1E"), ("饱食", pet["ha"], "#C9702C"),
             ("清洁", pet["cl"], "#3E86B5"), ("健康", pet["health"], "#C05262")]
    box_w, box_h, gap = 150, 84, 12
    total = box_w * 4 + gap * 3
    x0 = (W - total) // 2
    for i, (label, val, color) in enumerate(stats):
        bx = x0 + i * (box_w + gap)
        _rounded(draw, (bx, 706, bx + box_w, 706 + box_h), 18, "#FFF6E5", "#EAD4AC", 2)
        draw.text((bx + box_w / 2, 728), label, font=_font(20), fill="#9A7B4F", anchor="mm")
        draw.text((bx + box_w / 2, 762), f"{val:.0f}", font=_font(30, bold=True),
                  fill=color, anchor="mm")

    # 星辉 / 进化
    line2 = [f"亲密度 {bond_tier(pet.get('bond', 0))['name']} "
             f"{int(pet.get('bond', 0) or 0)}/100"]
    if pet.get("is_star"):
        line2.append(f"星辉 Lv.{int(pet.get('star_lv', 1) or 1)}")
    else:
        line2.append("普通形态")
    if pet.get("evo_branch"):
        line2.append(f"{pet['evo_branch']} · {pet.get('element') or '无'} "
                     f"{int(pet.get('evo_lv', 0))}/5")
    draw.text((W // 2, 818), "　".join(line2), font=_font(24), fill="#7A5B33", anchor="mm")

    # 图鉴进度条
    from pet_progress import DEX_TOTAL
    pct = got_dex / DEX_TOTAL if DEX_TOTAL else 0
    bar_x0, bar_x1, bar_y = 96, W - 96, 866
    _rounded(draw, (bar_x0, bar_y, bar_x1, bar_y + 22), 11, "#F0E3CB")
    _rounded(draw, (bar_x0, bar_y, bar_x0 + max(22, (bar_x1 - bar_x0) * pct), bar_y + 22),
             11, "#E2B459")
    draw.text((W // 2, 908), f"图鉴 {got_dex}/{DEX_TOTAL} · {pct * 100:.0f}%",
              font=_font(24), fill="#7A5B33", anchor="mm")
    draw.text((W // 2, 948), f"{date.today():%Y-%m-%d} · {season_of()['name']}第 "
                             f"{season_of()['day_in_season']} 天", font=_font(20),
              fill="#A98C62", anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    if out_path:
        with open(out_path, "wb") as f:
            f.write(data)
    return data


def _open_share(gs, pet):
    from io import BytesIO
    return Image.open(BytesIO(share_card(gs, pet))).convert("RGB")


def _band(draw, y, h, color):
    draw.rectangle([0, y, 720, y + h], fill=color)


def milestone_card(gs, pet, badge, note="", out_path=None):
    """里程碑卡：在分享卡上下各压一条横幅，写上徽章与说明。"""
    img = _open_share(gs, pet)
    draw = ImageDraw.Draw(img)
    _band(draw, 0, 96, "#3B2A18")
    f1 = _font(40, True)
    draw.text((360, 48), badge, font=f1, fill="#FFD86B", anchor="mm")
    _band(draw, 1000 - 110, 110, "#3B2A18")
    f2 = _font(24)
    draw.text((360, 945), note or "毛孩子的小屋 · 里程碑", font=f2,
              fill="#FFF3D6", anchor="mm")
    if out_path:
        img.save(out_path, "PNG")
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def month_card(gs, stats, out_path=None):
    """月度小结卡：纯文字排版，一行一条。"""
    W, H = 720, 1000
    img = Image.new("RGB", (W, H), "#FDF6E8")
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)],
                  fill=(253 - int(8 * t), 246 - int(26 * t), 232 - int(60 * t)))
    draw.rectangle([34, 34, W - 34, H - 34], outline="#C9702C", width=4)
    draw.text((360, 120), "本月小结", font=_font(52, True), fill="#3B2A18", anchor="mm")
    draw.text((360, 176), stats.get("month", ""), font=_font(24),
              fill="#7A5B33", anchor="mm")
    y = 250
    for label, value in stats.get("rows", []):
        draw.text((90, y), label, font=_font(26), fill="#7A5B33")
        draw.text((W - 90, y), str(value), font=_font(28, True), fill="#C9702C", anchor="ra")
        y += 54
    draw.line([(80, y + 6), (W - 80, y + 6)], fill="#EAD4AC", width=2)
    draw.text((360, y + 60), stats.get("line", ""), font=_font(22),
              fill="#8A6A3A", anchor="ma")
    if out_path:
        img.save(out_path, "PNG")
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()
