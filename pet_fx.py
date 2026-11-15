# -*- coding: utf-8 -*-
"""操作特效层：纯 CSS 动画，不依赖 JS（Streamlit 会丢掉 script，但样式照常生效）。

用法：
    fx("feed", "饱腹 +10")      # 记一笔特效
    render_fx()                 # 页面顶部渲染这一笔，播完自动消失

之所以要走 session_state 队列，是因为动作都在 st.rerun() 之前触发，
写入队列后在下一帧渲染，正好接在重绘的瞬间。
"""
import random

import streamlit as st

_CSS = """
<style>
.fx-wrap{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:99999;
  pointer-events:none;display:flex;flex-direction:column;gap:8px;align-items:center}
.fx-card{position:relative;min-width:180px;padding:12px 22px;border-radius:16px;
  background:rgba(255,252,244,.96);border:2px solid #EAD4AC;
  box-shadow:0 10px 26px rgba(120,86,32,.22);overflow:hidden;
  animation:fx-pop 1.9s cubic-bezier(.2,.8,.3,1) forwards}
.fx-label{position:relative;z-index:2;font-size:14px;font-weight:700;color:#7A5B33;
  text-align:center;white-space:nowrap}
.fx-p{position:absolute;bottom:6px;font-size:15px;opacity:0;z-index:1;
  animation:fx-rise 1.5s ease-out forwards}
.fx-ring{position:absolute;left:50%;top:50%;width:34px;height:34px;margin:-17px 0 0 -17px;
  border-radius:50%;border:3px solid rgba(255,255,255,.9);z-index:0;
  animation:fx-ring 1.4s ease-out forwards}
@keyframes fx-pop{0%{opacity:0;transform:translateY(-10px) scale(.88)}
  18%{opacity:1;transform:translateY(0) scale(1.03)}
  32%{transform:scale(1)} 78%{opacity:1;transform:translateY(0) scale(1)}
  100%{opacity:0;transform:translateY(-8px) scale(.98)}}
@keyframes fx-rise{0%{opacity:0;transform:translateY(10px) scale(.7)}
  22%{opacity:1} 100%{opacity:0;transform:translateY(-52px) scale(1.25)}}
@keyframes fx-ring{0%{transform:scale(.4);opacity:.85}100%{transform:scale(2.6);opacity:0}}
@keyframes fx-flash{0%{box-shadow:0 0 0 rgba(255,255,255,0)}
  30%{box-shadow:0 0 34px 8px var(--fx-glow,rgba(217,166,58,.55))}
  100%{box-shadow:0 0 0 rgba(255,255,255,0)}}
.fx-flash{animation:fx-pop 1.9s cubic-bezier(.2,.8,.3,1) forwards,
  fx-flash 1.6s ease-out 1}
.fx-big .fx-card{min-width:240px;padding:15px 26px;border-width:3px}
.fx-big .fx-label{font-size:16px}
@keyframes fx-shake{0%,100%{transform:translateX(0)}
  18%{transform:translateX(-6px)} 36%{transform:translateX(6px)}
  54%{transform:translateX(-4px)} 72%{transform:translateX(4px)}}
.shake-now .block-container{animation:fx-shake .42s ease-in-out 1}
</style>
"""

# kind：底色、边框、粒子符号、粒子数量、是否叠加光环
_KINDS = {
    "feed":      ("#FFE9D6", "#E2A46E", "♥", 6, False),
    "play":      ("#FFE1E7", "#E08A97", "★", 7, False),
    "bath":      ("#DDEEFA", "#7FB0CE", "●", 8, False),
    "heal":      ("#FFE1E7", "#D98A98", "✚", 7, False),
    "explore":   ("#EDF3E0", "#9DAD6A", "✦", 6, False),
    "explore_rare": ("#FFF3CE", "#DFB14A", "✦", 12, True),
    "lottery":   ("#FFF0C9", "#D9A63A", "◆", 10, True),
    "levelup":   ("#EDE5FA", "#9C82CC", "✧", 9, True),
    "star":      ("#E8DEFA", "#8A6AC0", "✧", 14, True),
    "ach":       ("#FFF1C9", "#D3A03F", "★", 8, True),
    "craft":     ("#F6EAD8", "#B48F5E", "◇", 6, False),
    "release":   ("#EDF3E0", "#9DAD6A", "✿", 7, False),
    "sign":      ("#FFF4DA", "#D8B978", "☀", 6, False),
    "touch":     ("#FFF0DE", "#E2A46E", "♥", 5, False),
    "sell":      ("#FFF4D0", "#D9A63A", "◆", 8, False),
    "shiny":     ("#F6ECFF", "#A97BD9", "✦", 16, True),
    "sunny":     ("#FFF5D6", "#E0B34C", "☀", 7, False),
    "rain":      ("#E3EEF7", "#7FA8C9", "☂", 8, False),
    "snow":      ("#F2F8FD", "#9DB9CE", "❄", 8, False),
    "thunder":   ("#EDEEF7", "#6E74A0", "⚡", 10, True),
    "festival":  ("#FFF0D2", "#D9534F", "🏮", 14, True),
    "decor":     ("#F3EAF6", "#A985C4", "✦", 7, False),
    "warn":      ("#FFE5E5", "#C05262", "!", 5, False),
}


def fx(kind, text="", big=False):
    """把一笔特效放进队列，下一帧渲染。"""
    st.session_state.setdefault("fx_queue", []).append(
        {"kind": kind, "text": str(text), "big": bool(big)}
    )


def _card(item):
    kind = item["kind"] if item["kind"] in _KINDS else "ach"
    bg, border, sym, n, ring = _KINDS[kind]
    rgba = "rgba(217,166,58,.5)"
    parts = []
    for i in range(n):
        left = 8 + random.randint(0, 84)
        delay = round(random.uniform(0, .45), 2)
        size = random.choice([13, 15, 18])
        parts.append(
            f'<span class="fx-p" style="left:{left}%;animation-delay:{delay}s;'
            f'font-size:{size}px;color:{border}">{sym}</span>'
        )
    ring_html = '<span class="fx-ring"></span>' if ring else ""
    return (
        f'<div class="fx-card" style="--fx-glow:{rgba};background:{bg};'
        f'border-color:{border}">{ring_html}{"".join(parts)}'
        f'<div class="fx-label">{_escape(item["text"])}</div></div>'
    )


def _escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_fx():
    """渲染并清空队列；没有待播特效时啥也不干。"""
    queue = st.session_state.get("fx_queue") or []
    if not queue:
        return
    st.session_state["fx_queue"] = []
    cards = []
    for item in queue[-3:]:
        cards.append(_card(item))
    _shake = any(i["kind"] == "warn" for i in queue[-3:])
    st.markdown(
        _CSS
        + ('<style>.block-container{animation:fx-shake .42s ease-in-out 1}</style>'
           if _shake else "")
        + '<div class="fx-wrap">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )
