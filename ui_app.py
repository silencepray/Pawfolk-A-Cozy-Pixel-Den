# -*- coding: utf-8 -*-
"""ui_app（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
import time
from datetime import date, datetime, timedelta
import html as _html
import os
import random
import streamlit as st
from pet_constants import *
from pet_progress import *
from pet_svg import *
from pet_room import *
from pet_state import *
from pet_ui_blocks import *
from pet_ui_blocks import (_short_name,)
from pet_fx import fx, render_fx
from pet_svg import (_r, _mx, _blob, _outline, _eyes, _mouth, _cheeks, _mood_prop, _star_deco, _legs, _PET_BODY, _PET_SKIN, _STAR_SKIN, _PET_BG, _pet_group, _frame, _theme_pal, _to_hue)
from pet_room import (_qr, _rz, _CSS)
from pet_progress import (_ICON_BODY, _ITEM_ICON)
from pet_scenes import scene_html, SCENE_LABELS
import pet_audio
from pet_audio import play as play_sfx
from pet_audio import SFX_KINDS


def room_extras(gs, limit=3):
    """同屋的其它宠物（最多 3 只），交给 room_svg 画在固定站位。"""
    out = []
    idx = int(gs.get("current_pet_idx", 0) or 0)
    for i, p in enumerate(gs.get("pet_list") or []):
        if i == idx or not isinstance(p, dict):
            continue
        out.append({
            "species": p.get("species") or p.get("name") or "猫",
            "mood": pet_mood(p),
            "star": bool(p.get("is_star")),
            "skin": skin_theme(p),
            "shiny": bool(p.get("shiny")),
        })
        if len(out) >= limit:
            break
    return out


from pet_env import gallery_home
GALLERY_DIR = gallery_home()


def record_milestone(gs, pet, key, badge, note=""):
    """里程碑落一张卡片到 gallery/，同一 key 只记一次。"""
    entries = gs.setdefault("gallery", [])
    if any(e.get("key") == key for e in entries):
        return False
    try:
        from pet_share import milestone_card
        os.makedirs(GALLERY_DIR, exist_ok=True)
        name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        path = os.path.join(GALLERY_DIR, name)
        png = milestone_card(gs, pet, badge, note, out_path=path)
        del png
        entries.append({"key": key, "badge": badge, "note": note,
                        "file": name, "at": datetime.now().strftime("%m-%d %H:%M")})
        gs["gallery"] = entries[-40:]
        return True
    except Exception:
        return False


def set_stage(scene, strength=1):
    """切换当前场景；下一次 rerun 生效，直到再次被动作改写。"""
    st.session_state["stage"] = {"scene": scene, "strength": int(strength)}

# ===================== Streamlit UI入口 =====================
st.set_page_config(page_title="毛孩子的小屋", layout="wide")


@st.fragment
def _bgm_block():
    """背景音乐开关 + 音量：放进 fragment，整页 rerun 时不会重头播。"""
    with st.expander("背景音乐", expanded=False):
        on = st.checkbox("开启背景音乐（默认关闭，白天/夜晚自动切）", key="bgm_on")
        vol = st.slider("音量", 0.0, 1.0, 0.45, 0.05, key="bgm_vol")
        st.caption(f"当前曲目：{'白天版' if pet_audio.bgm_kind() == 'day' else '夜晚版'}")
    if on:
        pet_audio.render_bgm(pet_audio.bgm_kind(), vol)

render(_CSS)
if "game_state" not in st.session_state:
    loaded = load_game()
    if loaded is None:
        render(
            '<div class="newgame-title">毛孩子的小屋</div>'
            '<div class="newgame-sub">选择你的第一只伙伴，开始温暖的陪伴</div>'
        )
        sel_pet = st.radio(
            "选择你的第一只宠物", PET_SPECIES, horizontal=True,
            label_visibility="collapsed",
        )
        with st.container(key="scene"):
            st.image(room_svg(sel_pet, "happy", False), width="stretch")
        _, mid, _ = st.columns([1, 1.2, 1])
        with mid:
            if st.button(
                "开始新游戏", type="primary", icon=":material/pets:",
                width="stretch",
            ):
                st.session_state.game_state = new_game(sel_pet)
                st.rerun()
        st.stop()
    else:
        st.session_state.game_state = loaded
if "flash" not in st.session_state:
    st.session_state.flash = []
gs = st.session_state.game_state
out_msgs = list(st.session_state.flash)
st.session_state.flash = []
# -------- 时间流逝、每日刷新、属性衰减（核心逻辑） --------
today = date.today()
if gs["current_pet_idx"] >= len(gs["pet_list"]):
    gs["current_pet_idx"] = 0
current_pet = gs["pet_list"][gs["current_pet_idx"]]
is_star = current_pet.get("is_star", False)
pet_species = species_of(current_pet)
# 图鉴同步：老存档里已有的宠物、仓库里的季节道具，自动补点亮（重复执行不会重复发积分）
dex_seed = []
for p in gs["pet_list"]:
    sp = species_of(p)
    dex_seed.append(f"{sp}|normal")
    if p.get("is_star"):
        dex_seed.append(f"{sp}|star")
dex_seed += [f"item|{it}" for it in gs["storehouse"] if it in DEX_LIMITED_ITEMS]
dex_add(gs, dex_seed, out_msgs)
# 每日任务刷新：从 10 条池子里按日期抽 3 条，每天不一样
if gs["task_day"] != today:
    gs["task_finished"] = []
    gs["task_day"] = today
    gs["task_feed_flag"] = 0
    gs["today_event_log"] = []
    gs["task_pool"] = pick_daily_tasks(today)
    out_msgs.append("新的一天！今日任务已刷新："
                    + "、".join(t["name"] for t in tasks_today(gs)))
if not gs.get("task_pool"):
    gs["task_pool"] = pick_daily_tasks(today)
# 老存档里可能留着旧固定任务的 id，先 prune 掉，免得和新池子混着误判
gs["task_finished"] = [i for i in gs.get("task_finished", [])
                      if i in gs["task_pool"]]
# 每日签到：连续第 1/2/3… 天分别 10 / 15 / 20…（+5 递增，上限 30），断签重置
# 主线章节推进 + 系统时间回拨检测
_now_ts = time.time()
if _now_ts < float(gs.get("last_seen_ts", 0) or 0) - 300:
    gs["sign_block_day"] = today.isoformat()
    out_msgs.append("检测到系统时间被回拨，本次不发放签到（冷却也按真实时间算）")
gs["last_seen_ts"] = max(_now_ts, float(gs.get("last_seen_ts", 0) or 0))
_old_chapter = int(gs.get("chapter", 0) or 0)
gs["chapter"] = max(_old_chapter, chapter_reached(gs))
if gs["chapter"] > _old_chapter:
    _cn = CHAPTERS[gs["chapter"] - 1]["name"]
    out_msgs.append(f"主线推进：第 {gs['chapter']} 章「{_cn}」开放")
    fx("star", f"第 {gs['chapter']} 章 · {_cn}", big=True)

if today > gs["last_get_date"] and gs.get("sign_block_day") != today.isoformat():
    gap = (today - gs["last_get_date"]).days
    if gap == 1:
        gs["sign_streak"] = int(gs.get("sign_streak", 1)) + 1
    else:
        gs["sign_streak"] = 1
    gs["sign_best"] = max(int(gs.get("sign_best", 1) or 1), gs["sign_streak"])
    sign_reward = min(30, 10 + 5 * (gs["sign_streak"] - 1))
    tomorrow_reward = min(30, 10 + 5 * gs["sign_streak"])
    gs["df"] += sign_reward
    gs["last_get_date"] = today
    out_msgs.append(
        f"每日签到：连续第 {gs['sign_streak']} 天，积分 +{sign_reward}"
        f"（明天记得来，可得 {tomorrow_reward} 积分）"
    )
    add_log(f"每日签到 +{sign_reward}（连续 {gs['sign_streak']} 天）", gs["game_log"])
    complete_task(gs, "sign", out_msgs)
    fx("sign", f"签到 +{sign_reward}")
week_key = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
if gs.get("week_key") != week_key:
    gs["week_key"] = week_key
    gs["week_base"] = {
        "feed": gs["total_feed"], "lottery": gs.get("total_lottery", 0),
        "explore": gs["total_explore"],
    }
    gs["week_done"] = []
    out_msgs.append("新的一周！周任务进度已重置")
month_key = month_key_of(today)
if gs.get("month_key") != month_key:
    _mb = gs.get("month_base") or {}
    gs["last_month_stats"] = {
        "month": str(gs.get("month_key") or ""),
        "feed": gs["total_feed"] - int(_mb.get("feed", gs["total_feed"])),
        "explore": gs["total_explore"] - int(_mb.get("explore", gs["total_explore"])),
        "dex": len(gs["dex"]) - int(_mb.get("dex", len(gs["dex"]))),
        "lottery": int(gs.get("total_lottery", 0) or 0),
    }
    gs["month_report"] = "pending"
    gs["month_key"] = month_key
    gs["month_base"] = {"feed": gs["total_feed"], "explore": gs["total_explore"],
                        "dex": len(gs["dex"])}
    gs["month_done"] = []
    out_msgs.append("新的一个月！月度目标已重置")
season = season_of(today)
if gs.get("last_season") != season["key"]:
    gs["last_season"] = season["key"]
    gs["season_count"] = int(gs.get("season_count", 0) or 0) + 1
    out_msgs.append(
        f"季节更替：进入{season['name']}（{season['note']}）"
        f"，本季持续到 {season['left_days']} 天后"
    )
    add_log(f"进入{season['name']}", gs["game_log"])
    st.session_state["_sfx_queue"] = st.session_state.get("_sfx_queue") or "season"
weather = weather_of(today)
if gs.get("last_weather") != weather["key"]:
    _first_weather = not gs.get("last_weather")
    gs["last_weather"] = weather["key"]
    if not _first_weather:
        out_msgs.append(f"天气转{weather['name']}：{weather['desc']}"
                        f"（{weather['tip']}）")
        add_log(f"天气转{weather['name']}", gs["game_log"])
        st.session_state["_sfx_queue"] = "weather"
        st.session_state["_weather_fx"] = weather["key"]
# 天气小剧情：连续三天的天气写进 weather_chain，凑成"雨/雷 → 放晴"给奖励
_chain = gs.setdefault("weather_chain", [])
if not _chain or _chain[-1] != today.isoformat() + "|" + weather["key"]:
    _chain.append(today.isoformat() + "|" + weather["key"])
    gs["weather_chain"] = _chain[-3:]
if (len(gs["weather_chain"]) == 3
        and gs["weather_chain"][-1].endswith("|晴")
        and any(w.endswith(("|雨", "|雷")) for w in gs["weather_chain"][:2])
        and gs.get("story_done") != season["key"]):
    gs["story_done"] = season["key"]
    gs["df"] = int(gs["df"]) + 60
    gs["today_event_log"].append("三天天气剧情收尾：雨后放晴，奖励 +60 积分")
    out_msgs.append("三天天气小剧情完成：雨过天晴，积分 +60")
    st.session_state["_weather_fx"] = "晴"
# 节日：当天第一次进入就触发一次专属事件，同一天只触发一次
fest = festival_of(today)
if gs.get("festival_day") != today:
    gs["festival_day"] = today
    gs["festival_fired"] = []
_fired = gs.setdefault("festival_fired", [])
if fest and fest["key"] not in _fired:
    _fired.append(fest["key"])
    _ev = fest["event"]
    out_msgs.append(f"{fest['name']}节日事件：{_ev['msg']}")
    add_log(f"{fest['name']} · {_ev['name']}", gs["game_log"])
    gs["today_event_log"].append(f"{fest['name']}·{_ev['msg']}")
    st.session_state["_festival_fx"] = fest["name"]
    st.session_state["_sfx_queue"] = "festival"
    if _ev.get("type") == "gain_item":
        gs["storehouse"].append(_ev["item"])
        out_msgs.append(f"获得道具：{_ev['item']}")
        dex_add(gs, [f"item|{_ev['item']}"], out_msgs)
    elif _ev.get("type") == "gain_hn":
        _val = random.randint(*_ev["val_range"]) if _ev.get("val_range") else 0
        current_pet["hn"] = min(150, float(current_pet["hn"]) + _val)
        out_msgs.append(f"开心 +{_val}")
# 亲密度：连续 2 天以上没互动，每天掉一点（每天只结算一次）
for _bm in bond_daily_decay(gs, today):
    out_msgs.append(_bm)
    add_log(_bm, gs["game_log"])
# 每日限时挑战：抽签 / 达标发奖 / 超时作废
for _cm in challenge_settle(gs):
    out_msgs.append(_cm)
now = datetime.now()
stats, _decay_msgs, delta_raw = passive_decay(
    gs, current_pet, now=now, season=season, weather=weather, is_star=is_star)
out_msgs.extend(_decay_msgs)
_dec_n, _dec_msgs2 = decay_bench(gs, now=now, season=season, weather=weather)
out_msgs.extend(_dec_msgs2)
pet_cl, pet_ha, pet_hn = stats["cl"], stats["ha"], stats["hn"]
health, exp = stats["health"], stats["exp"]
bonus = pet_bonus(current_pet)
if "last_rand_event_time" not in gs:
    gs["last_rand_event_time"] = now - RAND_EVENT_INTERVAL
rand_ready_at = gs["last_rand_event_time"] + RAND_EVENT_INTERVAL
rand_event_due = now >= rand_ready_at
gs["rand_event_next_time"] = rand_ready_at
good_w = 6
if is_star:
    # 星辉等级越高、灵能阶数越高，好事权重越大；不再是“一觉醒就拿满”
    good_w += bonus["star_lv"] // 3 + bonus["luck"] // 2
bonus_weights = [good_w, 3, 2, 3, 2, good_w, good_w, 2, 2, 3]
cur_mood = mood_tag(current_pet)
if "幸运徽章" in gs["storehouse"]:
    bonus_weights = [w + 1 if i in (0, 5, 6) else w
                     for i, w in enumerate(bonus_weights)]
if cur_mood["luck"] == "good":
    bonus_weights = [8, 4, 3, 4, 1, 8, 8, 1, 1, 3]
elif cur_mood["luck"] == "bad":
    bonus_weights = [3, 2, 2, 2, 3, 3, 3, 4, 4, 3]
if int(gs.get("bad_streak", 0)) >= 2:
    bonus_weights = [b + 4 if i in (0, 5, 6) else b for i, b in enumerate(bonus_weights)]
goodluck_on = gs["star_skill_cd"]["goodluck_stack"] > 0
if goodluck_on:
    bonus_weights = [9, 3, 2, 3, 2, 9, 9, 2, 2, 3]
BAD_EVENT_TYPES = ("lose_health", "lose_ha", "lose_cl")
season_pool = [e for e in SEASON_EVENTS[season["key"]]]
if season["key"] == "冬":
    season_pool_weights = [3, 4]
elif season["key"] == "春":
    season_pool_weights = [5, 4]
else:
    season_pool_weights = [4, 4]
weather_pool = [e for e in WEATHER_EVENTS.get(weather["key"], [])]
weather_weights = [3] * len(weather_pool)
event_pool = random_event_list + season_pool + weather_pool
all_weights = bonus_weights + season_pool_weights + weather_weights
if gs["rand_event_switch"] == 1 and rand_event_due:
    gs["last_rand_event_time"] = now
    if goodluck_on:
        gs["star_skill_cd"]["goodluck_stack"] -= 1
    event = random.choices(event_pool, weights=all_weights, k=1)[0]
    out_msgs.append(f"随机事件：{event['msg']}")
    add_log(f"随机事件：{event['msg']}", gs["game_log"])
    gs["today_event_log"].append(event["msg"])
    if len(gs["today_event_log"]) > 10:
        gs["today_event_log"].pop(0)
    if event["type"] in BAD_EVENT_TYPES:
        gs["bad_streak"] = int(gs.get("bad_streak", 0)) + 1
    elif event["type"] != "none":
        gs["bad_streak"] = 0
    # 数值每次触发时现算，不再使用导入时定死的值
    val = random.randint(*event["val_range"]) if event.get("val_range") else event.get("val", 0)
    if event["type"] == "gain_df":
        mult = bonus["df"] * (1.25 if (is_star and pet_species == "豹子") else 1.0)
        if mult > 1.001:
            val = max(1, int(round(val * mult)))
        gs["df"] += val
        out_msgs.append(f"积分 +{val}")
    elif event["type"] == "gain_item":
        gs["storehouse"].append(event["item"])
        out_msgs.append(f"获得道具：{event['item']}")
    elif event["type"] == "lose_health":
        health -= val
        out_msgs.append(f"健康 -{val}")
    elif event["type"] == "gain_hn":
        pet_hn += val
        out_msgs.append(f"开心值 +{val}")
    elif event["type"] == "lose_ha":
        pet_ha -= val
        out_msgs.append(f"饱腹值 -{val}")
    elif event["type"] == "lose_cl":
        pet_cl -= val
        out_msgs.append(f"清洁值 -{val}")
    elif event["type"] == "lose_hn":
        pet_hn -= val
        out_msgs.append(f"开心值 -{val}")
    pet_hn = max(0.0, min(pet_hn, 150))
    pet_ha = max(0.0, min(pet_ha, 150))
    pet_cl = max(0.0, min(pet_cl, 150))
    health = max(0.0, min(health, 150))
# 回写宠物属性
current_pet["hn"] = pet_hn
current_pet["ha"] = pet_ha
current_pet["cl"] = pet_cl
current_pet["health"] = health
current_pet["exp"] = exp
gs["last_auto_hour_time"] = now
# 成就判定
star_pet_count = sum(1 for p in gs["pet_list"] if p.get("is_star", False))
for aid in unlocked_achievements(gs, current_pet, star_pet_count):
    unlock(gs, aid, out_msgs)
# 自动存档：玩家做了动作就立刻写，只是属性自然衰减就节流到 30 秒一次
SAVE_THROTTLE_SEC = 30
if gs["auto_save_switch"] == 1:
    _sig = save_signature(gs)
    _now_ts = time.time()
    _last_sig = st.session_state.get("_save_sig")
    _last_ts = float(st.session_state.get("_last_save_ts", 0) or 0)
    if _sig != _last_sig or _now_ts - _last_ts >= SAVE_THROTTLE_SEC:
        save_game(gs)
        st.session_state["_save_sig"] = _sig
        st.session_state["_last_save_ts"] = _now_ts
# ===================== 主界面 =====================
render(hud_block(gs, star_pet_count, weather=weather, fest=fest))
_bgm_block()
_fc = forecast(2)
st.caption("　".join(
    f"{d.strftime('%m-%d')} {i['name']}：{i['desc']}（{i['tip']}）" for d, i in _fc))
_sfx_now = st.session_state.pop("_sfx_queue", None)
if _sfx_now:
    play_sfx(_sfx_now, key=str(date.today()))
_fest_fx = st.session_state.pop("_festival_fx", None)
if _fest_fx:
    fx("festival", f"{_fest_fx} · 节日快乐", big=True)
_wea_fx = st.session_state.pop("_weather_fx", None)
if _wea_fx:
    fx({"晴": "sunny", "雨": "rain", "雪": "snow", "雷": "thunder"}[_wea_fx],
       f"{_wea_fx}天 · {WEATHER_INFO[_wea_fx]['desc']}")
render_fx()
# 房间 + 右侧面板：每 60 秒只重跑这一块，翻页位置和别处的输入框都不受影响
@st.fragment(run_every=60)
def live_area():
    _tick_now = datetime.now()
    _ts = float(st.session_state.get("_live_ts", 0) or 0)
    if st.session_state.get("auto_tick", True) and time.time() - _ts >= 55:
        st.session_state["_live_ts"] = time.time()
        _seg = (_tick_now - gs["last_auto_hour_time"]).total_seconds() / 60
        if _seg >= 0.5:
            _stats, _msgs, _ = passive_decay(
                gs, current_pet, now=_tick_now, season=season,
                weather=weather, is_star=is_star)
            for _k, _v in _stats.items():
                current_pet[_k] = _v
            for _m in _msgs:
                add_log(_m, gs["game_log"])
            _bg_n, _bg_msgs = decay_bench(
                gs, now=_tick_now, season=season, weather=weather)
            _others = [p for i, p in enumerate(gs["pet_list"])
                       if i != int(gs.get("current_pet_idx", 0))][:3]
            if _others and random.random() < 0.22:
                _o = random.choice(_others)
                _kind = random.choice(["nap", "toy", "snack"])
                if _kind == "nap":
                    current_pet["hn"] = min(150.0, current_pet["hn"] + 5)
                    _o["hn"] = min(150.0, float(_o.get("hn", 0) or 0) + 5)
                    _line = f"{current_pet['name']} 和 {_o['name']} 挤在一起打了个盹，双方开心 +5"
                elif _kind == "toy":
                    current_pet["hn"] = max(0.0, current_pet["hn"] - 3)
                    _o["hn"] = min(150.0, float(_o.get("hn", 0) or 0) + 3)
                    _line = f"{_o['name']} 抢走了玩具，{current_pet['name']} 有点委屈（开心 -3 / +3）"
                else:
                    current_pet["ha"] = min(150.0, current_pet["ha"] + 5)
                    _line = f"{current_pet['name']} 蹭了 {_o['name']} 的饭，饱腹 +5"
                current_pet["bond"] = min(100.0, float(current_pet.get("bond", 0) or 0) + 1)
                _o["bond"] = min(100.0, float(_o.get("bond", 0) or 0) + 1)
                gs["today_event_log"].append(_line)
                if len(gs["today_event_log"]) > 10:
                    gs["today_event_log"].pop(0)
                add_log(_line, gs["game_log"])
                fx("play", _line)
            if gs.get("auto_save_switch") == 1:
                save_game(gs)
    scene_col, panel_col = st.columns([2.85, 1], gap="large")
    with scene_col:
        with st.container(key="scene"):
            _stage = st.session_state.get("stage") or {}
            _scene = _stage.get("scene") or "room"
            _strength = int(_stage.get("strength", 1) or 1)
            render(scene_html(_scene, pet_species, pet_mood(current_pet), is_star,
                              skin_theme(current_pet), _strength,
                              shiny=bool(current_pet.get("shiny")),
                              extras=room_extras(gs),
                              decor=decor_pal(gs), weather=weather["key"]))
            if _scene != "room":
                _sc_col, _sc_col2 = st.columns([3, 1])
                with _sc_col:
                    st.caption(f"场景：{SCENE_LABELS.get(_scene, _scene)}"
                               f"（强度 {_strength}/3）")
                with _sc_col2:
                    if st.button("回小屋", key="stage_home", width="stretch"):
                        st.session_state.pop("stage", None)
                        st.rerun()
            _th_now = skin_theme(current_pet)
            _wea_line = f"天气 {weather['icon']} {weather['name']} · {weather['tip']}"
            if _th_now:
                st.caption(f"小屋主题：{_th_now}（随皮肤自动切换，脱下即回默认小屋）"
                           f" · {_wea_line}")
            else:
                st.caption(_wea_line)
        # ---------- 摸摸头 / 逗猫棒：不占玩耍冷却，日限 10 次 ----------
        with st.container(key="touch"):
            _tc1, _tc2, _tc3 = st.columns([1, 1, 2.2], gap="small")
            _touch_day = gs.get("pet_touch_day")
            if _touch_day != date.today():
                gs["pet_touch_day"] = date.today()
                gs["pet_touch_count"] = 0
            _touch_used = int(gs.get("pet_touch_count", 0) or 0)
            with _tc1:
                if st.button("摸摸头", key="act_pet_head", icon=":material/front_hand:",
                             width="stretch", disabled=_touch_used >= TOUCH_DAILY):
                    _tmsg, _tok = pet_touch(gs, current_pet, "head")
                    flash(_tmsg)
                    if _tok:
                        fx("touch", _tmsg)
                        if float(current_pet.get("bond", 0) or 0) >= 100:
                            record_milestone(gs, current_pet, "bond100", "形影不离",
                                             f"{current_pet['name']} 的亲密度满档了")
                        save_game(gs)
                    st.rerun()
            with _tc2:
                if st.button("逗猫棒", key="act_pet_toy", icon=":material/toys:",
                             width="stretch", disabled=_touch_used + 2 > TOUCH_DAILY):
                    _tmsg, _tok = pet_touch(gs, current_pet, "toy")
                    flash(_tmsg)
                    if _tok:
                        fx("touch", _tmsg)
                        save_game(gs)
                    st.rerun()
            with _tc3:
                _tier_now = bond_tier(current_pet.get("bond", 0))
                st.caption(f"今日互动 {_touch_used}/{TOUCH_DAILY} 次 · "
                           f"亲密度越高台词越多（当前「{_tier_now['name']}」）")

        with st.container(key="dock"):
            d1, d2, d3, d4 = st.columns(4, gap="small")
            with d1:
                with st.popover(
                    "喂食", key="quick_feed", icon=":material/restaurant:", width="stretch"
                ):
                    inv = gs["storehouse"]
                    if not inv:
                        st.caption("仓库里还没有食物，先去商店买点吧。")
                    else:
                        feed_item = st.selectbox(
                            "选择食物", inv, key="dock_feed_item",
                            label_visibility="collapsed",
                        )
                        if st.button(
                            "投喂", key="dock_feed_go", type="primary", width="stretch"
                        ):
                            item = feed_item
                            pre_ha = float(current_pet["ha"])
                            msg_feed, theory_ha_add, add_exp = use_item(
                                gs, current_pet, item, pet_species, is_star, out_msgs)
                            current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                            current_pet["ha"] = max(0, min(current_pet["ha"], 150))
                            current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                            current_pet["health"] = max(0, min(current_pet["health"], 150))
                            skip_items = FEED_SKIP
                            is_skin = item.startswith("皮肤·")
                            if not is_skin and item not in skip_items and gs["task_feed_flag"] == 0:
                                gs["task_feed_flag"] = 1
                                complete_task(gs, "feed", out_msgs)
                            if int(gs.get("tutorial_step", 3)) == 0:
                                gs["tutorial_step"] = 1
                            if item not in skip_items and not is_skin:
                                gs["total_feed"] += 1
                                add_log(f"投喂 {item} 给 {current_pet['name']}", gs["game_log"])
                            _lv_msgs = check_levelup(current_pet, gs["game_log"])
                            for m in _lv_msgs:
                                flash(m)
                                fx("levelup", m, big=True)
                            if current_pet["lv"] % 10 == 0:
                                record_milestone(
                                    gs, current_pet, f"lv{current_pet['lv']}",
                                    f"Lv.{current_pet['lv']}",
                                    f"{current_pet['name']} 升到 {current_pet['lv']} 级")
                            st.session_state["_sfx_queue"] = (
                                "levelup" if _lv_msgs else "feed")
                            if add_exp:
                                fx("feed", f"{item} · 经验 +{add_exp:.0f}")
                            else:
                                fx("feed", f"使用 {item}")
                            if not is_skin:
                                set_stage("feed", 2 if add_exp >= 30 else 1)
                            verb = "使用" if item in ("除臭喷雾", "小零食礼包", "经验果") else "投喂"
                            flash(f"{verb} {item}：{msg_feed}")
                            # 饱腹接近上限提醒：继续喂只涨经验，属性不再增加
                            if theory_ha_add > 0 and pre_ha >= 145:
                                flash(f"⚠️ 饱腹已接近上限（{pre_ha:.0f}/150），继续投喂仍会增加 {add_exp:.0f} 点经验，"
                                      "但饱腹值不会继续上涨")
                            st.rerun()
            with d2:
                if st.button(
                    "玩耍", key="act_play", icon=":material/toys:", width="stretch"
                ):
                    now_b = datetime.now()
                    play_cd = timedelta(hours=float(TUNE["play_cd_h"]))
                    if float(current_pet.get("health", 150) or 0) < SICK_HEALTH:
                        flash("它正在生病（健康 <10），先去医院治疗，或者等它慢慢恢复")
                    elif now_b - gs["last_play_time"] >= play_cd:
                        gs["last_play_time"] = now_b
                        add_hn = 20
                        if is_star and pet_species == "猫":
                            add_hn = 30
                        current_pet["hn"] += add_hn
                        current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                        gs["total_play"] = int(gs.get("total_play", 0) or 0) + 1
                        add_log(f"和宠物玩耍，开心+{add_hn}", gs["game_log"])
                        complete_task(gs, "play", out_msgs)
                        if int(gs.get("tutorial_step", 3)) == 1:
                            gs["tutorial_step"] = 2
                        flash(f"和【{current_pet['name']}】玩耍，开心值 +{add_hn}")
                        fx("play", f"开心 +{add_hn}")
                        set_stage("play", 2 if is_star and pet_species == "猫" else 1)
                    else:
                        remain = play_cd - (now_b - gs["last_play_time"])
                        flash(f"玩耍冷却中，还要等 {fmt_wait(remain.total_seconds())}")
                    st.rerun()
            with d3:
                with st.popover(
                    "洗澡", key="quick_bath", icon=":material/bathtub:", width="stretch"
                ):
                    wash_add, soap_add = 20, 40
                    if is_star and pet_species == "小羊":
                        wash_add, soap_add = 30, 55
                    soap_have = gs["storehouse"].count("肥皂")
                    _bath_cd = timedelta(hours=float(TUNE["bath_cd_h"]))
                    _bath_left = _bath_cd - (datetime.now() - gs["last_bath_time"])
                    if _bath_left > timedelta(0):
                        st.caption(f"冷却中，还要等 {fmt_wait(_bath_left.total_seconds())}")
                    if soap_have:
                        bath_mode = st.radio(
                            "洗澡方式",
                            [f"用肥皂 · 清洁 +{soap_add}（消耗 1 个，仓里还有 {soap_have}）",
                             f"清水洗 · 清洁 +{wash_add}（不耗道具）"],
                            key="bath_mode", label_visibility="collapsed",
                        )
                        use_soap = bath_mode.startswith("用肥皂")
                    else:
                        st.caption(f"仓库里没有肥皂，这次只能清水洗（清洁 +{wash_add}）。")
                        use_soap = False
                    if st.button(
                        "开始洗澡", key="act_bath", type="primary", width="stretch",
                        disabled=_bath_left > timedelta(0),
                    ):
                        now_b = datetime.now()
                        bath_cd = timedelta(hours=float(TUNE["bath_cd_h"]))
                        if now_b - gs["last_bath_time"] >= bath_cd:
                            gs["last_bath_time"] = now_b
                            if use_soap and soap_have:
                                gs["storehouse"].remove("肥皂")
                                current_pet["cl"] += soap_add
                                gained, tool = soap_add, "肥皂"
                            else:
                                current_pet["cl"] += wash_add
                                gained, tool = wash_add, "清水"
                            current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                            gs["total_bath"] = int(gs.get("total_bath", 0) or 0) + 1
                            add_log(f"洗澡（{tool}），清洁+{gained}", gs["game_log"])
                            complete_task(gs, "bath", out_msgs)
                            flash(f"给【{current_pet['name']}】洗澡，清洁值 +{gained}"
                                  + ("（用了肥皂，泡泡更多）" if tool == "肥皂" else "（没用肥皂）"))
                            fx("bath", f"{tool} · 清洁 +{gained}",
                               big=(tool == "肥皂"))
                            set_stage("bath", 2 if tool == "肥皂" else 1)
                        else:
                            remain = bath_cd - (now_b - gs["last_bath_time"])
                            flash(f"洗澡冷却中，还要等 {fmt_wait(remain.total_seconds())}")
                        st.rerun()
            with d4:
                with st.popover(
                    "探索", key="quick_explore", icon=":material/explore:", width="stretch"
                ):
                    exp_options = ["短途（10 积分）", "中途（25 积分）", "长途（50 积分）"]
                    route = st.radio(
                        "选择路线", exp_options, key="dock_route", label_visibility="collapsed"
                    )
                    _cfg_pre = explore_config[str(exp_options.index(route) + 1)]
                    _rr_pre = explore_rare_rate(_cfg_pre, pet_species, is_star, bonus["rare"])
                    st.caption(f"本次稀有率 {_rr_pre * 100:.0f}% · 消耗 {_cfg_pre['cost']} 积分")
                    if st.button(
                        "出发", key="dock_explore_go", type="primary", width="stretch"
                    ):
                        now_b = datetime.now()
                        _exp_cd = timedelta(minutes=float(TUNE["explore_cd_min"]))
                        if float(current_pet.get("health", 150) or 0) < SICK_HEALTH:
                            flash("它病得走不动了（健康 <10），先治疗再出门")
                        elif now_b - gs["last_explore_time"] < _exp_cd:
                            remain = _exp_cd - (now_b - gs["last_explore_time"])
                            flash(f"探索冷却中，还要等 {fmt_wait(remain.total_seconds())}")
                        else:
                            cfg = explore_config[str(exp_options.index(route) + 1)]
                            if gs["df"] < cfg["cost"]:
                                flash("积分不足，无法出发探索")
                            else:
                                gs["df"] -= cfg["cost"]
                                gs["last_explore_time"] = now_b
                                gs["total_explore"] += 1
                                if is_star:
                                    gs["total_star_explore"] += 1
                                complete_task(gs, "explore", out_msgs)
                                if int(gs.get("tutorial_step", 3)) == 2:
                                    gs["tutorial_step"] = 3
                                rare_rate = explore_rare_rate(cfg, pet_species, is_star, bonus["rare"])
                                get_rare = random.random() < rare_rate
                                if get_rare:
                                    evt = next(e for e in explore_event_pool if e["rare"])
                                else:
                                    pool = [e for e in explore_event_pool if not e["rare"]]
                                    evt = random.choice(pool)
                                add_log(f"探索:{evt['msg']}", gs["game_log"])
                                set_stage("explore", exp_options.index(route) + 1)
                                fx("explore_rare" if get_rare else "explore",
                                   evt["msg"], big=get_rare)
                                detail = f"探索：{evt['msg']}"
                                if evt["type"] == "gain_df":
                                    lo, hi = evt["val_range"]
                                    g = random.randint(lo, hi)
                                    if bonus["df"] > 1.001:
                                        g = max(1, int(round(g * bonus["df"])))
                                    gs["df"] += g
                                    detail += f"（积分 +{g}）"
                                elif evt["type"] == "gain_item":
                                    it = random.choice(evt["item_list"])
                                    gs["storehouse"].append(it)
                                    detail += f"（获得 {it}）"
                                elif evt["type"] == "gain_rare_item":
                                    it = random.choice(evt["item_list"])
                                    gs["storehouse"].append(it)
                                    gs["explore_rare_once_flag"] = 1
                                    detail += f"（获得稀有道具 {it}）"
                                elif evt["type"] == "gain_hn":
                                    lo, hi = evt["val_range"]
                                    g = random.randint(lo, hi)
                                    current_pet["hn"] += g
                                    detail += f"（开心 +{g}）"
                                elif evt["type"] == "lose_health":
                                    lo, hi = evt["val_range"]
                                    ls = random.randint(lo, hi)
                                    current_pet["health"] -= ls
                                    detail += f"（健康 -{ls}）"
                                elif evt["type"] == "lose_cl":
                                    lo, hi = evt["val_range"]
                                    ls = random.randint(lo, hi)
                                    current_pet["cl"] -= ls
                                    detail += f"（清洁 -{ls}）"
                                current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                                current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                                current_pet["health"] = max(0, min(current_pet["health"], 150))
                                # 探索顺手捡到的进化材料
                                if random.random() < 0.30:
                                    gs["storehouse"].append(STAR_DUST)
                                    detail += "（顺手捡到 星尘）"
                                if get_rare and random.random() < 0.35:
                                    gs["storehouse"].append(STAR_CRYSTAL)
                                    detail += "（宝箱里还有 星尘结晶）"
                                if random.random() < SHINY_RATE and not current_pet.get("shiny"):
                                    current_pet["shiny"] = True
                                    dex_add(gs, [f"{pet_species}|shiny"], out_msgs)
                                    detail += (f"　★ {current_pet['name']}撞上异色花粉，"
                                               "变成异色形态！")
                                    add_log(f"{current_pet['name']} 异色觉醒", gs["game_log"])
                                    st.session_state["_sfx_queue"] = "shiny"
                                    fx("shiny", f"{current_pet['name']} 异色觉醒", big=True)
                                    record_milestone(gs, current_pet, "shiny",
                                                     "异色觉醒",
                                                     f"{current_pet['name']} 撞上异色花粉")
                                    set_stage("explore", 3)
                                flash(detail)
                                save_game(gs)
                        st.rerun()
    with panel_col:
        _bond = bond_tier(current_pet.get("bond", 0))
        render(pet_panel_block(gs, current_pet, star_pet_count, current_title(gs),
                               bond={"val": float(current_pet.get("bond", 0) or 0),
                                     "name": _bond["name"], "line": _bond["line"]}))
        _ps = persona_of(current_pet)
        _sk = active_skill_of(species_of(current_pet))
        _left_min = skill_left(gs, current_pet)
        st.caption(f"性格 · {_ps['name']}｜{_ps['line']}")
        if st.button(f"技能：{_sk['name']}", key="act_skill", width="stretch",
                     help=_sk["desc"]):
            _ok, _msg = use_skill(gs, current_pet)
            if _ok:
                flash(_msg)
                fx("star" if _sk["key"] != "dig" else "explore_rare", _msg, big=True)
                save_game(gs)
                st.rerun()
            else:
                flash("⚠️ " + _msg)
                fx("warn", _msg)
                st.rerun()
        st.caption("冷却中" if _left_min > 0 else f"可用 · 消耗 {_sk['bond']} 亲密度")


live_area()

_tut_step = int(gs.get("tutorial_step", 3))
if _tut_step < 3:
    _tut_steps = [
        "第 1 步：点下方「喂食」，选一件食物喂它一次",
        "第 2 步：点「玩耍」，陪它玩一次（开心值会涨）",
        "第 3 步：点「探索」，选短途出发一次",
    ]
    render(
        '<div style="display:flex;gap:10px;align-items:center;padding:12px 16px;'
        'margin:10px 0;border-radius:14px;background:#FFF4DB;border:2px dashed #E7CB92;'
        'color:#8A5A14;font-size:14px">'
        f'<b>新手引导 {_tut_step + 1}/3</b>'
        f'<span>{_tut_steps[min(_tut_step, 2)]}</span></div>'
    )
info_col, task_col = st.columns([1.15, 1], gap="large")
with info_col:
    section("bell", "小屋广播")
    render(messages_block(out_msgs, gs))
with task_col:
    section("task", "今日任务")
    render(tasks_block(gs))
    section("task", "本周任务")
    render(week_block(gs))
    week_prog = week_progress(gs)
    week_ready = [t for t in WEEK_TASK_LIST
                  if week_prog[t["id"]] >= t["target"] and t["id"] not in gs["week_done"]]
    if week_ready:
        if st.button(f"领取周任务奖励（+{sum(t['reward'] for t in week_ready)} 积分）",
                     type="primary", width="stretch"):
            total_r = 0
            for t in week_ready:
                gs["df"] += t["reward"]
                total_r += t["reward"]
                gs["week_done"].append(t["id"])
                add_log(f"完成周任务 {t['name']}，+{t['reward']}", gs["game_log"])
            flash(f"周任务奖励已发放：积分 +{total_r}")
            st.rerun()
    else:
        st.caption("周任务每周一重置，达标后在这里领取奖励。")
    section("star", "月度目标")
    render(month_block(gs))
    _m_ready = month_ready(gs)
    if _m_ready:
        if st.button(f"领取月度奖励（+{sum(t['reward'] for t in _m_ready)} 积分）",
                     type="primary", width="stretch"):
            _m_total = 0
            for t in _m_ready:
                gs["df"] += t["reward"]
                _m_total += t["reward"]
                gs.setdefault("month_done", []).append(t["id"])
                add_log(f"完成月度目标 {t['name']}，+{t['reward']}", gs["game_log"])
            flash(f"月度目标奖励已发放：积分 +{_m_total}")
            st.rerun()
    else:
        st.caption("月度目标每月 1 日重置，达标后在这里一次领完。")
    section("bolt", "限时挑战")
    _ch = challenge_today(gs)
    _cp, _ct, _cleft, _cdone = challenge_progress(gs)
    _win = str(gs.get("challenge_result")) == "win"
    st.markdown(f"**{_ch['name']}** · {_ch['desc']} · 奖励 +{_ch['reward']} 积分")
    st.progress(min(1.0, _cp / max(1, _ct)),
                text=f"进度 {_cp}/{_ct}")
    if _cdone:
        st.caption("已完成，今天这条就到这了" if _win else "已超时作废，明天换一条")
    else:
        st.caption(f"还剩 {fmt_wait(_cleft)}" if _cleft > 0 else "已超时，刷新后会作废")


def _help_markdown():
    """帮助页正文：数值全部从常量 / 数据表插值，不再手写第二份。"""
    h_play = float(TUNE["play_cd_h"])
    h_bath = float(TUNE["bath_cd_h"])
    m_exp = float(TUNE["explore_cd_min"])
    h_rand = int(RAND_EVENT_INTERVAL.total_seconds() // 3600)
    star_lo = 1 + 0.03 * 1
    star_hi = 1 + 0.03 * STAR_MAX_LV
    cut_lo = 1 - 0.04 * STAR_MAX_LV
    cut_hi = 1 - 0.04 * 1
    season_bits = "；".join(
        f"{v['name']} 饱腹 ×{v['ha']} / 清洁 ×{v['cl']} / 开心 ×{v['hn']}"
        for v in SEASON_INFO.values())
    rw = [a.get("reward", {}).get("df", 0) for a in achievement_list]
    rw = [x for x in rw if x]
    rw_txt = f"{min(rw)}~{max(rw)}" if rw else "少量"
    dex_txt = (f"{len(PET_SPECIES)} 物种 × 普通/星辉 + {len(DEX_SEASON_ITEMS)} 件季节限定"
               f" + {len(DEX_FESTIVAL_ITEMS)} 件节日限定 = {DEX_TOTAL} 格")
    trait_txt = "\n".join(species_trait_lines())
    fest_txt = "、".join(
        f"{f['name']}（{f['start'][0]}/{f['start'][1]}~{f['end'][0]}/{f['end'][1]}）"
        for f in FESTIVALS)
    return (
        "- **经验**：投喂按饱腹增量的一半折算经验（星辉按等级 "
        f"{star_lo:.2f}~{star_hi:.2f} 倍，星辉小鸡在此基础上再 ×1.1）；经验果直接 +35。"
        "升级所需经验 = 当前等级 × 50。\n"
        "- **衰减**：饱腹每分钟约 -0.5、清洁 -0.03；开心低于 75 / 清洁低于 60 时开心额外下降。"
        f"星辉按等级把衰减压到 {cut_lo:.2f}~{cut_hi:.2f}（{STAR_MAX_LV} 级最低），"
        "星辉机器人再 ×0.7，小羊清洁半速。\n"
        "- **心情标签**：开心 ≥130「超开心」，衰减 ×0.85、随机事件更偏好事；"
        "开心 <30「郁闷」，衰减 ×1.15、更容易踩坑。\n"
        "- **健康**：低于 125/100/50 逐档加速下降；健康 30~50 每分钟缓慢掉经验，<30 掉得更快"
        "（星辉 4 级起不受 <30 惩罚）。四项均 ≥80 时健康自动回升。\n"
        f"- **冷却**：玩耍 {h_play:g} 小时、洗澡 {h_bath:g} 小时、探索 {m_exp:g} 分钟、"
        f"切换宠物 3 分钟、随机事件 {h_rand} 小时最多一次；星辉技能各自独立冷却。\n"
        "- **签到**：连续签到第 1/2/3… 天分别 10/15/20…（上限 30），断签重置为 10。\n"
        f"- **每日任务**：从 {len(DAILY_TASK_POOL)} 条任务池里按日期抽 3 条"
        "（同一天固定、换天就换），完成后自动发积分；池子里包含签到、探索、合成、星辉技能等动作。\n"
        "- **周任务 / 月度目标**：每周、每月重置，达标后在对应卡片下方领取，月度奖励 150~300 积分。\n"
        "- **称号**：14 个成就各对应一个称号（如「星途无尽」→「星轨行者」），"
        "解锁后自动取已获得的最高称号，展示在宠物面板。\n"
        "- **合成台**：仓库页可把材料换成品——5 星尘→1 星尘结晶、2 面包→1 葡萄、"
        "2 药品+2 面包→1 高级营养液、3 药品→1 急救针，不花积分。\n"
        f"- **宠物上限**：最多同时养 {PET_MAX} 只，领养 {ADOPT_COST} 积分；"
        f"放生返还 {RELEASE_REFUND} 积分，图鉴点亮记录保留、不会因为放生而掉格。\n"
        "- **存档**：存档是纯文本（一行一条字段），可在「数据 · 服务」里导出/导入，"
        "自动备份保留最近 3 份到 save_backups/，「重新开始」会把旧档改名留存而不是直接删掉。\n"
        f"- **音效**：投喂 / 升级 / 中奖 / 换季 / 节日 / 异色 / 成就 共 {len(SFX_KINDS)} 种短音效，"
        "默认静音，在「日志 · 设置」里勾「开启音效」才会响。\n"
        f"- **存档槽**：{SLOT_COUNT} 个槽位，可以各自命名、存入当前进度、确认后读取覆盖；"
        "切换前会自动备份当前存档。\n"
        "- **时间维度**：数据面板会显示游玩天数、日均投喂、最长连续签到和首次游玩日期。\n"
        "- **分享卡片**：「数据 · 服务」里可以把当前宠物渲染成 720×1000 的 PNG，直接发出去。\n"
        "- **调参面板**：设置页勾选「显示调参面板」后可以临时改冷却 / 概率 / 衰减倍率，"
        "只影响当前进程，改回默认点一下就恢复。\n"
        "- **彩票**：普通 15 / 中级 40 / 高级 100 积分；概率固定为大奖 5%、高级奖 30%、"
        "不中奖 65%，中奖金额 20~300 积分不等；最近 5 次结果可在彩票店回看。\n"
        f"- **季节**：每 {SEASON_DAYS} 天循环 春→夏→秋→冬。{season_bits}。"
        "每季有对应专属随机事件和一件限定商品，换季后商品会轮换。\n"
        "- **星辉**：10 级后使用宠物强化剂觉醒，觉醒即为星辉 Lv.1；"
        f"星辉最高 {STAR_MAX_LV} 级，每级消耗「星尘」并需要积分，"
        "等级越高衰减越低、经验越多、健康回复越强，4 级起健康低于 30 时获得护体。\n"
        "- **进化**：宠物 25 级、持有「星尘结晶」时可选择进化方向（战意 / 守护 / 灵能），"
        "每个方向 5 阶，门槛依次为 25/30/35/40/45 级、材料 1~5 枚；主增益随阶数递增，"
        "副作用固定——战意衰减 ×1.15，守护经验 -10%，灵能饱腹衰减 ×1.25。\n"
        "- **五行元素**：金木水火土各有优点与代价：金 经验 +12%/开心衰减 +12%；"
        "木 健康回复 +25%/清洁衰减 +15%；水 清洁衰减 -25%/饱腹衰减 +12%；"
        "火 开心衰减 -20%/健康流失 +10%；土 饱腹衰减 -20%/开心衰减 +15%。\n"
        f"- **皮肤**：商店「皮肤」{SKIN_PRICE} 积分，购买时自动按当前宠物的物种记账，"
        "在仓库点「穿戴」即可换装，立绘与整间小屋同步换配色。\n"
        "- **天气**：按日期+季节当种子生成晴/雨/雪/雷，一天不变。雨天清洁 ×1.35、"
        "雪天饱腹 ×1.35、雷天心情 ×1.25，房间会飘雨丝/雪花/闪电，换天气有专属特效与提示音。\n"
        f"- **节日限定**：{fest_txt} 各有一件限定商品 + 一条专属事件，"
        "当天首次进游戏自动触发，过期就要等明年。\n"
        f"- **限时挑战**：每天从 {len(DAILY_CHALLENGES)} 条里抽 1 条（探索 / 投喂 / 玩耍 / "
        "抚摸 / 洗澡），带倒计时，达标自动发 "
        f"{min(c['reward'] for c in DAILY_CHALLENGES)}~"
        f"{max(c['reward'] for c in DAILY_CHALLENGES)} 积分，超时作废、第二天换一条。\n"
        "- **生病**：健康低于 10 就进入生病状态，不能玩耍也不能探索，"
        "得去医院治疗（基础 30 / 深度 80 积分）或等它慢慢恢复。\n"
        "- **物种小传**：图鉴里每只宠物都有一段设定和口头禅，亲密度到「亲近」（60）后解锁最后一段。\n"
        "- **小屋装修**：墙纸 / 地毯 / 挂画 / 窗景 四个槽位，在「小屋装修」页买和装，"
        "与整套皮肤可叠加。\n"
        f"- **图鉴**：{dex_txt}，按五类分栏展示。点亮即 +5 积分，双皮肤齐 +30，"
        "四十物种齐 +100，四季限定齐 +80，节日限定齐 +90，满册 +200。曾拥有即点亮。\n"
        f"- **成就**：{len(achievement_list)} 个成就各带称号，解锁即发积分奖励（{rw_txt}），"
        "「秘境欧皇」「星能掌控者」「五行归一」额外给星尘结晶 / 强化剂 / 星尘。\n"
        f"- **亲密度**：每只宠物一条独立的亲密度（0~{BOND_MAX}），"
        "分陌生 / 熟络 / 亲近 / 依赖 / 形影不离五档，档位越高面板台词越黏人。"
        "摸头、逗猫棒、喂爱吃的都会涨，喂它讨厌的会掉。"
        "**连续 2 天以上不理它，亲密度每天 -1（间隔越久一次掉得越多，单次最多 -3）**，"
        "最高档需要每天来维持。\n"
        "- **口味偏好**：每个物种各有 1 爱 1 嫌（物品说明里会写是谁）。"
        "喂爱吃的效果翻倍并额外 +3 亲密度；喂讨厌的效果减半、开心 -5、亲密度 -1。\n"
        f"- **互动**：房间下方「摸摸头」+1~3 开心、「逗猫棒」+3~5 开心（更费次数），"
        f"每次都会涨亲密度；合计每天 {TOUCH_DAILY} 次，不占用玩耍冷却，第二天自动刷新。\n"
        f"- **后台衰减**：不在台前的宠物也会按 {INACTIVE_DECAY_MUL:.0%} 速率掉属性（健康照实算），"
        "所以领满 6 只不能只养 1 只，切换是有意义的。\n"
        "- **同屋**：其它宠物会站在房间里陪你（最多 3 只），各自保留颜色、表情和星辉 / 异色外观。\n"
        "- **异色**：探索时约 1% 概率撞上「异色花粉」，宠物永久变成异色形态，图鉴多点亮一格。\n"
        f"- **变卖**：仓库页的「变卖」把道具按商店售价的 {SELL_RATE:.0%} 回收成积分（最低 1），"
        "勾确认即到账；卖掉就回不来。\n"
        "- **物种特性一览**（由口味表与特性表自动生成）：\n" + trait_txt
    )

_ALL_SECTIONS = ["商店 · 仓库", "彩票 · 医院", "星辉 · 进化", "小屋装修", "图鉴",
                 "宠物管理", "帮助 · 规则", "成就 · 宠物", "数据 · 服务", "日志 · 设置"]
_TAG_OF = {"商店 · 仓库": "shop", "彩票 · 医院": "fun", "星辉 · 进化": "star",
           "小屋装修": "decor", "图鉴": "dex", "宠物管理": "pet",
           "数据 · 服务": "svc", "日志 · 设置": "log",
           "帮助 · 规则": "help", "成就 · 宠物": "ach"}
_unlocked = unlock_sections(gs)
_SECTIONS = [n for n in _ALL_SECTIONS if _TAG_OF[n] in _unlocked]
_locked = [n for n in _ALL_SECTIONS if _TAG_OF[n] not in _unlocked]
if st.session_state.get("main_section") in _locked:
    st.session_state["main_section"] = "商店 · 仓库"
_tab = st.segmented_control(
    "功能分区", _SECTIONS, default="商店 · 仓库", key="main_section",
    label_visibility="collapsed",
) or "商店 · 仓库"
_TAB = _TAG_OF.get(_tab, "shop")
_ch = int(gs.get("chapter", 0) or 0)
if _ch:
    _seen = int(gs.get("chapter_claimed", 0) or 0)
    _cn = CHAPTERS[_ch - 1]
    _locked_txt = ("｜下一章解锁：" + "、".join(_locked)) if _locked else "｜全部分区已开放"
    render(f'<div class="pixel-card" style="margin:6px 0 10px">'
           f'<b>第 {_ch} 章 · {_cn["name"]}</b>　{_cn["desc"]}'
           f'<span style="color:#8A6A3A;font-size:13px">{_locked_txt}</span></div>')
    if _ch > _seen:
        if st.button(f"领取第 {_seen + 1}~{_ch} 章奖励", key="claim_chapter",
                     width="stretch"):
            _got = claim_chapters(gs, current_pet)
            for _g in _got:
                flash(_g)
            fx("ach", "章节奖励已领取", big=True)
            save_game(gs)
            st.rerun()
if _TAB == "shop":
    section("shop", "商店")
    sd_shop = season_of()
    season_item = sd_shop["shop"]
    fest_item = fest["item"] if fest else ""
    shop_list = shop_things + [season_item] + ([fest_item] if fest_item else [])
    st.caption(
        f"{sd_shop['name']}限定：{season_item}（还剩 {sd_shop['left_days']} 天换季，"
        f"下一季 {sd_shop['next']} 会换新商品）"
    )
    if fest:
        st.markdown(
            f'<div class="fest-banner">{fest["icon"]} {fest["name"]}限定 · '
            f'{fest["item"]}（还剩 {fest["left_days"]} 天，卖完就下架）</div>',
            unsafe_allow_html=True)
    buy_item = st.selectbox("选购商品", shop_list)
    render(item_card(buy_item))
    if buy_item == season_item:
        st.caption(f"★ 本季限定商品 · {shop_desc.get(season_item, '')}")
    if fest_item and buy_item == fest_item:
        st.caption(f"★ {fest['name']}限定商品 · {shop_desc.get(fest_item, '')}")
    if fest:
        _fq = gs.setdefault("fest_quest", {})
        if _fq.get("key") != fest["key"]:
            _fq = {"key": fest["key"], "steps": [False, False, False],
                   "explore_base": gs["total_explore"], "done": False}
            gs["fest_quest"] = _fq
        st.markdown(f"**{fest['name']}任务链** · 三步全做完给「节日挂画」（进装修库）+120 积分")
        _labels = [f"① 吃一次{fest['item']}", "② 换上任意一件装修",
                   "③ 节日期间再探索 3 次"]
        _cur = [False, False, False]
        _cur[0] = fest["item"] in gs["storehouse"]
        _cur[1] = bool(gs.get("decor"))
        _cur[2] = gs["total_explore"] - int(_fq.get("explore_base", gs["total_explore"])) >= 3
        for _i, _lb in enumerate(_labels):
            st.caption(("✅ " if _fq["steps"][_i] else ("• " if _cur[_i] else "🔒 ")) + _lb)
        if not _fq.get("done"):
            _b1, _b2, _b3 = st.columns(3)
            with _b1:
                if st.button("完成第 1 步", key="fq1", disabled=_fq["steps"][0] or not _cur[0]):
                    gs["storehouse"].remove(fest["item"])
                    current_pet["hn"] = min(150.0, current_pet["hn"] + 10)
                    _fq["steps"][0] = True
                    flash(f"{current_pet['name']} 吃掉了 {fest['item']}，开心 +10")
                    fx("festival", f"节日任务 1/3 · {fest['item']}")
                    st.rerun()
            with _b2:
                if st.button("完成第 2 步", key="fq2", disabled=_fq["steps"][1] or not _cur[1]):
                    _art = next((i for i in gs.get("decor_owned", [])
                                 if DECOR_BY_ID.get(i, {}).get("slot") == "art"), None)
                    if _art:
                        decor_apply(gs, "art", _art)
                    _fq["steps"][1] = True
                    flash("已换上节日装修")
                    fx("decor", "节日任务 2/3 · 换装修")
                    st.rerun()
            with _b3:
                if st.button("完成第 3 步", key="fq3", disabled=_fq["steps"][2] or not _cur[2]):
                    _fq["steps"][2] = True
                    flash("节日期间探索满 3 次")
                    fx("explore", "节日任务 3/3 · 探索")
                    st.rerun()
        if _fq["steps"][0] and _fq["steps"][1] and _fq["steps"][2] and not _fq.get("done"):
            _fq["done"] = True
            gs["df"] += 120
            if "art_fest" not in gs.get("decor_owned", []):
                gs.setdefault("decor_owned", []).append("art_fest")
            add_log("节日任务链完成：节日挂画 +120 积分", gs["game_log"])
            flash("节日任务链完成！获得「节日挂画」+120 积分")
            fx("festival", "任务链完成 · 节日挂画", big=True)
            st.balloons()
            st.rerun()
    if st.button("购买", type="primary"):
        price = price_dict[buy_item]
        if gs["df"] >= price:
            gs["df"] -= price
            gs["storehouse"].append(buy_item)
            if buy_item in DEX_LIMITED_ITEMS:
                dex_add(gs, [f"item|{buy_item}"], out_msgs)
            add_log(f"商店购买 {buy_item}", gs["game_log"])
            complete_task(gs, "shop", out_msgs)
            flash(f"购买成功：{buy_item}（积分 -{price}）")
            if fest_item and buy_item == fest_item:
                fx("festival", f"入手 {buy_item}", big=True)
                st.session_state["_sfx_queue"] = "festival"
            else:
                fx("craft", f"入手 {buy_item}")
            st.rerun()
        else:
            st.warning("积分不足！")
    st.divider()
    section("paint", "皮肤")
    st.caption(
        f"皮肤只改外观、不加属性。购买时按当前宠物【{current_pet['name']}·{pet_species}】自动记账，"
        f"买完到仓库「穿戴」，立绘会换成专属配色与光效。售价 {SKIN_PRICE} 积分。"
    )
    for k in SKIN_ORDER:
        st.caption(f"· {k}：{SKIN_THEMES[k]['desc']}")
    skin_pick = st.selectbox("选择皮肤主题", SKIN_ORDER, key="skin_buy")
    skin_item_name = f"皮肤·{skin_pick}·{pet_species}"
    st.caption(f"本次将购买：{skin_item_name}")
    st.image(room_svg(pet_species, pet_mood(current_pet), is_star, skin_pick,
                          stage=growth_stage(current_pet)), width=420)
    st.caption("预览：穿上后立绘和整间小屋都会换成这套主题配色")
    if st.button(f"购买皮肤（{SKIN_PRICE} 积分）", type="primary", width="stretch"):
        if gs["df"] < SKIN_PRICE:
            st.warning("积分不足！")
        else:
            gs["df"] -= SKIN_PRICE
            gs["storehouse"].append(skin_item_name)
            add_log(f"商店购买 {skin_item_name}", gs["game_log"])
            flash(f"购买成功：{skin_item_name}，去仓库穿戴")
            save_game(gs)
            st.rerun()
    st.divider()
    section("box", "仓库")
    render(inventory_block(gs["storehouse"]))
    skin_items = [it for it in dict.fromkeys(gs["storehouse"]) if it.startswith("皮肤·")]
    if skin_items:
        st.divider()
        st.caption("皮肤：穿戴后立绘立刻换装，脱下会退回仓库")
        for s_item in skin_items:
            parts = s_item.split("·")
            if len(parts) != 3:
                continue
            th, sp_of_item = parts[1], parts[2]
            worn = (species_of(current_pet) == sp_of_item
                    and skin_theme(current_pet) == th)
            cnt = gs["storehouse"].count(s_item)
            st.markdown(f"**{s_item}** ×{cnt}" + ("　·　当前已穿戴" if worn else ""))
            c_w, c_u = st.columns(2)
            with c_w:
                if st.button("穿戴", key=f"wear_{s_item}", width="stretch"):
                    if species_of(current_pet) != sp_of_item:
                        st.warning(f"这是 {sp_of_item} 的皮肤，请先切到 {sp_of_item} 宠物")
                    elif worn:
                        st.info("这件已经穿在身上了")
                    else:
                        gs["storehouse"].remove(s_item)
                        old = skin_theme(current_pet)
                        if old:
                            gs["storehouse"].append(f"皮肤·{old}·{sp_of_item}")
                        current_pet["skin"] = th
                        add_log(f"{current_pet['name']} 换上 {s_item}", gs["game_log"])
                        flash(f"{current_pet['name']} 换上了 {th} 皮肤")
                        save_game(gs)
                        st.rerun()
            with c_u:
                if st.button("脱下", key=f"unwear_{s_item}", width="stretch"):
                    if not worn:
                        st.info("当前没穿这件")
                    else:
                        gs["storehouse"].append(s_item)
                        current_pet["skin"] = "normal"
                        add_log(f"{current_pet['name']} 脱下 {s_item}", gs["game_log"])
                        flash(f"{current_pet['name']} 恢复原色")
                        save_game(gs)
                        st.rerun()
    st.caption("点击上方操作栏的【喂食】按钮即可投喂道具。")
    st.divider()
    section("sell", "变卖")
    st.caption(f"仓库里的东西都能按商店售价的 {int(SELL_RATE * 100)}% 回收成积分；"
               "整件卖出、当场到账，不可撤销。")
    _sell_pool = sorted(dict.fromkeys(gs["storehouse"]),
                        key=lambda x: (-gs["storehouse"].count(x), x))
    if not _sell_pool:
        st.caption("仓库是空的，暂时没东西可变卖。")
    else:
        _sell_sel = st.selectbox(
            "选择要卖的道具", _sell_pool, key="sell_item",
            format_func=lambda x: (f"{x}（有 {gs['storehouse'].count(x)} 个 · "
                                   f"回收 {sell_price(x)} 积分/个）"))
        _sell_max = gs["storehouse"].count(_sell_sel)
        _sell_n = st.number_input(f"卖出数量（最多 {_sell_max} 个）", min_value=1,
                                  max_value=int(_sell_max), value=1, step=1,
                                  key="sell_n")
        st.caption(f"本次可得 **{sell_price(_sell_sel) * int(_sell_n)}** 积分"
                   f"（原价 {price_dict.get(_sell_sel, 0)}，回收价减半）")
        _sell_ok = st.checkbox("确认卖出（卖掉就回不来了）", key="sell_ok")
        if st.button("卖出", key="act_sell", type="primary", width="stretch",
                     disabled=not _sell_ok):
            _got, _smsg = sell_items(gs, _sell_sel, int(_sell_n))
            flash(_smsg)
            if _got:
                fx("sell", f"{_sell_sel}×{int(_sell_n)} · 积分 +{_got}")
                save_game(gs)
            st.rerun()
    st.divider()
    section("box", "合成台")
    st.caption("把仓库里堆着的低级材料换成高级货，合成不消耗积分。")
    _recipe_names = [f"{r['out']}（" + "、".join(f"{k}×{v}" for k, v in r["need"].items()) + "）"
                     for r in CRAFT_RECIPES]
    _ridx = st.selectbox("选择配方", range(len(CRAFT_RECIPES)),
                         format_func=lambda i: _recipe_names[i])
    _recipe = CRAFT_RECIPES[_ridx]
    st.caption(_recipe["desc"])
    st.caption("现有：" + "　".join(
        f"{k} ×{gs['storehouse'].count(k)}" for k in _recipe["need"]))
    if st.button("合成", type="primary", width="stretch"):
        _ok, _msg = craft(gs, _recipe["id"], out_msgs)
        if _ok:
            fx("craft", f"合成 {_recipe['out']}")
            set_stage("craft", 2)
        flash(_msg)
        if _ok:
            st.rerun()
        else:
            st.warning(_msg)
    st.divider()
    section("info", "物品说明查询")
    query_item = st.selectbox("选择要查询的道具", shop_things, key="query_item")
    render(item_card(query_item))
    st.caption(f"用途：{shop_desc.get(query_item, '暂无说明')}")
    owned = gs["storehouse"].count(query_item)
    st.caption(f"仓库里目前有 {owned} 个 · 商店售价 {price_dict.get(query_item, 0)} 积分"
               f" · 回收价 {sell_price(query_item)} 积分")
    _t = taste_of(query_item)  # 只是为了下面那句口味提示不重复计算
    _love_by = [sp for sp in PET_SPECIES if TASTE.get(sp, {}).get("love") == query_item]
    _hate_by = [sp for sp in PET_SPECIES if TASTE.get(sp, {}).get("hate") == query_item]
    if _love_by:
        st.caption("最爱吃它：" + "、".join(_love_by[:8]) + ("…" if len(_love_by) > 8 else ""))
    if _hate_by:
        st.caption("讨厌它：" + "、".join(_hate_by[:8]) + ("…" if len(_hate_by) > 8 else ""))
# ---------- 彩票医院 ----------
if _TAB == "fun":
    section("ticket", "彩票店")
    lot_options = ["普通彩票（15 积分）", "中级彩票（40 积分）", "高级彩票（100 积分）"]
    lot_sel = st.radio("彩票类型", lot_options)
    lot_idx = lot_options.index(lot_sel)
    st.caption(f"中奖概率：大奖 {TUNE['big_p']}% · 高级奖 {TUNE['mid_p']}% · "
               f"不中奖 {100 - int(TUNE['big_p'] + TUNE['mid_p'])}%")
    if st.button("购买彩票", type="primary"):
        win_big = False
        res_text = ""
        # 概率固定：大奖 5%、高级奖 30%、不中奖 65%
        cost = [15, 40, 100][lot_idx]
        small_amt = [20, 60, 150][lot_idx]
        big_amt = [50, 120, 300][lot_idx]
        big_p = int(TUNE["big_p"])
        if gs["df"] >= cost:
            gs["df"] -= cost
            # 任务只在真的买下彩票、钱扣掉之后才结算，积分不足不算完成
            complete_task(gs, "lottery", out_msgs)
            r = random.randint(1, 100)
            if r <= big_p:
                gs["df"] += big_amt
                res_text = f"中大奖，积分 +{big_amt}"
                win_big = True
                gs["total_lottery_win"] = int(gs.get("total_lottery_win", 0)) + 1
            elif r <= big_p + int(TUNE["mid_p"]):
                gs["df"] += small_amt
                res_text = f"高级奖，积分 +{small_amt}"
                gs["total_lottery_win"] = int(gs.get("total_lottery_win", 0)) + 1
            else:
                res_text = "没有中奖"
        else:
            res_text = "积分不足"
        if win_big:
            gs["big_win_flag"] = 1
            add_log("彩票中大奖", gs["game_log"])
        add_log(f"彩票结果:{res_text}", gs["game_log"])
        if "积分不足" not in res_text:
            gs["total_lottery"] = int(gs.get("total_lottery", 0)) + 1
            lot_name = ["普通", "中级", "高级"][lot_idx]
            gs.setdefault("lottery_history", []).append(
                f"{datetime.now().strftime('%m-%d %H:%M')} · {lot_name}彩票 · {res_text}"
            )
            gs["lottery_history"] = gs["lottery_history"][-5:]
        if "积分不足" not in res_text and "没有中奖" not in res_text:
            fx("lottery", res_text, big=win_big)
        flash(f"彩票结果：{res_text}")
        st.rerun()
    hist = gs.get("lottery_history", [])
    if hist:
        st.caption("最近 5 次战果")
        for h in reversed(hist):
            st.caption(f"· {h}")
    else:
        st.caption("还没有买过彩票，历史记录会出现在这里。")
    st.divider()
    section("hospital", "宠物医院")
    h_options = ["基础治疗（30 积分 · 健康 +40）",
                 "深度治疗（80 积分 · 健康 +100）",
                 "ICU 急救（150 积分 · 健康拉满）"]
    h_sel = st.radio("治疗项目", h_options)
    h_idx = h_options.index(h_sel)
    if st.button("执行治疗", type="primary"):
        healed = False
        if h_idx == 0:
            c, h = 30, 40
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] += h
                healed = True
        elif h_idx == 1:
            c, h = 80, 100
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] += h
                healed = True
        else:
            c = 150
            if gs["df"] >= c:
                gs["df"] -= c
                current_pet["health"] = 150.0
                healed = True
        current_pet["health"] = max(0, min(current_pet["health"], 150))
        add_log(f"医院治疗，health={current_pet['health']:.1f}", gs["game_log"])
        if healed:
            complete_task(gs, "heal", out_msgs)
            set_stage("clinic", 2 if h_idx == 2 else 1)
            flash(f"治疗完成，当前健康值 {current_pet['health']:.1f}")
            fx("heal", f"健康 {current_pet['health']:.0f}")
        else:
            flash("积分不足，治疗取消")
        st.rerun()
if _TAB == "star":
    section("gem", "星辉等级")
    st.caption("星辉不再是“觉醒就拥有全部”，而是 1~10 级逐级增强：衰减更低、经验更多、护体更早生效。")
    if not is_star:
        st.warning("当前宠物还不是星辉形态。10 级后使用「宠物强化剂」觉醒，等级从 Lv.1 开始。")
    else:
        slv = max(1, int(current_pet.get("star_lv", 1) or 1))
        st.markdown(f"**{current_pet['name']}** · 星辉 Lv.**{slv}** / {STAR_MAX_LV}")
        st.caption(bonus_summary(current_pet))
        st.progress(min(1.0, slv / STAR_MAX_LV))
        if slv >= STAR_MAX_LV:
            st.success("星辉已满级 Lv.10：衰减 ×0.60、经验 ×1.30、健康回复 2 倍、护体常驻。")
        else:
            dust_need, df_need = star_up_cost(slv)
            have_dust = gs["storehouse"].count(STAR_DUST)
            st.caption(
                f"升到 Lv.{slv + 1} 需要：星尘 ×{dust_need}（现有 {have_dust}）、积分 {df_need}。"
                f"星尘可从探索稀有宝箱拾得，也可在商店购买。"
            )
            if st.button(f"升级星辉 → Lv.{slv + 1}", type="primary", width="stretch"):
                if have_dust < dust_need:
                    st.warning(f"星尘不足，还差 {dust_need - have_dust} 个")
                elif gs["df"] < df_need:
                    st.warning(f"积分不足，需要 {df_need} 积分")
                else:
                    # 先问一句再扣：点按钮只登记意向，真正的扣料在确认之后
                    st.session_state["star_confirm"] = {
                        "idx": gs["current_pet_idx"],
                        "name": current_pet["name"],
                        "from": slv,
                        "to": slv + 1,
                        "dust": dust_need,
                        "df": df_need,
                    }
                    st.rerun()
            _pending = st.session_state.get("star_confirm")
            if _pending and _pending.get("idx") == gs["current_pet_idx"] \
                    and _pending.get("from") == slv:
                st.warning(
                    f"要把「{_pending['name']}」的星辉从 Lv.{_pending['from']} "
                    f"升到 Lv.{_pending['to']} 吗？\n\n"
                    f"将消耗：星尘 ×{_pending['dust']}、积分 {_pending['df']}。"
                    "星尘和积分都不退还，确认后立即生效。"
                )
                _cf1, _cf2 = st.columns(2)
                with _cf1:
                    if st.button("确认升级", key="star_up_yes", type="primary",
                                 width="stretch"):
                        st.session_state.pop("star_confirm", None)
                        _p = gs["pet_list"][gs["current_pet_idx"]]
                        _need_dust, _need_df = star_up_cost(
                            max(1, int(_p.get("star_lv", 1) or 1)))
                        if gs["storehouse"].count(STAR_DUST) < _need_dust:
                            st.warning("星尘不够了，升级已取消")
                        elif gs["df"] < _need_df:
                            st.warning("积分不够了，升级已取消")
                        else:
                            for _ in range(_need_dust):
                                gs["storehouse"].remove(STAR_DUST)
                            gs["df"] -= _need_df
                            _p["star_lv"] = max(1, int(_p.get("star_lv", 1) or 1)) + 1
                            add_log(f"{_p['name']} 星辉升至 Lv.{_p['star_lv']}",
                                    gs["game_log"])
                            flash(f"星辉升至 Lv.{_p['star_lv']}：{bonus_summary(_p)}")
                            fx("star", f"星辉 Lv.{_p['star_lv']}", big=True)
                            set_stage("star", 3)
                            save_game(gs)
                            st.rerun()
                with _cf2:
                    if st.button("再想想", key="star_up_no", width="stretch"):
                        st.session_state.pop("star_confirm", None)
                        st.rerun()
    st.divider()
    section("skill", "星辉技能")
    st.caption("只有星辉形态的宠物才能释放技能，技能有独立冷却时间；数值随星辉等级提高。")
    sl_a = max(1, int(bonus["star_lv"]))
    _now_sk = datetime.now()

    def _cd_tag(key):
        """把技能冷却直接写进选项文案，不用点一下才知道还要等多久。"""
        cd = gs["star_skill_cd"].get(key)
        if not isinstance(cd, datetime):
            return "可用"
        left = (cd - _now_sk).total_seconds()
        return "可用" if left <= 0 else f"还剩 {fmt_wait(left)}"

    skill_options = [
        f"星沐 · {_cd_tag('star_mu')} · 开心/饱腹/清洁 +{30 + 2 * (sl_a - 1)}",
        f"星愈 · {_cd_tag('star_heal')} · 健康 +{60 + 4 * (sl_a - 1)}",
        f"星满 · {_cd_tag('star_full')} · 全属性 +{20 + (sl_a - 1)}",
        f"星启 · {_cd_tag('star_goodluck')} · 好事 {3 + sl_a // 4} 次",
    ]
    skill_sel = st.radio("技能", skill_options)
    skill_idx = skill_options.index(skill_sel)
    if st.button("释放技能", type="primary"):
        if not is_star:
            st.warning("当前宠物不是星辉形态！")
        else:
            now_b = datetime.now()
            cd_key = STAR_SKILL_KEYS[skill_idx]
            ok, cd_left = star_skill_start(gs, cd_key, now_b)
            if not ok:
                st.warning(f"技能冷却中，还要等 {fmt_wait(cd_left)}")
            else:
                fx("star", "星辉技能已释放")
                set_stage("star", 2)
                if skill_idx == 0:
                    mu_amt = 30 + 2 * (bonus["star_lv"] - 1)
                    current_pet["hn"] += mu_amt
                    current_pet["ha"] += mu_amt
                    current_pet["cl"] += mu_amt
                    current_pet["hn"] = max(0, min(current_pet["hn"], 150))
                    current_pet["ha"] = max(0, min(current_pet["ha"], 150))
                    current_pet["cl"] = max(0, min(current_pet["cl"], 150))
                    add_log("释放星辉技能【星沐】", gs["game_log"])
                    flash(f"释放星辉技能【星沐】：开心 / 饱腹 / 清洁各 +{mu_amt}")
                elif skill_idx == 1:
                    heal_amt = 60 + 4 * (bonus["star_lv"] - 1)
                    current_pet["health"] += heal_amt
                    current_pet["health"] = max(0, min(current_pet["health"], 150))
                    add_log("释放星辉技能【星愈】", gs["game_log"])
                    flash(f"释放星辉技能【星愈】：健康 +{heal_amt}")
                elif skill_idx == 2:
                    full_amt = 20 + (bonus["star_lv"] - 1)
                    current_pet["hn"] += full_amt
                    current_pet["ha"] += full_amt
                    current_pet["cl"] += full_amt
                    current_pet["health"] += full_amt
                    for _k in ("hn", "ha", "cl", "health"):
                        current_pet[_k] = max(0, min(current_pet[_k], 150))
                    add_log("释放星辉技能【星满】", gs["game_log"])
                    flash(f"释放星辉技能【星满】：全属性 +{full_amt}")
                else:
                    gs["star_skill_cd"]["goodluck_stack"] = 3 + bonus["star_lv"] // 4
                    add_log("释放星辉技能【星启】", gs["game_log"])
                    flash("释放星辉技能【星启】：接下来 "
                          f"{gs['star_skill_cd']['goodluck_stack']} 次随机事件更偏向好事")
                save_game(gs)
                st.rerun()
if _TAB == "decor":
    section("paint", "小屋装修")
    st.caption(
        f"皮肤是整套换（墙、地板、家具一起变），装修是分部位自己搭，两条线叠加。"
        f"当前天气 {weather['icon']} {weather['name']}，预览里能直接看到天气效果。"
    )
    st.image(room_svg(pet_species, pet_mood(current_pet), is_star,
                      skin_theme(current_pet), decor=decor_pal(gs),
                      weather=weather["key"], stage=growth_stage(current_pet)), width="stretch")
    st.caption("预览：上面这张就是装修 + 天气叠完的样子")
    for _slot in DECOR_SLOTS:
        st.divider()
        _sk = _slot["key"]
        _cur = (gs.get("decor") or {}).get(_sk, "")
        _owned = [i for i in gs.get("decor_owned", [])
                  if DECOR_BY_ID[i]["slot"] == _sk]
        st.markdown(f"**{_slot['name']}** · {_slot['note']}")
        _names = ["（默认）"] + [DECOR_BY_ID[i]["name"] for i in _owned]
        _idx = 0
        if _cur in _owned:
            _idx = _names.index(DECOR_BY_ID[_cur]["name"])
        _pick = st.selectbox(f"已买的{_slot['name']}",
                             _names, index=_idx, key=f"decor_pick_{_sk}")
        if st.button(f"换上这个{_slot['name']}", key=f"decor_go_{_sk}",
                     width="stretch"):
            if _pick == "（默认）":
                decor_apply(gs, _sk, "")
                flash(f"{_slot['name']}已换回默认")
                fx("decor", f"换回默认{_slot['name']}")
            else:
                _id = next(i for i in _owned if DECOR_BY_ID[i]["name"] == _pick)
                ok, msg = decor_apply(gs, _sk, _id)
                if ok:
                    flash(msg)
                    fx("decor", msg)
                    add_log(msg, gs["game_log"])
                else:
                    st.warning(msg)
            save_game(gs)
            st.rerun()
        _left = [it for it in DECOR_ITEMS[_sk]
                 if it["id"] not in gs.get("decor_owned", [])]
        if _left:
            st.caption("还没买的：")
            for _it in _left:
                _d1, _d2 = st.columns([3, 1])
                with _d1:
                    st.caption(f"· {_it['name']}（{_it['price']} 积分）：{_it['desc']}")
                with _d2:
                    if st.button("购买", key=f"decor_buy_{_it['id']}",
                                 width="stretch"):
                        ok, msg = decor_buy(gs, _it["id"])
                        if ok:
                            flash(msg)
                            fx("decor", msg)
                            add_log(msg, gs["game_log"])
                            save_game(gs)
                            st.rerun()
                        else:
                            st.warning(msg)

if _TAB == "dex":
    section("trophy", "图鉴")
    dex_set = set(gs.get("dex", []))
    got_n = len([k for k in DEX_ALL_KEYS if k in dex_set])
    st.caption(
        f"已点亮 {got_n}/{DEX_TOTAL} 格 · 点亮即 +5 积分，成组另有奖励 · "
        "只要曾经拥有就会记录，不需要一直留着宠物"
    )
    st.progress(min(1.0, got_n / DEX_TOTAL))
    _only_unlit = st.toggle("只看未点亮（找漏的那格）", value=False, key="dex_only_unlit")
    for cat in PET_CATEGORIES:
        cat_pets = [sp for sp in cat["pets"] if sp in PET_SPECIES]
        cat_lit = len([1 for sp in cat_pets for k in ("normal", "star")
                       if f"{sp}|{k}" in dex_set])
        render(
            f'<div class="dex-cat dex-{cat["key"]}">'
            f'<span class="dex-cat-name">{cat["name"]}</span>'
            f'<span class="dex-cat-desc">{cat["desc"]} · {len(cat_pets)} 种 · '
            f'点亮 {cat_lit}/{len(cat_pets) * 2}</span></div>'
        )
        st.progress(min(1.0, cat_lit / max(1, len(cat_pets) * 2)))
        if _only_unlit:
            cat_pets = [sp for sp in cat_pets
                        if f"{sp}|normal" not in dex_set and f"{sp}|star" not in dex_set]
        for row_start in range(0, len(cat_pets), 6):
            cols = st.columns(6)
            for c, sp in zip(cols, cat_pets[row_start:row_start + 6]):
                with c:
                    for skin in ("normal", "star"):
                        key = f"{sp}|{skin}"
                        if key in dex_set:
                            st.image(pet_svg(sp, "happy", skin == "star"), width=64)
                        else:
                            st.markdown('<div class="dex-lock">?</div>', unsafe_allow_html=True)
                        st.caption(f"{sp}·{'星辉' if skin == 'star' else '普通'}")
                    if f"{sp}|shiny" in dex_set:
                        st.image(pet_svg(sp, "happy", False, "", True), width=48)
                        st.caption(f"{sp}·异色")
    st.caption(f"限定区（四季 {len(DEX_SEASON_ITEMS)} 件 + 节日 "
               f"{len(DEX_FESTIVAL_ITEMS)} 件，共 {len(DEX_LIMITED_ITEMS)} 件，"
               "买过或拿到过即点亮）")
    for _row in range(0, len(DEX_LIMITED_ITEMS), 4):
        scols = st.columns(4)
        for c, it in zip(scols, DEX_LIMITED_ITEMS[_row:_row + 4]):
            with c:
                key = f"item|{it}"
                if key in dex_set:
                    st.markdown(
                        f'<div class="dex-item on">'
                        f'{icon(_ITEM_ICON.get(it, "box"), 26, "#9A6A1E")}'
                        f'<span>{it}</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="dex-lock">?</div>',
                                unsafe_allow_html=True)
                st.caption(it if key in dex_set else "未点亮"
                           + ("（节日限定）" if it in DEX_FESTIVAL_ITEMS else ""))
    st.divider()
    section("info", "还差哪些物种")
    _missing = [sp for sp in PET_SPECIES
                if f"{sp}|normal" not in dex_set and f"{sp}|star" not in dex_set]
    if _missing:
        st.caption(f"还有 {len(_missing)} 个物种一次都没点亮："
                   + "、".join(_missing[:12]) + ("…" if len(_missing) > 12 else ""))
        _pick_miss = st.selectbox("挑一只去领养（80 积分）", _missing,
                                  key="dex_missing_pick")
        if st.button(f"把「{_pick_miss}」设为领养选择", width="stretch"):
            st.session_state["adopt_species"] = _pick_miss
            flash(f"已选好，去「宠物管理」页点「领养」即可")
            st.rerun()
    else:
        st.caption("所有物种都点亮了，可以专心收集星辉和异色了。")

    st.divider()
    section("heart", "物种小传")
    st.caption("图鉴点亮的物种都能读前半段；亲密度到「亲近」以后解锁最后一段。")
    _bio_sp = st.selectbox("选择物种", PET_SPECIES, key="dex_bio_pick",
                           format_func=lambda sp: f"{PET_CATEGORY_OF.get(sp, '')} · {sp}")
    _bio = BIO.get(_bio_sp, {})
    _lit_any = any(f"{_bio_sp}|{k}" in dex_set for k in ("normal", "star", "shiny"))
    _max_bond = max([float(p.get("bond", 0) or 0) for p in gs["pet_list"]
                     if species_of(p) == _bio_sp] or [0])
    if not _lit_any:
        st.caption(f"还没点亮「{_bio_sp}」，领养或觉醒后就能读它的小传。")
    else:
        st.markdown(f"**{_bio_sp}**　{_bio.get('quote', '')}")
        st.caption(_bio.get("intro", ""))
        if _max_bond >= 60:
            st.markdown(_bio.get("deep", ""))
        else:
            st.caption(f"（亲密度 {_max_bond:.0f}/60 后解锁最后一段）")

    st.divider()
    section("paw", "进化方向（三选一）")
    st.caption("三个方向与五种元素全部列在这里；未进化时点「进化」，进化之后仍可花积分更换。")
    cur_branch = current_pet.get("evo_branch") or ""
    cur_elem = current_pet.get("element") or ""
    for name in EVO_ORDER:
        info = EVO_BRANCHES[name]
        now_mark = "【当前】" if name == cur_branch else ""
        st.caption(
            f"{now_mark}{name}（{info['tag']}）：{info['desc']}"
            f"　优：{info['pro']}　代价：{info['con']}"
        )
    branch_default = EVO_ORDER.index(cur_branch) if cur_branch in EVO_ORDER else 0
    branch_pick = st.radio("选择进化方向", EVO_ORDER, index=branch_default,
                           horizontal=True, key="dex_branch")
    st.divider()
    section("element", "五行元素（五选一）")
    for k in ELEMENT_ORDER:
        info = ELEMENTS[k]
        now_mark = "【当前】" if k == cur_elem else ""
        st.caption(f"{now_mark}{k}·{info['tag']}：{info['pro']}　代价：{info['con']}")
    elem_default = ELEMENT_ORDER.index(cur_elem) if cur_elem in ELEMENT_ORDER else 0
    elem_pick = st.radio("选择五行元素", ELEMENT_ORDER, index=elem_default,
                         horizontal=True, key="dex_elem")
    evo_lv = int(current_pet.get("evo_lv", 0) or 0)
    have_c = gs["storehouse"].count(STAR_CRYSTAL)
    if not is_star:
        st.caption("当前宠物还未觉醒星辉，进化暂不开放（先升到 10 级并使用宠物强化剂）。")
    elif evo_lv == 0:
        gate, cc = EVO_LV_GATE[1], EVO_LV_COST[1]
        st.caption(f"进化到 1 阶：需要 Lv.{gate}、星尘结晶 ×{cc}（现有 {have_c}）")
        if st.button(f"进化 · {branch_pick} · {elem_pick}元素", type="primary", width="stretch"):
            if current_pet["lv"] < gate:
                st.warning(f"宠物等级不足，需要 Lv.{gate}")
            elif have_c < cc:
                st.warning(f"星尘结晶不足，还需要 {cc - have_c} 枚")
            else:
                for _ in range(cc):
                    gs["storehouse"].remove(STAR_CRYSTAL)
                current_pet["evo_branch"] = branch_pick
                current_pet["element"] = elem_pick
                current_pet["evo_lv"] = 1
                add_log(f"{current_pet['name']} 进化为【{branch_pick}·{elem_pick}】1 阶", gs["game_log"])
                flash(f"进化成功：【{current_pet['name']}】{branch_pick}·{elem_pick}元素 1 阶")
                save_game(gs)
                st.rerun()
    else:
        st.caption(f"当前：{cur_branch} · {cur_elem}元素 · {evo_lv}/{EVO_MAX_LV} 阶")
        if evo_lv < EVO_MAX_LV:
            nxt = evo_lv + 1
            gate, cc = EVO_LV_GATE[nxt], EVO_LV_COST[nxt]
            st.caption(f"升到 {nxt} 阶：需要 Lv.{gate}、星尘结晶 ×{cc}（现有 {have_c}）")
            if st.button(f"升阶 → {nxt} 阶", type="primary", width="stretch"):
                if current_pet["lv"] < gate:
                    st.warning(f"宠物等级不足，需要 Lv.{gate}")
                elif have_c < cc:
                    st.warning(f"星尘结晶不足，还需要 {cc - have_c} 枚")
                else:
                    for _ in range(cc):
                        gs["storehouse"].remove(STAR_CRYSTAL)
                    current_pet["evo_lv"] = nxt
                    add_log(f"{current_pet['name']} 进化阶数升至 {nxt}", gs["game_log"])
                    flash(f"进化阶数升至 {nxt}/{EVO_MAX_LV}")
                    save_game(gs)
                    st.rerun()
        else:
            st.success("已是 5 阶满阶；方向与元素仍可更换。")
        if branch_pick != cur_branch:
            if st.button(f"更换方向 → {branch_pick}（-{ELEM_RESET_COST} 积分）", width="stretch"):
                if gs["df"] < ELEM_RESET_COST:
                    st.warning("积分不足")
                else:
                    gs["df"] -= ELEM_RESET_COST
                    current_pet["evo_branch"] = branch_pick
                    add_log(f"{current_pet['name']} 方向更换 {cur_branch} → {branch_pick}", gs["game_log"])
                    flash(f"方向已更换为 {branch_pick}（阶数保持 {evo_lv}）")
                    save_game(gs)
                    st.rerun()
        if elem_pick != cur_elem:
            if st.button(f"更换元素 → {elem_pick}（-{ELEM_RESET_COST} 积分）", width="stretch"):
                if gs["df"] < ELEM_RESET_COST:
                    st.warning("积分不足")
                else:
                    gs["df"] -= ELEM_RESET_COST
                    current_pet["element"] = elem_pick
                    add_log(f"{current_pet['name']} 元素更换 {cur_elem} → {elem_pick}", gs["game_log"])
                    flash(f"元素已更换为 {elem_pick}")
                    save_game(gs)
                    st.rerun()

    ready = dex_ready_groups(gs)
    st.divider()
    if ready:
        names = "、".join(g["name"] for g in ready)
        total_r = sum(g["reward"] for g in ready)
        st.caption(f"可领取：{names}")
        if st.button(f"领取图鉴组奖励（+{total_r} 积分）", type="primary", width="stretch"):
            for g in ready:
                dex_claim(gs, g["gid"], out_msgs)
            flash(f"图鉴奖励已发放 {len(ready)} 组，积分 +{total_r}")
            st.rerun()
    else:
        st.caption(
            f"组奖励：{len(PET_SPECIES)} 组双皮肤各 +30 · 集齐全物种双皮肤 +100 · "
            "集齐四季限定 +80 · 集齐节日限定 +90 · 满册 +200"
        )
    _shiny_n = len([sp for sp in PET_SPECIES if f"{sp}|shiny" in dex_set])
    st.caption(f"异色图鉴：{_shiny_n}/{len(PET_SPECIES)} 只（探索时有 {SHINY_RATE * 100:.0f}% "
               "概率撞上异色花粉，宠物会永久变成异色形态，立绘配色整体移位）")
    st.caption("图鉴点亮来源：领养（普通）、星辉觉醒（星辉）、异色花粉（异色）、"
               "购买或获得限定商品（四季 + 节日）。")
    st.divider()
    section("element", "进化方向 & 五行元素 · 详细数值")
    with st.expander("展开查看全部方向、元素与各阶门槛", expanded=False):
        for name in EVO_ORDER:
            info = EVO_BRANCHES[name]
            st.markdown(f"**{info['name']}（{info['tag']}）**  {info['desc']}")
            st.caption(f"　主增益：{info['pro']}　｜　代价：{info['con']}")
            st.caption("　" + "　".join(
                f"{lv} 阶：需 Lv.{EVO_LV_GATE[lv]} + 结晶 {EVO_LV_COST[lv]}"
                for lv in range(1, EVO_MAX_LV + 1)))
        st.divider()
        for k in ELEMENT_ORDER:
            el = ELEMENTS[k]
            st.markdown(f"**{el['name']}（{el['tag']}）**")
            st.caption(f"　优点：{el['pro']}　｜　代价：{el['con']}")
    st.divider()
    section("paw", "我的宠物进化状态")
    for p in gs["pet_list"]:
        nm = _short_name(p.get("name", "?"))
        if p.get("is_star"):
            head = f"星辉 Lv.{int(p.get('star_lv', 1) or 1)}"
            if p.get("evo_branch"):
                body = (f"{p['evo_branch']} · {p.get('element') or '无'}元素 · "
                        f"{int(p.get('evo_lv', 0))}/{EVO_MAX_LV} 阶")
            else:
                body = "尚未进化（25 级 + 星尘结晶可进化）"
            st.markdown(f"**{nm}**（{species_of(p)}）：{head}　｜　{body}")
        else:
            st.caption(f"{nm}（{species_of(p)}）：普通形态，星辉觉醒后才能进化")
if _TAB == "pet":
    section("paw", "切换宠物")
    if st.button("全家喂食（每只各吃一份）", key="all_feed", width="stretch"):
        _n, _m = all_feed(gs)
        if _n:
            add_log(_m, gs["game_log"])
            save_game(gs)
            fx("feed", _m, big=True)
            flash(_m)
        else:
            flash("⚠️ 仓库里没有能喂的食物，先买点面包吧")
            fx("warn", "没有食物")
        st.rerun()
    st.caption(f"后院托管：其它宠物按 {INACTIVE_DECAY_MUL:.0%} 速率掉状态，健康不低于 10，不涨经验")
    pet_names = [
        f"{i}. {p['name']}{'（星辉）' if p.get('is_star', False) else ''}"
        for i, p in enumerate(gs["pet_list"])
    ]
    sel_idx = st.selectbox(
        "选择要切换的宠物（3 分钟冷却）",
        options=list(range(len(pet_names))),
        index=min(gs["current_pet_idx"], len(pet_names) - 1),
        format_func=lambda x: pet_names[x],
    )
    sel_pet = gs["pet_list"][sel_idx]
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image(pet_art(sel_pet), width=76)
    with col_b:
        st.markdown(f"**{sel_pet['name']}**")
        st.caption(
            f"{PET_LABEL.get(species_of(sel_pet), '')} · Lv.{sel_pet['lv']} · "
            f"开心 {sel_pet['hn']:.1f} · 饱腹 {sel_pet['ha']:.1f}"
        )
    if st.button("确认切换", type="primary"):
        now_b = datetime.now()
        if now_b - gs["last_switch_pet_time"] >= timedelta(minutes=3):
            gs["current_pet_idx"] = sel_idx
            gs["last_switch_pet_time"] = now_b
            add_log(f"切换宠物至 {gs['pet_list'][sel_idx]['name']}", gs["game_log"])
            flash(f"已切换到【{gs['pet_list'][sel_idx]['name']}】")
            st.rerun()
        else:
            st.warning("切换宠物冷却中")
    st.divider()
    section("paw", "领养新宠物")
    new_pet_sel = st.selectbox(
        "领养新宠物（80 积分）", PET_SPECIES, key="adopt_species",
        format_func=lambda sp: f"{PET_CATEGORY_OF.get(sp, '')} · {PET_LABEL.get(sp, sp)}",
    )
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image(pet_svg(new_pet_sel, "happy", False), width=76)
    with col_b:
        st.markdown(f"**{new_pet_sel}**")
        st.caption("等级 1 · 初始属性 100")
    st.caption(f"宠物栏位：{len(gs['pet_list'])}/{PET_MAX}")
    if st.button("领养", type="primary"):
        cost = ADOPT_COST
        if len(gs["pet_list"]) >= PET_MAX:
            st.warning(f"已经有 {PET_MAX} 只了，要先放生一只再领养新的")
        elif gs["df"] >= cost:
            gs["df"] -= cost
            np = {"name": new_pet_sel, "species": new_pet_sel, "lv": 1,
                  "hn": 100.0, "ha": 100.0, "cl": 100.0, "health": 150.0,
                  "exp": 0.0, "is_star": False,
                  "star_lv": 0, "evo_branch": "", "evo_lv": 0, "element": "",
                  "bond": 0.0, "shiny": False, "skill_cd": "",
                  "bond_day": date.today().isoformat()}
            np["persona"] = persona_for(np)
            gs["pet_list"].append(np)
            dex_add(gs, [f"{new_pet_sel}|normal"], out_msgs)
            add_log(f"领养新宠物 {new_pet_sel}", gs["game_log"])
            flash(f"领养新宠物：【{new_pet_sel}】，花费 80 积分")
            st.rerun()
        else:
            st.warning("积分不足 80！")
    st.divider()
    section("paw", "放生")
    st.caption(f"放生返还 {RELEASE_REFUND} 积分，图鉴记录会保留（点亮过的不会掉）。")
    _rel_names = [f"{i + 1}. {p['name']}（{species_of(p)} Lv.{p['lv']}）"
                  for i, p in enumerate(gs["pet_list"])]
    _rel_idx = st.selectbox("选择要放生的宠物", range(len(gs["pet_list"])),
                            format_func=lambda i: _rel_names[i])
    _rel_ok = st.checkbox("我确认要放生它（不可撤销）", key="release_confirm")
    if st.button("放生", disabled=not _rel_ok):
        if len(gs["pet_list"]) <= 1:
            st.warning("至少留一只宠物陪着你")
        else:
            _gone = gs["pet_list"].pop(_rel_idx)
            if gs["current_pet_idx"] >= len(gs["pet_list"]):
                gs["current_pet_idx"] = 0
            gs["df"] += RELEASE_REFUND
            add_log(f"放生 {_gone['name']}，+{RELEASE_REFUND} 积分", gs["game_log"])
            flash(f"{_gone['name']} 回到了野外（积分 +{RELEASE_REFUND}）")
            fx("release", f"放生 {_gone['name']}")
            set_stage("garden", 1)
            st.session_state.pop("release_confirm", None)
            st.rerun()
    st.divider()
    section("paw", "改名与存档")
    new_name = st.text_input("给当前宠物改名", value=current_pet["name"])
    st.caption(f"改名消耗 {RENAME_COST} 积分（改名后自动写入存档）")
    if st.button("确认改名", type="primary"):
        old = current_pet["name"]
        new_name_clean = strip_emoji(new_name).strip()
        if not new_name_clean:
            st.warning("名字不能为空")
        elif new_name_clean == old:
            st.info("名字没有变化，不扣积分")
        elif gs["df"] < RENAME_COST:
            st.warning(f"积分不足，改名需要 {RENAME_COST} 积分")
        else:
            new_name_clean = new_name_clean[:18]
            gs["df"] -= RENAME_COST
            current_pet["name"] = new_name_clean
            current_pet.setdefault("persona", persona_for(current_pet))
            add_log(f"改名 {old} -> {new_name_clean}（-{RENAME_COST} 积分）", gs["game_log"])
            save_game(gs)
            flash(f"改名成功：{old} -> {new_name_clean}（积分 -{RENAME_COST}）")
            st.rerun()
    if st.button("手动存档"):
        ok, msg = save_game(gs)
        st.success(msg if ok else msg)
    st.caption(f"存档位置：{SAVE_PATH}")
if _TAB == "svc":
    section("chart", "数据面板")
    _dex_set = set(gs.get("dex", []))
    _got_dex = len(_dex_set)
    _lot_n = int(gs.get("total_lottery", 0))
    _lot_w = int(gs.get("total_lottery_win", 0))
    _rate = (_lot_w / _lot_n * 100) if _lot_n else 0.0
    _shiny_owned = len([sp for sp in PET_SPECIES if f"{sp}|shiny" in _dex_set])

    def _bar(label, value, total, text, color):
        pct = 0.0 if total <= 0 else min(100.0, value / total * 100.0)
        return (
            '<div style="margin:10px 0">'
            '<div style="display:flex;justify-content:space-between;font-size:13px;'
            'color:#7A5B33"><span>' + _html.escape(label) + '</span><b>' + text + '</b></div>'
            '<div style="height:9px;border-radius:6px;background:#F2E6D0;overflow:hidden;'
            'margin-top:5px"><i style="display:block;height:100%;width:'
            f'{pct:.1f}%;background:{color};border-radius:6px"></i></div></div>'
        )

    render(
        _bar("累计投喂", gs["total_feed"], max(20, gs["total_feed"]),
             f"{gs['total_feed']} 次", "#C9702C")
        + _bar("累计探索", gs["total_explore"], max(20, gs["total_explore"]),
               f"{gs['total_explore']} 次", "#3E86B5")
        + _bar("完成每日任务", gs["total_task"], max(20, gs["total_task"]),
               f"{gs['total_task']} 条", "#7E8F3F")
        + _bar("彩票胜率", _rate, 100, f"{_rate:.0f}%（{_lot_w}/{_lot_n} 张）", "#B7791F")
        + _bar("图鉴完成度", _got_dex, DEX_TOTAL, f"{_got_dex}/{DEX_TOTAL} 格", "#8A6AC0")
        + _bar("异色收藏", _shiny_owned, len(PET_SPECIES),
               f"{_shiny_owned}/{len(PET_SPECIES)} 只", "#4AA3C0")
    )
    st.caption(f"星辉宠物 {star_pet_count} 只 · 宠物栏位 {len(gs['pet_list'])}/{PET_MAX} · "
               f"当前称号「{current_title(gs)}」")
    _days = play_days(gs)
    _avg_feed = (float(gs["total_feed"]) / _days) if _days else 0.0
    _est = "（首次日按存档创建时间估算）" if gs.get("start_date_est") else ""
    _avg_txt = f"{_avg_feed:.1f} 次" if _days >= 2 else "—（第一天，明天起有数）"
    st.caption(f"游玩第 {_days} 天（首次 {gs.get('start_date')}）{_est} · "
               f"日均投喂 {_avg_txt} · "
               f"最长连续签到 {int(gs.get('sign_best', 1) or 1)} 天")
    st.caption(f"累计抚摸 {int(gs.get('total_pet_touch', 0))} 次 · "
               f"累计变卖 {int(gs.get('total_sell', 0))} 件 · "
               f"今日互动 {int(gs.get('pet_touch_count', 0))}/{TOUCH_DAILY} 次")

    st.divider()
    section("box", "存档中心")
    st.caption(f"存档就是纯文本，可以直接打开手改：{SAVE_PATH}")
    _save_bytes = export_text(gs).encode("utf-8")
    st.download_button(
        "导出存档（.txt）", data=_save_bytes,
        file_name=f"player_pet_{datetime.now():%Y%m%d-%H%M}.txt",
        mime="text/plain", width="stretch", key="export_save",
    )
    _up = st.file_uploader("导入存档（会覆盖当前进度）", type=["txt", "json"],
                          key="save_upload")
    if _up is not None:
        _imp_ok = st.checkbox("确认用这份文件覆盖当前进度", key="import_confirm")
        if st.button("导入", disabled=not _imp_ok, key="import_btn"):
            try:
                _raw = _up.getvalue().decode("utf-8", "ignore")
            except Exception:
                _raw = ""
            _ok, _msg = import_save(_raw)
            if _ok:
                st.session_state.pop("game_state", None)
                flash(_msg)
                st.rerun()
            else:
                st.warning(_msg)
    _col_a, _col_b = st.columns(2)
    with _col_a:
        if st.button("立即备份一份", width="stretch", key="backup_now"):
            _bak = snapshot_backup()
            flash("已备份" if _bak else "备份失败（可能还没有存档）")
            st.rerun()
    with _col_b:
        st.caption(f"自动备份保留最近 {BACKUP_KEEP} 份")
    _baks = list_backups()
    if _baks:
        st.caption("最近备份：")
        for _b in _baks:
            st.caption(f"· {os.path.basename(_b)}")
    else:
        st.caption("还没有备份，点上面的按钮或手动存档时会自动留一份。")
    st.divider()
    st.divider()
    section("chart", "总进度看板")
    _ach_n = len(achievement_list)
    _ach_do = len(gs.get("unlock_ach") or [])
    _dex_n = len(gs["dex"])
    st.caption(f"成就 {_ach_do}/{_ach_n}　图鉴 {_dex_n}/{DEX_TOTAL}　"
               f"称号 {len(gs.get('titles') or [])}/{len(TITLES)}")
    _left = [a for a in achievement_list
             if a.get("aid") not in set(gs.get("unlock_ach") or [])][:3]
    if _left:
        render('<div class="pixel-card"><b>还差一点的成就</b><br>' +
               "<br>".join(f'· {a["title"]}（{a["desc"]}）' for a in _left) +
               '</div>')
    else:
        st.caption("成就全收了，等下一批更新。")

    section("save", f"存档槽位（{SLOT_COUNT} 个）")
    st.caption("3 个槽位，可以各自命名、存入当前进度、确认后读取覆盖；切换前会自动备份当前存档。"
               "想给家人开一档 / 玩多周目，把当前进度存进空槽位再「重新开始」就行。")
    for _i in range(1, SLOT_COUNT + 1):
        _sm = slot_summary(_i)
        _nm = slot_meta().get(_i, SLOT_NAMES[_i - 1])
        _c1, _c2 = st.columns([3, 2])
        if _sm:
            try:
                st.markdown(
                    '<div class="slot-thumb">' + pet_svg(_sm["species"]) + '</div>',
                    unsafe_allow_html=True)
            except Exception:
                pass
        with _c1:
            if _sm:
                st.markdown(f"**{_nm}** · {_sm['pet']}（{_sm['species']}）Lv.{_sm['lv']}")
                st.caption(f"{_sm['df']} 积分 · 游玩 {_sm['days']} 天 · 存于 {_sm['mtime']}")
            else:
                st.markdown(f"**{_nm}** · 空槽位")
                st.caption("还没存过东西")
        with _c2:
            _new_name = st.text_input("名字", value=_nm, key=f"slot_name_{_i}",
                                      label_visibility="collapsed")
            if st.button("改名", key=f"slot_rename_{_i}", width="stretch"):
                _ok, _msg = slot_rename(_i, _new_name)
                flash(_msg)
                st.rerun()
            if st.button("存入当前进度", key=f"slot_put_{_i}", width="stretch"):
                _ok, _msg = slot_store(_i, gs)
                flash(_msg)
                st.rerun()
            if _sm:
                _cf = st.checkbox("确认覆盖当前进度", key=f"slot_cf_{_i}")
                if st.button("读取这个槽位", disabled=not _cf,
                             key=f"slot_get_{_i}", width="stretch"):
                    _ok, _msg = slot_restore(_i)
                    if _ok:
                        st.session_state.pop("game_state", None)
                        flash(_msg)
                        st.rerun()
                    else:
                        st.warning(_msg)
    st.divider()
    st.caption("重新开始会把当前存档改名留存（.reset-时间.bak），不会直接抹掉。")
    _reset_ok = st.checkbox("我确认重新开始（宠物、积分、图鉴都会清空）",
                            key="reset_confirm")
    if st.button("重新开始", disabled=not _reset_ok, key="reset_btn"):
        _dst = reset_save()
        st.session_state.pop("game_state", None)
        flash(f"已从头开始，旧存档留存为 {os.path.basename(_dst)}" if _dst else "已经从头开始")
        st.rerun()

    st.divider()
    section("star", "分享卡片")
    st.caption("把当前宠物渲染成一张 720×1000 的 PNG，可以直接发出去。")
    if st.button("生成分享卡片", type="primary", width="stretch", key="share_make"):
        try:
            from pet_share import share_card
            st.session_state["share_png"] = share_card(gs, current_pet)
        except Exception as _e:
            st.session_state.pop("share_png", None)
            st.warning(f"生成失败：{_e}")
    _png = st.session_state.get("share_png")
    if _png:
        st.image(_png, width="stretch")
        st.download_button(
            "下载分享卡片（.png）", data=_png,
            file_name=f"share_{current_pet['species']}_{datetime.now():%m%d-%H%M}.png",
            mime="image/png", width="stretch", key="share_dl",
        )
    st.divider()
    section("chart", "相册 · 里程碑")
    _gal = gs.get("gallery") or []
    st.caption(f"升级到 10 的倍数、异色觉醒、亲密度满档时会自动存一张卡，共 {len(_gal)} 张。")
    if not _gal:
        st.info("还没有里程碑卡片，先升到 10 级试试。")
    else:
        for _e in reversed(_gal[-6:]):
            _fp = os.path.join(GALLERY_DIR, _e.get("file", ""))
            st.caption(f"{_e.get('at','')} · {_e.get('badge','')} · {_e.get('note','')}")
            if os.path.exists(_fp):
                st.image(_fp, width="stretch")
                with open(_fp, "rb") as _fh:
                    st.download_button("下载这张卡", data=_fh.read(),
                                       file_name=os.path.basename(_fp), mime="image/png",
                                       key=f"gal_dl_{_e.get('file')}")
    if st.button("手动戳一张当前宠物里程碑卡", key="gal_make"):
        if record_milestone(gs, current_pet,
                            f"manual-{datetime.now():%Y%m%d%H%M%S}",
                            "此刻的它", "手动记录的当下"):
            flash("已存入相册")
            st.rerun()

    st.divider()
    section("chart", "月度小结卡")
    _ms = gs.get("last_month_stats")
    if gs.get("month_report") == "pending" and _ms:
        try:
            from pet_share import month_card
            os.makedirs(GALLERY_DIR, exist_ok=True)
            _mn = f"month-{datetime.now():%Y%m}.png"
            _mp = os.path.join(GALLERY_DIR, _mn)
            month_card(gs, {
                "month": _ms.get("month", ""),
                "rows": [("投喂次数", _ms.get("feed", 0)),
                         ("探索次数", _ms.get("explore", 0)),
                         ("彩票累计", _ms.get("lottery", 0)),
                         ("新点亮图鉴", _ms.get("dex", 0)),
                         ("最长连续签到", int(gs.get("sign_best", 1) or 1))],
                "line": "下个月也请多关照",
            }, out_path=_mp)
            gs["month_report"] = _mn
            gs.setdefault("gallery", []).append(
                {"key": f"month-{_ms.get('month')}", "badge": "月度小结",
                 "note": _mn, "file": _mn, "at": datetime.now().strftime("%m-%d %H:%M")})
            save_game(gs)
        except Exception as _e:
            st.caption(f"月报生成失败：{_e}")
    if gs.get("month_report") and gs["month_report"] != "pending":
        _mp2 = os.path.join(GALLERY_DIR, str(gs["month_report"]))
        if os.path.exists(_mp2):
            st.image(_mp2, width="stretch")
    else:
        st.caption("每月 1 日结算时自动生成，记在相册里。")

    st.divider()
    section("chart", "经济收支表")
    _hours = max(1, int(gs.get("total_explore", 0) or 0))
    _daily = [(f"每日 {len(DAILY_CHALLENGES[:3])} 条任务", 60),
              ("全勤签到", 30), ("限时挑战", 50), ("探索（每次约 12）", 12 * 3),
              ("彩票期望", 8), ("成就 / 图鉴", 10)]
    _spend = [("领养", ADOPT_COST), ("皮肤", SKIN_PRICE), ("改名", RENAME_COST),
              ("治疗", f"30~{HEAL_COST_MAX if 'HEAL_COST_MAX' in globals() else 150}"),
              ("装修", "40~70"), ("星辉升级", "星尘 + 积分")]
    _inc = "".join(f"<tr><td>{k}</td><td style='text-align:right'>+{v}</td></tr>"
                   for k, v in _daily)
    _out = "".join(f"<tr><td>{k}</td><td style='text-align:right'>-{v}</td></tr>"
                   for k, v in _spend)
    render(f"""<div class='pixel-card'><b>每日收入（估算）</b>
<table style='width:100%;font-size:13px;border-collapse:collapse'>{_inc}</table>
<b style='display:block;margin-top:12px'>主要支出</b>
<table style='width:100%;font-size:13px;border-collapse:collapse'>{_out}</table>
<p style='margin:10px 0 0;color:#7A5B33;font-size:13px'>
按每天玩 15 分钟、做满任务算，净收益约 <b>+140/天</b>；集齐 40 物种按领养 80 算需
<b>约 3200 积分 ≈ 23 天</b>。当前存档共探索 {gs.get('total_explore', 0)} 次，
累计投喂 {gs.get('total_feed', 0)} 次。</p></div>""")

if _TAB == "log":
    section("log", "游戏日志")
    render(log_block(gs["game_log"]))
    st.divider()
    section("gear", "设置")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("切换随机事件开关"):
            gs["rand_event_switch"] = 1 - gs["rand_event_switch"]
            st.rerun()
    with col_b:
        if st.button("切换自动存档开关"):
            gs["auto_save_switch"] = 1 - gs["auto_save_switch"]
            st.rerun()
    st.checkbox("开启音效（投喂 / 升级 / 中奖 / 换季 / 节日 / 异色 / 成就，默认关闭）",
                value=False, key="sfx_on")
    _sd = st.date_input("首次游玩日（用于统计游玩天数 / 日均投喂）",
                        value=gs.get("start_date") or date.today(),
                        key="start_date_pick")
    if _sd != (gs.get("start_date") or date.today()):
        gs["start_date"] = _sd
        gs.pop("start_date_est", None)
        flash(f"首次游玩日已改为 {_sd}")
        st.rerun()
    st.checkbox("页面停留时每分钟自动结算一次", value=True, key="auto_tick",
                help="关闭后属性只在你点击/刷新时结算")
    st.divider()
    st.markdown("**存档导出 / 导入**")
    st.caption("云端存档在重启、休眠后会回到初始状态，重要进度请导出保存。")
    st.download_button(
        "导出存档（.txt）", data=export_text(gs).encode("utf-8"),
        file_name=f"player_pet_{datetime.now():%Y%m%d-%H%M}.txt",
        mime="text/plain", width="stretch", key="export_save_log",
    )
    _up_log = st.file_uploader("导入存档（会覆盖当前进度）", type=["txt", "json"],
                               key="save_upload_log")
    if _up_log is not None:
        _imp_log = st.checkbox("确认用这份文件覆盖当前进度", key="import_confirm_log")
        if st.button("导入", disabled=not _imp_log, key="import_btn_log"):
            try:
                _raw_log = _up_log.getvalue().decode("utf-8", "ignore")
            except Exception:
                _raw_log = ""
            _ok_log, _msg_log = import_save(_raw_log)
            if _ok_log:
                st.session_state.pop("game_state", None)
                flash(_msg_log)
                st.rerun()
            else:
                st.warning(_msg_log)
    st.divider()
    st.checkbox("显示调参面板（自己找平衡用，定稿后关掉）", value=False, key="tune_on")
    if st.session_state.get("tune_on"):
        TUNE["play_cd_h"] = st.slider("玩耍冷却（小时）", 0.0, 12.0,
                                      float(TUNE["play_cd_h"]), 0.5)
        TUNE["bath_cd_h"] = st.slider("洗澡冷却（小时）", 0.0, 12.0,
                                       float(TUNE["bath_cd_h"]), 0.5)
        TUNE["explore_cd_min"] = st.slider("探索冷却（分钟）", 0.0, 180.0,
                                           float(TUNE["explore_cd_min"]), 5.0)
        TUNE["decay_mul"] = st.slider("属性衰减倍率", 0.0, 3.0,
                                      float(TUNE["decay_mul"]), 0.05)
        TUNE["rare_cap"] = st.slider("探索稀有率上限", 0.10, 1.00,
                                     float(TUNE["rare_cap"]), 0.05)
        TUNE["big_p"] = st.slider("彩票大奖概率 %", 0, 50, int(TUNE["big_p"]))
        TUNE["mid_p"] = st.slider("彩票高级奖概率 %", 0, 80, int(TUNE["mid_p"]))
        if st.button("恢复默认数值"):
            TUNE.update(TUNE_DEFAULTS)
            st.rerun()
    next_evt = gs.get("last_rand_event_time", datetime.now()) + RAND_EVENT_INTERVAL
    if gs["rand_event_switch"] == 1:
        left = (next_evt - datetime.now()).total_seconds()
        if left > 0:
            st.caption(f"随机事件每 {int(RAND_EVENT_INTERVAL.total_seconds() // 3600)} 小时最多触发一次"
                       f"，下一次约 {fmt_wait(left)} 后")
        else:
            st.caption(f"随机事件每 {int(RAND_EVENT_INTERVAL.total_seconds() // 3600)} 小时最多触发一次"
                       "，下一次触发已就绪（刷新页面即可能触发）")
    else:
        st.caption("随机事件当前已关闭，历史触发节奏不受影响")
    st.divider()
    section("star", "季节")
    sd_tab = season_of()
    st.markdown(f"**{sd_tab['name']}**（第 {sd_tab['day_in_season']}/{SEASON_DAYS} 天）· {sd_tab['note']}")
    st.caption(
        f"衰减系数：饱腹 ×{sd_tab['ha']}、清洁 ×{sd_tab['cl']}、开心 ×{sd_tab['hn']}　|　"
        f"本季限定商品：{sd_tab['shop']}　|　剩 {sd_tab['left_days']} 天后进入{sd_tab['next']}季"
    )
    st.divider()
    section("bell", "今日事件")
    todays = gs.get("today_event_log", [])
    if todays:
        for e in reversed(todays):
            st.caption(f"· {e}")
    else:
        st.caption("今天还没有触发随机事件（每 2 小时最多一次）。")
if _TAB == "help":
    section("info", "帮助 · 规则说明")
    st.caption("这里所有数字都从常量与数据表自动生成（季节天数、冷却、稀有率、物种特性），改数值后自动同步。")
    render(_help_markdown())

if _TAB == "ach":
    section("trophy", "成就")
    render(achievements_block(gs))
    st.divider()
    section("paw", "全部宠物一览")
    for idx, p in enumerate(gs["pet_list"]):
        c_img, c_txt = st.columns([1, 5])
        with c_img:
            st.image(pet_art(p), width=72)
        with c_txt:
            star_mark = ""
            if p.get("is_star", False):
                star_mark = f" · 星辉 Lv.{int(p.get('star_lv', 1) or 1)}"
                if p.get("evo_branch"):
                    star_mark += f" · {p['evo_branch']}·{p.get('element') or '无'} {int(p.get('evo_lv', 0))}/5"
            st.markdown(
                f"**{p['name']}**（{species_of(p)}） · Lv.{p['lv']}{star_mark}"
            )
            st.caption(
                f"开心 {p['hn']:.1f} · 饱腹 {p['ha']:.1f} · "
                f"清洁 {p['cl']:.1f} · 健康 {p['health']:.1f}"
            )
st.divider()
st.caption("提示：关闭终端窗口会停止游戏，仅关闭网页标签程序仍在后台运行；存档文件 player_pet.txt 保存在程序同级目录")
