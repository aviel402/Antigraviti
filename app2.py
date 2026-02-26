import random
import uuid
from flask import Flask, redirect, session
from jinja2 import Environment, BaseLoader

app = Flask(__name__)
# מפתח הצפנה עבור עוגיות ה-Session (שמירת המשתמש על הענן/Vercel)
app.secret_key = "rpg_legend_secret_super_key_123"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # שמירה ל-30 יום

# --- HTML TEMPLATE (ותוקן הניתוח תחת הדיספאצ'ר `/game2`) ---
HTML_TEMPLATE_STR = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPG Legends</title>
    <style>
        body { background-color: #1a1a1d; color: #c5c6c7; font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .game-card { background: #2b2e31; width: 100%; max-width: 500px; padding: 15px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.5); border-top: 4px solid #66fcf1; }
        h2 { margin: 5px 0; color: #66fcf1; text-align: center; }
        .stats { display: flex; justify-content: space-between; background: #0b0c10; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px; font-weight: bold; }
        
        .hp-container { background: #444; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; box-shadow: inset 0 0 5px black;}
        .hp-fill { height: 100%; width: {{ (p.hp / p.max_hp) * 100 }}%; transition: width 0.3s ease-in-out; }
        
        {% set hp_percent = (p.hp / p.max_hp) %}
        {% if hp_percent <= 0.3 %}
        /* אזור סכנה: יהבהב באדום זוהר */
        .hp-fill { background-color: #ff3333; animation: blinker 1s linear infinite; }
        @keyframes blinker { 50% { opacity: 0.5; } }
        {% else %}
        .hp-fill { background-color: #4CAF50; }
        {% endif %}

        .scene { background-color: #222; height: 150px; border-radius: 8px; margin-bottom: 15px; position: relative; display: flex; justify-content: center; align-items: center; font-size: 50px; text-shadow: 0 0 10px black; border: 2px solid #000; box-shadow: inset 0 0 30px rgba(0,0,0,0.8);}
        .scene-text { position: absolute; bottom: 8px; font-size: 14px; background: rgba(0,0,0,0.8); padding: 4px 10px; border-radius: 4px; color: #eee; border: 1px solid #444;}
        
        .logs { background: #0c0d11; color: #45a29e; padding: 10px; height: 90px; overflow-y: auto; border-radius: 5px; margin-bottom: 15px; font-size: 13.5px; font-family: 'Courier New', monospace; border: 1px solid #333; display:flex; flex-direction:column-reverse; }
        .log-line { margin-bottom: 5px; border-bottom: 1px dotted #222; padding-bottom: 3px; }
        .log-good { color: #5ce65c; }
        .log-bad { color: #ff6666; }
        .log-alert { color: #ffcc00; font-weight: bold; }

        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { background: #1f2833; border: 1px solid #45a29e; color: white; padding: 14px; font-size: 15px; cursor: pointer; border-radius: 8px; font-weight: bold; transition: all 0.2s; }
        button:hover { background: #45a29e; color: black; transform: scale(1.02); }
        .combat-btn { background: #3e1212; border-color: #ff4d4d; }
        .combat-btn:hover { background: #ff4d4d; color: white;}
        .heal-btn { background: #0f3d0f; border-color: #4dff4d; }
        .shop-btn { background: #3d3d0f; border-color: #ffff4d; }
        a.back-menu { display:block; margin-top: 20px; color: #888; font-size: 12px; text-decoration:none; transition: 0.2s; text-align: center;}
        a.back-menu:hover { color: #fff;}
    </style>
</head>
<body>
    <div class="game-card">
        <h2>⚔️ ממלכת הצללים 🛡️</h2>
        <div class="stats">
            <div style="width:40%;">❤️ {{ p.hp }}/{{ p.max_hp }} <div class="hp-container"><div class="hp-fill"></div></div></div>
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
                {% set log_class = "" %}
                {% if "נפגעת" in log or "איבדת" in log or "חסר" in log or "החלמקת דממת" in log %} {% set log_class = "log-bad" %}
                {% elif "שיקוי" in log or "שודרג" in log or "+" in log or "מלאים" in log or "ניצחון" in log or "רמה" in log %} {% set log_class = "log-good" %}
                {% elif "מארב פתע" in log or "אנושה" in log %} {% set log_class = "log-alert" %}
                {% endif %}
                <div class="log-line {{ log_class }}">➜ {{ log }}</div>
            {% endfor %}
        </div>

        <div class="actions">
            <!-- שים לב שהוספנו את ה- /game2 לפני הקישורים עבור תמיכה בדיספאצ'ר הראשי שלך! -->
            {% if p.hp <= 0 %}
                <button onclick="window.location.href='/game2/restart'" style="grid-column: span 2; background: #990000; border:2px solid red;">☠️ מסעך הסתיים. לחץ להתחלה חדשה</button>
            {% elif p.in_combat %}
                <button class="combat-btn" onclick="window.location.href='/game2/action/attack'">⚔️ התקפה על {{p.current_enemy.name}}</button>
                <button class="heal-btn" onclick="window.location.href='/game2/action/heal'">🧪 שיקוי ({{p.potions}})</button>
                <button onclick="window.location.href='/game2/action/flee'">🏃 נסיגה פחדנית</button>
            {% elif p.location == 'town' %}
                <button onclick="window.location.href='/game2/travel/forest'">🌲 צא לסייר ביער</button>
                <button style="border-color: red" onclick="window.location.href='/game2/travel/cave'">🦇 למערת הבוס</button>
                <button class="shop-btn" onclick="window.location.href='/game2/shop/buy_potion'">🧪 שיקוי חיים (30ג)</button>
                <button class="shop-btn" onclick="window.location.href='/game2/shop/upgrade_weapon'">⚔️ שדרג נשק ({{ p.weapon_level * 100 }}ג)</button>
                <button class="heal-btn" onclick="window.location.href='/game2/action/inn'">🏨 נוח בפונדק (10ג)</button>
            {% elif p.location == 'forest' or p.location == 'cave' %}
                <button class="combat-btn" onclick="window.location.href='/game2/action/explore'">🔍 חפש באזור</button>
                <button onclick="window.location.href='/game2/travel/town'">🏠 חזור לעיר</button>
            {% endif %}
        </div>
    </div>
    
    <!-- לחזור למערכת הראשי של Aviel - הArcade hub -->
    <a href="/" class="back-menu">⮜ חזרה לארקייד הראשי </a>
</body>
</html>
"""

jinja_env = Environment(loader=BaseLoader())
game_template = jinja_env.from_string(HTML_TEMPLATE_STR)

# --- MODELS ---
class Enemy:
    def __init__(self, name, level, hp=None):
        self.name = name; self.level = level; self.max_hp = 20 + (level * 10)
        self.hp = hp if hp is not None else self.max_hp
        self.damage = 3 + (level * 2); self.xp_reward = 20 * level
        self.gold_reward = random.randint(10, 25) * level
        
    def to_dict(self): return {"name": self.name, "level": self.level, "hp": self.hp}
    @classmethod
    def from_dict(cls, data):
        if not data: return None
        return cls(data["name"], data["level"], data["hp"])

class Player:
    def __init__(self, data=None):
        if data:
            self.id = data.get("id", str(uuid.uuid4())); self.hp = data.get("hp", 100); self.max_hp = data.get("max_hp", 100)
            self.level = data.get("level", 1); self.xp = data.get("xp", 0); self.next_level_xp = data.get("next_level_xp", 100)
            self.gold = data.get("gold", 50); self.damage = data.get("damage", 10); self.potions = data.get("potions", 3)
            self.location = data.get("location", "town"); self.in_combat = data.get("in_combat", False)
            self.current_enemy = Enemy.from_dict(data.get("current_enemy"))
            self.weapon_level = data.get("weapon_level", 1); self.logs = data.get("logs", ["ברוכים הבאים לממלכה."])
        else:
            self.id = str(uuid.uuid4()); self.hp = 100; self.max_hp = 100; self.level = 1
            self.xp = 0; self.next_level_xp = 100; self.gold = 50
            self.damage = 10; self.potions = 3; self.location = "town"
            self.in_combat = False; self.current_enemy = None
            self.weapon_level = 1; self.logs = ["הגעת לממלכה. הבס את האויבים!"]

    def to_dict(self):
        return {
            "id": self.id, "hp": self.hp, "max_hp": self.max_hp, "level": self.level, "xp": self.xp, 
            "next_level_xp": self.next_level_xp, "gold": self.gold, "damage": self.damage, "potions": self.potions,
            "location": self.location, "in_combat": self.in_combat, "weapon_level": self.weapon_level,
            "logs": self.logs, "current_enemy": self.current_enemy.to_dict() if self.current_enemy else None
        }

    def add_log(self, text):
        self.logs.insert(0, text)
        if len(self.logs) > 6: self.logs.pop()

    def heal(self):
        if self.potions > 0:
            if self.hp >= self.max_hp: return self.add_log("החיים שלך מלאים לחלוטין!")
            heal_amount = 40 + (self.level * 5)
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.potions -= 1
            self.add_log(f"שתית שיקוי מרענן! נותרו {self.potions} 🧪.")
        else: self.add_log("אין לך שיקויים בכלל... חזור לחנות!")

    def gain_xp(self, amount):
        self.xp += amount
        self.add_log(f"+ צברת {amount} XP")
        if self.xp >= self.next_level_xp:
            self.level += 1; self.xp -= self.next_level_xp; self.next_level_xp = int(self.next_level_xp * 1.5)
            self.max_hp += 20; self.hp = self.max_hp; self.damage += 6
            self.add_log(f"🎉 עלית לרמה {self.level}!")

# --- Serverless STATE MGMT - Unique for Game2 ---
def load_player():
    data = session.get('rpg_player_data') # הוספנו תחילית כדי למנוע דריסת עוגיות ממשחקים אחרים בהאב
    if data: return Player(data)
    return None

def save_player(player):
    session.permanent = True
    session['rpg_player_data'] = player.to_dict()

# --- ROUTES ---

@app.route('/')
def home():
    p = load_player()
    if not p:
        p = Player(); save_player(p)
        return redirect('/game2/')  # החזרה אל /game2 תקינה

    bg_color = "#20252a"; icon = "🏘️"; loc_name = "העיר המרכזית (בטוח)"
    if p.in_combat:
        bg_color = "#361616"; icon = f"😈 {p.current_enemy.name}"; loc_name = f"זירת קרב! (Lv.{p.current_enemy.level})"
    elif p.location == "forest":
        bg_color = "#163520"; icon = "🌳 🌲 🌳"; loc_name = "יער המפלצות"
    elif p.location == "cave":
        bg_color = "#121215"; icon = "🦇 🏔️ 🦇"; loc_name = "מערת האופל"

    save_player(p)
    return game_template.render(p=p, bg_color=bg_color, emoji_icon=icon, location_name=loc_name)

@app.route('/restart')
def restart():
    session.pop('rpg_player_data', None)
    return redirect('/game2/')

@app.route('/travel/<destination>')
def travel(destination):
    p = load_player()
    if not p or p.hp <= 0 or p.in_combat: return redirect('/game2/')
    
    if destination in {"town", "forest", "cave"}:
        if destination == "cave" and p.level < 3:
            p.add_log("שומר: 'רק לוחמים ברמה 3+ מורשים להיכנס לפה!'")
        else:
            p.location = destination
            p.add_log(f"הגעת אל -> {destination}.")
    save_player(p); return redirect('/game2/')

@app.route('/shop/<action>')
def shop(action):
    p = load_player()
    if not p or p.location != "town": return redirect('/game2/')

    if action == "buy_potion":
        if p.gold >= 30: p.gold -= 30; p.potions += 1; p.add_log("רכשת שיקוי 🧪.")
        else: p.add_log("הסוחר דחה אותך, חסר זהב (30).")
    elif action == "upgrade_weapon":
        cost = p.weapon_level * 100
        if p.gold >= cost:
            p.gold -= cost; p.damage += 6; p.weapon_level += 1; p.add_log(f"הנשק שודרג! רמת נזק כעת: {p.damage}")
        else: p.add_log(f"חסר מספיק זהב ({cost}).")
    save_player(p); return redirect('/game2/')

@app.route('/action/<act>')
def perform_action(act):
    p = load_player()
    if not p: return redirect('/game2/')

    if act == "explore" and not p.in_combat and p.hp > 0:
        if random.random() > 0.65: p.add_log("סיירת באזור, אך הכל שקט.")
        else: start_combat(p)

    elif act == "attack" and p.in_combat and p.hp > 0: handle_combat_round(p)

    elif act == "heal" and p.hp > 0:
        if p.potions > 0: p.heal(); 
        if p.in_combat: enemy_turn(p)

    elif act == "flee" and p.in_combat:
        loss = int(p.gold * 0.15)
        p.gold -= loss; p.in_combat = False; p.current_enemy = None
        p.add_log(f"ברחת חזרה! במהלך הריצה איבדת {loss} זהב.")

    elif act == "inn" and p.location == "town":
        if p.gold >= 10: p.gold -= 10; p.hp = p.max_hp; p.add_log("השינה השתלמה! נרפאת לחלוטין. 💤")
        else: p.add_log("אין לך מספיק זהב לפונדק (10).")

    save_player(p); return redirect('/game2/')

# --- קרב מנוע ---
def start_combat(p):
    enemies_f =[("זאב רעב", 1), ("זחל ביצות מזוהם", 2), ("עכביש רעיל", 3)]
    enemies_c =[("עטלף מפלצתי", 4), ("גולם שחור", 6), ("אביר המימדים הרעים (בוס)", 10)]
    
    choice = random.choice(enemies_f) if p.location == "forest" else random.choice(enemies_c)
    if choice[1] == 10 and p.level < 6: choice = ("שד מאסטר מעונה", 5) # לא יופיע בוס אם השחקן חלש מדי

    p.current_enemy = Enemy(choice[0], choice[1]); p.in_combat = True
    p.add_log(f"⚠️ מארב פתע! {p.current_enemy.name} הופיע!")

def handle_combat_round(p):
    e = p.current_enemy
    is_crit = random.random() > 0.75
    dmg = int(p.damage * 1.5) if is_crit else p.damage
    e.hp -= dmg
    p.add_log(f"⚡ מכה אנושה! {dmg} נזק." if is_crit else f"גרמת {dmg} נזק.")

    if e.hp <= 0:
        p.in_combat = False; p.gold += e.gold_reward; p.gain_xp(e.xp_reward)
        p.add_log(f"🏆 זכית ב: +{e.gold_reward} זהב.")
        p.current_enemy = None
    else: enemy_turn(p)

def enemy_turn(p):
    if random.random() > 0.88: p.add_log(f"חמקת מההתקפה בזריזות!")
    else:
        dmg = max(1, p.current_enemy.damage - random.randint(1, 3))
        p.hp -= dmg
        p.add_log(f"נפגעת. איבדת {dmg} חיים.")
    if p.hp <= 0:
        p.hp = 0; p.in_combat = False; p.add_log("☠️ הובסת והמערכה תמה...")

if __name__ == '__main__':
    # ניתן גם להריץ ישירות
    app.run(port=5000, debug=True)
