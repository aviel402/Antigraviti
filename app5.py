import random
from flask import Flask, render_template_string, redirect, session

app = Flask(__name__)
# סשן שמור לענן 
app.secret_key = "iron_legion_commander_secured_token_v1"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # שמירת התקדמות ל-30 יום

# --- נתוני יחידות צבא (עברית נקייה הפעם!) ---
UNIT_TYPES = {
    "grunt": {"name": "לוחם חי\"ר מתקדם", "cost": 50, "dmg": 2, "hp": 10, "icon": "🔫"},
    "sniper": {"name": "צלף מובחר", "cost": 150, "dmg": 15, "hp": 5, "icon": "🔭"},
    "tank": {"name": "טנק שריון כבד", "cost": 500, "dmg": 50, "hp": 100, "icon": "🚜"},
    "mech": {"name": "אב-טיפוס גוליית (רובוט קרב)", "cost": 2000, "dmg": 150, "hp": 300, "icon": "🤖"},
}

UPGRADES = {
    "weapons": {"name": "פיתוח נשק (+20% לנזק כללי)", "cost": 1000, "factor": 1.2, "type": "dmg", "icon": "⚔️"},
    "armor": {"name": "חיזוק שריון (+20% לחיי הצבא)", "cost": 1000, "factor": 1.2, "type": "hp", "icon": "🛡️"},
}

# --- לוגיקת המשחק בסביבת שרת מאובטחת ---
class GameState:
    def __init__(self, data=None):
        if data:
            self.gold = data.get("gold", 300)
            self.wave = data.get("wave", 1)
            self.army = data.get("army", {"grunt": 0, "sniper": 0, "tank": 0, "mech": 0})
            self.tech = data.get("tech", {"weapons": 1, "armor": 1})
            self.upgrade_costs = data.get("upgrade_costs", {"weapons": 1000, "armor": 1000})
            self.last_battle_log = data.get("last_battle_log",["🛡️ ברוך הבא למפקדה המרכזית, גנרל.", "כדי לשרוד מול הגלים שיגיעו - עליך לבנות צבא גדול. הקרבות הקלים יובילו לקשים."])
        else:
            self.reset()

    def reset(self):
        self.gold = 300
        self.wave = 1
        self.army = {"grunt": 0, "sniper": 0, "tank": 0, "mech": 0}
        self.tech = {"weapons": 1, "armor": 1}
        self.upgrade_costs = {"weapons": 1000, "armor": 1000}
        self.last_battle_log =["מערכות שרת אופסו מחדש. ממתין להנחיות קומנדר... 🛡️"]
        
    def to_dict(self):
        return {
            "gold": self.gold, "wave": self.wave, "army": self.army,
            "tech": self.tech, "upgrade_costs": self.upgrade_costs, "last_battle_log": self.last_battle_log
        }

    def get_army_stats(self):
        total_dmg = 0; total_hp = 0; count = 0
        for u_key, amount in self.army.items():
            if amount > 0:
                stats = UNIT_TYPES[u_key]
                total_dmg += (stats["dmg"] * amount) * self.tech["weapons"]
                total_hp += (stats["hp"] * amount) * self.tech["armor"]
                count += amount
        return int(total_dmg), int(total_hp), count

    def get_intel(self):
        return {
             "hp": int(20 * (self.wave ** 1.5)),
             "dmg": int(5 * (self.wave ** 1.3))
        }

    def fight(self):
        intel = self.get_intel()
        enemy_hp, enemy_dmg = intel["hp"], intel["dmg"]
        enemy_name = f"גל אויב מספר #{self.wave}"
        
        my_dmg, my_hp, my_count = self.get_army_stats()
        
        # אימות שאפשר לצאת בכלל לקרב:
        if my_count == 0:
            self.last_battle_log =["⚠️ אי אפשר לצאת לשטח! צבאך ריק מלוחמים. עליך להקצות זהב לרכישת כוחות לפני הקרב."]
            return

        combat_log =[f"/// 🚨 דיווח מהשטח: תקיפת פולשים מה-{enemy_name} מתחילה! ///"]
        combat_log.append(f"כוח המכה שלך : ⚔️ {my_dmg} / 🛡️ {my_hp}")
        combat_log.append(f"כוח המכה של האויב : ⚔️ {enemy_dmg} / 🛡️ {enemy_hp}")
        
        rounds = 0
        while my_hp > 0 and enemy_hp > 0:
            rounds += 1
            enemy_hp -= my_dmg
            
            if enemy_hp > 0:
                damage_taken = enemy_dmg
                my_hp -= damage_taken
                
                lost_percent = min(0.12, damage_taken / (my_hp + damage_taken + 0.1)) 
                self.kill_units(lost_percent)
                my_dmg, new_hp, _ = self.get_army_stats() 
                if new_hp <= 0: my_hp = 0

        # הכרעת הדין של הקרב בעברית אמיתית
        if my_hp > 0:
            reward = int(100 * (self.wave ** 1.25))
            self.gold += reward
            self.wave += 1
            combat_log.append(f"✅ יעד הושג: צבא האויב חוסל לחלוטין (קרב שערך {rounds} סבבים). חיילנו גבו רכוש ושלל בסך של: {reward} 💳 זהב.")
        else:
            self.kill_units(0.65) # השארת רעשים בעמי פרישות והלוויות משקל 
            consolation = int(35 * self.wave)
            self.gold += consolation
            combat_log.append(f"❌ מערך ההגנה הושמד וצבא האויב רמס אותנו. חלקים נכבדים מהצבא יושמדו ותבוסה נרשמה... ניצלנו פריטים מזירת האסון כנחמה : {consolation} 💳 קופה אומללה...")

        self.last_battle_log = combat_log

    def kill_units(self, percentage):
        for u_key in self.army:
            if self.army[u_key] > 0:
                dead = int(self.army[u_key] * percentage)
                if dead == 0 and random.random() < (percentage * 2): dead = 1
                self.army[u_key] = max(0, self.army[u_key] - dead)

# --- טיפול עוגיות ענן לפרוייקט ---
def load_game():
    data = session.get('legion_data')
    return GameState(data)

def save_game(g):
    session['legion_data'] = g.to_dict()
    session.permanent = True

# --- HTML CSS עיברי, ללא משחקי השטן וללא תאונות מילים ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iron Legion Commander</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Assistant:wght@400;700;800&display=swap');
        :root { --dark: #0a0e17; --neon: #38bdf8; --warn: #f43f5e; --succ: #10b981; --panel: rgba(15, 23, 42, 0.85); }
        
        body { 
            background: radial-gradient(circle at 50% 10%, #1e293b, var(--dark) 90%);
            color: #cbd5e1; font-family: 'Assistant', sans-serif;
            margin: 0; padding: 15px; text-align: center;
        }

        body::before {
            content:""; position:fixed; top:0; left:0; width:100%; height:100%;
            background: linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
            background-size: 30px 30px; pointer-events: none; z-index: -1;
        }

        h1 { margin: 5px; color: var(--neon); text-transform: uppercase; letter-spacing: 5px; font-family:'Share Tech Mono', sans-serif; font-size: 28px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.5);}
        .back-nav { display: inline-flex; justify-content: center; align-items:center; color: #aaa; text-decoration:none; margin-bottom: 20px; font-weight: bold; background: #1e293b; padding: 5px 15px; border-radius: 20px; font-size:12px;}
        .back-nav:hover { color:#fff; background:var(--warn); }
        
        .container { max-width: 600px; margin: 0 auto; padding-bottom: 60px; position:relative;}
        
        .dashboard {
            display: flex; gap: 10px; background: var(--panel); padding: 15px; border-radius: 12px; margin-bottom: 15px;
            border-bottom: 3px solid var(--succ); border-top: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); justify-content:space-around;
        }
        .stat-block { flex:1;}
        .stat-val { display: block; font-size: 22px; color: #f8fafc; font-weight: 800; font-family: 'Share Tech Mono', monospace;}
        .stat-label { font-size: 13px; text-transform: uppercase; color: #94a3b8; font-weight: bold;}
        
        .army-power { 
           background: rgba(15, 23, 42, 0.95); padding:10px; border: 1px dashed var(--succ); 
           font-size: 14px; margin-bottom:20px; color:#fff; display:flex; justify-content:space-between;
           border-radius:6px; align-items:center; font-weight: bold;
        }

        .battle-log { 
            background: #020617; color: #38bdf8; font-family: 'Share Tech Mono', monospace; padding: 15px; 
            border-radius: 8px; text-align: right; margin-bottom: 20px; font-size: 14px; line-height: 1.6; border: 1px solid #1e293b;
            min-height: 60px; box-shadow: inset 0 0 20px rgba(56, 189, 248, 0.1); 
        }
        .intel-badge { background: #331515; border-right: 4px solid var(--warn); padding: 12px; margin-bottom:20px; border-radius: 4px; color:#fff; text-align:right;}

        .btn-fight {
            width: 100%; padding: 15px; background: linear-gradient(135deg, #e11d48, #9f1239);
            color: white; border: 1px solid #f43f5e; font-size: 18px; font-weight: bold; border-radius: 8px;
            cursor: pointer; animation: pulseGlow 2.5s infinite; letter-spacing: 1px;
        }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.6); } 70% { box-shadow: 0 0 0 12px rgba(225, 29, 72, 0); } 100% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0); } }

        .units-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }
        .unit-card { background: var(--panel); padding: 12px; border-radius: 10px; text-align: right; border: 1px solid #334155; position: relative; transition: 0.2s; overflow:hidden;}
        .unit-card::before {content:''; position:absolute; top:0;left:0; width:4px; height:100%; background: #475569;}
        .unit-card:hover { transform: translateY(-3px); border-color:var(--succ); }
        .unit-icon { float: right; margin-left:10px; font-size: 32px; filter: drop-shadow(0 0 8px rgba(255,255,255,0.2));}
        .unit-name { color: #f8fafc; font-weight: bold; display: block; font-size: 15px; margin-bottom:2px;}
        .u-dt { font-size:12px; color:#64748b; font-weight:bold;}
        .unit-cost { color: #fde047; font-size: 13px; font-weight:800; margin-top:3px;}
        .unit-owned { font-size: 13px; color: var(--succ); margin-top: 10px; font-weight:800; border-top:1px dashed #334155; padding-top:5px; text-align:right;}
        .btn-buy { width: 100%; margin-top: 8px; padding: 10px; border: none; background: #2563eb; color: white; border-radius: 5px; cursor: pointer; font-weight: bold; font-family:'Assistant', sans-serif; transition:0.2s;}
        .btn-buy:hover { background: #1d4ed8; }

        .tech-box { background: rgba(15, 23, 42, 0.5); padding: 15px; border-radius: 12px; border:1px solid #1e293b; text-align:right;}
        .tech-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dotted #334155; padding:10px 0; }
        .btn-upgrade { background: #059669; padding: 8px 15px; color: white; font-weight:bold; border:none; border-radius: 6px; cursor: pointer; display:flex; align-items:center; gap:5px;}

    </style>
</head>
<body>

<div class="container">
    <a href="/" class="back-nav">◀ חזרה לארקייד הראשי (Arcade Hub)</a>
    <h1>[ IRON - LEGION ]</h1>
    
    <!-- פנל סטטוס עילי -->
    <div class="dashboard">
        <div class="stat-block"><span class="stat-label">קופת צבא:</span><span class="stat-val" style="color:#fde047">💳 {{ game.gold }}</span></div>
        <div class="stat-block"><span class="stat-label">שלב / גל נוכחי:</span><span class="stat-val" style="color:#cbd5e1">🚩 {{ game.wave }}</span></div>
        <div class="stat-block"><span class="stat-label">חיילים פעילים:</span><span class="stat-val" style="color:var(--succ)">🪖 {{ total_units }}</span></div>
    </div>

    <div class="army-power">
         <span>עוצמת הארמייה הנוכחית שלך במלואה:</span>
         <b>{ התקפה ⚔️{{my_dmg}}  |  חיים 🛡️{{my_hp}} }</b>
    </div>

    <!-- לוג המערכת על המשחק -->
    <div class="battle-log">
        {% for line in game.last_battle_log %}
            <div style="margin-bottom:6px; color: {{ 'var(--warn)' if '❌' in line or '💀' in line or '⚠️' in line else 'inherit' }};">{{ line }}</div>
        {% endfor %}
    </div>

    <!-- תיבת אזהרת הראדאר (אירועים וזיהויים מתקדמים לשלב הסטנדרטי הבא) -->
    <div class="intel-badge">
       <b>⚠️ אינדיקציה של כוחות אויב על הרדאר...</b><br>
       מודיעין צבאי מאשר כי יריבים קרובים לגבול ויחצו בשנית, כוח מוערך: ⚔️ {{ intel.dmg }} נזק סופי. וכוח מחיה של סך 🛡️ {{ intel.hp }} שריון לאיתור ותיכנון קדם מערכי! חמש את רכוזיי הירי והמוני העמדות!
    </div>

    <!-- הכפתור המפוצץ אל המלחמות!!! -->
    <div style="margin-bottom: 25px;">
        <a href="/game5/fight"><button class="btn-fight">🧨 צא לחזית הלחימה - מצא את גל ההשמדה הנוכחי! 🧨</button></a>
    </div>

    <h3 style="text-align:right; border-bottom:1px solid #334155; padding-bottom:5px; margin-top:40px;">לשכת גיוס חיילים [Garrison Center]</h3>
    <div class="units-grid">
        {% for key, unit in units.items() %}
        <div class="unit-card">
            <span class="unit-icon">{{ unit.icon }}</span>
            <div style="float: right;">
                <span class="unit-name">{{ unit.name }}</span>
                <div class="u-dt">⚔️ התקפה: {{unit.dmg}} | 🛡️ שריון: {{unit.hp}}</div>
            </div>
            <div style="clear: both; padding-top:10px;"></div>
            <div class="unit-cost">עלות כספית: {{ unit.cost }} 💳</div>
            <a href="/game5/buy/{{ key }}" style="text-decoration:none;">
                <button class="btn-buy">רכוש ציוד ואמץ (+1 לשטח האסמכות!)</button>
            </a>
            <div class="unit-owned">מניין יחידה אצלך בארמיה > <span>{{ game.army[key] }}</span> איש צבא קנוי. </div>
        </div>
        {% endfor %}
    </div>

    <h3 style="text-align:right; border-bottom:1px solid #334155; padding-bottom:5px;">מעבדת אבזור טכנולוגית צבאית [TECH UPGRADES]</h3>
    <div class="tech-box">
        {% for key, upg in upgrades.items() %}
        <div class="tech-row">
            <div>
                <div style="font-weight:800; color: #fff; display:flex; gap:8px;"><span>{{upg.icon}}</span> {{ upg.name }}</div>
                <div style="font-size:14px; color:#94a3b8; margin-top:2px;">אתה כעת על מצב של פקטור ברמה של >> Lv. <b>{{ game.tech[key] }}</b></div>
            </div>
            <a href="/game5/upgrade/{{ key }}" style="text-decoration:none;">
                <button class="btn-upgrade">{{ game.upgrade_costs[key] }} 💳 העלה סבב כספי לשדרוג תשתית > </button>
            </a>
        </div>
        {% endfor %}
    </div>
    
    <div style="margin-top:40px; border-top:1px dashed #333; padding-top:20px;">
        <a href="/game5/reset" style="color: #64748b; font-size:12px; font-weight:bold; background:#0f172a; padding: 10px; border-radius:5px; border:1px solid #1e293b;">שריפת תיק משימתי מהרכוש: מחק מצב לאיפוס מסף התחלתי נקי מתקן.</a>
    </div>

</div>

</body>
</html>
"""

# ===============================
# נקודות התחלה על גבי מערך Vercel כלילת Flask הדיספאצי שלנו Game 5 !!
# ===============================
@app.route('/')
def home():
    state = load_game()
    dmg, hp, count = state.get_army_stats()
    return render_template_string(HTML, game=state, units=UNIT_TYPES, upgrades=UPGRADES, total_units=count, intel=state.get_intel(), my_dmg=dmg, my_hp=hp)

@app.route('/buy/<unit_key>')
def buy(unit_key):
    state = load_game()
    if unit_key in UNIT_TYPES:
        cost = UNIT_TYPES[unit_key]['cost']
        if state.gold >= cost:
            state.gold -= cost
            state.army[unit_key] += 1
            save_game(state)
    return redirect('/game5/')

@app.route('/upgrade/<upg_key>')
def upgrade(upg_key):
    state = load_game()
    if upg_key in state.tech:
        cost = state.upgrade_costs[upg_key]
        if state.gold >= cost:
            state.gold -= cost
            state.tech[upg_key] = round(state.tech[upg_key] * UPGRADES[upg_key]['factor'], 2)
            state.upgrade_costs[upg_key] = int(cost * 1.8)
            save_game(state)
    return redirect('/game5/')

@app.route('/fight')
def battle():
    state = load_game()
    state.fight()
    save_game(state)
    return redirect('/game5/')

@app.route('/reset')
def reset():
    state = load_game()
    state.reset()
    save_game(state)
    return redirect('/game5/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
