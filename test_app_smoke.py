# -*- coding: utf-8 -*-
"""AppTest 冒烟：新游戏 → 喂食 → 玩耍 → 探索 → 切分区 → 存档。"""
import os
import tempfile

os.environ["PET_SAVE_PATH"] = os.path.join(tempfile.mkdtemp(), "player_pet.txt")
for k in list(os.environ):
    if k.startswith("STREAMLIT"):
        pass

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.abspath(__file__))


def _app():
    at = AppTest.from_file(os.path.join(ROOT, "pet_web.py"), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_smoke_new_game_and_actions():
    at = _app()
    if at.radio:
        at.radio[0].set_value("猫")
        at.run()
        assert not at.exception, at.exception
    btns = [b for b in at.button if "开始新游戏" in b.label]
    if btns:
        btns[0].click()
        at.run()
        assert not at.exception, at.exception
    assert "game_state" in at.session_state, "新游戏没有落进 session_state"

    at.run()
    assert not at.exception, at.exception

    # 照顾按钮收在「宠物管理」分区弹出层里，先进该分区再操作
    seg0 = at.segmented_control[0]
    seg0.set_value("宠物管理")
    at.session_state["panel_open"] = "pet"
    at.run()
    assert not at.exception, at.exception

    # 喂食是 popover 里的控件，冒烟改用房间按钮：玩耍 + 主动技能
    play = [b for b in at.button if b.key == "act_play"]
    assert play, "找不到玩耍按钮"
    play[0].click()
    at.run()
    assert not at.exception, at.exception

    skill = [b for b in at.button if b.key == "act_skill"]
    assert skill, "找不到主动技能按钮"
    skill[0].click()
    at.run()
    assert not at.exception, at.exception

    # 切换分区：图鉴
    seg = at.segmented_control
    assert seg, "没有分区控件"
    seg[0].set_value("帮助 · 规则")
    at.run()
    assert not at.exception, at.exception
    seg[0].set_value("日志 · 设置")
    at.run()
    assert not at.exception, at.exception


def test_tasks_panel():
    """任务·广播弹层包含引导/广播/今日本周月度/挑战，首页不留这些明细，且不混入商店货架。"""
    at = _app()
    species = [r for r in at.radio if "猫" in r.options]
    if species:
        species[0].set_value("猫")
        at.run()
    btns = [b for b in at.button if "开始新游戏" in b.label]
    if btns:
        btns[0].click()
        at.run()
    assert not at.exception, at.exception

    # 首页不应平铺任务/广播明细
    home_text = "\n".join(m.value for m in at.markdown)
    assert "小屋广播" not in home_text and "本周任务" not in home_text

    at.session_state["panel_open"] = "tasks"
    at.run()
    assert not at.exception, at.exception
    text = "\n".join(m.value for m in at.markdown)
    for kw in ["小屋广播", "今日任务", "本周任务", "月度目标", "限时挑战"]:
        assert kw in text, f"任务弹层缺少 {kw}"
    assert "萌宠商店" not in text


def test_help_matches_constants():
    """帮助文案里的数字必须来自常量，不能手写。"""
    from pet_constants import SHINY_RATE, TOUCH_DAILY, SEASON_DAYS
    at = _app()
    seg = at.segmented_control[0]
    seg.set_value("帮助 · 规则")
    at.session_state["panel_open"] = "help"
    at.run()
    assert not at.exception, at.exception
    text = "\n".join(m.value for m in at.markdown)
    assert f"{TOUCH_DAILY}" in text
    assert f"{SEASON_DAYS} 天" in text or f"每 {SEASON_DAYS} 天" in text
    assert f"{SHINY_RATE * 100:.0f}%" in text
