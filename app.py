from flask import Flask, render_template, redirect, url_for
import random, json, os

app = Flask(__name__)

SAVE_FILE = "save.json"

# =====================
# 무기 / 방어구 정의
# =====================
WEAPONS = {
    "기본 검": {"atk": 0},
    "강철 검": {"atk": 5},
    "화염 검": {"atk": 10, "effect": "burn"},
    "얼음 검": {"atk": 8, "effect": "freeze"}
}

ARMORS = {
    "천 갑옷": {"def": 0},
    "철 갑옷": {"def": 4}
}

# =====================
# 플레이어
# =====================
player = {
    "hp": 100,
    "max_hp": 100,
    "mp": 50,
    "max_mp": 50,
    "base_atk": 10,
    "base_def": 5,
    "gold": 100,
    "ult_ready": False,
    "inventory": {"potion": 2},
    "weapon": "기본 검",
    "armor": "천 갑옷"
}

# =====================
# 상점
# =====================
SHOP_ITEMS = {
    "potion": {"name": "🧪 포션", "price": 15},
    "sword": {"name": "강철 검", "price": 80},
    "fire_sword": {"name": "화염 검", "price": 150},
    "ice_sword": {"name": "얼음 검", "price": 130},
    "armor": {"name": "철 갑옷", "price": 70}
}

# =====================
# 몬스터
# =====================
MONSTERS = [
    {"name": "🕷 섀도우 스파이더", "hp": 70, "atk": (8, 14)},
    {"name": "🧟 폐허의 망령", "hp": 90, "atk": (10, 16)},
    {"name": "🦂 사막 스콜피온", "hp": 80, "atk": (9, 15)}
]

MID_BOSS = {"name": "👑 공허의 수호자", "hp": 180, "atk": (18, 26)}

monster = None
state = "menu"
log_msg = "메뉴"

# =====================
# 유틸
# =====================
def player_atk():
    return player["base_atk"] + WEAPONS[player["weapon"]]["atk"]

def player_def():
    return player["base_def"] + ARMORS[player["armor"]]["def"]

def spawn_monster():
    global monster, log_msg
    base = MID_BOSS if random.random() < 0.2 else random.choice(MONSTERS)
    monster = base.copy()
    monster["max_hp"] = monster["hp"]
    monster["effects"] = {}
    log_msg = f"{monster['name']} 등장!"

def apply_weapon_effect():
    effect = WEAPONS[player["weapon"]].get("effect")
    if effect == "burn":
        monster["effects"]["burn"] = 3
        return "🔥 화염! 3턴 도트딜"
    if effect == "freeze":
        monster["effects"]["freeze"] = 2
        return "❄ 빙결! 공격력 감소"
    return ""

def apply_monster_effects():
    msg = ""
    if "burn" in monster["effects"]:
        monster["hp"] -= 5
        monster["effects"]["burn"] -= 1
        msg += " 🔥 불타며 5 피해"
        if monster["effects"]["burn"] <= 0:
            del monster["effects"]["burn"]
    return msg

def counter_attack():
    global state, log_msg

    effect_msg = apply_monster_effects()

    atk_min, atk_max = monster["atk"]
    if "freeze" in monster["effects"]:
        atk_min = max(1, atk_min - 4)
        atk_max = max(2, atk_max - 4)
        monster["effects"]["freeze"] -= 1
        effect_msg += " ❄ 공격력 감소"
        if monster["effects"]["freeze"] <= 0:
            del monster["effects"]["freeze"]

    dmg = max(0, random.randint(atk_min, atk_max) - player_def())
    player["hp"] -= dmg

    log_msg += effect_msg + f" 👾 반격! {dmg} 피해"

    if player["hp"] <= 0:
        player["hp"] = 0
        state = "menu"
        log_msg = "💀 쓰러졌다… 메뉴로 복귀"

def use_potion():
    if player["inventory"]["potion"] <= 0:
        return "❌ 포션이 없다"
    player["inventory"]["potion"] -= 1
    player["hp"] = min(player["hp"] + 40, player["max_hp"])
    return "🧪 포션 사용!"

def buy_item(key):
    if key not in SHOP_ITEMS:
        return "❌ 없는 아이템"

    item = SHOP_ITEMS[key]
    if player["gold"] < item["price"]:
        return "💰 골드 부족"

    player["gold"] -= item["price"]

    if key == "potion":
        player["inventory"]["potion"] += 1
    elif key == "sword":
        player["weapon"] = "강철 검"
    elif key == "fire_sword":
        player["weapon"] = "화염 검"
    elif key == "ice_sword":
        player["weapon"] = "얼음 검"
    elif key == "armor":
        player["armor"] = "철 갑옷"

    return f"✅ {item['name']} 구매 완료!"

# =====================
# 라우트
# =====================
@app.route("/")
def index():
    return render_template("index.html", player=player, monster=monster, state=state, log=log_msg)

@app.route("/battle")
def battle():
    global state
    state = "battle"
    spawn_monster()
    return redirect(url_for("index"))

@app.route("/attack/<mode>")
def attack(mode):
    global log_msg, state

    if mode == "normal":
        dmg = random.randint(5, 10) + player_atk()
    elif mode == "skill" and player["mp"] >= 10:
        player["mp"] -= 10
        dmg = random.randint(15, 25)
    elif mode == "ult" and player["ult_ready"]:
        player["ult_ready"] = False
        dmg = random.randint(40, 60)
    else:
        log_msg = "❌ 사용할 수 없음"
        return redirect(url_for("index"))

    monster["hp"] -= dmg
    log_msg = f"💥 공격! {dmg} 피해"

    effect_msg = apply_weapon_effect()
    if effect_msg:
        log_msg += " " + effect_msg

    if monster["hp"] <= 0:
        gold = random.randint(30, 60)
        player["gold"] += gold
        state = "menu"
        log_msg = f"🏆 승리! GOLD +{gold}"
    else:
        counter_attack()

    return redirect(url_for("index"))

@app.route("/use_potion")
def potion():
    global log_msg
    log_msg = use_potion()
    return redirect(url_for("index"))

@app.route("/shop")
def shop():
    global state
    state = "shop"
    return redirect(url_for("index"))

@app.route("/menu")
def menu():
    global state
    state = "menu"
    return redirect(url_for("index"))

@app.route("/buy/<item>")
def buy(item):
    global log_msg
    log_msg = buy_item(item)
    return redirect(url_for("shop"))

@app.route("/save")
def save():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(player, f, ensure_ascii=False)
    return redirect(url_for("index"))

@app.route("/load")
def load():
    global player
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            player = json.load(f)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
