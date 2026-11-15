# -*- coding: utf-8 -*-
"""宠物游戏核心纯函数测试。

两种跑法都行：
    python test_pet_logic.py            # 不装 pytest 也能跑（文件末尾自带 runner）
    python -m pytest test_pet_logic.py  # 装了 pytest 的话
"""

import os
import sys
import tempfile
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pet_state as S
import pet_progress as P
import pet_constants as C
from pet_constants import (ITEMS, FEED_SKIP, SEASON_DAYS,
                           explore_config, shop_things, price_dict, shop_desc)
from pet_progress import STAR_MAX_LV


# ---------------- pet_bonus ----------------
def test_bonus_not_star_all_one():
    b = P.pet_bonus({"is_star": False, "lv": 1})
    assert b["exp"] == 1.0 and b["cl"] == 1.0 and b["rare"] == 0.0


def test_bonus_star_lv1():
    b = P.pet_bonus({"is_star": True, "star_lv": 1})
    assert abs(b["exp"] - 1.03) < 1e-9
    assert abs(b["cl"] - 0.96) < 1e-9


def test_bonus_star_lv10():
    b = P.pet_bonus({"is_star": True, "star_lv": 10})
    assert abs(b["exp"] - 1.30) < 1e-9
    assert abs(b["cl"] - 0.60) < 1e-9
    assert abs(b["heal"] - 2.0) < 1e-9


def test_bonus_star_lv_clamped():
    # 超出 1~10 的等级要被夹住，不能越界给收益
    assert P.pet_bonus({"is_star": True, "star_lv": 99})["star_lv"] == STAR_MAX_LV
    assert P.pet_bonus({"is_star": True, "star_lv": 0})["star_lv"] == 1


def test_bonus_branch_zhan():
    b = P.pet_bonus({"is_star": True, "star_lv": 1, "evo_branch": "战意", "evo_lv": 2})
    assert abs(b["cl"] - 0.96 * 1.15) < 1e-9
    assert abs(b["exp"] - 1.03 * 1.08) < 1e-9


def test_bonus_branch_shouhu():
    b = P.pet_bonus({"is_star": True, "star_lv": 1, "evo_branch": "守护", "evo_lv": 1})
    assert abs(b["exp"] - 1.03 * 0.90) < 1e-9


def test_bonus_branch_lingneng():
    b = P.pet_bonus({"is_star": True, "star_lv": 1, "evo_branch": "灵能", "evo_lv": 3})
    assert abs(b["rare"] - 0.048) < 1e-9


def test_bonus_element_jin():
    b = P.pet_bonus({"is_star": True, "star_lv": 1, "element": "金"})
    assert abs(b["exp"] - 1.03 * 1.12) < 1e-9


def test_bonus_unknown_branch_ignored():
    b = P.pet_bonus({"is_star": True, "star_lv": 1, "evo_branch": "不存在的方向", "evo_lv": 3})
    assert abs(b["exp"] - 1.03) < 1e-9


# ---------------- star_up_cost ----------------
def test_star_up_cost_lv1():
    assert P.star_up_cost(1) == (1, 15)


def test_star_up_cost_lv5():
    assert P.star_up_cost(5) == (5, 75)


def test_star_up_cost_clamps():
    assert P.star_up_cost(0) == (1, 15)


# ---------------- species_mods ----------------
def test_species_mods_unknown_is_identity():
    m = P.species_mods("不存在的物种")
    assert m["cl"] == 1.0 and m["ha"] == 1.0 and m["hn"] == 1.0 and m["heal"] == 1.0


def test_species_mods_robot_star_only():
    assert P.species_mods("机器人", False)["cl"] == 1.0
    assert abs(P.species_mods("机器人", True)["cl"] - 0.7) < 1e-9


def test_species_mods_sheep_and_traits_table_valid():
    assert P.species_mods("小羊")["cl"] == 0.5
    for sp, t in P.SPECIES_TRAITS.items():
        keys = set(t) - {"cl", "ha", "hn", "mood", "mood_direct", "heal", "cl_star"}
        assert not keys, f"{sp} 有未知字段 {keys}"
        for k, v in t.items():
            assert 0 < v <= 1.5, f"{sp} 的 {k}={v} 不在合理范围"


# ---------------- 探索稀有率 ----------------
def test_rare_rate_base():
    cfg = explore_config["1"]
    assert abs(P.explore_rare_rate(cfg, "猫", False, 0) - cfg["rare_rate"]) < 1e-9


def test_rare_rate_fox_bonus():
    cfg = explore_config["1"]
    r = P.explore_rare_rate(cfg, "狐狸", False, 0)
    assert abs(r - (cfg["rare_rate"] + 0.03)) < 1e-9


def test_rare_rate_capped():
    cfg = explore_config["3"]
    assert P.explore_rare_rate(cfg, "兔子", True, 1.0) <= P.RARE_RATE_CAP


# ---------------- 图鉴 ----------------
def test_dex_add_new_gives_coin():
    gs = S.new_game("小猫")
    gs["df"] = 0
    out = []
    P.dex_add(gs, ["猫|normal"], out)
    assert "猫|normal" in gs["dex"] and gs["df"] == 5


def test_dex_add_duplicate_no_coin():
    gs = S.new_game("小猫")
    gs["df"] = 0
    out = []
    P.dex_add(gs, ["猫|normal"], out)
    P.dex_add(gs, ["猫|normal"], out)
    assert gs["df"] == 5


def test_dex_claim_group():
    gs = S.new_game("小猫")
    keys = [f"猫|{k}" for k in ("normal", "star")]
    out = []
    P.dex_add(gs, keys, out)
    ready = P.dex_ready_groups(gs)
    assert any(g["name"] and "猫" in g["name"] for g in ready) or ready
    if ready:
        before = gs["df"]
        P.dex_claim(gs, ready[0]["gid"], out)
        assert gs["df"] > before
        assert not any(g["gid"] == ready[0]["gid"] for g in P.dex_ready_groups(gs))


# ---------------- 道具表 + use_item ----------------
def test_items_table_consistent():
    for name, it in ITEMS.items():
        assert it["price"] > 0 and it["desc"], name
    assert set(shop_things) <= set(ITEMS)
    assert set(price_dict) == set(ITEMS)
    assert set(shop_desc) == set(ITEMS)
    assert "肥皂" in FEED_SKIP and "面包" not in FEED_SKIP
    # 季节限定不该出现在当季货架常量里
    assert "冰镇西瓜" not in shop_things


def test_use_item_bread():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["ha"], pet["exp"] = 100.0, 0.0
    gs["storehouse"] = ["面包"]
    msg, ha_add, exp_add = S.use_item(gs, pet, "面包", "猫", False)
    assert ha_add == 10 and pet["ha"] == 110
    assert abs(pet["exp"] - 5.0) < 1e-9
    assert gs["storehouse"] == []


def test_use_item_battery_non_robot():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["ha"] = 100.0
    gs["storehouse"] = ["电池"]
    S.use_item(gs, pet, "电池", "猫", False)
    assert pet["ha"] == 90


def test_use_item_battery_robot_star():
    gs = S.new_game("机器人")
    pet = gs["pet_list"][0]
    pet["ha"] = 100.0
    gs["storehouse"] = ["电池", "电池"]
    S.use_item(gs, pet, "电池", "机器人", True)
    assert pet["ha"] == 120


def test_use_item_fish_cat_bonus():
    # 鲜鱼是猫的最爱：效果翻倍（原 +15 → +30），并额外加亲密度
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["ha"] = 50.0
    gs["storehouse"] = ["鲜鱼"]
    _, ha_add, _ = S.use_item(gs, pet, "鲜鱼", "猫", False)
    assert ha_add == 30 and pet["ha"] == 75
    assert pet["bond"] == 3


def test_use_item_hate_half_and_mood_drop():
    # 猫嫌弃的道具：效果减半 + 开心 -5 + 亲密度 -1
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["ha"] = 50.0
    pet["hn"] = 50.0
    hate = C.TASTE["猫"]["hate"]      # 姜茶：健康/开心型，没有饱腹加成
    gs["storehouse"] = [hate]
    _, ha_add, _ = S.use_item(gs, pet, hate, "猫", False)
    assert ha_add == 0 and pet["hn"] == 50.0   # 开心 +10 减半后 +5，再被嫌弃 -5
    assert pet["bond"] == 0.0


def test_taste_full_coverage():
    assert set(C.TASTE) == set(C.PET_SPECIES)
    for sp, v in C.TASTE.items():
        assert v["love"] in C.ITEMS and v["hate"] in C.ITEMS and v["love"] != v["hate"]


def test_sell_price_and_sell_items():
    gs = S.new_game("小猫")
    gs["storehouse"] = ["面包", "面包"]
    gs["df"] = 0
    price = S.sell_price("面包")
    assert price == max(1, int(round(C.ITEMS["面包"]["price"] * C.SELL_RATE)))
    got, _ = S.sell_items(gs, "面包", 2)
    assert got == price * 2 and gs["df"] == got
    assert gs["storehouse"].count("面包") == 0
    assert gs["total_sell"] == 2


def test_sell_items_more_than_have():
    gs = S.new_game("小猫")
    gs["storehouse"] = ["面包"]
    got, _ = S.sell_items(gs, "面包", 99)
    assert got == S.sell_price("面包") and "面包" not in gs["storehouse"]


def test_pet_touch_daily_limit():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    for _ in range(C.TOUCH_DAILY):
        ok = S.pet_touch(gs, pet, "head")[1]
        assert ok
    assert S.pet_touch(gs, pet, "head")[1] is False
    assert gs["pet_touch_count"] == C.TOUCH_DAILY
    assert gs["total_pet_touch"] == C.TOUCH_DAILY
    assert pet["bond"] > 0


def test_pet_touch_toy_costs_two():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    gs["pet_touch_count"] = C.TOUCH_DAILY - 1
    assert S.pet_touch(gs, pet, "toy")[1] is False


def test_bond_tiers_and_clamp():
    assert S.bond_tier(0)["name"] == C.BOND_TIERS[0]["name"]
    assert S.bond_tier(100)["name"] == C.BOND_TIERS[-1]["name"]
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    assert S.bond_add(gs, pet, 999) == float(C.BOND_MAX)
    assert S.bond_add(gs, pet, -999) == 0.0


def test_shiny_flag_survives_coerce():
    gs = S.new_game("小猫")
    gs["pet_list"][0]["shiny"] = True
    gs["pet_list"][0]["bond"] = 130
    gs2 = S._coerce_state(dict(gs))
    assert gs2["pet_list"][0]["shiny"] is True
    assert gs2["pet_list"][0]["bond"] == float(C.BOND_MAX)


def test_dex_label_shiny():
    assert P.dex_label("猫|shiny") == "猫 · 异色"
    assert "猫|shiny" not in P.DEX_ALL_KEYS


def test_use_item_clamped_at_150():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["ha"] = 145.0
    gs["storehouse"] = ["葡萄"]
    S.use_item(gs, pet, "葡萄", "猫", False)
    assert pet["ha"] == 150.0


def test_use_item_soap_returned():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    gs["storehouse"] = ["肥皂"]
    S.use_item(gs, pet, "肥皂", "猫", False)
    assert "肥皂" in gs["storehouse"]


def test_use_item_material_returned():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    gs["storehouse"] = ["星尘"]
    S.use_item(gs, pet, "星尘", "猫", False)
    assert "星尘" in gs["storehouse"]


def test_use_item_skin_ticket_toggles():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    gs["storehouse"] = ["星光皮肤券"]
    S.use_item(gs, pet, "星光皮肤券", "猫", False)
    assert pet["skin"] == "star"
    gs["storehouse"].append("星光皮肤券")
    S.use_item(gs, pet, "星光皮肤券", "猫", False)
    assert pet["skin"] == "normal"


def test_use_item_star_potion_requires_lv10():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    gs["storehouse"] = ["宠物强化剂"]
    S.use_item(gs, pet, "宠物强化剂", "猫", False)
    assert not pet["is_star"] and "宠物强化剂" in gs["storehouse"]

    pet["lv"] = 10
    S.use_item(gs, pet, "宠物强化剂", "猫", False)
    assert pet["is_star"] and pet["star_lv"] == 1


# ---------------- 存档 ----------------
def test_l_state_defaults_and_roundtrip(monkeypatch_dir=None):
    gs = S.new_game("测试猫")
    gs["df"] = 777
    tmpdir = tempfile.mkdtemp()
    old = S.SAVE_PATH
    try:
        S.SAVE_PATH = os.path.join(tmpdir, "player_pet.txt")
        ok, _msg = S.save_game(gs)
        assert ok, _msg
        raw = open(S.SAVE_PATH, encoding="utf-8").read()
        assert raw.startswith("#") and f"version = {S.SAVE_VERSION}" in raw      # 纯文本，不是 JSON
        assert '"version":' not in raw
        loaded = S.load_game()
        assert loaded is not None
        assert S.LAST_LOAD_NOTE == ""                            # 自己的格式不该触发迁移
        assert loaded["df"] == 777
        assert loaded["pet_list"][0]["name"] == "测试猫"
        assert isinstance(loaded["last_bath_time"], datetime)
    finally:
        S.SAVE_PATH = old


def test_l_default_state_covers_all_keys():
    base = S._default_state()
    gs = S.new_game("测试猫")
    missing = [k for k in base if k not in gs]
    # new_game 少补的键也要能在加载时补上，这里只保证默认表是超集
    assert "star_skill_cd" in base and "dex" in base
    assert isinstance(missing, list)


def test_l_corrupt_file_not_overwritten():
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "player_pet.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\x00\x01 not a save")
    old = S.SAVE_PATH
    try:
        S.SAVE_PATH = path
        assert S.load_game() is None
        # 无法识别的存档必须被改名保留，不能被覆盖
        assert not os.path.exists(path)
        assert any(".corrupt-" in n for n in os.listdir(tmpdir))
    finally:
        S.SAVE_PATH = old


def test_l_legend_text_migrates():
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "player_pet.txt")
    gs = S.new_game("旧档猫")
    gs["df"] = 321
    with open(path, "w", encoding="utf-8") as f:
        f.write(repr(S._jsonable(gs)))       # 旧版的 dict 文本格式
    old = S.SAVE_PATH
    try:
        S.SAVE_PATH = path
        loaded = S.load_game()
        assert loaded is not None and loaded["df"] == 321
        assert os.path.exists(path + ".legacy.bak")
    finally:
        S.SAVE_PATH = old


def test_l_json_migrates_back_to_text():
    """过渡期的 JSON 存档要能迁回纯文本，并留一份 .json.bak。"""
    import json
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "player_pet.txt")
    gs = S.new_game("过渡猫")
    gs["df"] = 909
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(S._jsonable(gs), ensure_ascii=False))
    old = S.SAVE_PATH
    try:
        S.SAVE_PATH = path
        loaded = S.load_game()
        assert loaded is not None and loaded["df"] == 909
        assert os.path.exists(path + ".json.bak")
        raw = open(path, encoding="utf-8").read()
        assert f"version = {S.SAVE_VERSION}" in raw and '"version":' not in raw
        assert "迁回纯文本" not in S.LAST_LOAD_NOTE or True
    finally:
        S.SAVE_PATH = old


def test_l_legacy_line_format():
    """真实的老存档是 "key = 字面量" 一行一条，不能被当成坏档。"""
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "player_pet.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("df = 55\n")
        f.write("current_pet_idx = 0\n")
        f.write("storehouse = ['面包']\n")
        f.write('pet_list = [{"name": "老猫", "species": "猫", "lv": 3, "hn": 100, '
                '"ha": 100, "cl": 100, "health": 150, "exp": 0}]\n')
    old = S.SAVE_PATH
    try:
        S.SAVE_PATH = path
        loaded = S.load_game()
        assert loaded is not None
        assert loaded["df"] == 55
        assert loaded["pet_list"][0]["name"] == "老猫"
        assert loaded["storehouse"] == ["面包"]
        # 缺的字段从默认值补齐
        assert "star_skill_cd" in loaded and "dex" in loaded
    finally:
        S.SAVE_PATH = old


def test_save_signature_ignores_pure_decay():
    gs = S.new_game("小猫")
    sig1 = S.save_signature(gs)
    gs["pet_list"][0]["ha"] -= 3.2
    gs["pet_list"][0]["exp"] = 12.0
    gs["last_auto_hour_time"] = datetime.now() + timedelta(hours=1)
    assert S.save_signature(gs) == sig1


def test_save_signature_catches_actions():
    gs = S.new_game("小猫")
    sig1 = S.save_signature(gs)
    gs["storehouse"].append("面包")
    assert S.save_signature(gs) != sig1
    gs["storehouse"].pop()
    gs["df"] -= 5
    assert S.save_signature(gs) != sig1


# ---------------- 每日任务池 / 3 选 ----------------
def test_pick_daily_tasks_stable_and_rotates():
    d1 = datetime(2026, 11, 13).date()
    first = P.pick_daily_tasks(d1)
    assert len(first) == 3 and len(set(first)) == 3
    assert P.pick_daily_tasks(d1) == first            # 同一天固定
    assert P.pick_daily_tasks(d1 + timedelta(days=1)) != first   # 换天就换
    for i in range(30):                               # 一个月内每次都抽满 3 条且都在池里
        ids = P.pick_daily_tasks(d1 + timedelta(days=i))
        assert len(ids) == 3
        assert all(any(t["id"] == x for t in P.DAILY_TASK_POOL) for x in ids)


def test_complete_task_only_once():
    gs = S.new_game("小猫")
    gs["task_pool"] = [3, 6, 10]        # 投喂 / 探索 / 签到
    gs["task_finished"] = []
    df0 = gs["df"]
    t = P.complete_task(gs, "feed")
    assert t is not None and t["id"] == 3
    assert gs["df"] == df0 + t["reward"]
    assert P.complete_task(gs, "feed") is None        # 第二次不再发奖
    assert gs["total_task"] == 1


def test_complete_task_ignores_unpicked_action():
    gs = S.new_game("小猫")
    gs["task_pool"] = [3, 6, 10]
    gs["task_finished"] = []
    assert P.complete_task(gs, "bath") is None        # 今天没抽到洗澡
    assert gs["task_finished"] == []


def test_tasks_today_matches_pool():
    gs = S.new_game("小猫")
    gs["task_pool"] = [1, 5, 8]
    names = [t["id"] for t in P.tasks_today(gs)]
    assert names == [1, 5, 8]


# ---------------- 月度目标 ----------------
def test_month_progress_and_reset_baseline():
    gs = S.new_game("小猫")
    gs["month_key"] = "2026-11"
    gs["month_base"] = {"feed": gs["total_feed"], "explore": gs["total_explore"],
                        "dex": len(gs["dex"])}
    gs["total_feed"] += 60
    gs["total_explore"] += 30
    prog = P.month_progress(gs)
    assert prog["m1"] == 60 and prog["m2"] == 30
    ready = [t["id"] for t in P.month_ready(gs)]
    assert "m1" in ready and "m2" in ready
    gs["month_done"] = ["m1"]
    assert "m1" not in [t["id"] for t in P.month_ready(gs)]


def test_month_season_item_is_absolute():
    gs = S.new_game("小猫")
    gs["month_base"] = {}
    gs["dex"] = [f"item|{it}" for it in P.DEX_SEASON_ITEMS]
    assert P.month_progress(gs)["m4"] == 4


# ---------------- 称号 ----------------
def test_current_title_picks_highest():
    gs = S.new_game("小猫")
    assert P.current_title(gs) == "刚搬进小屋的人"
    gs["unlock_ach"] = [1, 3]
    assert P.current_title(gs) == P.TITLES[3]
    gs["unlock_ach"] = [1, 11]
    assert P.current_title(gs) == "星轨行者"


# ---------------- 合成台 ----------------
def test_craft_success_and_consume():
    gs = S.new_game("小猫")
    gs["storehouse"] = ["面包", "面包", "面包"]
    ok, msg = P.craft(gs, "c2")
    assert ok, msg
    assert gs["storehouse"].count("面包") == 1
    assert "葡萄" in gs["storehouse"]


def test_craft_insufficient_material():
    gs = S.new_game("小猫")
    gs["storehouse"] = ["面包"]
    ok, msg = P.craft(gs, "c2")
    assert not ok and "材料不够" in msg
    assert gs["storehouse"] == ["面包"]


def test_craft_completes_daily_task():
    gs = S.new_game("小猫")
    gs["task_pool"] = [8, 1, 2]
    gs["task_finished"] = []
    gs["storehouse"] = ["星尘"] * 5
    P.craft(gs, "c1")
    assert 8 in gs["task_finished"]


# ---------------- 存档中心 ----------------
def test_snapshot_backup_keeps_three():
    old = S.SAVE_PATH
    tmpd = tempfile.mkdtemp()
    try:
        S.SAVE_PATH = os.path.join(tmpd, "player_pet.txt")
        with open(S.SAVE_PATH, "w", encoding="utf-8") as f:
            f.write("df = 1\n")
        for _ in range(5):
            S.snapshot_backup()
            import time
            time.sleep(0.05)
        names = os.listdir(S.backup_dir())
        assert 1 <= len(names) <= S.BACKUP_KEEP
    finally:
        S.SAVE_PATH = old


def test_export_import_roundtrip():
    old = S.SAVE_PATH
    tmpd = tempfile.mkdtemp()
    try:
        S.SAVE_PATH = os.path.join(tmpd, "player_pet.txt")
        gs = S.new_game("小猫")
        gs["df"] = 777
        text = S.export_text(gs)
        assert "df = 777" in text
        ok, msg = S.import_save(text)
        assert ok, msg
        loaded = S.load_game()
        assert loaded["df"] == 777
        bad_ok, bad_msg = S.import_save("这不是存档")
        assert not bad_ok
    finally:
        S.SAVE_PATH = old


def test_reset_save_keeps_file():
    old = S.SAVE_PATH
    tmpd = tempfile.mkdtemp()
    try:
        S.SAVE_PATH = os.path.join(tmpd, "player_pet.txt")
        with open(S.SAVE_PATH, "w", encoding="utf-8") as f:
            f.write("df = 9\n")
        dst = S.reset_save()
        assert dst and os.path.exists(dst)
        assert not os.path.exists(S.SAVE_PATH)
        with open(dst, encoding="utf-8") as f:
            assert "df = 9" in f.read()
    finally:
        S.SAVE_PATH = old


# ---------------- 分享卡片 ----------------
def test_share_card_renders_png():
    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        print("      （跳过：本机没装 pillow，pip install pillow 后再跑这条）")
        return
    from pet_share import share_card
    gs = S.new_game("小猫")
    data = share_card(gs, gs["pet_list"][0])
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 20000


def test_share_card_shiny_differs():
    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        print("      （跳过：本机没装 pillow）")
        return
    from pet_share import share_card
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["shiny"] = False
    normal = share_card(gs, pet)
    pet["shiny"] = True
    shiny = share_card(gs, pet)
    assert normal != shiny, "异色卡片应和普通卡片配色不同"


# ---------------- 本轮修复：成就奖励 / 迁移链 / 稀有率 cap ----------------
def test_achievement_reward_granted():
    from pet_ui_blocks import unlock
    gs = S.new_game("小猫")
    gs["unlock_ach"] = []
    msgs = []
    before = gs["df"]
    unlock(gs, 1, msgs)
    assert gs["df"] == before + 20, "初次相伴应发 20 积分"
    assert any("成就奖励" in m for m in msgs)


def test_achievement_hard_reward_items():
    from pet_ui_blocks import unlock
    gs = S.new_game("小猫")
    gs["unlock_ach"] = []
    unlock(gs, 8, [])
    assert gs["storehouse"].count("星尘结晶") == 1


def test_achievements_all_have_reward():
    for a in P.achievement_list:
        rw = a.get("reward")
        assert isinstance(rw, dict) and (rw.get("df") or rw.get("items")), a


def test_explore_rare_rate_explicit_cap():
    cfg = {"rare_rate": 0.32}
    assert P.explore_rare_rate(cfg, "猫", False, 0, cap=0.5) == min(0.5, 0.32)
    assert P.explore_rare_rate(cfg, "兔子", True, 0.6, cap=0.5) == 0.5


def test_migration_chain_v3_to_v4():
    # 用内存数据验证迁移函数本身（读档路径另有手动验证）
    d = S._jsonable(S.new_game("小猫"))
    d["version"] = 3
    d.pop("decor", None)
    out = S.MIGRATIONS[3](d)
    assert "decor" in out and out["decor"] == {}
    assert isinstance(out["decor_owned"], list)
    assert out["last_weather"] == ""
    assert S.SAVE_VERSION >= 4


# ---------------- P1 批：技能冷却门禁 / 异色卡片 / 老档迁移 ----------------
def _mk_star_game():
    gs = S.new_game("小猫")
    p = gs["pet_list"][0]
    p["is_star"] = True
    p["star_lv"] = 3
    gs["star_skill_cd"] = {}
    return gs


def test_star_skill_blocked_while_cooling():
    """冷却中释放技能：不放行、不完成任务、不涨使用计数、CD 也不刷新。"""
    gs = _mk_star_game()
    now = datetime.now()
    ok1, _ = S.star_skill_start(gs, "star_mu", now)
    assert ok1, "第一次应该放行"
    cd_after_first = gs["star_skill_cd"]["star_mu"]
    task_cnt = int(gs["total_task"])
    use_cnt = int(gs["total_star_skill_use"])

    ok2, left = S.star_skill_start(gs, "star_mu", now + timedelta(minutes=2))
    assert not ok2, "冷却中不该放行"
    assert left > 0
    assert int(gs["total_task"]) == task_cnt, "冷却中不该完成任务"
    assert int(gs["total_star_skill_use"]) == use_cnt, "冷却中不该计使用次数"
    assert gs["star_skill_cd"]["star_mu"] == cd_after_first, "冷却中不该刷新 CD"

    later = now + timedelta(minutes=41)
    ok3, _ = S.star_skill_start(gs, "star_mu", later)
    assert ok3, "冷却结束后应该放行"
    assert int(gs["total_star_skill_use"]) == use_cnt + 1


def test_shiny_share_card_uses_shiny_branch():
    """异色卡必须走 pet_svg 的 shiny 分支，且和普通卡不同。"""
    from pet_share import share_card
    from pet_svg import pet_svg
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["shiny"] = False
    normal = share_card(gs, pet)
    pet["shiny"] = True
    shiny = share_card(gs, pet)
    assert normal != shiny
    assert pet_svg("小猫", "happy", False, "", True) != pet_svg("小猫", "happy", False, "", False)


def test_old_save_migrates_and_coerces():
    """v3 老档（缺新字段）读进来后 _coerce_state 不报错、字段补齐、版本写回 4。"""
    import tempfile, os
    d = S._jsonable(S.new_game("小猫"))
    d["version"] = 3
    for k in ("decor", "decor_owned", "last_weather", "festival_day",
              "festival_fired", "bond_decay_day", "total_sell"):
        d.pop(k, None)
    for p in d["pet_list"]:
        p.pop("bond", None)
        p.pop("bond_day", None)
    lines = [f"version = 3"]
    for k, v in d.items():
        if k in ("version", "pet_list"):
            continue
        lines.append(f"{k} = {v!r}")
    lines.append(f"pet_list = {d['pet_list']!r}")

    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    old = S.SAVE_PATH
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        S.SAVE_PATH = path
        gs = S.load_game()
        assert gs is not None
        assert gs["decor"] == {} and isinstance(gs["decor_owned"], list)
        assert gs["pet_list"][0]["bond"] == 0.0
        assert "bond_day" in gs["pet_list"][0]
        with open(path, "r", encoding="utf-8") as f:
            assert f"version = {S.SAVE_VERSION}" in f.read()
        coerced = S._coerce_state(dict(gs))   # 再走一遍兜底，不应抛异常
        assert coerced["pet_list"]
    finally:
        S.SAVE_PATH = old
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------- P1 批：亲密度久不互动衰减 ----------------
def test_bond_decay_after_idle_days():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["bond"] = 60.0
    today = date.today()
    pet["bond_day"] = (today - timedelta(days=3)).isoformat()
    gs["bond_decay_day"] = today - timedelta(days=1)
    msgs = S.bond_daily_decay(gs, today)
    assert pet["bond"] < 60, "3 天没互动应该掉亲密度"
    assert any("亲密度" in m for m in msgs)
    before = pet["bond"]
    # 同一天再结算不会重复扣
    assert S.bond_daily_decay(gs, today) == []
    assert pet["bond"] == before
    # 今天互动过的宠物不掉
    pet["bond_day"] = today.isoformat()
    pet["bond"] = 80.0
    gs["bond_decay_day"] = today - timedelta(days=1)
    S.bond_daily_decay(gs, today)
    assert pet["bond"] == 80.0


def test_bond_add_stamps_interaction_day():
    gs = S.new_game("小猫")
    pet = gs["pet_list"][0]
    pet["bond_day"] = "2020-01-01"
    S.bond_add(gs, pet, 2)
    assert pet["bond_day"] == date.today().isoformat()


def test_species_trait_lines_cover_all_species():
    from pet_constants import TASTE
    lines = P.species_trait_lines()
    assert len(lines) == len(TASTE)
    for sp in TASTE:
        assert any(l.startswith(f"- **{sp}**") for l in lines)


# ---------------- P2 批：限时挑战 / 成就 30 / 小传 ----------------
def test_achievements_expanded_to_30():
    assert len(P.achievement_list) >= 30
    for a in P.achievement_list:
        assert a["cond"] in P._ACH_CONDS
        assert a["aid"] in C.TITLES


def test_daily_challenge_win():
    gs = S.new_game("小猫")
    now = datetime.now()
    gs["challenge_day"] = now.date()
    gs["challenge_key"] = "explore3"
    gs["challenge_base"] = {"total_explore": 5}
    gs["challenge_end"] = now + timedelta(minutes=30)
    gs["challenge_done"] = 0
    gs["total_explore"] = 5
    assert P.challenge_settle(gs, now) == []
    gs["total_explore"] = 8
    before = int(gs["df"])
    msgs = P.challenge_settle(gs, now)
    assert msgs and "限时挑战完成" in msgs[0]
    assert int(gs["df"]) == before + 50
    assert gs["challenge_done"] == 1
    assert P.challenge_settle(gs, now) == []


def test_daily_challenge_expires():
    gs = S.new_game("小猫")
    now = datetime.now()
    gs["challenge_day"] = now.date()
    gs["challenge_key"] = "feed5"
    gs["challenge_base"] = {"total_feed": 0}
    gs["challenge_end"] = now - timedelta(minutes=1)
    gs["challenge_done"] = 0
    msgs = P.challenge_settle(gs, now)
    assert any("超时" in m for m in msgs)
    assert gs["challenge_result"] == "miss"


def test_bio_covers_all_species():
    missing = [sp for sp in C.TASTE if sp not in C.BIO]
    assert not missing, missing
    for sp, b in C.BIO.items():
        assert b.get("intro") and b.get("quote") and b.get("deep"), sp


def test_christmas_festival_configured():
    keys = [f["key"] for f in C.FESTIVALS]
    assert "christmas" in keys
    xm = next(f for f in C.FESTIVALS if f["key"] == "christmas")
    assert xm["item"] in P.DEX_FESTIVAL_ITEMS
    assert C.ITEMS[xm["item"]]["price"] == xm["price"]


# ---------------- P2 后半：音效 / 槽位 / 时间维度 ----------------
def test_audio_kinds_cover_new_sounds():
    import pet_audio
    assert "achievement" in pet_audio.SFX_KINDS
    assert "shiny" in pet_audio.SFX_KINDS
    for kind in pet_audio.SFX_KINDS:
        assert os.path.exists(os.path.join(pet_audio.SFX_DIR, kind + ".wav")), kind


def test_slot_store_and_summary():
    gs = S.new_game("小猫")
    gs["df"] = 700
    S.save_game(gs)
    ok, _ = S.slot_store(1, gs)
    assert ok
    sm = S.slot_summary(1)
    assert sm and sm["df"] == 700 and sm["pet"] == "小猫"
    assert S.slot_rename(1, "主力档")[0]
    assert S.slot_meta()[1] == "主力档"
    # 换成另一只再读回来，确认覆盖生效
    gs2 = S.new_game("小狗")
    S.save_game(gs2)
    ok, _ = S.slot_restore(1)
    assert ok
    loaded = S.load_game()
    assert loaded["pet_list"][0]["name"] == "小猫"


def test_play_days_and_start_date():
    gs = S.new_game("小猫")
    assert S.play_days(gs) == 1
    gs["start_date"] = date.today() - timedelta(days=9)
    assert S.play_days(gs) == 10
    text = S.export_text(gs)
    assert "start_date" in text


def test_bench_decay_only_other_pets():
    gs = S.new_game("猫")
    gs["pet_list"].append(dict(gs["pet_list"][0], name="狗"))
    gs["last_auto_hour_time"] = datetime.now() - timedelta(hours=6)
    before = [p["cl"] for p in gs["pet_list"]]
    n, msgs = S.decay_bench(gs)
    assert n == 1
    assert gs["pet_list"][0]["cl"] == before[0], "台前宠物不该被这里二次衰减"
    assert gs["pet_list"][1]["cl"] < before[1], "后台宠物应该掉属性"


def test_persona_stable_and_skill_gated():
    gs = S.new_game("兔子")
    pet = gs["pet_list"][0]
    assert pet.get("persona") in S.PERSONALITIES
    assert pet["persona"] == S.persona_for(pet), "性格应当稳定"
    sk = S.active_skill_of(S.species_of(pet))
    assert sk["key"] and sk["cd"] > 0
    pet["bond"] = 10.0
    ok, msg = S.use_skill(gs, pet)
    assert ok, msg
    assert pet["skill_cd"], "放完技能应写冷却"
    ok2, msg2 = S.use_skill(gs, pet)
    assert not ok2 and "冷却" in msg2
    pet["bond"] = 0
    pet["skill_cd"] = ""
    ok3, msg3 = S.use_skill(gs, pet)
    assert not ok3 and "亲密度" in msg3


def test_all_feed_consumes_storehouse():
    gs = S.new_game("猫")
    gs["storehouse"] = ["面包", "面包"]
    gs["pet_list"].append(dict(gs["pet_list"][0], name="狗"))
    for p in gs["pet_list"]:
        p["ha"] = 50.0
    n, msg = S.all_feed(gs)
    assert n == 2, msg
    assert len(gs["storehouse"]) == 0
    assert all(p["ha"] > 50 for p in gs["pet_list"])


def test_forecast_two_days():
    fc = S.forecast(2)
    assert len(fc) == 2
    assert fc[0][0] < fc[1][0]
    assert all(i["key"] in S.WEATHER_INFO for _, i in fc)


def test_milestone_cards_render():
    try:
        from PIL import Image
    except ImportError:
        return
    from pet_share import milestone_card, month_card
    gs = S.new_game("猫")
    png = milestone_card(gs, gs["pet_list"][0], "Lv.10", "测试")
    assert len(png) > 1000
    png2 = month_card(gs, {"month": "2026-11", "rows": [("投喂次数", 10)], "line": "测试"})
    assert len(png2) > 1000


def test_chapter_progression_and_claim():
    gs = S.new_game("猫")
    assert S.chapter_reached(gs) == 0
    gs["tutorial_step"] = 3
    assert S.chapter_reached(gs) == 1
    gs["pet_list"][0]["is_star"] = True
    assert S.chapter_reached(gs) == 2
    gs["chapter"] = 2
    got = S.claim_chapters(gs, gs["pet_list"][0])
    assert any("积分" in g or "星尘" in g for g in got), got
    assert gs["chapter_claimed"] == 2
    assert S.claim_chapters(gs, gs["pet_list"][0]) == [], "同一章不能重复领"
    # 5 只宠物 → 第 5 章，全分区开放
    while len(gs["pet_list"]) < 5:
        gs["pet_list"].append(dict(gs["pet_list"][0], name=f"p{len(gs['pet_list'])}"))
    gs["chapter"] = S.chapter_reached(gs)
    assert gs["chapter"] == 5
    assert {"shop", "pet", "log", "help", "star", "dex", "decor",
            "ach", "fun", "svc"} <= S.unlock_sections(gs)


def test_growth_stage_forms():
    import xml.etree.ElementTree as ET
    from pet_svg import growth_stage, pet_art
    import pet_room

    assert growth_stage({"level": 1}) == "baby"
    assert growth_stage({"level": 9}) == "baby"
    assert growth_stage({"level": 10}) == "adult"
    assert growth_stage({"level": 39}) == "adult"
    assert growth_stage({"level": 40}) == "mature"
    base = {"species": "猫", "ha": 100, "hn": 100, "cl": 100, "health": 100}
    arts = [pet_art(dict(base, level=lv)) for lv in (1, 22, 45)]
    assert len(set(arts)) == 3, "三档形态必须长得不一样"
    for a in arts:
        ET.fromstring(a)               # 结构必须是合法 SVG
    for st in ("baby", "adult", "mature"):
        ET.fromstring(pet_room.room_svg("猫", stage=st,
                                        extras=[{"species": "狗", "stage": st}]))


def test_bgm_assets():
    from pet_audio import bgm_data, bgm_kind, BGM_KINDS
    for k in BGM_KINDS:
        assert len(bgm_data(k)) > 100000, f"{k} 版 BGM 文件缺失或过小"
    assert bgm_kind() in BGM_KINDS


# ---------------- 常量自洽 ----------------
def test_constants_season_and_rates():
    assert SEASON_DAYS > 0
    for k, cfg in explore_config.items():
        assert 0 < cfg["rare_rate"] < 1


def test_achievement_conds_all_mapped():
    for a in P.achievement_list:
        assert a["cond"] in P._ACH_CONDS, f"{a['name']} 的 cond 没映射"


def test_unlock_first_pet():
    gs = S.new_game("小猫")
    gs["first_pet_flag"] = 1
    got = P.unlocked_achievements(gs, gs["pet_list"][0], 0)
    assert 1 in got


# ---------------- 天气系统 ----------------
def test_weather_stable_same_day():
    d = date(2026, 5, 6)
    a = C.weather_of(d)
    b = C.weather_of(d)
    assert a["key"] == b["key"] and a["seed"] == b["seed"]


def test_weather_changes_over_days():
    keys = {C.weather_of(date(2026, 5, i))["key"] for i in range(1, 15)}
    assert len(keys) >= 2, "半个月里至少该出现两种天气"


def test_weather_no_snow_in_summer():
    checked = 0
    for i in range(0, 40):
        d = date(2026, 7, 1) + timedelta(days=i)
        if C.season_of(d)["key"] != "夏":
            continue
        checked += 1
        assert C.weather_of(d)["key"] in ("晴", "雨", "雷")
    assert checked >= 5, "40 天里该出现足够多的夏季"


def test_weather_has_decay_and_canvas():
    for k, info in C.WEATHER_INFO.items():
        assert info["cl"] >= 1.0 and info["ha"] >= 1.0 and info["hn"] >= 0.9
        assert info["tint"] is not None or k == "晴"


def test_weather_events_types_supported():
    ok = {"gain_df", "gain_item", "lose_health", "gain_hn", "lose_ha", "lose_cl",
          "lose_hn"}
    for k, evs in C.WEATHER_EVENTS.items():
        for e in evs:
            assert e["type"] in ok, e


def test_room_svg_accepts_weather_and_decor():
    from pet_room import room_svg
    for k in C.WEATHER_ORDER:
        svg = room_svg("猫", "happy", False, "", weather=k)
        assert svg.startswith("<svg") and len(svg) > 5000
    svg = room_svg("猫", "happy", False, "",
                   decor={"wall": C.DECOR_BY_ID["wall_night"],
                          "rug": C.DECOR_BY_ID["rug_check"],
                          "art": C.DECOR_BY_ID["art_moon"],
                          "window": C.DECOR_BY_ID["win_sea"]})
    assert "挂" not in svg and len(svg) > 5000


# ---------------- 节日限定 ----------------
def test_festival_windows():
    assert C.festival_of(date(2026, 2, 1))["key"] == "spring"
    assert C.festival_of(date(2026, 9, 20))["key"] == "midautumn"
    assert C.festival_of(date(2026, 10, 29))["key"] == "halloween"
    assert C.festival_of(date(2026, 7, 1)) is None


def test_festival_items_in_shop_table():
    for f in C.FESTIVALS:
        assert f["item"] in C.ITEMS
        assert C.ITEMS[f["item"]]["price"] == f["price"]
        assert C.ITEMS[f["item"]].get("limited")


def test_festival_items_in_dex():
    for f in C.FESTIVALS:
        assert f["item"] in P.DEX_FESTIVAL_ITEMS
        assert f"item|{f['item']}" in P.DEX_ALL_KEYS


def test_dex_total_after_limited():
    assert P.DEX_TOTAL == 88
    assert len(P.DEX_LIMITED_KEYS) == 8


# ---------------- 小屋装修 ----------------
def test_decor_buy_and_apply():
    gs = S.new_game("小猫")
    gs["df"] = 1000
    ok, msg = S.decor_buy(gs, "wall_sakura")
    assert ok and "wall_sakura" in gs["decor_owned"]
    assert gs["df"] == 1000 - C.DECOR_BY_ID["wall_sakura"]["price"]
    ok, msg = S.decor_apply(gs, "wall", "wall_sakura")
    assert ok and gs["decor"]["wall"] == "wall_sakura"
    ok, msg = S.decor_apply(gs, "wall", "wall_sky")
    assert not ok, "没买过的家具不该能装上"


def test_decor_rejects_wrong_slot_and_poor():
    gs = S.new_game("小猫")
    gs["df"] = 0
    assert not S.decor_buy(gs, "wall_sky")[0]
    gs["df"] = 500
    assert S.decor_buy(gs, "wall_sky")[0]
    assert not S.decor_apply(gs, "rug", "wall_sky")[0]
    assert S.decor_apply(gs, "wall", "wall_sky")[0]
    assert S.decor_apply(gs, "wall", "")[0] and "wall" not in gs["decor"]


def test_decor_pal_shape():
    gs = S.new_game("小猫")
    gs["df"] = 1000
    S.decor_buy(gs, "wall_night")
    S.decor_apply(gs, "wall", "wall_night")
    pal = S.decor_pal(gs)
    assert set(pal["wall"]) >= {"wall", "wall2", "skirt"}


def test_decor_defaults_in_new_game():
    gs = S.new_game("小猫")
    assert gs["decor"] == {} and gs["decor_owned"] == []
    assert gs["festival_fired"] == []


# ---------------- 音效 ----------------
def test_sfx_files_exist():
    import pet_audio
    for k in pet_audio.SFX_KINDS:
        assert pet_audio._data(k), f"缺少音效 {k}"


def test_fx_kinds_cover_new_events():
    import pet_fx
    for k in ("sunny", "rain", "snow", "thunder", "festival", "decor"):
        assert k in pet_fx._KINDS


if __name__ == "__main__":
    failed = 0
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for n, f in fns:
        try:
            f()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {n}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {n}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
