# -*- coding: utf-8 -*-
"""极简音效层：短 wav 直接播，不占版面。"""
import functools
import os

import streamlit as st

from pet_env import SFX_HOME
SFX_DIR = SFX_HOME
SFX_KINDS = ("feed", "levelup", "win", "season", "festival", "weather",
             "achievement", "shiny")


@functools.lru_cache(maxsize=16)
def _data(kind):
    p = os.path.join(SFX_DIR, f"{kind}.wav")
    if not os.path.exists(p):
        return b""
    with open(p, "rb") as f:
        return f.read()


def play(kind, key=""):
    """播一个音效。重复调用同一种音效时靠 key 去重，避免一次操作响两遍。

    浏览器要求先有一次用户点击才允许自动播放；这里的播放都发生在按钮点击后的
    rerun 里，所以正常能响。
    """
    if not st.session_state.get("sfx_on", False):
        return                  # 默认静音，设置页打开才响
    data = _data(kind)
    if not data:
        return
    slot = f"sfxplayer_{kind}_{key}"
    holder = st.container(key=slot)
    with holder:
        st.audio(data, format="audio/wav", autoplay=True)


# ---------------- 背景音乐 ----------------
BGM_KINDS = ("day", "night")


@functools.lru_cache(maxsize=4)
def bgm_data(kind):
    p = os.path.join(SFX_DIR, f"bgm_{kind}.wav")
    if not os.path.exists(p):
        return b""
    with open(p, "rb") as f:
        return f.read()


def bgm_kind():
    """按本地时间切白天/夜晚两版；6:00~18:00 白天。"""
    from datetime import datetime
    return "day" if 6 <= datetime.now().hour < 18 else "night"


def render_bgm(kind, volume=0.4):
    """把循环播放器塞进一个 0 高度的 HTML 组件里。

    必须放在 st.fragment 里调用：整页 rerun 不会重建 fragment，音乐才不会每次
    点按钮都从头开始。
    """
    import base64
    import streamlit.components.v1 as components
    data = bgm_data(kind)
    if not data:
        return
    b64 = base64.b64encode(data).decode("ascii")
    vol = max(0.0, min(1.0, float(volume)))
    html = (
        '<audio autoplay loop style="display:none" '
        f'id="bgm"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'
        '<script>var a=document.getElementById("bgm");'
        f'a.volume={vol:.2f};'
        'var p=a.play();if(p&&p.catch){p.catch(function(){});}</script>'
    )
    components.html(html, height=0)
