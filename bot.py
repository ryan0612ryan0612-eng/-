import os
import random
import time
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

ONE_HOUR_SEC = 3600
FOUR_HOUR_SEC = 4 * ONE_HOUR_SEC
TWELVE_HOUR_SEC = 12 * ONE_HOUR_SEC
WARD_PRICE = 120
MAX_BREAK_BONUS = 0.45

MONGO_URI = os.environ.get("MONGO_URI", "")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

client = MongoClient(MONGO_URI) if MONGO_URI else None
players_col = client["shenqi_db"]["players"] if client else None

# ========================
# 1. 修仙境界（上下界 20 境）
# ========================
REALMS = [
    # 下界（0 ~ 9）
    {"name": "星啟境", "tier": "下界", "req_exp": 120, "power": 10, "success": 0.90, "fall_rate": 0.02},
    {"name": "開宇境", "tier": "下界", "req_exp": 350, "power": 25, "success": 0.83, "fall_rate": 0.04},
    {"name": "蛻骸境", "tier": "下界", "req_exp": 900, "power": 55, "success": 0.76, "fall_rate": 0.06},
    {"name": "淵輪境", "tier": "下界", "req_exp": 2200, "power": 110, "success": 0.69, "fall_rate": 0.08},
    {"name": "道種境", "tier": "下界", "req_exp": 5500, "power": 220, "success": 0.62, "fall_rate": 0.11},
    {"name": "神藏境", "tier": "下界", "req_exp": 13000, "power": 420, "success": 0.55, "fall_rate": 0.14},
    {"name": "空神境", "tier": "下界", "req_exp": 30000, "power": 800, "success": 0.48, "fall_rate": 0.18},
    {"name": "瀚海境", "tier": "下界", "req_exp": 70000, "power": 1500, "success": 0.41, "fall_rate": 0.22},
    {"name": "天寂境", "tier": "下界", "req_exp": 160000, "power": 2800, "success": 0.34, "fall_rate": 0.26},
    {"name": "逆劫境", "tier": "下界", "req_exp": 360000, "power": 5000, "success": 0.28, "fall_rate": 0.32},
    # 上界（10 ~ 19）
    {"name": "斬我境", "tier": "上界", "req_exp": 800000, "power": 9000, "success": 0.25, "fall_rate": 0.36},
    {"name": "玄胎境", "tier": "上界", "req_exp": 1700000, "power": 16000, "success": 0.22, "fall_rate": 0.40},
    {"name": "法相境", "tier": "上界", "req_exp": 3500000, "power": 28000, "success": 0.20, "fall_rate": 0.45},
    {"name": "裂空境", "tier": "上界", "req_exp": 7000000, "power": 48000, "success": 0.18, "fall_rate": 0.50},
    {"name": "界域境", "tier": "上界", "req_exp": 14000000, "power": 82000, "success": 0.16, "fall_rate": 0.55},
    {"name": "司命境", "tier": "上界", "req_exp": 28000000, "power": 140000, "success": 0.14, "fall_rate": 0.60},
    {"name": "朔時境", "tier": "上界", "req_exp": 55000000, "power": 240000, "success": 0.12, "fall_rate": 0.65},
    {"name": "掌律境", "tier": "上界", "req_exp": 105000000, "power": 410000, "success": 0.10, "fall_rate": 0.70},
    {"name": "震天境", "tier": "上界", "req_exp": 200000000, "power": 700000, "success": 0.08, "fall_rate": 0.76},
    {"name": "窺仙境", "tier": "上界", "req_exp": 999999999, "power": 1200000, "success": 0.06, "fall_rate": 0.82},
]

# 功法（決定每小時基礎修為與功法戰力）
MANUALS = {
    "star_breath": {"name": "星引吐納訣", "price": 0, "hourly": 30, "power": 5},
    "open_cosmos": {"name": "開宇凝神經", "price": 150, "hourly": 110, "power": 20},
    "molt_nine": {"name": "蛻骸九轉功", "price": 480, "hourly": 320, "power": 60},
    "abyss_wheel": {"name": "淵輪道藏篇", "price": 1600, "hourly": 900, "power": 180},
    "god_store": {"name": "神藏太虛引", "price": 5200, "hourly": 2600, "power": 500},
    "reverse_chaos": {"name": "逆劫混沌訣", "price": 18000, "hourly": 7500, "power": 1400},
    "sever_self": {"name": "斬我太初經", "price": 120000, "hourly": 38000, "power": 12000},
    "law_sovereign": {"name": "掌律窺仙典", "price": 1500000, "hourly": 300000, "power": 180000},
}

# 100 種靈根（決定每小時修為倍率與靈根戰力）
ROOT_ELEMENTS = ["金", "木", "水", "火", "土", "風", "雷", "冰", "星", "混沌"]
ROOT_GRADES = ["凡品", "靈品", "玄品", "地品", "天品", "聖品", "仙品", "帝品", "神品", "無極"]
SPIRIT_ROOTS = []
for i in range(100):
    elem = ROOT_ELEMENTS[i % len(ROOT_ELEMENTS)]
    grade = ROOT_GRADES[i // 10]
    SPIRIT_ROOTS.append({
        "id": i + 1,
        "name": f"{grade}{elem}靈根",
        "power_bonus": (i + 1) * 12,
        "exp_mult": round(1.0 + (i + 1) * 0.025, 4),
    })

# 100 種天賦
TALENT_PREFIXES = ["道心", "劍意", "煉體", "悟道", "聚靈", "鎮魔", "禦風", "踏虛", "神識", "天機"]
TALENT_SUFFIXES = ["如淵", "通明", "不滅", "天成", "歸一", "破妄", "凌霄", "逆命", "超凡", "太初"]
TALENTS = []
for i in range(100):
    pre = TALENT_PREFIXES[i % len(TALENT_PREFIXES)]
    suf = TALENT_SUFFIXES[i // 10]
    TALENTS.append({
        "id": i + 1,
        "name": f"{pre}{suf}天賦",
        "power_bonus": (i + 1) * 10,
        "break_bonus": round(min(0.15, (i + 1) * 0.0015), 4),
    })

# ========================
# 2. 副本獨立職業、衍生職業、隱藏職業與專屬技能
# ========================
JOBS = {
    "初心修士": {
        "tier": 0,
        "req_lv": 1,
        "parent": None,
        "power_mult": 1.0,
        "break_bonus": 0.0,
        "desc": "尚未轉職的初學者（副本等級達 30 級可轉職）。",
        "skills": [
            {"name": "靈氣彈", "mult": 1.15, "desc": "凝聚基礎靈力攻擊"},
            {"name": "護體微光", "mult": 1.25, "desc": "小幅提升攻防"},
        ],
    },
    # 基礎五大職業（Lv.30 轉職）
    "正道": {
        "tier": 1,
        "req_lv": 30,
        "parent": "初心修士",
        "power_mult": 1.12,
        "break_bonus": 0.04,
        "desc": "浩然正氣護體，渡劫成功率 +4%，技能穩健。",
        "skills": [
            {"name": "浩然正氣斬", "mult": 1.35, "desc": "正氣凛然破除邪祟"},
            {"name": "清心鎮魔印", "mult": 1.55, "desc": "鎮壓妖邪並穩固心神"},
            {"name": "天地正法", "mult": 1.80, "desc": "引動正道法理重創敵首"},
        ],
    },
    "魔修": {
        "tier": 1,
        "req_lv": 30,
        "parent": "初心修士",
        "power_mult": 1.24,
        "break_bonus": -0.02,
        "desc": "吞噬煞氣爆發極高，副本掠奪靈石加成，渡劫風險略增。",
        "skills": [
            {"name": "嗜血魔爪", "mult": 1.45, "desc": "撕裂敵陣並吸取煞氣"},
            {"name": "萬魂噬心陣", "mult": 1.70, "desc": "怨魂纏身造成高額傷害"},
            {"name": "天魔解體大法", "mult": 2.05, "desc": "燃燒魔元換取毀滅一擊"},
        ],
    },
    "散修": {
        "tier": 1,
        "req_lv": 30,
        "parent": "初心修士",
        "power_mult": 1.10,
        "break_bonus": 0.02,
        "desc": "機緣深厚不拘一格，副本掉落藥材與裝備機率提升。",
        "skills": [
            {"name": "百家雜學術", "mult": 1.30, "desc": "信手拈來各派術法"},
            {"name": "踏風遁影步", "mult": 1.50, "desc": "身法靈動出奇制勝"},
            {"name": "紅塵萬象訣", "mult": 1.78, "desc": "融匯百藝打出奇襲"},
        ],
    },
    "體修": {
        "tier": 1,
        "req_lv": 30,
        "parent": "初心修士",
        "power_mult": 1.28,
        "break_bonus": 0.03,
        "desc": "肉身成聖氣血如海，基礎戰力極高且副本不易失手。",
        "skills": [
            {"name": "搬山崩拳", "mult": 1.40, "desc": "純粹肉身巨力正面轟擊"},
            {"name": "金剛不壞身", "mult": 1.60, "desc": "氣血沸騰硬撼強敵"},
            {"name": "荒古聖體震", "mult": 1.92, "desc": "肉身極境震碎虛空"},
        ],
    },
    "劍修": {
        "tier": 1,
        "req_lv": 30,
        "parent": "初心修士",
        "power_mult": 1.26,
        "break_bonus": 0.0,
        "desc": "一劍破萬法，單體輸出與暴擊穿透力最強。",
        "skills": [
            {"name": "流光御劍術", "mult": 1.45, "desc": "飛劍破空疾刺要害"},
            {"name": "萬劍歸宗", "mult": 1.75, "desc": "劍氣化雨覆蓋戰場"},
            {"name": "一劍開天門", "mult": 2.10, "desc": "凝聚畢生劍意斬斷一切"},
        ],
    },
    # 衍生進階職業（Lv.60 進階）
    "太上道尊": {
        "tier": 2,
        "req_lv": 60,
        "parent": "正道",
        "power_mult": 1.35,
        "break_bonus": 0.07,
        "desc": "【正道衍生】執掌天道正統，渡劫 +7% 且神通威能大增。",
        "skills": [
            {"name": "太上紫霄雷", "mult": 1.75, "desc": "引九天神雷誅滅萬邪"},
            {"name": "乾坤定界圖", "mult": 2.05, "desc": "展開道圖鎮封四方"},
            {"name": "大道無極頌", "mult": 2.45, "desc": "化身天道代行者施展絕殺"},
        ],
    },
    "九幽魔帝": {
        "tier": 2,
        "req_lv": 60,
        "parent": "魔修",
        "power_mult": 1.52,
        "break_bonus": -0.01,
        "desc": "【魔修衍生】統御九幽魔域，毀滅性輸出無人能擋。",
        "skills": [
            {"name": "九幽冥火海", "mult": 1.90, "desc": "冥火焚盡萬物生機"},
            {"name": "修羅滅世輪", "mult": 2.25, "desc": "召喚修羅魔輪碾碎敵軍"},
            {"name": "吞天魔域", "mult": 2.75, "desc": "展開魔域吞噬敵首本源"},
        ],
    },
    "逍遙真仙": {
        "tier": 2,
        "req_lv": 60,
        "parent": "散修",
        "power_mult": 1.34,
        "break_bonus": 0.05,
        "desc": "【散修衍生】超脫紅塵束縛，掉寶率與奇遇大幅躍升。",
        "skills": [
            {"name": "星河倒掛", "mult": 1.72, "desc": "借星辰之力隨意揮灑"},
            {"name": "大夢千秋術", "mult": 2.05, "desc": "神識入夢瓦解敵方戰意"},
            {"name": "逍遙遊天訣", "mult": 2.48, "desc": "無跡可尋的絕世仙術"},
        ],
    },
    "不滅武祖": {
        "tier": 2,
        "req_lv": 60,
        "parent": "體修",
        "power_mult": 1.56,
        "break_bonus": 0.05,
        "desc": "【體修衍生】滴血重生萬劫不磨，戰力加成冠絕同階。",
        "skills": [
            {"name": "崩星神拳", "mult": 1.85, "desc": "一拳之力足以碎裂星辰"},
            {"name": "不滅金身訣", "mult": 2.15, "desc": "萬法不侵反震強敵"},
            {"name": "開天闢地式", "mult": 2.65, "desc": "以力證道打出開天一擊"},
        ],
    },
    "無上劍仙": {
        "tier": 2,
        "req_lv": 60,
        "parent": "劍修",
        "power_mult": 1.54,
        "break_bonus": 0.02,
        "desc": "【劍修衍生】人劍合一念動即斬，極致攻伐之巔。",
        "skills": [
            {"name": "誅仙四劍陣", "mult": 1.92, "desc": "四道絕世劍氣封鎖天地"},
            {"name": "太虛無形劍", "mult": 2.28, "desc": "無聲無息斬滅神魂"},
            {"name": "劍道永恆", "mult": 2.80, "desc": "萬古劍意匯聚於一鋒"},
        ],
    },
    # 隱藏職業（需擁有「混沌轉職令」或通關高階副本機率領悟）
    "混沌神魔": {
        "tier": 3,
        "req_lv": 45,
        "parent": "HIDDEN",
        "power_mult": 1.75,
        "break_bonus": 0.08,
        "desc": "【隱藏職業】仙魔同修執掌混沌本源，全屬性與技能倍率極度逆天。",
        "skills": [
            {"name": "混沌青蓮爆", "mult": 2.20, "desc": "演化混沌青蓮炸裂虛空"},
            {"name": "陰陽逆亂劫", "mult": 2.65, "desc": "顛倒乾坤法則重創一切"},
            {"name": "鴻蒙歸墟滅", "mult": 3.20, "desc": "重演地水火風，萬物歸於混沌"},
        ],
    },
    "輪迴守墓人": {
        "tier": 3,
        "req_lv": 45,
        "parent": "HIDDEN",
        "power_mult": 1.68,
        "break_bonus": 0.10,
        "desc": "【隱藏職業】執掌六道輪迴生死簿，渡劫 +10% 且掉落極品裝備機率暴增。",
        "skills": [
            {"name": "黃泉引渡燈", "mult": 2.15, "desc": "幽冥燈火灼燒敵方魂魄"},
            {"name": "六道輪迴盤", "mult": 2.55, "desc": "轉動輪迴磨盤碾壓強敵"},
            {"name": "葬天埋仙棺", "mult": 3.10, "desc": "鎮壓諸天仙魔永世不得超生"},
        ],
    },
}

# ========================
# 3. 十階裝備系統（創世 > 永劫 > 輪迴 > 燦星 > 遠古 > 幻想 > 史詩 > 稀有 > 一般 > 凡物）
# ========================
EQUIP_GRADES = [
    {"name": "凡物", "mult": 1, "price": 80},
    {"name": "一般", "mult": 3, "price": 250},
    {"name": "稀有", "mult": 8, "price": 800},
    {"name": "史詩", "mult": 22, "price": 2600},
    {"name": "幻想", "mult": 60, "price": 8500},
    {"name": "遠古", "mult": 160, "price": 28000},
    {"name": "燦星", "mult": 450, "price": 95000},
    {"name": "輪迴", "mult": 1300, "price": 320000},
    {"name": "永劫", "mult": 3800, "price": 1100000},
    {"name": "創世", "mult": 12000, "price": 4000000},
]

EQUIP_SLOTS = {
    "武器": {"base_power": 15, "suffix": "神兵"},
    "護甲": {"base_power": 12, "suffix": "戰鎧"},
    "護符": {"base_power": 10, "suffix": "道符"},
}

EQUIPMENTS: dict[str, dict] = {}
for g_idx, g in enumerate(EQUIP_GRADES):
    for slot_name, s_info in EQUIP_SLOTS.items():
        eq_id = f"eq_{g_idx + 1:02d}_{slot_name}"
        eq_name = f"【{g['name']}】{slot_name}·{s_info['suffix']}"
        EQUIPMENTS[eq_name] = {
            "id": eq_id,
            "name": eq_name,
            "slot": slot_name,
            "grade": g["name"],
            "grade_idx": g_idx,
            "power": s_info["base_power"] * g["mult"],
            "price": g["price"],
        }

# ========================
# 4. 千種藥材與千種丹方
# ========================
HERB_PREFIXES = ["青靈", "赤炎", "玄冰", "紫霄", "九葉", "太初", "星髓", "幽冥", "金龍", "混沌"]
HERB_FORMS = ["草", "果", "芝", "參", "蓮", "花", "根", "藤", "露", "晶"]
HERBS = [
    f"{HERB_PREFIXES[i % len(HERB_PREFIXES)]}{HERB_FORMS[(i // 10) % len(HERB_FORMS)]}·{i + 1:03d}"
    for i in range(1000)
]

PILL_PREFIXES = ["培元", "聚靈", "破境", "固本", "洗髓", "凝神", "斬厄", "歸真", "化道", "造化"]
PILL_TYPES = ["丹", "丸", "散", "液", "露", "膏", "魄", "髓", "胎", "劫丹"]
RECIPES = {}
for i in range(1, 1001):
    recipe_id = f"recipe_{i:04d}"
    pill_name = f"{PILL_PREFIXES[i % len(PILL_PREFIXES)]}{PILL_TYPES[(i // 10) % len(PILL_TYPES)]}方·{i:03d}"
    tier = min(10, (i - 1) // 100 + 1)
    herb_idx = (i * 7) % len(HERBS)
    RECIPES[recipe_id] = {
        "id": recipe_id,
        "name": pill_name,
        "tier": tier,
        "price": tier * 180 + i * 5,
        "herb": HERBS[herb_idx],
        "herb_qty": 2 + (tier // 2),
        "bonus_gain": round(0.01 + tier * 0.005, 4),
        "exp_gain": tier * 150,
    }


def tier_herbs(tier_idx: int) -> list[str]:
    start = max(0, min(900, tier_idx * 50))
    return HERBS[start : start + 50]


def tier_recipes(tier_idx: int) -> list[str]:
    start = max(1, min(950, tier_idx * 50 + 1))
    end = min(1000, start + 49)
    return [f"recipe_{idx:04d}" for idx in range(start, end + 1)]


# ========================
# 5. 4h / 12h 歷練 + 4 特殊地 + 混沌之地
# ========================
SPECIAL_ITEMS = {
    "破禁星羅盤": {"name": "破禁星羅盤", "price": 800, "desc": "進入特殊歷練地【星羅古禁】的信物。"},
    "九幽鎮魂印": {"name": "九幽鎮魂印", "price": 4500, "desc": "進入特殊歷練地【九幽鎮魂塔】的信物。"},
    "太虛溯光鏡": {"name": "太虛溯光鏡", "price": 35000, "desc": "進入特殊歷練地【太虛溯光境】的信物。"},
    "天道劫源令": {"name": "天道劫源令", "price": 250000, "desc": "進入特殊歷練地【天道劫源池】的信物。"},
    "混沌轉職令": {"name": "混沌轉職令", "price": 500000, "desc": "持有後可在 /job 轉職為隱藏職業！"},
}

EXPEDITIONS: dict[str, dict] = {}
for idx, r in enumerate(REALMS):
    scale = max(1, (r["power"] // 10))
    place_4h = f"{r['name']}·外圍靈脈"
    place_12h = f"{r['name']}·深處古地"
    h_pool = tier_herbs(idx)
    r_pool = tier_recipes(idx)

    EXPEDITIONS[place_4h] = {
        "kind": "normal_4h",
        "duration": FOUR_HOUR_SEC,
        "req_realm": idx,
        "req_item": None,
        "rec_power": max(10, int(r["power"] * 0.9)),
        "stones": (25 * scale, 55 * scale),
        "exp": (40 * scale, 80 * scale),
        "danger": min(0.65, 0.12 + idx * 0.02),
        "encounter": 0.25,
        "mats": h_pool[:15],
        "recipes": r_pool[:10],
        "mat_qty_range": (1, 1 + idx // 4),
    }
    EXPEDITIONS[place_12h] = {
        "kind": "normal_12h",
        "duration": TWELVE_HOUR_SEC,
        "req_realm": idx,
        "req_item": None,
        "rec_power": max(20, int(r["power"] * 1.4)),
        "stones": (80 * scale, 180 * scale),
        "exp": (140 * scale, 280 * scale),
        "danger": min(0.75, 0.20 + idx * 0.022),
        "encounter": 0.36,
        "mats": h_pool[15:40],
        "recipes": r_pool[10:35],
        "mat_qty_range": (2, 3 + idx // 3),
    }

SPECIAL_SPOTS = [
    ("星羅古禁", 2, "破禁星羅盤", FOUR_HOUR_SEC, 120, HERBS[120:220], [f"recipe_{i:04d}" for i in range(120, 220)]),
    ("九幽鎮魂塔", 6, "九幽鎮魂印", TWELVE_HOUR_SEC, 1200, HERBS[300:450], [f"recipe_{i:04d}" for i in range(300, 450)]),
    ("太虛溯光境", 11, "太虛溯光鏡", FOUR_HOUR_SEC, 25000, HERBS[550:750], [f"recipe_{i:04d}" for i in range(550, 750)]),
    ("天道劫源池", 15, "天道劫源令", TWELVE_HOUR_SEC, 180000, HERBS[750:920], [f"recipe_{i:04d}" for i in range(750, 920)]),
]

for name, req_r, req_item, dur, rec_pwr, mats_list, rec_list in SPECIAL_SPOTS:
    base_s = max(50, rec_pwr * 2)
    base_e = max(100, rec_pwr * 4)
    EXPEDITIONS[name] = {
        "kind": "special",
        "duration": dur,
        "req_realm": req_r,
        "req_item": req_item,
        "rec_power": rec_pwr,
        "stones": (base_s, base_s * 2),
        "exp": (base_e, base_e * 2),
        "danger": 0.30,
        "encounter": 0.45,
        "mats": mats_list,
        "recipes": rec_list,
        "mat_qty_range": (2, 6),
    }

CHAOS_PLACE = "混沌之地"
EXPEDITIONS[CHAOS_PLACE] = {
    "kind": "chaos",
    "duration": TWELVE_HOUR_SEC,
    "req_realm": 0,
    "req_item": None,
    "rec_power": 50000,
    "stones": (500000, 1200000),
    "exp": (2500000, 6000000),
    "danger": 0.35,
    "encounter": 0.60,
    "mats": HERBS[850:1000],
    "recipes": [f"recipe_{i:04d}" for i in range(850, 1001)],
    "mat_qty_range": (4, 10),
}

ALL_REQUIRED_PLACES = [k for k in EXPEDITIONS.keys() if k != CHAOS_PLACE]

# ========================
# 6. 副本關卡（獨立副本等級與怪物）
# ========================
DUNGEONS = {
    "幽冥枯骨林": {"rec_lv": 1, "monster": "枯骨妖將", "hp": 120, "rpg_exp": 45, "stones": (35, 80), "herb_tier": 0, "max_eq_grade": 2},
    "赤焰妖王殿": {"rec_lv": 15, "monster": "赤焰妖王", "hp": 650, "rpg_exp": 140, "stones": (220, 500), "herb_tier": 3, "max_eq_grade": 4},
    "萬象劍冢": {"rec_lv": 30, "monster": "殘魂劍靈", "hp": 3200, "rpg_exp": 320, "stones": (2500, 6000), "herb_tier": 7, "max_eq_grade": 6},
    "上界古神窟": {"rec_lv": 55, "monster": "墮落古神", "hp": 25000, "rpg_exp": 750, "stones": (80000, 180000), "herb_tier": 12, "max_eq_grade": 8},
    "永劫創世淵": {"rec_lv": 80, "monster": "混沌原初獸", "hp": 180000, "rpg_exp": 1600, "stones": (600000, 1500000), "herb_tier": 17, "max_eq_grade": 9},
}

DEFAULT_PLAYER = {
    "realm_idx": 0,
    "exp": 0,
    "stones": 100,
    "break_bonus": 0.0,
    "last_claimed_slot": -1,
    "last_duel_ts": 0.0,
    "last_dungeon_ts": 0.0,
    "rpg_level": 1,
    "rpg_exp": 0,
    "job_name": "初心修士",
    "unlocked_hidden_jobs": [],
    "root_id": 1,
    "talent_id": 1,
    "manual": "star_breath",
    "owned_manuals": ["star_breath"],
    "owned_recipes": ["recipe_0001"],
    "equipped": {"武器": None, "護甲": None, "護符": None},
    "owned_equips": [],
    "power_bonus": 0,
    "wards": 1,
    "items": {},
    "materials": {},
    "visited_places": [],
    "active_expedition": None,
}


def get_root(p: dict) -> dict:
    rid = max(1, min(100, int(p.get("root_id", 1))))
    return SPIRIT_ROOTS[rid - 1]


def get_talent(p: dict) -> dict:
    tid = max(1, min(100, int(p.get("talent_id", 1))))
    return TALENTS[tid - 1]


def get_job_info(p: dict) -> dict:
    return JOBS.get(p.get("job_name", "初心修士"), JOBS["初心修士"])


def rpg_next_lv_exp(lv: int) -> int:
    return 100 + (lv - 1) * 45


def get_player(user_id: int) -> dict:
    if players_col is None:
        raise RuntimeError("尚未設定 MONGO_URI 環境變數，無法連線至雲端資料庫。")

    uid = str(user_id)
    doc = players_col.find_one({"_id": uid})
    if not doc:
        doc = {
            "_id": uid,
            **DEFAULT_PLAYER,
            "root_id": random.randint(1, 100),
            "talent_id": random.randint(1, 100),
            "owned_manuals": ["star_breath"],
            "owned_recipes": ["recipe_0001"],
            "equipped": {"武器": None, "護甲": None, "護符": None},
            "owned_equips": [],
            "unlocked_hidden_jobs": [],
            "items": {},
            "materials": {},
            "visited_places": [],
            "active_expedition": None,
        }
        players_col.insert_one(doc)
    else:
        for k, v in DEFAULT_PLAYER.items():
            if k not in doc:
                doc[k] = v.copy() if isinstance(v, (dict, list)) else v
        doc["realm_idx"] = max(0, min(int(doc.get("realm_idx", 0)), len(REALMS) - 1))
    return doc


def save_player(user_id: int, player_data: dict) -> None:
    if players_col is None:
        return
    uid = str(user_id)
    payload = {k: v for k, v in player_data.items() if k != "_id"}
    players_col.update_one({"_id": uid}, {"$set": payload}, upsert=True)


def hourly_rate(p: dict) -> int:
    """每小時領取修為：只與所修功法與靈根倍率有關"""
    m = MANUALS.get(p["manual"], MANUALS["star_breath"])
    root = get_root(p)
    return max(1, int(m["hourly"] * root["exp_mult"]))


def equip_power(p: dict) -> int:
    eq_map = p.get("equipped", {})
    total = 0
    for slot in ("武器", "護甲", "護符"):
        eq_name = eq_map.get(slot)
        if eq_name and eq_name in EQUIPMENTS:
            total += EQUIPMENTS[eq_name]["power"]
    return total


def total_power(p: dict) -> int:
    m = MANUALS.get(p["manual"], MANUALS["star_breath"])
    r = REALMS[p["realm_idx"]]
    root = get_root(p)
    talent = get_talent(p)
    job = get_job_info(p)
    lv_power = p.get("rpg_level", 1) * 15
    raw = (
        r["power"]
        + m["power"]
        + p.get("power_bonus", 0)
        + root["power_bonus"]
        + talent["power_bonus"]
        + equip_power(p)
        + lv_power
    )
    return max(1, int(raw * job["power_mult"]))


def has_unlocked_chaos(p: dict) -> bool:
    visited = set(p.get("visited_places", []))
    return all(place in visited for place in ALL_REQUIRED_PLACES)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"神啟 Bot（v0.0.6）已上線：{bot.user}")


@bot.tree.command(name="status", description="查看修仙境界、副本等級、職業、裝備、靈根與天賦")
async def status_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    r = REALMS[p["realm_idx"]]
    m = MANUALS.get(p["manual"], MANUALS["star_breath"])
    root = get_root(p)
    talent = get_talent(p)
    slot = int(time.time() // ONE_HOUR_SEC)
    can_claim = p["last_claimed_slot"] < slot
    mins_left = max(1, int((ONE_HOUR_SEC - (time.time() % ONE_HOUR_SEC)) // 60) + 1)

    eq_map = p.get("equipped", {})
    eq_lines = (
        f"武器：{eq_map.get('武器') or '無'}\n"
        f"護甲：{eq_map.get('護甲') or '無'}\n"
        f"護符：{eq_map.get('護符') or '無'}"
    )

    exp_info = "無進行中歷練"
    act = p.get("active_expedition")
    if act:
        rem = int(act["end_ts"] - time.time())
        if rem > 0:
            exp_info = f"【{act['place']}】剩餘 {rem // 3600}時{(rem % 3600) // 60}分"
        else:
            exp_info = f"【{act['place']}】已完成，可用 /collect 領取！"

    rpg_lv = p.get("rpg_level", 1)
    rpg_exp = p.get("rpg_exp", 0)
    req_rpg = rpg_next_lv_exp(rpg_lv)

    embed = discord.Embed(
        title=f"⚔️ {interaction.user.display_name} 的神啟面板",
        color=discord.Color.gold(),
    )
    embed.add_field(name="修仙境界", value=f"{r['tier']} · **{r['name']}**", inline=True)
    embed.add_field(name="修為進度", value=f"{p['exp']} / {r['req_exp']}", inline=True)
    embed.add_field(name="靈石", value=f"{p['stones']} 💎", inline=True)
    embed.add_field(name="副本等級（獨立）", value=f"Lv.**{rpg_lv}** ({rpg_exp}/{req_rpg})", inline=True)
    embed.add_field(name="當前職業", value=f"**{p.get('job_name', '初心修士')}**", inline=True)
    embed.add_field(name="總戰力", value=f"{total_power(p)} ⚔️", inline=True)
    embed.add_field(name="所修功法", value=f"{m['name']}", inline=True)
    embed.add_field(name="靈根（影響每時修為）", value=f"{root['name']} (×{root['exp_mult']})", inline=True)
    embed.add_field(name="天賦", value=f"{talent['name']}", inline=True)
    embed.add_field(name="已穿戴裝備", value=eq_lines, inline=False)
    embed.add_field(name="歷練狀態", value=exp_info, inline=True)
    embed.add_field(
        name="每小時修為（功法×靈根）",
        value=f"可領 +{hourly_rate(p)}" if can_claim else f"+{hourly_rate(p)}/時（{mins_left}分後可領）",
        inline=True,
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="job", description="副本等級達 30 級可轉職，60 級可進階衍生職業或隱藏職業")
@app_commands.describe(action="查看可轉職列表或執行轉職", job_name="要轉職的職業名稱")
@app_commands.choices(
    action=[
        app_commands.Choice(name="查看職業與技能樹", value="list"),
        app_commands.Choice(name="執行轉職 / 進階", value="change"),
    ]
)
async def job_cmd(interaction: discord.Interaction, action: str, job_name: str = ""):
    p = get_player(interaction.user.id)
    lv = p.get("rpg_level", 1)
    cur_job = p.get("job_name", "初心修士")

    if action == "list":
        lines = []
        for j_name, info in JOBS.items():
            if j_name == "初心修士":
                continue
            tag = "【隱藏】" if info["parent"] == "HIDDEN" else f"Lv.{info['req_lv']}"
            sk_names = "、".join(s["name"] for s in info["skills"])
            lines.append(f"• **{j_name}**（{tag}）：{info['desc']}\n  └ 專屬技能：{sk_names}")
        embed = discord.Embed(
            title=f"🎭 轉職神殿（目前副本等級：Lv.{lv}｜職業：{cur_job}）",
            description="\n".join(lines),
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed)
        return

    if job_name not in JOBS or job_name == "初心修士":
        await interaction.response.send_message(
            "❌ 找不到該職業名稱，請先使用 `/job action:查看職業與技能樹` 查看。", ephemeral=True
        )
        return

    target = JOBS[job_name]
    if lv < target["req_lv"]:
        await interaction.response.send_message(
            f"🔒 副本等級不足！轉職【**{job_name}**】需要副本等級 **Lv.{target['req_lv']}**（目前：Lv.{lv}，與修仙境界無關）。",
            ephemeral=True,
        )
        return

    if target["parent"] == "HIDDEN":
        has_token = p.get("items", {}).get("混沌轉職令", 0) > 0
        unlocked = job_name in p.get("unlocked_hidden_jobs", [])
        if not has_token and not unlocked:
            await interaction.response.send_message(
                f"🗝️ 隱藏職業【**{job_name}**】需要持有【**混沌轉職令**】或副本奇遇解鎖才能轉職！",
                ephemeral=True,
            )
            return
        if not unlocked and has_token:
            p["items"]["混沌轉職令"] -= 1
            p.setdefault("unlocked_hidden_jobs", []).append(job_name)
    elif target["tier"] == 2 and cur_job != target["parent"]:
        await interaction.response.send_message(
            f"⚠️ 【**{job_name}**】是【**{target['parent']}**】的衍生進階職業，請先轉職為【**{target['parent']}**】！",
            ephemeral=True,
        )
        return

    p["job_name"] = job_name
    save_player(interaction.user.id, p)
    sk_list = "、".join(s["name"] for s in target["skills"])
    await interaction.response.send_message(
        f"🌟 **轉職成功！** 你已成為【**{job_name}**】！\n習得專屬職業技能：**{sk_list}**"
    )


@bot.tree.command(name="skills", description="查看當前職業的專屬技能組")
async def skills_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    cur_job = p.get("job_name", "初心修士")
    info = get_job_info(p)
    lines = [
        f"**{idx}. {sk['name']}**（傷害倍率 ×{sk['mult']}）：{sk['desc']}"
        for idx, sk in enumerate(info["skills"], start=1)
    ]
    embed = discord.Embed(
        title=f"🔥 【{cur_job}】專屬職業技能組",
        description="\n".join(lines),
        color=discord.Color.red(),
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="equip", description="查看或穿戴裝備（支援武器、護甲、護符；十階品級）")
@app_commands.describe(action="查看已擁有裝備或穿戴指定裝備", equip_name="要穿戴的完整裝備名稱")
@app_commands.choices(
    action=[
        app_commands.Choice(name="查看已擁有裝備", value="list"),
        app_commands.Choice(name="穿戴裝備", value="wear"),
    ]
)
async def equip_cmd(interaction: discord.Interaction, action: str, equip_name: str = ""):
    p = get_player(interaction.user.id)
    owned = p.get("owned_equips", [])
    eq_map = p.get("equipped", {"武器": None, "護甲": None, "護符": None})

    if action == "list":
        cur_text = (
            f"• 武器：{eq_map.get('武器') or '（空）'}\n"
            f"• 護甲：{eq_map.get('護甲') or '（空）'}\n"
            f"• 護符：{eq_map.get('護符') or '（空）'}"
        )
        inv_lines = [
            f"• **{name}**（{EQUIPMENTS[name]['slot']}｜戰力 +{EQUIPMENTS[name]['power']}）"
            for name in owned
            if name in EQUIPMENTS
        ]
        embed = discord.Embed(title="🛡️ 裝備欄與兵器庫", color=discord.Color.dark_gold())
        embed.add_field(name="當前穿戴", value=cur_text, inline=False)
        embed.add_field(
            name="持有裝備（可複製名稱用 /equip 穿戴）",
            value="\n".join(inv_lines[:20]) if inv_lines else "（尚未獲得裝備，可至 /shop 或 /dungeon 獲取）",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)
        return

    if equip_name not in EQUIPMENTS:
        await interaction.response.send_message(
            "❌ 找不到該裝備名稱，請先用 `/equip action:查看已擁有裝備` 複製正確名稱。",
            ephemeral=True,
        )
        return
    if equip_name not in owned:
        await interaction.response.send_message(
            f"⚠️ 你尚未持有【**{equip_name}**】！", ephemeral=True
        )
        return

    info = EQUIPMENTS[equip_name]
    slot = info["slot"]
    eq_map[slot] = equip_name
    p["equipped"] = eq_map
    save_player(interaction.user.id, p)
    await interaction.response.send_message(
        f"⚔️ 已在【**{slot}**】欄位裝備【**{equip_name}**】（戰力 **+{info['power']}**）！"
    )


@bot.tree.command(name="dungeon", description="使用職業技能討伐副本怪物，提升獨立副本等級並掉落裝備")
@app_commands.describe(stage="選擇要挑戰的副本")
@app_commands.choices(stage=[app_commands.Choice(name=k, value=k) for k in DUNGEONS.keys()])
async def dungeon_cmd(interaction: discord.Interaction, stage: str):
    p = get_player(interaction.user.id)
    now = time.time()
    rem = int(35 - (now - p.get("last_dungeon_ts", 0.0)))
    if rem > 0:
        await interaction.response.send_message(f"⏳ 副本調息中，請等 **{rem} 秒**。", ephemeral=True)
        return

    dg = DUNGEONS[stage]
    job_name = p.get("job_name", "初心修士")
    job_info = get_job_info(p)
    skill = random.choice(job_info["skills"])

    pwr = total_power(p)
    effective_atk = int(pwr * skill["mult"])
    monster_hp = dg["hp"]

    p["last_dungeon_ts"] = now
    win_prob = max(0.15, min(0.96, (effective_atk / max(1, monster_hp)) * 0.72))

    if random.random() <= win_prob:
        gain_stones = random.randint(*dg["stones"])
        gain_rpg_exp = dg["rpg_exp"]
        herb = random.choice(tier_herbs(dg["herb_tier"]))

        p["stones"] += gain_stones
        p["materials"][herb] = p["materials"].get(herb, 0) + 1
        p["rpg_exp"] = p.get("rpg_exp", 0) + gain_rpg_exp

        # 獨立副本等級升級判定（與修仙境界完全無關）
        lv_up_msg = ""
        while p["rpg_exp"] >= rpg_next_lv_exp(p.get("rpg_level", 1)):
            p["rpg_exp"] -= rpg_next_lv_exp(p["rpg_level"])
            p["rpg_level"] = p.get("rpg_level", 1) + 1
            lv_up_msg = f"\n🎉 **副本等級提升至 Lv.{p['rpg_level']}！**"
            if p["rpg_level"] == 30:
                lv_up_msg += "（已達 **30 級**，可使用 `/job` 轉職！）"

        # 機率掉落裝備（依副本最高品階）
        drop_eq_msg = ""
        if random.random() < 0.35:
            g_idx = random.randint(0, dg["max_eq_grade"])
            slot = random.choice(["武器", "護甲", "護符"])
            g_name = EQUIP_GRADES[g_idx]["name"]
            eq_name = f"【{g_name}】{slot}·{EQUIP_SLOTS[slot]['suffix']}"
            if eq_name not in p.get("owned_equips", []):
                p.setdefault("owned_equips", []).append(eq_name)
                drop_eq_msg = f"\n🎁 掉落新裝備：**{eq_name}**（可用 `/equip` 穿戴）！"

        save_player(interaction.user.id, p)
        await interaction.response.send_message(
            f"⚔️ 【**{job_name}**】施展專屬技能《**{skill['name']}**》（×{skill['mult']}）擊敗【**{dg['monster']}**】！\n"
            f"獲得 **+{gain_rpg_exp}** 副本經驗、**+{gain_stones}** 💎 與藥材【{herb}】×1{lv_up_msg}{drop_eq_msg}"
        )
    else:
        loss_stones = min(p["stones"], max(10, dg["stones"][0] // 3))
        p["stones"] -= loss_stones
        save_player(interaction.user.id, p)
        await interaction.response.send_message(
            f"🛡️ 【**{job_name}**】雖施展《**{skill['name']}**》，仍不敵【**{dg['monster']}**】，撤退損失 **{loss_stones}** 💎。"
        )


@bot.tree.command(name="bag", description="查看儲物袋（藥材、丹方、特殊道具與護身玉符）")
async def bag_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    mats = p.get("materials", {})
    non_zero_mats = [(k, v) for k, v in mats.items() if v > 0]
    if non_zero_mats:
        mats_text = "\n".join(f"• {k} × {v}" for k, v in non_zero_mats[:20])
        if len(non_zero_mats) > 20:
            mats_text += f"\n…另有 {len(non_zero_mats) - 20} 種藥材"
    else:
        mats_text = "（尚無藥材）"

    items = p.get("items", {})
    items_text = "\n".join(f"• **{k}** × {v}" for k, v in items.items() if v > 0) or "（無特殊道具）"

    recipes_count = len(p.get("owned_recipes", []))
    recent_recipes = [
        RECIPES[rid]["name"] for rid in p.get("owned_recipes", [])[-5:] if rid in RECIPES
    ]
    recipes_text = f"共持有 **{recipes_count}** 種丹方（近期：{'、'.join(recent_recipes) if recent_recipes else '無'}）"

    embed = discord.Embed(
        title=f"🎒 {interaction.user.display_name} 的儲物袋",
        color=discord.Color.blue(),
    )
    embed.add_field(name="護身玉符", value=f"{p.get('wards', 0)} 枚", inline=True)
    embed.add_field(name="突破加成", value=f"+{int(p.get('break_bonus', 0.0) * 100)}%", inline=True)
    embed.add_field(name="特殊道具", value=items_text, inline=False)
    embed.add_field(name="已得丹方", value=recipes_text, inline=False)
    embed.add_field(name="秘境藥材", value=mats_text, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="explore", description="派遣出發歷練（需等待 4 小時或 12 小時後用 /collect 領取）")
@app_commands.describe(place="選擇歷練地點（包含 4h/12h 境界地、特殊道具地、混沌之地）")
async def explore_cmd(interaction: discord.Interaction, place: str):
    p = get_player(interaction.user.id)
    if p.get("active_expedition"):
        act = p["active_expedition"]
        rem = max(0, int(act["end_ts"] - time.time()))
        await interaction.response.send_message(
            f"⏳ 你目前正在【**{act['place']}**】歷練中，剩餘 **{rem // 3600} 小時 {(rem % 3600) // 60} 分**，請到期後使用 `/collect` 領取。",
            ephemeral=True,
        )
        return

    if place not in EXPEDITIONS:
        sample = "、".join(list(EXPEDITIONS.keys())[:6])
        await interaction.response.send_message(
            f"❌ 找不到地點「{place}」。例如：{sample}、{CHAOS_PLACE}。",
            ephemeral=True,
        )
        return

    spot = EXPEDITIONS[place]
    if spot["kind"] == "chaos":
        if not has_unlocked_chaos(p):
            visited_count = len(set(p.get("visited_places", [])) & set(ALL_REQUIRED_PLACES))
            await interaction.response.send_message(
                f"🌀 【**{CHAOS_PLACE}**】尚未開啟！需完成所有歷練地各至少 1 次（目前進度：{visited_count}/{len(ALL_REQUIRED_PLACES)}）。",
                ephemeral=True,
            )
            return
    else:
        if p["realm_idx"] < spot["req_realm"]:
            req_name = REALMS[spot["req_realm"]]["name"]
            await interaction.response.send_message(
                f"🔒 境界不足！需達【**{req_name}**】才能前往「{place}」。",
                ephemeral=True,
            )
            return
        req_item = spot.get("req_item")
        if req_item:
            have_item = p.get("items", {}).get(req_item, 0)
            if have_item < 1:
                await interaction.response.send_message(
                    f"🗝️ 缺少特殊道具【**{req_item}**】！可至 `/shop` 萬寶閣購買。",
                    ephemeral=True,
                )
                return
            p["items"][req_item] = have_item - 1

    now = time.time()
    dur = spot["duration"]
    p["active_expedition"] = {
        "place": place,
        "start_ts": now,
        "end_ts": now + dur,
    }
    save_player(interaction.user.id, p)
    await interaction.response.send_message(
        f"🧭 你已踏入【**{place}**】，預計歷練 **{dur // 3600} 小時**。時間到後請使用 `/collect` 領取獎勵！"
    )


@bot.tree.command(name="collect", description="領取已完成（4h / 12h）的歷練獎勵")
async def collect_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    act = p.get("active_expedition")
    if not act:
        await interaction.response.send_message("⚠️ 你目前沒有進行中的歷練。", ephemeral=True)
        return

    now = time.time()
    if now < act["end_ts"]:
        rem = int(act["end_ts"] - now)
        await interaction.response.send_message(
            f"⏳ 歷練尚未完成！還需等待 **{rem // 3600} 小時 {(rem % 3600) // 60} 分**。",
            ephemeral=True,
        )
        return

    place = act["place"]
    spot = EXPEDITIONS.get(place, list(EXPEDITIONS.values())[0])
    p["active_expedition"] = None

    visited = set(p.get("visited_places", []))
    visited.add(place)
    p["visited_places"] = list(visited)

    ratio = min(1.5, total_power(p) / max(1, spot["rec_power"]))
    eff_danger = max(0.05, spot["danger"] - (ratio - 1) * 0.10)
    eff_enc = min(0.75, spot["encounter"] + (ratio - 1) * 0.10)

    base_stones = random.randint(*spot["stones"])
    base_exp = random.randint(*spot["exp"])
    min_q, max_q = spot.get("mat_qty_range", (1, 2))
    roll = random.random()

    dropped_recipe_name = None
    if spot.get("recipes") and random.random() < 0.25:
        rid = random.choice(spot["recipes"])
        if rid not in p["owned_recipes"]:
            p["owned_recipes"].append(rid)
            dropped_recipe_name = RECIPES[rid]["name"]

    if roll < eff_danger:
        if p.get("wards", 0) > 0:
            p["wards"] -= 1
            s_exp = int(base_exp * 0.8)
            s_stones = int(base_stones * 0.7)
            p["exp"] += s_exp
            p["stones"] += s_stones
            msg = f"📿 **護身玉符發動！** 完成【**{place}**】歷練，帶回 **+{s_exp}** 修為、**+{s_stones}** 💎。"
        else:
            m_exp = max(10, int(base_exp * 0.3))
            l_stones = min(p["stones"], max(10, int(base_stones * 0.35)))
            p["exp"] += m_exp
            p["stones"] -= l_stones
            msg = f"💀 【**{place}**】歷練遭遇險境，損失 **{l_stones}** 💎，僅獲得 **+{m_exp}** 修為。"
    elif roll < eff_danger + eff_enc:
        herb = random.choice(spot["mats"])
        qty = random.randint(min_q, max_q) + 1
        p["exp"] += base_exp * 2
        p["stones"] += base_stones * 2
        p["materials"][herb] = p["materials"].get(herb, 0) + qty
        msg = (
            f"✨ **天降奇遇！** 完成【**{place}**】歷練，獲得 **+{base_exp * 2}** 修為、"
            f"**+{base_stones * 2}** 💎，並收穫藥材【{herb}】×{qty}！"
        )
    else:
        herb = random.choice(spot["mats"])
        qty = random.randint(min_q, max_q)
        p["exp"] += base_exp
        p["stones"] += base_stones
        p["materials"][herb] = p["materials"].get(herb, 0) + qty
        msg = (
            f"🧭 完成【**{place}**】歷練！獲得 **+{base_exp}** 修為、"
            f"**+{base_stones}** 💎，並收穫藥材【{herb}】×{qty}。"
        )

    if dropped_recipe_name:
        msg += f"\n📜 **額外機緣！** 拾得丹方【**{dropped_recipe_name}**】！"

    save_player(interaction.user.id, p)
    await interaction.response.send_message(msg)


@bot.tree.command(name="shop", description="萬寶閣：購買丹方、十階裝備、護身玉符或特殊道具")
@app_commands.describe(category="選擇商品類別", code="丹方代號、裝備名稱或道具名稱")
@app_commands.choices(
    category=[
        app_commands.Choice(name="查看清單", value="list"),
        app_commands.Choice(name="購買丹方", value="recipe"),
        app_commands.Choice(name="購買裝備", value="equip"),
        app_commands.Choice(name="購買護身玉符", value="ward"),
        app_commands.Choice(name="購買特殊道具", value="item"),
    ]
)
async def shop_cmd(interaction: discord.Interaction, category: str, code: str = ""):
    p = get_player(interaction.user.id)

    if category == "list":
        items_lines = [
            f"• **{v['name']}**（{v['price']} 💎）：{v['desc']}"
            for v in SPECIAL_ITEMS.values()
        ]
        sample_recipes = [
            f"• `{RECIPES[k]['id']}`｜**{RECIPES[k]['name']}**（{RECIPES[k]['price']} 💎，需 {RECIPES[k]['herb']} ×{RECIPES[k]['herb_qty']}）"
            for k in tier_recipes(p["realm_idx"])[:5]
        ]
        sample_equips = [
            f"• **{eq['name']}**（{eq['price']} 💎｜戰力 +{eq['power']}）"
            for eq in list(EQUIPMENTS.values())[:6]
        ]
        embed = discord.Embed(title="🏯 萬寶閣珍品", color=discord.Color.teal())
        embed.add_field(name="特殊信物與轉職令", value="\n".join(items_lines), inline=False)
        embed.add_field(name="十階裝備範例（凡物～創世）", value="\n".join(sample_equips), inline=False)
        embed.add_field(name="本境界推薦丹方（共 1,000 種）", value="\n".join(sample_recipes), inline=False)
        await interaction.response.send_message(embed=embed)
        return

    if category == "ward":
        if p["stones"] < WARD_PRICE:
            await interaction.response.send_message("⚠️ 靈石不足。", ephemeral=True)
            return
        p["stones"] -= WARD_PRICE
        p["wards"] = p.get("wards", 0) + 1
        save_player(interaction.user.id, p)
        await interaction.response.send_message(f"📿 購買了 1 枚護身玉符（現有：{p['wards']} 枚）。")
        return

    if category == "item":
        if code not in SPECIAL_ITEMS:
            await interaction.response.send_message(
                f"❌ 找不到道具「{code}」。可選：{'、'.join(SPECIAL_ITEMS.keys())}",
                ephemeral=True,
            )
            return
        info = SPECIAL_ITEMS[code]
        if p["stones"] < info["price"]:
            await interaction.response.send_message(f"⚠️ 靈石不足（需 {info['price']} 💎）。", ephemeral=True)
            return
        p["stones"] -= info["price"]
        p["items"][code] = p.get("items", {}).get(code, 0) + 1
        save_player(interaction.user.id, p)
        await interaction.response.send_message(f"🗝️ 成功購得【**{info['name']}**】！")
        return

    if category == "equip":
        if code not in EQUIPMENTS:
            await interaction.response.send_message(
                "❌ 找不到該裝備名稱（格式如：`【凡物】武器·神兵` 或 `【創世】護甲·戰鎧`）。",
                ephemeral=True,
            )
            return
        eq = EQUIPMENTS[code]
        if code in p.get("owned_equips", []):
            await interaction.response.send_message(f"🛡️ 你已持有【**{code}**】。", ephemeral=True)
            return
        if p["stones"] < eq["price"]:
            await interaction.response.send_message(f"⚠️ 靈石不足（需 {eq['price']} 💎）。", ephemeral=True)
            return
        p["stones"] -= eq["price"]
        p.setdefault("owned_equips", []).append(code)
        save_player(interaction.user.id, p)
        await interaction.response.send_message(
            f"⚔️ 購得裝備【**{code}**】（戰力 +{eq['power']}），可使用 `/equip` 穿戴！"
        )
        return

    if category == "recipe":
        if code not in RECIPES:
            await interaction.response.send_message(
                "❌ 丹方代號格式為 `recipe_0001` ～ `recipe_1000`。", ephemeral=True
            )
            return
        rec = RECIPES[code]
        if code in p.get("owned_recipes", []):
            await interaction.response.send_message(f"📜 你已擁有丹方【**{rec['name']}**】。", ephemeral=True)
            return
        if p["stones"] < rec["price"]:
            await interaction.response.send_message(f"⚠️ 靈石不足（需 {rec['price']} 💎）。", ephemeral=True)
            return
        p["stones"] -= rec["price"]
        p["owned_recipes"].append(code)
        save_player(interaction.user.id, p)
        await interaction.response.send_message(f"📜 購得丹方【**{rec['name']}**】（`{code}`）！")


@bot.tree.command(name="alchemy", description="消耗已擁有的丹方與對應藥材進行煉丹")
@app_commands.describe(recipe_id="輸入已持有的丹方代號（例如：recipe_0001）")
async def alchemy_cmd(interaction: discord.Interaction, recipe_id: str):
    p = get_player(interaction.user.id)
    if recipe_id not in RECIPES:
        await interaction.response.send_message("❌ 查無此丹方代號。", ephemeral=True)
        return
    if recipe_id not in p.get("owned_recipes", []):
        await interaction.response.send_message("⚠️ 你尚未獲得此丹方。", ephemeral=True)
        return

    rec = RECIPES[recipe_id]
    herb = rec["herb"]
    need_qty = rec["herb_qty"]
    have_qty = p.get("materials", {}).get(herb, 0)
    if have_qty < need_qty:
        await interaction.response.send_message(
            f"⚠️ 藥材不足！煉製【**{rec['name']}**】需要 **{herb} ×{need_qty}**（目前：{have_qty}）。",
            ephemeral=True,
        )
        return

    p["materials"][herb] = have_qty - need_qty
    p["exp"] += rec["exp_gain"]
    p["break_bonus"] = min(MAX_BREAK_BONUS, round(p.get("break_bonus", 0.0) + rec["bonus_gain"], 4))
    save_player(interaction.user.id, p)
    await interaction.response.send_message(
        f"⚗️ 開爐煉成【**{rec['name']}**】！獲得 **+{rec['exp_gain']}** 修為、突破加成升至 **+{int(p['break_bonus'] * 100)}%**！"
    )


@bot.tree.command(name="claim", description="領取本小時修為（依所修功法與靈根計算，過期不保留）")
async def claim_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    slot = int(time.time() // ONE_HOUR_SEC)
    if p["last_claimed_slot"] >= slot:
        mins_left = max(1, int((ONE_HOUR_SEC - (time.time() % ONE_HOUR_SEC)) // 60) + 1)
        await interaction.response.send_message(
            f"⏳ 本小時修為已領取，請於 **{mins_left} 分鐘**後下一整點再領。",
            ephemeral=True,
        )
        return
    gain = hourly_rate(p)
    p["last_claimed_slot"] = slot
    p["exp"] += gain
    save_player(interaction.user.id, p)
    await interaction.response.send_message(
        f"📖 運轉【**{MANUALS[p['manual']]['name']}**】並引動【**{get_root(p)['name']}**】，領取修為 **+{gain}**！"
    )


@bot.tree.command(name="breakthrough", description="衝擊境界突破（境界越高失敗與隕落機率越高）")
async def breakthrough_cmd(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    r = REALMS[p["realm_idx"]]
    talent = get_talent(p)
    job = get_job_info(p)

    if p["realm_idx"] >= len(REALMS) - 1:
        await interaction.response.send_message(f"👑 已達最高境界【**{r['name']}**】！", ephemeral=True)
        return
    if p["exp"] < r["req_exp"]:
        await interaction.response.send_message(
            f"⚠️ 修為不足，需 **{r['req_exp']}**（目前：{p['exp']}）。",
            ephemeral=True,
        )
        return

    chance = max(
        0.02,
        min(0.98, r["success"] + p.get("break_bonus", 0.0) + talent["break_bonus"] + job["break_bonus"]),
    )
    p["break_bonus"] = 0.0

    if random.random() <= chance:
        p["exp"] -= r["req_exp"]
        p["realm_idx"] += 1
        nxt = REALMS[p["realm_idx"]]
        save_player(interaction.user.id, p)
        if r["tier"] == "下界" and nxt["tier"] == "上界":
            msg = f"🌌 **破界飛升！** 跨越下界極限，踏入【**{nxt['tier']} · {nxt['name']}**】！"
        else:
            msg = f"⚡ **渡劫成功！** 晉升為【**{nxt['name']}**】！"
        await interaction.response.send_message(msg)
        return

    fall_chance = max(0.0, min(0.92, r["fall_rate"] - (0.05 if p.get("wards", 0) > 0 else 0.0)))
    if random.random() <= fall_chance:
        if p.get("wards", 0) > 0:
            p["wards"] -= 1
        new_root = SPIRIT_ROOTS[random.randint(0, 99)]
        new_talent = TALENTS[random.randint(0, 99)]
        p["realm_idx"] = 0
        p["exp"] = 0
        p["root_id"] = new_root["id"]
        p["talent_id"] = new_talent["id"]
        save_player(interaction.user.id, p)
        await interaction.response.send_message(
            f"☄️ **天劫反噬，道消隕落！**\n"
            f"境界重歸【**{REALMS[0]['name']}**】，**背包、裝備、副本等級與職業全數保留**。\n"
            f"重抽獲得新靈根：**{new_root['name']}**、新天賦：**{new_talent['name']}**！"
        )
        return

    lost = int(r["req_exp"] * 0.2)
    p["exp"] = max(0, p["exp"] - lost)
    save_player(interaction.user.id, p)
    await interaction.response.send_message(
        f"💥 **突破失敗！** 損失 **{lost}** 點修為（未隕落，靈根與天賦不變）。"
    )


@bot.tree.command(name="manual_buy", description="購買或切換修練功法")
@app_commands.describe(key="功法代號，可先輸入 /manuals 查看")
async def manual_buy_cmd(interaction: discord.Interaction, key: str):
    p = get_player(interaction.user.id)
    if key not in MANUALS:
        await interaction.response.send_message("❌ 找不到該功法代號。", ephemeral=True)
        return
    m = MANUALS[key]
    if key in p["owned_manuals"]:
        p["manual"] = key
        save_player(interaction.user.id, p)
        await interaction.response.send_message(f"📖 已切換修練功法為【**{m['name']}**】！")
        return
    if p["stones"] < m["price"]:
        await interaction.response.send_message(f"⚠️ 靈石不足（需 {m['price']} 💎）。", ephemeral=True)
        return
    p["stones"] -= m["price"]
    p["owned_manuals"].append(key)
    p["manual"] = key
    save_player(interaction.user.id, p)
    await interaction.response.send_message(f"📖 習得並修練【**{m['name']}**】！")


@bot.tree.command(name="manuals", description="查看所有可修練功法")
async def manuals_cmd(interaction: discord.Interaction):
    lines = [
        f"`{k}`｜**{v['name']}**：價格 {v['price']} 💎｜基礎每時 +{v['hourly']}｜戰力 +{v['power']}"
        for k, v in MANUALS.items()
    ]
    await interaction.response.send_message("\n".join(lines))


@bot.tree.command(name="leaderboard", description="查看修仙境界與戰力排行榜")
async def leaderboard_cmd(interaction: discord.Interaction):
    if players_col is None:
        await interaction.response.send_message("雲端資料庫尚未設定。", ephemeral=True)
        return

    all_docs = list(players_col.find({}))
    if not all_docs:
        await interaction.response.send_message("目前尚無修仙者紀錄。", ephemeral=True)
        return

    ranked = []
    for doc in all_docs:
        uid_str = str(doc.get("_id", ""))
        for k, v in DEFAULT_PLAYER.items():
            if k not in doc:
                doc[k] = v.copy() if isinstance(v, (dict, list)) else v
        r_idx = max(0, min(int(doc.get("realm_idx", 0)), len(REALMS) - 1))
        pwr = total_power(doc)
        ranked.append((r_idx, pwr, doc.get("rpg_level", 1), uid_str, REALMS[r_idx], doc.get("job_name", "初心修士")))

    ranked.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    top = ranked[:10]

    lines = [
        f"**#{idx}** <@{uid_str}> — 【{r_info['tier']}·{r_info['name']}】｜Lv.{lv} {j_name}｜戰力 **{pwr}** ⚔️"
        for idx, (_, pwr, lv, uid_str, r_info, j_name) in enumerate(top, start=1)
    ]

    embed = discord.Embed(
        title="🏆 神啟修仙榜",
        description="\n".join(lines),
        color=discord.Color.purple(),
    )
    await interaction.response.send_message(embed=embed)


if not DISCORD_TOKEN:
    raise RuntimeError("尚未設定 DISCORD_TOKEN 環境變數！")

bot.run(DISCORD_TOKEN)