# -*- coding: utf-8 -*-
"""运行位置与数据目录：源码运行、PyInstaller 打包、Streamlit Cloud 三种环境统一入口。"""
import os
import sys
import tempfile

FROZEN = bool(getattr(sys, "frozen", False))
APP_HOME = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
_BUNDLE = getattr(sys, "_MEIPASS", "")


def _cloud_like():
    if os.environ.get("PETGAME_CLOUD"):
        return True
    try:
        return os.getcwd().replace("\\", "/").startswith("/mount/src")
    except OSError:
        return False


def data_home():
    override = os.environ.get("PETGAME_DATA_DIR")
    if override:
        return os.path.abspath(override)
    if _cloud_like():
        return os.path.join(tempfile.gettempdir(), "petgame_data")
    return APP_HOME


DATA_HOME = data_home()


def sfx_home():
    local = os.path.join(APP_HOME, "sfx")
    if os.path.isdir(local):
        return local
    if _BUNDLE and os.path.isdir(os.path.join(_BUNDLE, "sfx")):
        return os.path.join(_BUNDLE, "sfx")
    return local


SFX_HOME = sfx_home()


def gallery_home():
    return os.path.join(DATA_HOME, "gallery")


def ensure_dirs():
    for d in (DATA_HOME, gallery_home(), os.path.join(DATA_HOME, "save_backups")):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
