# -*- coding: utf-8 -*-
"""毛孩子的小屋 —— 入口。

运行：streamlit run pet_web.py
界面代码在 ui_app.py，每次 rerun 都重新执行，行为与单文件版一致。

依赖：streamlit（必需）、pillow（分享卡片用，缺了只影响卡片）。
缺少 pillow 时游戏照常能玩，页面顶部会提示装依赖的办法。
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import PIL  # noqa: F401
    HAS_PIL = True
except ModuleNotFoundError:
    HAS_PIL = False

if "ui_app" in sys.modules:
    importlib.reload(sys.modules["ui_app"])
else:
    import ui_app  # noqa: F401

if not HAS_PIL:
    import streamlit as st

    st.warning("缺少依赖 Pillow，分享卡片暂时用不了（其它功能正常）。"
               "安装：pip install pillow，或 pip install -r requirements.txt")
