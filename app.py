from flask import Flask, render_template, redirect, url_for
import random, json, os

app = Flask(__name__)

SAVE_FILE = "save.json"

# =====================
# 플레이어
# =====================
player = {
    "hp": 100,
    "max_hp": 100,
    "mp": 50,
    "max_mp": 50,
    "atk": 10,
    "def": 5,
    "gold": 100,
    "ult_ready": False
}

# =====================
# 몬스터
# =====================
MONSTERS = [
    {"name": "🕷 섀도우 스파이더", "hp": 70, "atk": (8, 14)},
    {"name": "🧟 폐허의 망령", "hp": 90, "atk": (10, 16)},
    {"name": "🦂 사막 스콜피온", "hp": 80, "atk": (9, 15)},
    {"name": "🦴 고대 해골 전사", "hp": 110, "atk": (12, 18)}
]

MID_BOSS = {"name": "👑 공허의 수호자", "hp": 180, "atk": (18, 26)}

monster = None
state = "menu"
log_msg = "메뉴"

# =====================
# 유틸
# =====================
def spawn_monster():
    global monster, log_msg
    base = MID_BOSS if random.random() < 0.2 else random.choice(MONSTERS)
    monster = base.copy()
    monster["max_hp"] = monster["hp"]
    log_msg = f"{monster['name']} 등장!"

def counter_attack():
    global state, log_msg
    dmg = max(0, random.randint(*monster["atk"]) - player["def"])
    player["hp"] -= dmg
    log_msg = f"👾 반격! {dmg} 피해"

    if player["hp"] <= 0:
        player["hp"] = 0
        state = "menu"
        log_msg = "💀 쓰러졌다… 메뉴로 복귀"

    if random.random() < 0.3:
        player["ult_ready"] = True
        log_msg += " | ⚡ 궁극기 준비!"

# =====================
# 라우트
# =====================
@app.route("/")
def index():
    return render_template(
        "index.html",
        player=player,
        monster=monster,
        state=state,
        log=log_msg
    )

@app.route("/battle")
def battle():
    global state
    state = "battle"
    spawn_monster()
    return redirect(url_for("index"))

@app.route("/attack/<mode>")
def attack(mode):
    global log_msg, state

    if not monster:
        return redirect(url_for("index"))

    if mode == "normal":
        dmg = random.randint(8, 14)
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
    log_msg = f"💥 {mode} 공격! {dmg} 데미지"

    if monster["hp"] <= 0:
        reward = random.randint(30, 60)
        player["gold"] += reward
        state = "menu"
        log_msg = f"🏆 승리! GOLD +{reward}"
    else:
        counter_attack()

    return redirect(url_for("index"))

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
    app.run(debug=True)
