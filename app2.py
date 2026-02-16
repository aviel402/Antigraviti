
import random
import uuid
import time
from collections import deque
from threading import Thread
from flask import Flask, request, redirect, make_response
from jinja2 import Environment, BaseLoader

app = Flask(__name__)
app.secret_key = "rpg_legend_secret"

# --- אופטימיזציה 1: הגדרת התבנית פעם אחת בלבד ---
# במקום render_template_string בכל בקשה, אנחנו טוענים את התבנית לזיכרון פעם אחת.

HTML_TEMPLATE_STR = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPG Legends - Fast Version</title>
    <style>
        body {
            background-color: #1a1a1d; color: #c5c6c7; font-family: 'Segoe UI', Tahoma, sans-serif;
            margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; min-height: 100vh;
        }
        .game-card {
            background: #2b2e31; width: 100%; max-width: 500px; padding: 15px; border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.5); border-top: 4px solid #66fcf1;
        }
        h2 { margin: 5px 0; color: #66fcf1; text-align: center; }
        .stats { display: flex; justify-content: space-between; background: #0b0c10; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px; }
        .hp-container { background: #444; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 2px; }
        .hp-fill { height: 100%; background: #ff4d4d; width: {{ (p.hp / p.max_hp) * 100 }}%; transition: width 0.3s; }
        .scene {
            background-color: #222; height: 150px; border-radius: 8px; margin-bottom: 15px; position: relative;
            display: flex; justify-content: center; align-items: center; font-size: 40px; text-shadow: 0 0 10px black;
        }
        .scene-text { position: absolute; bottom: 5px; font-size: 14px; background: rgba(0,0,0,0.7); padding: 2px 8px; border-radius: 4px; color: white;}
        .logs { background: #111; color: #45a29e; padding: 10px; height: 80px; overflow-y: auto; border-radius: 5px; margin-bottom: 15px; font-size: 13px; font-family: monospace; border: 1px solid #333; }
        .log-line { margin-bottom: 4px; border-bottom: 1px solid #222; }
        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button {
            background: #1f2833; border: 1px solid #45a29e; color: white; padding: 15px;
            font-size: 16px; cursor: pointer; border-radius: 8px; font-weight: bold; transition: 0.1s;
        }
        button:hover { background: #45a29e; color: black; }
        .combat-btn { background: #3e1212; border-color: #ff4d4d; }
        .heal-btn { background: #0f3d0f; border-color: #4dff4d; }
        .shop-btn { background: #3d3d0f; border-color: #ffff4d; }
        a.back-menu { margin-top: 20px; color: #aaa; font-size: 12px; }
    </style>
</head>
<body>
    <div class="game-card">
        <h2>⚔️ ממלכת הצללים 🛡️</h2>
        <div class="stats">
            <div>❤️ {{ p.hp }}/{{ p.max_hp }}<div class="hp-container"><div class="hp-fill"></div></div></div>
            <div>⭐ {{ p.level }}</div>
            <div>💰 {{ p.gold }}</div>
            <div>🧪 {{ p.potions }}</div>
        </div>

        <div class="scene" style="background: {{ bg_color }}">
            {{ emoji_icon }}
            <div class="scene-text">{{ location_name }}</div>
        </div>

        <div class="logs">
            {% for log in p.logs %}
                <div class="log-line">➜ {{ log }}</div>
            {% endfor %}
        </div>

        <div class="actions">
            {% if p.hp <= 0 %}
                <button onclick="window.location.href='/game2/restart'" style="grid-column: span 2; background: red;">☠️ מתת! התחל מחדש</button>
            {% elif p.in_combat %}
                <button class="combat-btn" onclick="window.location.href='/game2/action/attack'">⚔️ התקפה</button>
                <button class="heal-btn" onclick="window.location.href='/game2/action/heal'">🧪 שיקוי</button>
                <button onclick="window.location.href='/game2/action/flee'">🏃 ברח</button>
            {% elif p.location == 'town' %}
                <button onclick="window.location.href='/game2/travel/forest'">🌲 צא ליער (1-3)</button>
                <button style="border-color: red" onclick="window.location.href='/game2/travel/cave'">💀 למערת הבוס</button>
                <button class="shop-btn" onclick="window.location.href='/game2/shop/buy_potion'">🧪 קנה שיקוי (30)</button>
                <button class="shop-btn" onclick="window.location.href='/game2/shop/upgrade_weapon'">⚔️ שדרג נשק (100)</button>
                <button class="heal-btn" onclick="window.location.href='/game2/action/inn'">🏨 פונדק (10)</button>
            {% elif p.location == 'forest' or p.location == 'cave' %}
                <button class="combat-btn" onclick="window.location.href='/game2/action/explore'">🔍 סייר (חפש)</button>
                <button onclick="window.location.href='/game2/travel/town'">🏠 לעיר</button>
            {% endif %}
        </div>
    </div>
    <a href="/" class="back-menu">תפריט ראשי</a>
</body>
</html>
"""

# יצירת סביבת ג'ינג'ה מהירה
jinja_env = Environment(loader=BaseLoader())
game_template = jinja_env.from_string(HTML_TEMPLATE_STR)


# --- מסד נתונים פנימי ---
players = {}

# ניקוי שחקנים לא פעילים (למנוע פיצוץ זיכרון)
def cleanup_inactive_players():
    current_time = time.time()
    inactive_limit = 3600  # שעה אחת
    to_remove = [uid for uid, p in players.items() if current_time - p.last_active > inactive_limit]
    for uid in to_remove:
        del players[uid]

# --- מחלקות המשחק משופרות ---

class Enemy:
    # __slots__ חוסך המון זיכרון ומונע יצירת מילון לכל אובייקט
    __slots__ = ['name', 'level', 'max_hp', 'hp', 'damage', 'xp_reward', 'gold_reward']
    
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.max_hp = 20 + (level * 10)
        self.hp = self.max_hp
        self.damage = 3 + (level * 2)
        self.xp_reward = 20 * level
        self.gold_reward = random.randint(10, 25) * level

class Player:
    # שימוש ב-Slots לביצועים וחיסכון ב-RAM
    __slots__ = ['id', 'name', 'hp', 'max_hp', 'level', 'xp', 'next_level_xp', 
                 'gold', 'damage', 'potions', 'location', 'in_combat', 
                 'current_enemy', 'weapon_level', 'logs', 'last_active']

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.name = "גיבור"
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.xp = 0
        self.next_level_xp = 100
        self.gold = 50
        self.damage = 10
        self.potions = 3
        self.location = "town"
        self.in_combat = False
        self.current_enemy = None
        self.weapon_level = 1
        # שימוש ב-Deque - רשימה מהירה מאוד ששומרת רק את ה-5 האחרונים
        self.logs = deque(["הגעת לממלכה. המטרה: הבס את אביר הצללים במערה."], maxlen=5)
        self.last_active = time.time()

    def touch(self):
        # מעדכן זמן פעילות אחרון
        self.last_active = time.time()

    def add_log(self, text):
        # deque מטפל לבד במחיקת הישנים (O(1))
        self.logs.appendleft(text)

    def heal(self):
        if self.potions > 0:
            if self.hp >= self.max_hp:
                self.add_log("החיים שלך מלאים!")
                return
            heal_amount = 40
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.potions -= 1
            self.add_log(f"שתית שיקוי. החיים: {self.hp}. נותרו {self.potions}.")
        else:
            self.add_log("אין לך שיקויים! לך לחנות.")

    def gain_xp(self, amount):
        self.xp += amount
        self.add_log(f"קיבלת {amount} נק\"ן!")
        if self.xp >= self.next_level_xp:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp = 0
        self.next_level_xp = int(self.next_level_xp * 1.5)
        self.max_hp += 20
        self.hp = self.max_hp
        self.damage += 5
        self.add_log(f"🎉 עלית לרמה {self.level}!")


# --- Helper Functions ---

def get_player():
    # פונקציה אופטימלית יותר - בודקת ומעדכנת זמן באותה פעולה
    uid = request.cookies.get('rpg_uid')
    if uid and uid in players:
        p = players[uid]
        p.touch()
        # מפעיל ניקוי רק אחת ל-50 בקשות בערך כדי לא להכביד
        if random.random() < 0.02: 
            cleanup_inactive_players()
        return p
    return None

def create_new_player():
    new_p = Player()
    players[new_p.id] = new_p
    return new_p

# --- Routes ---

@app.route('/')
def home():
    # נתיב זה מיועד כאשר הפנייה היא ישירות (בלי DispatcherMiddleware)
    # בקוד המקורי השתמשת ב /game2/ בהפניה, אנחנו שומרים על הלוגיקה
    # אבל כאן ה-App הוא הראשי.
    p = get_player()
    if not p:
        p = create_new_player()
        resp = redirect('/game2/') 
        resp.set_cookie('rpg_uid', p.id, max_age=86400) # Cookie for 24 hours
        return resp

    # הגדרות תצוגה
    bg_color = "#333"
    icon = "🏠"
    loc_name = "הכפר הבטוח"

    # גישה ישירה משפרת ביצועים על פני בדיקות מיותרות
    if p.in_combat:
        bg_color = "#4a1c1c"
        e = p.current_enemy
        icon = f"😈 {e.name} (Lv{e.level})"
        loc_name = "זירת קרב"
    elif p.location == "forest":
        bg_color = "#1b4d3e"
        icon = "🌲🌲🌲"
        loc_name = "היער האפל"
    elif p.location == "cave":
        bg_color = "#2c2c2c"
        icon = "🦇🏔️🦇"
        loc_name = "מערת האבדון"

    # רינדור מהיר עם התבנית המקומפלת מראש
    return game_template.render(p=p, bg_color=bg_color, emoji_icon=icon, location_name=loc_name)

@app.route('/restart')
def restart():
    p = create_new_player()
    resp = redirect('/game2/')
    resp.set_cookie('rpg_uid', p.id, max_age=86400)
    return resp

@app.route('/travel/<destination>')
def travel(destination):
    p = get_player()
    if not p or p.hp <= 0 or p.in_combat: return redirect('/game2/')
    
    # אופטימיזציה: שימוש ב-Set לבדיקה מהירה במקום If/Or
    valid_locations = {"town", "forest", "cave"}
    if destination not in valid_locations: return redirect('/game2/')

    if destination == "cave" and p.level < 3:
        p.add_log("השומר: 'רק לוחמים ברמה 3+!'")
    else:
        p.location = destination
        p.add_log(f"עברת ל-{destination}.")
    
    return redirect('/game2/')

@app.route('/shop/<action>')
def shop(action):
    p = get_player()
    if not p or p.location != "town": return redirect('/game2/')

    if action == "buy_potion":
        if p.gold >= 30:
            p.gold -= 30
            p.potions += 1
            p.add_log("קנית שיקוי.")
        else:
            p.add_log("חסר זהב (30).")
    
    elif action == "upgrade_weapon":
        cost = p.weapon_level * 100
        if p.gold >= cost:
            p.gold -= cost
            p.damage += 5
            p.weapon_level += 1
            p.add_log(f"נשק שודרג! נזק: {p.damage}")
        else:
            p.add_log(f"חסר זהב ({cost}).")

    return redirect('/game2/')

@app.route('/action/<act>')
def perform_action(act):
    p = get_player()
    if not p: return redirect('/game2/')

    # קיבוץ הפעולות לביצועים ונקיון קוד
    
    if act == "explore" and not p.in_combat:
        if p.hp <= 0: return redirect('/game2/')
        # חישוב מתמטי מהיר
        if random.random() > 0.7:
            p.add_log("אין אויבים באזור.")
        else:
            start_combat(p)

    elif act == "attack" and p.in_combat:
        handle_combat_round(p) # העברנו לפונקציה נפרדת לקריאות

    elif act == "heal":
        p.heal()
        if p.in_combat:
            enemy_turn(p)

    elif act == "flee" and p.in_combat:
        loss = int(p.gold * 0.2)
        p.gold -= loss
        p.in_combat = False
        p.add_log(f"ברחת! איבדת {loss} זהב.")

    elif act == "inn" and p.location == "town":
        if p.gold >= 10:
            p.gold -= 10
            p.hp = p.max_hp
            p.add_log("ישנת בפונדק. חיים מלאים! 💤")
        else:
            p.add_log("חסר זהב ללינה (10).")

    return redirect('/game2/')

# --- Combat Logic Optimized ---

ENEMIES_FOREST = [("זאב רעב", 1), ("שדון יער", 2), ("עכביש ענק", 3)]
ENEMIES_CAVE = [("עטלף ערפד", 4), ("שומר שלד", 5), ("אביר הצללים", 10)]

def start_combat(p):
    # שימוש בטבלאות קבועות מראש (Global Consts) כדי לא ליצור Lists בכל פעם
    if p.location == "forest":
        choice = random.choice(ENEMIES_FOREST)
    else: # cave
        choice = random.choice(ENEMIES_CAVE)
        if choice[0] == "אביר הצללים" and p.level < 6:
            choice = ("שומר שלד חזק", 5)

    p.current_enemy = Enemy(choice[0], choice[1])
    p.in_combat = True
    p.add_log(f"⚠️ {p.current_enemy.name} (Lv{p.current_enemy.level}) הופיע!")

def handle_combat_round(p):
    enemy = p.current_enemy
    
    # חישוב נזק
    is_crit = random.random() > 0.8
    dmg = p.damage * 2 if is_crit else p.damage
    enemy.hp -= dmg
    
    # בנית מחרוזת פעם אחת
    msg = f"גרמת {dmg} נזק" + (" (קריטי!)" if is_crit else "")
    p.add_log(msg)

    if enemy.hp <= 0:
        p.in_combat = False
        p.gold += enemy.gold_reward
        p.gain_xp(enemy.xp_reward)
        p.add_log(f"🏆 ניצחון! +{enemy.gold_reward} זהב.")
        
        if enemy.name == "אביר הצללים":
            p.add_log("🔥 ניצחת את המשחק! 🔥")
    else:
        enemy_turn(p)

def enemy_turn(p):
    enemy = p.current_enemy
    damage = max(1, enemy.damage - random.randint(0, 2))
    p.hp -= damage
    p.add_log(f"נפגעת ב-{damage} נזק.")
    
    if p.hp <= 0:
        p.add_log("☠️ הובסת...")
        p.in_combat = False

if __name__ == '__main__':
    # Threaded=True מאפשר טיפול בכמה בקשות במקביל
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
