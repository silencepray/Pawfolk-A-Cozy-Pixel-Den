# -*- coding: utf-8 -*-
"""pet_ui_blocks（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
from datetime import date, datetime, timedelta
import html as _html
import random
import streamlit as st
from pet_constants import *
from pet_progress import *
from pet_svg import *
from pet_room import *
from pet_state import *
from pet_svg import (_r, _mx, _blob, _outline, _eyes, _mouth, _cheeks, _mood_prop, _star_deco, _legs, _PET_BODY, _PET_SKIN, _STAR_SKIN, _PET_BG, _pet_group, _frame, _theme_pal, _to_hue)
from pet_room import (_qr, _rz, _CSS)
from pet_progress import (_ICON_BODY, _ITEM_ICON)
from pet_fx import fx

def render(html_text):
    st.markdown(html_text, unsafe_allow_html=True)
def section(icon_name, title):
    render(
        f'<div class="pe-sec">{icon(icon_name, 18, "#9A6A2E")}'
        f'<span>{_html.escape(title)}</span></div>'
    )
def fmt_wait(seconds):
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    if h:
        return f"{h} 小时 {m} 分"
    if m:
        return f"{m} 分 {s} 秒"
    return f"{s} 秒"
def hud_block(gs, star_count, weather=None, fest=None):
    sd = season_of()
    weather = weather or weather_of()
    fest = fest if fest is not None else festival_of()
    w_info = WEATHER_INFO.get(weather["key"], {})
    w_chip = (f'<span class="weather-chip" style="background:{w_info.get("tint", "#F1E3C4")};'
              f'border-color:#8A6A44">'
              f'{w_info.get("icon", "")} {w_info.get("name", "")}</span>')
    f_chip = (f'<span class="weather-chip fest-chip" style="background:{fest["color"]};'
              f'border-color:#6B4423">{fest["icon"]} {fest["name"]}</span>'
              if fest else "")
    return (
        '<div class="game-hud">'
        '<div class="hud-brand">'
        '<div class="hud-title">毛孩子的小屋</div>'
        f'<div class="hud-sub">{date.today().strftime("%Y年%m月%d日")}'
        f'<span class="season-chip season-{sd["key"]}">{sd["name"]} · 第 {sd["day_in_season"]}/{SEASON_DAYS} 天</span>'
        f'{w_chip}{f_chip} · 今天也要好好照顾它</div>'
        '</div>'
        '<div class="hud-money">'
        f'<div class="money-pill"><span class="m-ico">{icon("coin", 22, "#BB851F")}</span>'
        f'<b>{gs["df"]}</b></div>'
        f'<div class="money-pill gem"><span class="m-ico">{icon("gem", 22, "#3F7FC4")}</span>'
        f'<b>{star_count}</b></div>'
        '</div>'
        '</div>'
    )
def _stat_row(label, icon_name, color, bg, value):
    return (
        f'<div class="stat-row"><span class="stat-ico" style="background:{bg}">'
        f'{icon(icon_name, 18, color)}</span>'
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value:.0f}</span></div>'
    )
def _short_name(name, limit=10):
    """面板里的名字只展示前 limit 个字，超长名字不再撑破卡片（存档里的全名不变）。"""
    name = str(name)
    return name if len(name) <= limit else name[:limit] + "…"
def pet_panel_block(gs, pet, star_count, title=None, bond=None):
    """bond: {"val": float, "name": str, "line": str}，没有就只显示基础面板。"""
    sp = species_of(pet)
    need = max(1, pet["lv"] * 50)
    pct = max(0.0, min(100.0, float(pet["exp"]) / need * 100.0))
    left_exp = max(0.0, need - float(pet["exp"]))
    status = {"happy": "心情不错", "sad": "需要照顾", "sick": "状态不佳"}[pet_mood(pet)]
    mt = mood_tag(pet)
    mood_note = {"great": "衰减-15% · 好事更多",
                 "low": "衰减+15% · 易遇坏事",
                 "normal": "无额外加成"}[mt["key"]]
    rows = "".join([
        _stat_row("心情", "happy", "#C08A1E", "#FFF1C4", pet["hn"]),
        _stat_row("饱食", "food", "#C9702C", "#FFE5D0", pet["ha"]),
        _stat_row("清洁", "clean", "#3E86B5", "#DCEEF9", pet["cl"]),
        _stat_row("健康", "heart", "#C05262", "#FFE1E5", pet["health"]),
    ])
    tags = [
        (f"星辉 Lv.{int(pet.get('star_lv', 1) or 1)}" if pet.get("is_star") else "普通皮肤"),
        (f"装扮 {skin_theme(pet)}" if skin_theme(pet) else "无装扮"),
        f"{season_of()['name']} 剩 {season_of()['left_days']} 天",
        f"成长 · {STAGE_LABEL[growth_stage(pet)]}",
        f"探索 {gs['total_explore']} 次",
        "事件 开" if gs["rand_event_switch"] else "事件 关",
        "存档 开" if gs["auto_save_switch"] else "存档 关",
    ]
    if pet.get("evo_branch"):
        tags.append(f"{pet['evo_branch']}·{pet.get('element') or '无'} {int(pet.get('evo_lv', 0))}/5")
    if star_count:
        tags.append(f"星辉 {star_count} 只")
    title = title or current_title(gs)
    tags.insert(0, f"称号 · {title}")
    tag_html = "".join(f'<span class="panel-tag">{t}</span>' for t in tags)
    bond_html = ""
    if bond:
        _pct = max(0.0, min(100.0, float(bond["val"]) / 100.0 * 100.0))
        bond_html = (
            f'<div class="bond-box"><div class="bond-top">'
            f'<span>亲密度 {float(bond["val"]):.0f}/100 · {bond["name"]}</span>'
            f'<span class="bond-pct">{_pct:.0f}%</span></div>'
            f'<div class="bond-bar"><i style="width:{_pct:.1f}%"></i></div>'
            f'<div class="bond-line">{_html.escape(bond["line"])}</div></div>'
        )
    badge = icon("star", 20, "#D9A63A")
    return (
        '<div class="pet-panel">'
        '<div class="panel-head">'
        f'<div class="avatar">{pet_art(pet)}</div>'
        f'<div class="lv-box"><span>等级</span><b>{pet["lv"]}</b></div>'
        f'<div class="star-badge">{badge}</div>'
        '</div>'
        f'<div class="pet-name">{_html.escape(_short_name(pet["name"]))}'
        f'<small>{PET_LABEL.get(sp, sp)}</small></div>'
        f'<div class="pet-status">{status}'
        f'<span class="mood-tag mood-{mt["key"]}">{mt["label"]}</span></div>'
        f'<div class="mood-note">{mood_note}</div>'
        f'<div class="bonus-line">{_html.escape(bonus_summary(pet))}</div>'
        f'<div class="stat-list">{rows}</div>'
        '<div class="exp-box">'
        f'<div class="exp-top"><span class="exp-label">{icon("star", 13, "#A9741F")}'
        f'<span>经验</span></span><b>{pet["exp"]:.0f} / {need}</b></div>'
        f'<div class="exp-bar"><i style="width:{pct:.1f}%"></i></div>'
        f'<div class="exp-left">距离 Lv.{pet["lv"] + 1} 还需要 <b>{left_exp:.0f}</b> 经验</div>'
        '</div>'
        f'{bond_html}'
        f'<div class="panel-tags">{tag_html}</div>'
    )
def tasks_block(gs):
    """只显示今天抽到的 3 条任务，而不是固定 5 条。"""
    rows = []
    for t in tasks_today(gs):
        done = t["id"] in gs["task_finished"]
        cls = "pe-task done" if done else "pe-task"
        ic = icon("check", 16, "#7E8F3F") if done else icon("task", 16, "#C0A57C")
        rows.append(
            f'<div class="{cls}">{ic}<div>'
            f'<div class="pe-task-title">{_html.escape(t["name"])}</div>'
            f'<div class="pe-task-desc">{_html.escape(t["desc"])}</div></div>'
            f'<div class="pe-task-reward">+{t["reward"]}</div></div>'
        )
    return "".join(rows)
def week_progress(gs):
    """按“总量 - 本周起点”算出每项周任务进度。"""
    base = gs.get("week_base", {}) or {}
    cur = {
        "feed": gs["total_feed"],
        "lottery": int(gs.get("total_lottery", 0)),
        "explore": gs["total_explore"],
    }
    out = {}
    for t in WEEK_TASK_LIST:
        b = int(base.get(t["metric"], cur[t["metric"]]))
        out[t["id"]] = max(0, cur[t["metric"]] - b)
    return out
def week_block(gs):
    prog = week_progress(gs)
    rows = []
    for t in WEEK_TASK_LIST:
        got = min(prog[t["id"]], t["target"])
        done = got >= t["target"]
        cls = "pe-task week done" if done else "pe-task week"
        ic = icon("check", 16, "#7E8F3F") if done else icon("task", 16, "#C0A57C")
        rows.append(
            f'<div class="{cls}">{ic}<div>'
            f'<div class="pe-task-title">{_html.escape(t["name"])}</div>'
            f'<div class="pe-task-desc">{_html.escape(t["desc"])}'
            f' · 进度 {got}/{t["target"]}</div></div>'
            f'<div class="pe-task-reward">+{t["reward"]}</div></div>'
        )
    return "".join(rows)
def month_block(gs):
    """月度目标：进度按“总量 - 月初起点”，m4 是“集齐四季限定”的绝对值。"""
    prog = month_progress(gs)
    done_ids = gs.get("month_done") or []
    rows = []
    for t in MONTH_TASK_LIST:
        got = min(prog[t["id"]], t["target"])
        claimed = t["id"] in done_ids
        done = got >= t["target"]
        cls = "pe-task week done" if done else "pe-task week"
        ic = icon("check", 16, "#7E8F3F") if done else icon("task", 16, "#C0A57C")
        tag = "已领取" if claimed else ("可领取" if done else f"{got}/{t['target']}")
        rows.append(
            f'<div class="{cls}">{ic}<div>'
            f'<div class="pe-task-title">{_html.escape(t["name"])}</div>'
            f'<div class="pe-task-desc">{_html.escape(t["desc"])} · {tag}</div></div>'
            f'<div class="pe-task-reward">+{t["reward"]}</div></div>'
        )
    return "".join(rows)
def messages_block(msgs, gs=None):
    tips = [
        "四项属性均衡时，健康值会慢慢恢复。",
        "每日任务每天刷新，完成后记得领取积分。",
        "宠物 10 级后使用宠物强化剂，可以觉醒星辉形态。",
        "玩耍和洗澡都有 2 小时冷却，合理安排时间。",
        "探索有 30 分钟冷却，长途探索更容易遇到稀有宝箱。",
    ]
    rows = ["<div class=\"pe-empty\">小屋很安静，来看看今天的小贴士：</div>"] if not msgs else []
    rows.extend(
        f'<div class="pe-msg">{icon("bell", 15, "#B7791F")}'
        f'<span>{_html.escape(str(m))}</span></div>'
        for m in msgs
    )
    rows.extend(
        f'<div class="pe-msg">{icon("info", 15, "#B7791F")}'
        f'<span>{_html.escape(t)}</span></div>'
        for t in tips
    )
    return "".join(rows)
def _item_icon_name(item):
    if item.startswith("皮肤·"):
        return "paint"
    return _ITEM_ICON.get(item, "box")


def item_card(item):
    return (
        f'<div class="pe-item"><div class="pe-item-ico">'
        f'{icon(_item_icon_name(item), 30, "#9A6A1E")}</div>'
        f'<div><div class="pe-item-name">{_html.escape(item)}</div>'
        f'<div class="pe-item-desc">{_html.escape(shop_desc.get(item, ""))}</div></div>'
        f'<div class="pe-item-price">{icon("coin", 15, "#B7791F")}'
        f'<b>{price_dict.get(item, 0)}</b></div></div>'
    )
def inventory_block(inv):
    if not inv:
        return '<div class="pe-empty">仓库空空如也，去商店买点东西吧</div>'
    counts = {}
    for it in inv:
        counts[it] = counts.get(it, 0) + 1
    cards = "".join(
        f'<div class="pe-inv-item">{icon(_item_icon_name(it), 20, "#9A6A1E")}'
        f'<span>{_html.escape(it)}</span><b>x{n}</b></div>'
        for it, n in counts.items()
    )
    return f'<div class="pe-inv">{cards}</div>'
def achievements_block(gs):
    rows = []
    for a in achievement_list:
        got = a["aid"] in gs["unlock_ach"]
        cls = "pe-ach" if got else "pe-ach locked"
        tname = TITLES.get(a["aid"])
        _rw = a.get("reward") or {}
        _rw_txt = []
        if _rw.get("df"):
            _rw_txt.append(f"+{int(_rw['df'])} 积分")
        for _n2, _c2 in (_rw.get("items") or []):
            _rw_txt.append(f"{_n2} ×{int(_c2)}")
        _rw_html = (f'<div class="pe-ach-rw">奖励 {_html.escape(" · ".join(_rw_txt))}</div>'
                    if _rw_txt else "")
        tag = ("已解锁 · 称号「" + tname + "」") if (got and tname) else ("已解锁" if got else "未解锁")
        rows.append(
            f'<div class="{cls}">{icon("trophy", 18, "#C08A1E" if got else "#C0A57C")}'
            f'<div><div class="pe-ach-title">{_html.escape(a["title"])}</div>'
            f'<div class="pe-ach-desc">{_html.escape(a["desc"])}</div>{_rw_html}</div>'
            f'<span class="pe-ach-tag">{_html.escape(tag)}</span></div>'
        )
    return "".join(rows)
def log_block(log_lines):
    lines = log_lines or ["暂无日志"]
    return '<div class="pe-log">' + "".join(
        f"<div>{_html.escape(str(x))}</div>" for x in lines
    ) + "</div>"
def flash(msg):
    st.session_state.setdefault("flash", []).append(msg)
def unlock(gs, aid, out_msgs):
    if aid in gs["unlock_ach"]:
        return
    gs["unlock_ach"].append(aid)
    try:
        st.session_state["_sfx_queue"] = "achievement"
    except Exception:
        pass
    title = next((a["title"] for a in achievement_list if a["aid"] == aid), str(aid))
    out_msgs.append(f"解锁成就：【{title}】")
    add_log(f"解锁成就：{title}", gs["game_log"])
    fx("ach", f"解锁成就「{title}」", big=True)
    reward = next((a.get("reward") for a in achievement_list if a["aid"] == aid), None) or {}
    _df = int(reward.get("df", 0) or 0)
    if _df:
        gs["df"] += _df
        out_msgs.append(f"成就奖励：+{_df} 积分")
        add_log(f"成就奖励：+{_df} 积分", gs["game_log"])
    for _name, _cnt in (reward.get("items") or []):
        for _ in range(int(_cnt)):
            gs["storehouse"].append(_name)
        out_msgs.append(f"成就奖励：{_name} ×{int(_cnt)}")
        add_log(f"成就奖励：{_name} ×{int(_cnt)}", gs["game_log"])
