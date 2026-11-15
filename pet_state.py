# -*- coding: utf-8 -*-
"""pet_state（从单文件 pet_web.py 拆出，逻辑未改）。"""
import re
from datetime import date, datetime, timedelta
import ast
import json
import os
import random
import hashlib
from pet_constants import *
from pet_progress import *
from pet_svg import (_r, _mx, _blob, _outline, _eyes, _mouth, _cheeks, _mood_prop, _star_deco, _legs, _PET_BODY, _PET_SKIN, _STAR_SKIN, _PET_BG, _pet_group, _frame, _theme_pal, _to_hue)
from pet_progress import (_ICON_BODY, _ITEM_ICON)


# ===================== 存档工具 =====================


def _save_candidates():
    # 测试/多账号时可用 PET_SAVE_PATH 指定独立存档，避免跑到玩家真实存档
    override = os.environ.get("PET_SAVE_PATH")
    if override:
        return [override]
    from pet_env import DATA_HOME
    home = os.path.expanduser("~")
    return [
        os.path.join(DATA_HOME, "player_pet.txt"),
        os.path.join(home, "Documents", "宠物游戏", "player_pet.txt"),
        os.path.join(home, "player_pet.txt"),
    ]


def _can_write(path):
    folder = os.path.dirname(path) or "."
    try:
        os.makedirs(folder, exist_ok=True)
        probe = os.path.join(folder, ".save_write_probe.tmp")
        with open(probe, "w", encoding="utf-8") as fp:
            fp.write("ok")
        os.remove(probe)
    except OSError:
        return False
    if os.path.exists(path):
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except OSError:
            return False
    return True


def _pick_save_path():
    for p in _save_candidates():
        if _can_write(p):
            return p
    return _save_candidates()[0]


def _next_writable(current):
    for p in _save_candidates():
        if os.path.abspath(p) != os.path.abspath(current) and _can_write(p):
            return p
    return None


SAVE_PATH = _pick_save_path()


# ===================== 游戏逻辑工具 =====================


def check_levelup(pet, game_log):
    need_exp = pet["lv"] * 50
    msgs = []
    while pet["exp"] >= need_exp:
        pet["exp"] -= need_exp
        pet["lv"] += 1
        pet["hn"] += 20
        pet["ha"] += 20
        pet["hn"] = max(0.0, min(pet["hn"], 150.0))
        pet["ha"] = max(0.0, min(pet["ha"], 150.0))
        msgs.append(f"升级啦！【{pet['name']}】升到 Lv.{pet['lv']}！开心 +20，饱腹 +20")
        add_log(f"{pet['name']}升级到Lv.{pet['lv']}", game_log)
        need_exp = pet["lv"] * 50
    return msgs


def fix_petlist_is_star(pet_list):
    for p in pet_list:
        normalize_pet(p)
    return pet_list


def _serialize_star_cd(cd):
    """星辉技能冷却：datetime 一律存 ISO 字符串，读档时再还原。"""
    return {k: (v if k == "goodluck_stack" else v.isoformat(timespec="seconds"))
            for k, v in cd.items()}


SAVE_VERSION = 4          # 3 = 纯文本格式（一行一条），2 是过渡期的 JSON，4 起带迁移链

# 版本 → 升到下一版的迁移函数。加字段时在这里补一条，读档时自动逐级往上走。
MIGRATIONS = {}


def _mig_3_to_4(data):
    """3 → 4：补齐装修/天气/节日字段，并把亲密度收敛到 0~100。"""
    data = dict(data)
    data.setdefault("decor", {})
    data.setdefault("decor_owned", [])
    data.setdefault("last_weather", "")
    data.setdefault("festival_day", "")
    data.setdefault("festival_fired", [])
    pets = data.get("pet_list")
    if isinstance(pets, list):
        fixed = []
        for p in pets:
            if isinstance(p, dict):
                p = dict(p)
                try:
                    b = float(p.get("bond", 0) or 0)
                except (TypeError, ValueError):
                    b = 0.0
                p["bond"] = max(0.0, min(float(BOND_MAX), b))
                p["shiny"] = bool(p.get("shiny", False))
            fixed.append(p)
        data["pet_list"] = fixed
    return data


MIGRATIONS[3] = _mig_3_to_4
LAST_LOAD_NOTE = ""

_TIME_FIELDS = ("last_play_time", "last_bath_time", "last_auto_hour_time",
                "last_rand_event_time", "last_switch_pet_time", "last_explore_time",
                "challenge_end")
_DATE_FIELDS = ("last_get_date", "task_day", "pet_touch_day", "festival_day",
                 "bond_decay_day", "challenge_day", "start_date")
_INT_FIELDS = ("df", "current_pet_idx", "task_feed_flag", "total_task", "total_feed",
               "big_win_flag", "first_pet_flag", "rand_event_switch", "auto_save_switch",
               "total_explore", "explore_rare_once_flag", "total_star_explore",
               "total_star_skill_use", "sign_streak", "total_lottery", "bad_streak",
               "total_lottery_win", "tutorial_step",
               "pet_touch_count", "total_pet_touch", "total_sell",
               "total_play", "total_bath", "total_craft", "total_sell_df",
               "total_heal", "challenge_done", "sign_best",
               "chapter", "chapter_claimed", "season_count", "other_pet_decay")
_LIST_FIELDS = ("storehouse", "pet_list", "task_finished", "unlock_ach", "today_event_log",
                "decor_owned", "festival_fired",
                "game_log", "lottery_history", "week_done", "dex", "dex_claimed",
                "task_pool", "month_done", "gallery", "weather_chain")


def _default_state():
    """所有字段的唯一真源：老档缺字段、坏字段都回落到这里。"""
    now = datetime.now()
    return {
        "df": 100, "storehouse": [], "pet_list": [], "current_pet_idx": 0,
        "last_get_date": date.today(), "task_day": date.today(),
        "last_play_time": now - timedelta(hours=2),
        "last_bath_time": now - timedelta(hours=2),
        "last_auto_hour_time": now,
        "last_rand_event_time": now - RAND_EVENT_INTERVAL,
        "last_switch_pet_time": now - timedelta(minutes=3),
        "last_explore_time": now - EXPLORE_BASE_COOLDOWN,
        "task_finished": [], "task_feed_flag": 0, "unlock_ach": [],
        "total_task": 0, "total_feed": 0, "big_win_flag": 0, "first_pet_flag": 1,
        "rand_event_switch": 1, "today_event_log": [], "game_log": [],
        "auto_save_switch": 1, "total_explore": 0, "explore_rare_once_flag": 0,
        "star_skill_cd": {
            "star_mu": now - timedelta(minutes=40),
            "star_heal": now - timedelta(minutes=60),
            "star_full": now - timedelta(minutes=50),
            "star_goodluck": now - timedelta(minutes=120),
            "goodluck_stack": 0,
        },
        "total_star_explore": 0, "total_star_skill_use": 0,
        "start_date": date.today(), "sign_best": 1,
        "other_pet_decay": 1, "gallery": [], "fest_quest": {},
        "chapter": 0, "chapter_claimed": 0, "season_count": 0,
        "last_seen_ts": 0.0, "sign_block_day": "",
        "weather_chain": [], "story_done": "", "month_report": "",
        "sign_streak": 1, "total_lottery": 0, "lottery_history": [],
        "total_lottery_win": 0,
        "week_key": "", "week_base": {}, "week_done": [], "bad_streak": 0,
        "month_key": "", "month_base": {}, "month_done": [],
        "task_pool": [], "tutorial_step": 3,
        "last_season": "", "dex": [], "dex_claimed": [],
        "pet_touch_day": date.today(), "pet_touch_count": 0,
        "bond_decay_day": date.today(),
        "total_play": 0, "total_bath": 0, "total_craft": 0,
        "total_sell_df": 0, "total_heal": 0,
        "challenge_day": date.today(), "challenge_key": "", "challenge_base": {},
        "challenge_end": now, "challenge_done": 0, "challenge_result": "",
        "total_pet_touch": 0, "total_sell": 0,
        # 装修：decor 是"槽位 → 家具 id"，decor_owned 是已买过的家具 id
        "decor": {}, "decor_owned": [],
        # 天气/节日：记录上次看到的天气，用于"换天气"提示与音效
        "last_weather": "", "festival_day": date.today(), "festival_fired": [],
    }


def _jsonable(state):
    out = {"version": SAVE_VERSION}
    for k, v in state.items():
        if k == "star_skill_cd":
            out[k] = _serialize_star_cd(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, date):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _dump_text(state):
    """纯文本存档：一行一条 `字段 = 值`，值用 repr 写出。

    读取端走 ast.literal_eval，既不执行任何代码，又能直接手改某一行。
    """
    lines = ["# 毛孩子的小屋 存档 · 纯文本，一行一条，可以直接手改",
             f"version = {SAVE_VERSION}"]
    for k, v in _jsonable(state).items():
        if k == "version":
            continue
        lines.append(f"{k} = {v!r}")
    return "\n".join(lines) + "\n"


BACKUP_KEEP = 3          # save_backups/ 里只留最近 3 份快照


def backup_dir():
    base = os.path.dirname(SAVE_PATH) or os.getcwd()
    return os.path.join(base, "save_backups")


def snapshot_backup():
    """把当前存档拷进 save_backups/，只保留最近 BACKUP_KEEP 份。返回备份路径或 None。"""
    if not os.path.exists(SAVE_PATH):
        return None
    d = backup_dir()
    try:
        os.makedirs(d, exist_ok=True)
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        dst = os.path.join(d, "player_pet_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(raw)
        names = sorted(n for n in os.listdir(d)
                       if n.startswith("player_pet_") and n.endswith(".txt"))
        for n in names[:-BACKUP_KEEP]:
            try:
                os.remove(os.path.join(d, n))
            except OSError:
                pass
        return dst
    except OSError:
        return None


def list_backups():
    d = backup_dir()
    if not os.path.isdir(d):
        return []
    return sorted((os.path.join(d, n) for n in os.listdir(d)
                   if n.startswith("player_pet_") and n.endswith(".txt")), reverse=True)


def export_text(state):
    """导出用：返回这段存档的纯文本内容（直接给 st.download_button 用）。"""
    return _dump_text(state)


def import_save(raw):
    """导入一段存档文本：解析不通过就拒绝，通过则先备份旧档再写回。"""
    data, _suffix, _note = _parse_save(raw)
    if data is None:
        return False, "这段内容不像存档（既读不到 df 也读不到 pet_list）"
    st = _coerce_state(data)
    if not st["pet_list"]:
        return False, "存档里一只宠物都没有，已拒绝导入"
    if st["current_pet_idx"] >= len(st["pet_list"]):
        st["current_pet_idx"] = 0
    bak = snapshot_backup()
    ok, msg = save_game(st)
    if not ok:
        return False, msg
    return True, "导入成功" + (f"，旧存档已备份到 {os.path.basename(bak)}" if bak else "")


def reset_save():
    """重新开始：把现有存档改名留存（不会被覆盖），返回留存路径。"""
    if not os.path.exists(SAVE_PATH):
        return None
    dst = SAVE_PATH + ".reset-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak"
    try:
        os.replace(SAVE_PATH, dst)
        return dst
    except OSError:
        return None


def save_game(state):
    global SAVE_PATH
    payload = _dump_text(state)
    for _try in range(3):
        tmp = SAVE_PATH + ".tmp"
        try:
            folder = os.path.dirname(SAVE_PATH)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, SAVE_PATH)      # 先写临时文件再原子替换，写一半断电也不会毁档
            return True, f"存档已保存到 {SAVE_PATH}"
        except OSError:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            SAVE_PATH = _next_writable(SAVE_PATH)
            if not SAVE_PATH:
                return False, "没有可写的存档位置，本次进度未保存！"
    return False, "保存失败"


def parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间：{s}")


def _to_dt(v, fallback):
    if isinstance(v, datetime):
        return v
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(float(v))
        except (OSError, ValueError, OverflowError):
            return fallback
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.strip())
        except ValueError:
            try:
                return parse_dt(v)
            except ValueError:
                return fallback
    return fallback


def _to_date(v, fallback):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return datetime.strptime(v.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return fallback
    return fallback


def _load_legacy_text(raw):
    """旧格式是 "key = python字面量"，用 literal_eval 解析，任何代码都不会被执行。"""
    data = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or " = " not in line:
            continue
        k, v = line.split(" = ", 1)
        try:
            data[k] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            data[k] = v          # 时间、字符串之类原样留成 str，后面再按字段类型转
    return data


def _coerce_state(data):
    """把 dict 里的字段逐个转成运行时类型，转换失败就用默认值，绝不让读档抛异常。"""
    st = _default_state()
    if "last_get_df_date" in data and "last_get_date" not in data:
        data = dict(data, last_get_date=data["last_get_df_date"])
    for k in _INT_FIELDS:
        if k in data:
            try:
                st[k] = int(float(data[k]))
            except (TypeError, ValueError):
                pass
    for k in _DATE_FIELDS:
        if k in data:
            st[k] = _to_date(data[k], st[k])
    for k in _TIME_FIELDS:
        if k in data:
            st[k] = _to_dt(data[k], st[k])
    for k in _LIST_FIELDS:
        if k in data and isinstance(data[k], (list, tuple)):
            st[k] = list(data[k])
    if isinstance(data.get("week_base"), dict):
        st["week_base"] = dict(data["week_base"])
    if isinstance(data.get("month_base"), dict):
        st["month_base"] = dict(data["month_base"])
    if isinstance(data.get("challenge_base"), dict):
        st["challenge_base"] = dict(data["challenge_base"])
    for _dk in ("fest_quest", "last_month_stats"):
        if isinstance(data.get(_dk), dict):
            st[_dk] = dict(data[_dk])
    try:
        st["last_seen_ts"] = float(data.get("last_seen_ts", 0) or 0)
    except (TypeError, ValueError):
        st["last_seen_ts"] = 0
    for k in ("week_key", "month_key", "last_season", "last_weather",
              "challenge_key", "challenge_result", "story_done",
              "month_report", "sign_block_day"):
        if isinstance(data.get(k), str):
            st[k] = data[k].strip()
    if isinstance(data.get("decor"), dict):
        st["decor"] = {str(k): str(v) for k, v in data["decor"].items()
                       if str(k) in ("wall", "rug", "art", "window")}
    cd = data.get("star_skill_cd")
    if isinstance(cd, dict):
        merged = dict(st["star_skill_cd"])
        for kk, vv in cd.items():
            if kk == "goodluck_stack":
                try:
                    merged[kk] = int(vv)
                except (TypeError, ValueError):
                    merged[kk] = 0
            else:
                merged[kk] = _to_dt(vv, merged.get(kk, datetime.now()))
        st["star_skill_cd"] = merged
    if st["pet_list"]:
        st["pet_list"] = fix_petlist_is_star(list(st["pet_list"]))
        for _p in st["pet_list"]:
            if not isinstance(_p, dict):
                continue
            try:
                _p["bond"] = max(0.0, min(float(BOND_MAX),
                                          float(_p.get("bond", 0) or 0)))
            except (TypeError, ValueError):
                _p["bond"] = 0.0
            _p["shiny"] = bool(_p.get("shiny", False))
            _p.setdefault("bond_day", date.today().isoformat())
    if not st.get("start_date"):
        # 老档没有起始日：退回存档文件的创建时间，并标记为估算
        try:
            st["start_date"] = datetime.fromtimestamp(
                os.path.getctime(SAVE_PATH)).date()
        except OSError:
            st["start_date"] = date.today()
        st["start_date_est"] = True
    return st


def _parse_save(raw):
    """把一段存档文本解析成 dict，返回 (data, 需要留的备份后缀, 迁移说明)。

    认不出来就 data=None；这里不碰文件，读档和“导入存档”共用同一套判定。
    """
    txt = _load_legacy_text(raw)
    if "df" in txt or "pet_list" in txt:
        if "version" in txt:
            return txt, "", ""
        return txt, ".legacy.bak", "旧文本存档已整理成标准格式"
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        obj = None
    if isinstance(obj, dict) and ("df" in obj or "pet_list" in obj):
        return obj, ".json.bak", "JSON 存档已迁回纯文本格式"
    # 也兼容“整个存档就是一个 dict 字面量”的老写法
    try:
        whole = ast.literal_eval(raw.strip())
    except (ValueError, SyntaxError):
        whole = None
    if isinstance(whole, dict) and ("df" in whole or "pet_list" in whole):
        return whole, ".legacy.bak", "旧文本存档已整理成标准格式"
    return None, "", ""


def load_game():
    """读存档：默认是纯文本；遇到 JSON / 老格式就备份后迁成文本；坏档改名保留，不覆盖。"""
    global LAST_LOAD_NOTE
    LAST_LOAD_NOTE = ""
    if not os.path.exists(SAVE_PATH):
        return None
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return None
    if not raw.strip():
        return None

    # 纯文本是现在的正式格式；认出是旧 JSON 就顺手迁回来，各留一份备份
    data, bak_suffix, src_note = _parse_save(raw)

    if data is None:
        bad = SAVE_PATH + ".corrupt-" + datetime.now().strftime("%Y%m%d%H%M%S")
        try:
            os.replace(SAVE_PATH, bad)
            LAST_LOAD_NOTE = f"存档无法识别，已另存为 {os.path.basename(bad)}，本次开了新档。"
        except OSError:
            LAST_LOAD_NOTE = "存档无法识别，未做任何覆盖。"
        return None

    ver = data.get("version")
    _migrated = False
    if not isinstance(ver, int):
        ver = 1                       # 没有版本号的老档，从 1 开始往上迁
    if ver > SAVE_VERSION:
        LAST_LOAD_NOTE = (f"存档来自更新版本（v{ver}，本程序是 v{SAVE_VERSION}），"
                          "已按当前规则读取，建议先备份存档。")
    else:
        trail = []
        while ver < SAVE_VERSION:
            fn = MIGRATIONS.get(ver)
            if fn is None:
                break
            data = fn(data)
            ver += 1
            trail.append(f"v{ver}")
        if trail:
            _migrated = True
            note = "存档已迁移：" + " → ".join(trail)
            LAST_LOAD_NOTE = (LAST_LOAD_NOTE + "；" if LAST_LOAD_NOTE else "") + note

    st = _coerce_state(data)
    if bak_suffix or _migrated:
        bak = SAVE_PATH + bak_suffix
        if bak_suffix:
            try:
                if not os.path.exists(bak):
                    with open(bak, "w", encoding="utf-8") as f:
                        f.write(raw)
            except OSError:
                pass
        ok, _msg = save_game(st)
        if bak_suffix:
            LAST_LOAD_NOTE = (src_note
                              + (f"，原文件备份为 {os.path.basename(bak)}。"
                                 if ok else "，但写回失败。"))
        elif not ok:
            LAST_LOAD_NOTE += "，但写回新版本失败。"
    return st


def save_signature(gs):
    """把“玩家做过什么”压成指纹：属性随时间自然衰减不算改动，动作算。

    用来决定这次 rerun 到底要不要立刻落盘——避免每点一下按钮就全量重写，
    又不至于把刚喂完/刚买完的进度拖到 30 秒后才写。
    """
    view = {}
    for k, v in gs.items():
        if k == "last_auto_hour_time":       # 每次 rerun 都会更新，天然“总是变化”
            continue
        view[k] = v
    view["pet_list"] = [
        {kk: vv for kk, vv in p.items() if kk not in ("ha", "hn", "cl", "health", "exp")}
        for p in gs.get("pet_list", [])
    ]
    return json.dumps(_jsonable(view), sort_keys=True, ensure_ascii=False, default=str)


def use_item(gs, pet, item, species, is_star, out_msgs=None):
    """投喂/使用一件道具。

    道具的价格、文案、效果全部来自 ITEMS 表，加新道具不用再改这一段。
    返回 (给玩家看的提示, 理论饱腹增量, 本次获得经验)。
    """
    if out_msgs is None:
        out_msgs = []
    inv = gs["storehouse"]
    if item in inv:
        inv.remove(item)
    cfg = ITEMS.get(item, {})
    fx = dict(cfg.get("eff", {}))
    special = cfg.get("special")
    msg = ""
    theory_ha = 0

    if special == "battery":
        if species == "机器人":
            theory_ha = 20 if is_star else 10
            pet["ha"] += theory_ha
            msg = f"机器人充电，饱腹值 +{theory_ha}"
        else:
            pet["ha"] -= 10
            msg = "非机器人吃电池，饱腹值 -10"
    elif special == "fish":
        theory_ha = 10
        pet["ha"] += 10
        if species == "猫":
            extra = 10 if is_star else 5
            pet["ha"] += extra
            theory_ha += extra
        msg = f"饱腹值 +{theory_ha}"
    elif special == "heal_to_50":
        pet["health"] = max(float(pet["health"]), 50.0)
        msg = "健康值已拉到 50"
    elif special == "lucky":
        inv.append(item)
        msg = "幸运徽章是被动道具，已放回仓库"
    elif special == "soap":
        inv.append(item)
        msg = "肥皂只能在洗澡时使用，已放回仓库"
    elif special == "cooldown_reset":
        _now_cd = datetime.now()
        gs["last_play_time"] = _now_cd - timedelta(hours=6)
        gs["last_bath_time"] = _now_cd - timedelta(hours=6)
        gs["last_explore_time"] = (_now_cd - EXPLORE_BASE_COOLDOWN
                                   - timedelta(minutes=1))
        msg = "冷却清零：玩耍 / 洗澡 / 探索立刻就能再用"
        add_log(f"{pet['name']} 用了时间秒表，冷却全部清零", gs["game_log"])
    elif special in ("catnip", "chew"):
        for k, v in fx.items():
            pet[k] = pet.get(k, 0) + v
        theory_ha = fx.get("ha", 0)
        _bonus = 0
        if special == "catnip" and species == "猫":
            _bonus = 20
            pet["hn"] = pet.get("hn", 0) + _bonus
            msg = "开心 +50，猫闻到猫薄荷额外 +20"
        elif special == "chew" and species == "狗":
            _bonus = 15
            pet["hn"] = pet.get("hn", 0) + _bonus
            msg = "开心 +35，狗啃磨牙棒额外 +15"
        else:
            msg = "开心 +35" if special == "chew" else "开心 +50"
    elif special == "wish_coin":
        _gain = random.randint(30, 120)
        gs["df"] = gs.get("df", 0) + _gain
        msg = f"许愿瓶摇出 {_gain} 积分"
        add_log(f"{pet['name']} 摇开星星许愿瓶，得到 {_gain} 积分", gs["game_log"])
    elif special == "star_potion":
        if pet["lv"] >= 10 and not pet.get("is_star"):
            pet["is_star"] = True
            pet["star_lv"] = 1
            msg = "星辉觉醒成功！星辉 Lv.1，去「图鉴 · 进化」页可以继续升阶"
            add_log(f"{pet['name']}进化星辉形态", gs["game_log"])
            dex_add(gs, [f"{species}|star"], out_msgs)
        else:
            inv.append(item)
            msg = "等级不足或已是星辉形态，强化剂已放回仓库"
    elif special == "snack_pack":
        gifts = random.choices(["零食", "葡萄", "面包", "鲜鱼"], k=2)
        inv.extend(gifts)
        msg = f"礼包打开，开出 {' + '.join(gifts)}，已放回仓库"
    elif special == "exp_fruit":
        msg = "经验 +35（不影响饱腹）"
    elif special == "material":
        inv.append(item)
        msg = "这是进化材料，请到「图鉴」页使用"
    elif special == "skin_ticket":
        if pet.get("skin") == "star":
            pet["skin"] = "normal"
            msg = "已切回普通皮肤"
        else:
            pet["skin"] = "star"
            msg = "已换上星辉皮肤（纯外观，数值不变）"
        add_log(f"{pet['name']} 换肤：{pet['skin']}", gs["game_log"])
    elif item.startswith("皮肤·"):
        inv.append(item)
        msg = "这是皮肤不是食物，请到商店下方「仓库」点穿戴"
    else:
        for k, v in fx.items():
            pet[k] = pet.get(k, 0) + v
        theory_ha = fx.get("ha", 0)
        labels = (("ha", "饱腹"), ("hn", "开心"), ("cl", "清洁"), ("health", "健康"))
        msg = cfg.get("use_msg") or "、".join(
            f"{label} +{fx[k]}" for k, label in labels if k in fx
        ) or "没有效果"

    if special == "exp_fruit":
        add_exp = 35.0
    elif "exp" in cfg:
        add_exp = float(cfg["exp"])
    else:
        exp_mod = pet_bonus(pet)["exp"]
        if is_star and species == "小鸡":
            exp_mod *= 1.1
        add_exp = theory_ha / 2 * exp_mod
    pet["exp"] = pet.get("exp", 0) + add_exp

    _taste = taste_of(species)
    _is_love = bool(item) and item == _taste["love"]
    _is_hate = bool(item) and item == _taste["hate"]
    _gains = {k: fx.get(k, 0) for k in ("ha", "hn", "cl", "health")}
    if _is_love and any(_gains.values()):
        for k, v in _gains.items():
            if k in pet and v:
                pet[k] = float(pet[k]) + v        # 再补一份 = 双倍
        theory_ha *= 2
        bond_add(gs, pet, 3)
        msg += f"（{species}最爱{item}，效果翻倍，亲密度 +3）"
    elif _is_hate and any(_gains.values()):
        for k, v in _gains.items():
            if k in pet and v:
                pet[k] = float(pet[k]) - v * 0.5  # 退回一半
        theory_ha *= 0.5
        pet["hn"] = float(pet.get("hn", 0)) - 5
        bond_add(gs, pet, -1)
        msg += f"（{species}不喜欢{item}，效果减半、开心 -5）"

    for k in ("hn", "ha", "cl", "health"):
        if k in pet:
            pet[k] = max(0, min(float(pet[k]), 150))
    return msg, theory_ha, add_exp


def taste_of(species):
    """这个物种最爱 / 最嫌弃的道具名。"""
    return TASTE.get(species, {"love": "", "hate": ""})


INACTIVE_DECAY_MUL = 0.50     # 不在台前的宠物：衰减按这个比例（放着不动也慢慢掉）


def decay_bench(gs, now=None, season=None, weather=None):
    """给所有不在台前的宠物结算一轮衰减，直接写回 pet。

    台前那只是全额衰减，其余按 INACTIVE_DECAY_MUL 折算；健康不折，
    避免放着不管就病死。返回 (结算只数, 提示列表)。
    """
    now = now or datetime.now()
    season = season or season_of(now.date())
    weather = weather or weather_of(now.date())
    idx = int(gs.get("current_pet_idx", 0) or 0)
    done = 0
    msgs = []
    for i, pet in enumerate(gs["pet_list"]):
        if i == idx:
            continue
        stats, _m, raw = passive_decay(
            gs, pet, now=now, season=season, weather=weather,
            is_star=bool(pet.get("is_star", False)))
        for k in ("cl", "ha", "hn", "health", "exp"):
            if k not in stats:
                continue
            old = float(pet.get(k, 0) or 0)
            new = float(stats[k])
            if k == "health":
                pet[k] = max(10.0, new)   # 后院不会病死，最低停在 10
            elif k == "exp":
                continue                  # 后院不涨经验
            else:
                pet[k] = old + (new - old) * INACTIVE_DECAY_MUL
        done += 1
    if done:
        msgs.append(f"后台 {done} 只宠物也结算了衰减（{INACTIVE_DECAY_MUL:.0%} 速率）")
    return done, msgs


def passive_decay(gs, pet, now=None, season=None, weather=None, is_star=False):
    """按上次结算到现在的时间给四项属性/健康/经验做衰减。

    只算数值、不写 pet、不碰随机事件；返回 (stats, msgs, delta_raw)。
    stats 里的 hn/ha/cl/health/exp 是 float，调用方自己回写。
    """
    now = now or datetime.now()
    season = season or season_of(now.date())
    weather = weather or weather_of(now.date())
    OFFLINE_CAP_MIN = 480
    delta_raw = (now - gs["last_auto_hour_time"]).total_seconds() / 60
    delta_min = min(delta_raw, OFFLINE_CAP_MIN) * float(TUNE["decay_mul"])
    msgs = []
    if delta_raw > OFFLINE_CAP_MIN:
        msgs.append(f"离线约 {delta_raw / 60:.1f} 小时，超过 8 小时的部分不再结算，"
                    "属性不会被一次性清零")
    pet_cl = float(pet["cl"])
    pet_ha = float(pet["ha"])
    pet_hn = float(pet["hn"])
    health = float(pet["health"])
    exp = float(pet["exp"])
    bonus = pet_bonus(pet)
    mods = species_mods(species_of(pet), is_star)
    cur_mood = mood_tag(pet)
    mood_decay = cur_mood["decay"] * mods["mood"]
    pet_cl_decay = (0.03 * bonus["cl"] * mods["cl"] * season["cl"] * weather["cl"]
                    * mood_decay)
    pet_ha_mod = bonus["ha"] * season["ha"] * weather["ha"] * mood_decay * mods["ha"]
    pet_hn_mod = bonus["hn"] * season["hn"] * weather["hn"] * mood_decay * mods["hn"]
    pet_cl -= delta_min * pet_cl_decay
    pet_cl = max(0.0, min(pet_cl, 150.0))
    pet_ha -= delta_min * 0.5 * pet_ha_mod
    pet_ha = max(0.0, min(pet_ha, 150.0))
    pet_hn -= (delta_min * 0.1 * bonus["hn"] * season["hn"] * weather["hn"]
               * mood_decay * mods["mood_direct"])
    if pet_ha < 75:
        pet_hn -= delta_min * 0.5 * pet_hn_mod
    if pet_cl < 60:
        pet_hn -= delta_min * 0.3 * pet_hn_mod
    pet_hn = max(0.0, min(pet_hn, 150.0))
    if pet_hn < 50:
        exp_loss_base = delta_min * 0.2
        if is_star:
            exp_loss_base *= 0.7
        exp -= exp_loss_base
        exp = max(0.0, exp)
    health_loss = 0.0
    for val in (pet_ha, pet_cl, pet_hn):
        if val < 50:
            health_loss += 0.15
        elif val < 100:
            health_loss += 0.10
        elif val < 125:
            health_loss += 0.05
    health_loss *= bonus["guard"] * bonus["hloss"]
    heal_rate = 0.12 * bonus["heal"] * mods["heal"]
    if pet_ha >= 80 and pet_cl >= 80 and pet_hn >= 80:
        if is_star:
            heal_rate = 0.24
        health += delta_min * heal_rate
        health_loss = 0
    health -= health_loss * delta_min
    health = max(0.0, min(health, 150.0))
    if health < 30 and not (is_star and bonus["star_lv"] >= 4):
        exp -= delta_min * 0.8
    elif 30 <= health < 50:
        exp -= delta_min * 0.2
    exp = max(0.0, exp)
    name = pet.get("name", "它")
    if health < 30:
        if is_star and bonus["star_lv"] >= 4:
            msgs.append(f"提醒：【{name}】健康低于 30，星辉护体（4 级起生效），不再快速损失经验！")
        elif is_star:
            msgs.append(f"警告：【{name}】健康低于 30！星辉等级不足 4 级，护体尚未生效，快去治疗！")
        else:
            msgs.append(f"严重警告：【{name}】健康低于 30！快去治疗！")
    elif health < 50:
        msgs.append(f"提醒：【{name}】健康 30~50，正在缓慢损失经验！")
    gs["last_auto_hour_time"] = now
    stats = {"hn": pet_hn, "ha": pet_ha, "cl": pet_cl,
             "health": health, "exp": exp}
    return stats, msgs, delta_raw


def bond_tier(bond):
    """亲密度档位：返回 {"min","name","line","act"}。"""
    tier = BOND_TIERS[0]
    try:
        b = float(bond or 0)
    except (TypeError, ValueError):
        b = 0.0
    for t in BOND_TIERS:
        if b >= t["min"]:
            tier = t
    return tier


def bond_add(gs, pet, delta):
    """加减亲密度（自动夹在 0~100）。涨的时候顺手记下"最后一次互动日"。"""
    try:
        cur = float(pet.get("bond", 0) or 0)
    except (TypeError, ValueError):
        cur = 0.0
    pet["bond"] = max(0.0, min(float(BOND_MAX), cur + float(delta)))
    if float(delta) > 0:
        pet["bond_day"] = date.today().isoformat()
    return pet["bond"]


def bond_daily_decay(gs, today=None):
    """连续 2 天以上没互动，亲密度每天掉 1 点（间隔越长一次掉得越多，单次最多 3）。

    每天只结算一次（用 bond_decay_day 记），同一天刷多少次页面都不会重复扣。
    """
    today = today or date.today()
    if gs.get("bond_decay_day") == today:
        return []
    gs["bond_decay_day"] = today
    msgs = []
    for pet in gs.get("pet_list", []):
        if not isinstance(pet, dict):
            continue
        raw = str(pet.get("bond_day") or "")
        try:
            last = date.fromisoformat(raw)
        except ValueError:
            continue          # 没有记录的新档宠物不惩罚
        gap = (today - last).days
        if gap < 2:
            continue
        try:
            before = float(pet.get("bond", 0) or 0)
        except (TypeError, ValueError):
            before = 0.0
        loss = min(3.0, float(gap - 1))
        pet["bond"] = max(0.0, before - loss)
        if pet["bond"] < before:
            name = pet.get("name", "它")
            msgs.append(f"{name} 有 {gap} 天没互动，亲密度 -{loss:.0f}"
                        f"（{before:.0f} → {pet['bond']:.0f}）")
    return msgs


STAR_SKILL_KEYS = ("star_mu", "star_heal", "star_full", "star_goodluck")
STAR_SKILL_CD_MIN = {"star_mu": 40, "star_heal": 60,
                     "star_full": 50, "star_goodluck": 120}


def star_skill_cd_left(gs, key, now=None):
    """技能还剩多少秒冷却，0 表示可用。"""
    now = now or datetime.now()
    cd = (gs.get("star_skill_cd") or {}).get(key)
    if not isinstance(cd, datetime):
        return 0.0
    return max(0.0, (cd - now).total_seconds())


def star_skill_start(gs, key, now=None):
    """释放技能的记账部分：冷却中直接拒绝（不完成任务、不计数），可用才推进。

    返回 (是否放行, 剩余秒数)。
    """
    now = now or datetime.now()
    left = star_skill_cd_left(gs, key, now)
    if left > 0:
        return False, left
    from pet_progress import complete_task
    complete_task(gs, "star_skill")
    gs["total_star_skill_use"] = int(gs.get("total_star_skill_use", 0)) + 1
    gs.setdefault("star_skill_cd", {})[key] = now + timedelta(
        minutes=STAR_SKILL_CD_MIN.get(key, 60))
    return True, 0.0


def sell_price(item):
    """单件回收价：原价一半，最低 1 积分。"""
    cfg = ITEMS.get(item, {})
    return max(1, int(round(float(cfg.get("price", 10)) * SELL_RATE)))


def sell_items(gs, item, count=1):
    """从仓库卖出若干件，返回 (实得积分, 提示文本)。"""
    inv = gs["storehouse"]
    count = max(1, int(count))
    have = inv.count(item)
    if have <= 0:
        return 0, f"仓库里没有{item}"
    n = min(count, have)
    for _ in range(n):
        inv.remove(item)
    got = sell_price(item) * n
    gs["df"] = int(gs.get("df", 0)) + got
    gs["total_sell"] = int(gs.get("total_sell", 0)) + n
    gs["total_sell_df"] = int(gs.get("total_sell_df", 0)) + got
    add_log(f"变卖 {item}×{n}，回收 {got} 积分", gs["game_log"])
    return got, f"卖出 {item}×{n}，回收 {got} 积分（单价 {sell_price(item)}）"


def pet_touch(gs, pet, kind="head"):
    """摸摸头 / 逗猫棒：加开心 + 亲密度，日限 TOUCH_DAILY 次，不占玩耍冷却。

    kind="head" 记 1 次，kind="toy" 记 2 次（更费次数但更开心）。
    """
    today = date.today()
    if gs.get("pet_touch_day") != today:
        gs["pet_touch_day"] = today
        gs["pet_touch_count"] = 0
    used = int(gs.get("pet_touch_count", 0) or 0)
    cost = 2 if kind == "toy" else 1
    if used + cost > TOUCH_DAILY:
        return f"今天已经摸够了（{used}/{TOUCH_DAILY}），明天再来吧", False
    gs["pet_touch_count"] = used + cost
    gain = random.randint(3, 5) if kind == "toy" else random.randint(1, 3)
    pet["hn"] = max(0, min(150.0, float(pet.get("hn", 0)) + gain))
    bond_add(gs, pet, 2 if kind == "toy" else 1)
    gs["total_pet_touch"] = int(gs.get("total_pet_touch", 0)) + 1
    word = "拿逗猫棒逗它" if kind == "toy" else f"摸了摸{pet.get('name', '宠物')}的头"
    return f"{word}，开心 +{gain}（今日 {gs['pet_touch_count']}/{TOUCH_DAILY}）", True



# ===================== 装修（家具槽位） =====================
DECOR_SLOT_KEYS = ("wall", "rug", "art", "window")


def decor_slot(gs, slot):
    """当前这个槽位装的是哪件家具，返回家具 dict（没装就是 None）。"""
    item_id = (gs.get("decor") or {}).get(slot, "")
    return DECOR_BY_ID.get(item_id)


def decor_apply(gs, slot, item_id):
    """装上一件家具（已买过的才能装），返回 (ok, 文案)。"""
    if slot not in DECOR_SLOT_KEYS:
        return False, "没有这个槽位"
    if not item_id:
        gs.setdefault("decor", {}).pop(slot, None)
        return True, "已换回默认"
    if item_id not in gs.get("decor_owned", []):
        return False, "还没买过这件家具"
    if item_id not in DECOR_BY_ID or DECOR_BY_ID[item_id]["slot"] != slot:
        return False, "这件家具不属于这个槽位"
    gs.setdefault("decor", {})[slot] = item_id
    return True, f"已换上「{DECOR_BY_ID[item_id]['name']}」"


def decor_buy(gs, item_id):
    """买家具，返回 (ok, 文案)。"""
    item = DECOR_BY_ID.get(item_id)
    if not item:
        return False, "没有这件家具"
    if item_id in gs.get("decor_owned", []):
        return False, "已经买过了，直接在装修页装上就行"
    if gs["df"] < item["price"]:
        return False, "积分不足"
    gs["df"] -= item["price"]
    gs.setdefault("decor_owned", []).append(item_id)
    return True, f"买到「{item['name']}」，去装修页装上"


def decor_pal(gs):
    """把当前装修整理成 room_svg 需要的调色覆盖表。"""
    out = {}
    for slot in DECOR_SLOT_KEYS:
        item = decor_slot(gs, slot)
        if item:
            out[slot] = item["pal"]
    return out

def new_game(pet_name):
    today = date.today()
    state = {}
    state["pet_list"] = [{
        "name": pet_name, "species": pet_name, "lv": 1, "hn": 100.0, "ha": 100.0,
        "cl": 100.0, "health": 150.0, "exp": 0.0, "is_star": False,
        "bond": 0.0, "shiny": False,
        "bond_day": today.isoformat(),
    }]
    state["pet_list"][0]["persona"] = persona_for(state["pet_list"][0])
    state["pet_list"][0]["skill_cd"] = ""
    state["chapter"] = 0
    state["chapter_claimed"] = 0
    state["season_count"] = 0
    state["last_seen_ts"] = 0.0
    state["sign_block_day"] = ""
    state["current_pet_idx"] = 0
    state["df"] = 100
    state["storehouse"] = []
    state["last_get_date"] = today
    state["last_bath_time"] = datetime.now() - timedelta(hours=2)
    state["last_auto_hour_time"] = datetime.now()
    state["last_play_time"] = datetime.now() - timedelta(hours=2)
    state["last_switch_pet_time"] = datetime.now() - timedelta(minutes=3)
    state["last_explore_time"] = datetime.now() - EXPLORE_BASE_COOLDOWN
    state["total_explore"] = 0
    state["explore_rare_once_flag"] = 0
    state["star_skill_cd"] = {
        "star_mu": datetime.now() - timedelta(minutes=40),
        "star_heal": datetime.now() - timedelta(minutes=60),
        "star_full": datetime.now() - timedelta(minutes=50),
        "star_goodluck": datetime.now() - timedelta(minutes=120),
        "goodluck_stack": 0
    }
    state["total_star_explore"] = 0
    state["total_star_skill_use"] = 0
    state["task_finished"] = []
    state["task_day"] = today
    state["task_feed_flag"] = 0
    state["unlock_ach"] = []
    state["total_task"] = 0
    state["total_feed"] = 0
    state["big_win_flag"] = 0
    state["first_pet_flag"] = 1
    state["rand_event_switch"] = 1
    state["last_rand_event_time"] = datetime.now() - RAND_EVENT_INTERVAL
    state["today_event_log"] = []
    state["game_log"] = []
    state["auto_save_switch"] = 1
    state["sign_streak"] = 1
    state["total_lottery"] = 0
    state["lottery_history"] = []
    state["week_key"] = ""
    state["week_base"] = {}
    state["week_done"] = []
    state["bad_streak"] = 0
    state["last_season"] = ""
    state["decor"] = {}
    state["decor_owned"] = []
    state["last_weather"] = ""
    state["festival_day"] = date.today()
    state["festival_fired"] = []
    state["dex"] = []
    state["dex_claimed"] = []
    state["task_pool"] = []
    state["month_key"] = ""
    state["month_base"] = {}
    state["month_done"] = []
    state["total_lottery_win"] = 0
    state["tutorial_step"] = 0          # 新档才走 3 步引导，老档默认当已完成
    state["pet_touch_day"] = today
    state["pet_touch_count"] = 0
    state["total_pet_touch"] = 0
    state["total_sell"] = 0
    return state


# ===================== 存档槽（3 个） =====================
SLOT_COUNT = 3
SLOT_NAMES = ["槽位 1", "槽位 2", "槽位 3"]


def slot_dir():
    return os.path.join(os.path.dirname(SAVE_PATH) or os.getcwd(), "saves")


def _slot_meta_path():
    return os.path.join(slot_dir(), "slots_meta.txt")


def _slot_path(i):
    return os.path.join(slot_dir(), f"slot{i}.txt")


def slot_meta():
    """槽位自定义名：纯文本 `1 = '名字'`，坏行直接跳过。"""
    out = {}
    p = _slot_meta_path()
    if not os.path.exists(p):
        return out
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if " = " not in line:
                    continue
                k, v = line.strip().split(" = ", 1)
                if k.isdigit():
                    try:
                        out[int(k)] = str(ast.literal_eval(v))[:14]
                    except (ValueError, SyntaxError):
                        out[int(k)] = v[:14]
    except OSError:
        return {}
    return out


def slot_rename(i, name):
    name = (name or "").strip()[:14]
    if not name:
        return False, "名字不能为空"
    d = slot_meta()
    d[i] = name
    os.makedirs(slot_dir(), exist_ok=True)
    tmp = _slot_meta_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("# 存档槽名字 · 一行一条\n")
        for k in sorted(d):
            f.write(f"{k} = {d[k]!r}\n")
    os.replace(tmp, _slot_meta_path())
    return True, f"槽位 {i} 已改名为「{name}」"


def slot_summary(i):
    """槽位缩略信息：宠物、物种、等级、积分、游玩天数；空槽返回 None。"""
    p = _slot_path(i)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = _load_legacy_text(f.read())
    except OSError:
        return None
    pets = data.get("pet_list") or []
    pet = pets[0] if isinstance(pets, list) and pets else {}
    try:
        sd = _to_date(data.get("start_date"), date.today())
    except Exception:
        sd = date.today()
    days = max(1, (date.today() - sd).days + 1)
    return {
        "pet": str(pet.get("name", "—")),
        "species": str(pet.get("species", "")),
        "lv": int(float(pet.get("lv", 1) or 1)),
        "df": int(float(data.get("df", 0) or 0)),
        "days": days,
        "start": sd.isoformat(),
        "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
    }


def slot_store(i, state=None):
    """把当前进度写进槽位 i（state 为空就直接用现成的 player_pet.txt）。"""
    os.makedirs(slot_dir(), exist_ok=True)
    src = SAVE_PATH if state is None else None
    if state is not None:
        ok, msg = save_game(state)
        if not ok:
            return False, msg
    if not os.path.exists(SAVE_PATH):
        return False, "还没有存档可以存"
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        with open(_slot_path(i), "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        return False, f"槽位写入失败：{e}"
    return True, f"已存进「{slot_meta().get(i, SLOT_NAMES[i-1])}」"


def slot_restore(i):
    """把槽位 i 读成当前存档（先把当前进度自动备份一份）。"""
    p = _slot_path(i)
    if not os.path.exists(p):
        return False, "这个槽位还是空的"
    snapshot_backup()
    try:
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
        tmp = SAVE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, SAVE_PATH)
    except OSError as e:
        return False, f"切换失败：{e}"
    global LAST_LOAD_NOTE
    LAST_LOAD_NOTE = f"已切换到「{slot_meta().get(i, SLOT_NAMES[i-1])}」"
    return True, LAST_LOAD_NOTE


def play_days(gs):
    sd = gs.get("start_date") or date.today()
    if isinstance(sd, datetime):
        sd = sd.date()
    return max(1, (date.today() - sd).days + 1)


# ===================== 性格 / 技能 / 托管 =====================
def persona_for(pet):
    """按名字 + 物种稳定地抽一个性格，读档重开也不会变。"""
    _k = f"persona|{pet.get('species')}|{pet.get('name')}".encode()
    seed = int(hashlib.sha1(_k).hexdigest()[:12], 16)
    return random.Random(seed).choice(list(PERSONALITIES))


def persona_of(pet):
    key = pet.get("persona") or persona_for(pet)
    return PERSONALITIES.get(key, PERSONALITIES["lively"])


def skill_left(gs, pet, now=None):
    """主动技能剩余冷却（分钟小数），0 表示可用。"""
    now = now or datetime.now()
    cd = pet.get("skill_cd")
    if not cd:
        return 0.0
    try:
        t = datetime.fromisoformat(str(cd))
    except ValueError:
        return 0.0
    return max(0.0, (t.timestamp() + active_skill_of(species_of(pet))["cd"] * 60
                     - now.timestamp()) / 60.0)


def use_skill(gs, pet, now=None):
    """释放主动技能：冷却 / 亲密度双重门禁，成功后直接改 pet 和 gs。"""
    now = now or datetime.now()
    sk = active_skill_of(species_of(pet))
    left = skill_left(gs, pet, now)
    if left > 0:
        return False, f"「{sk['name']}」还在冷却，还要等 {int(left) + 1} 分钟"
    if float(pet.get("bond", 0) or 0) < sk["bond"]:
        return False, f"亲密度不够（需要 {sk['bond']}，现在 {float(pet.get('bond', 0) or 0):.0f}）"
    pet["bond"] = max(0.0, float(pet.get("bond", 0) or 0) - sk["bond"])
    pet["skill_cd"] = now.strftime("%Y-%m-%dT%H:%M:%S")
    key = sk["key"]
    msg = ""
    if key == "overclock":
        gain = random.randint(35, 55)
        gs["df"] = int(gs["df"]) + gain
        msg = f"{sk['name']}：齿轮转出 {gain} 积分"
    elif key == "dig":
        pool = [k for k, v in ITEMS.items()
                if not v.get("limited") and v.get("shop") and v.get("price", 0) >= 30]
        item = random.choice(pool) if pool else "面包"
        gs["storehouse"].append(item)
        msg = f"{sk['name']}：刨出了一份「{item}」"
    elif key == "tide":
        for k in ("hn", "ha", "cl", "health"):
            pet[k] = min(150.0, float(pet.get(k, 0) or 0) + 8.0)
        msg = f"{sk['name']}：四项状态各 +8"
    elif key == "heal":
        pet["health"] = min(150.0, float(pet.get("health", 0) or 0) + 25.0)
        msg = f"{sk['name']}：健康 +25"
    else:
        pet["hn"] = min(150.0, float(pet.get("hn", 0) or 0) + 25.0)
        pet["bond"] = min(100.0, float(pet.get("bond", 0) or 0) + 2.0)
        msg = f"{sk['name']}：开心 +25、亲密度 +2"
    return True, msg


def all_feed(gs):
    """后院托管：逐只走 use_item 的完整结算（口味偏好、物种特判、经验都算）。"""
    if not gs["pet_list"]:
        return 0, "没有宠物"
    fed = 0
    _msgs = []
    for pet in gs["pet_list"]:
        foods = [k for k in gs["storehouse"]
                 if ITEMS.get(k, {}).get("eff", {}).get("ha")
                 and not ITEMS.get(k, {}).get("limited")]
        if not foods:
            break
        item = foods[0]
        _m, _, _exp = use_item(gs, pet, item, species_of(pet),
                               bool(pet.get("is_star")), _msgs)
        for k in ("hn", "ha", "cl", "health"):
            pet[k] = max(0.0, min(150.0, float(pet.get(k, 0) or 0)))
        check_levelup(pet, gs["game_log"])
        fed += 1
    gs["total_feed"] = int(gs.get("total_feed", 0) or 0) + fed
    return fed, f"全家喂食：{fed} 只各吃了一份（含口味偏好与经验）"


# ===================== 主线 / 时间检测 =====================
def chapter_reached(gs):
    """按当前进度算出已经达到第几章。"""
    pets = [p for p in gs.get("pet_list") or [] if isinstance(p, dict)]
    dex_n = len(gs.get("dex") or [])
    c = 1 if int(gs.get("tutorial_step", 3) or 0) >= 3 else 0
    if c >= 1 and any(p.get("is_star") for p in pets):
        c = max(c, 2)
    _star_lv = max([int(p.get("star_lv", 0) or 0) for p in pets] or [0])
    # 每条条件独立判定，谁先达成就先跳章，避免"卡在前置上"
    if dex_n >= 30 and _star_lv >= 5:
        c = max(c, 3)
    if int(gs.get("season_count", 0) or 0) >= 40:
        c = max(c, 4)
    if len(pets) >= 5 or dex_n >= 44:
        c = max(c, 5)
    return c


def unlock_sections(gs):
    """返回当前已解锁的分区 tag 集合。"""
    ch = int(gs.get("chapter", 0) or 0)
    out = set(ALWAYS_SECTIONS)
    for item in CHAPTERS:
        if item["id"] <= max(1, ch):
            out.update(item["sections"])
    if ch >= 5:
        out.update(("star", "dex", "decor", "ach", "fun", "svc"))
    return out


def claim_chapters(gs, current_pet=None):
    """领取所有已达到但没领的章节奖励，返回发放文案列表。"""
    ch = int(gs.get("chapter", 0) or 0)
    done = int(gs.get("chapter_claimed", 0) or 0)
    out = []
    for item in CHAPTERS:
        if item["id"] > ch or item["id"] <= done:
            continue
        rw = item.get("reward") or {}
        if "df" in rw:
            gs["df"] = int(gs["df"]) + int(rw["df"])
            out.append(f"第 {item['id']} 章「{item['name']}」奖励 +{rw['df']} 积分")
        if "item" in rw:
            gs["storehouse"].extend([rw["item"]] * int(rw.get("n", 1)))
            out.append(f"第 {item['id']} 章奖励 {rw['item']}×{rw.get('n', 1)}")
        if "decor" in rw:
            if rw["decor"] not in gs.get("decor_owned", []):
                gs.setdefault("decor_owned", []).append(rw["decor"])
            out.append(f"第 {item['id']} 章奖励「节日挂画」×1")
    gs["chapter_claimed"] = ch
    if out and current_pet is not None:
        add_log("章节奖励：" + "；".join(out), gs["game_log"])
    return out



def forecast(days=2):
    """未来 N 天天气（纯函数算出），返回 [(date, info)]。"""
    return [(date.today() + timedelta(days=i), weather_of(date.today() + timedelta(days=i)))
            for i in range(1, days + 1)]
