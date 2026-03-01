import random
from flask import Flask, render_template_string, redirect, session

app = Flask(__name__)
# סשן קבוע וסודי במיוחד למנוע דריסת ארקייד מאובטח:
app.secret_key = "iron_legion_commander_secured_token_v1"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # הצבא נשמר חודש לכל משתמש מנקודת גל חזר!

# --- נתוני יחידות (סטטי / עולמי) ---
UNIT_TYPES = {
    "grunt": {"name": "לוחם חי\"ר ממונע", "cost": 50, "dmg": 2, "hp": 10, "icon": "🔫"},
    "sniper": {"name": "צלף מובחר", "cost": 150, "dmg": 15, "hp": 5, "icon": "🔭"},
    "tank": {"name": "פנצר ברזל", "cost": 500, "dmg": 50, "hp": 100, "icon": "🚜"},
    "mech": {"name": "אב-טיפוס גוליית", "cost": 2000, "dmg": 150, "hp": 300, "icon": "🤖"},
}

UPGRADES = {
    "weapons": {"name": "ארסנל מחקר (+20% עוצמת אש לכלל חטיבה)", "cost": 1000, "factor": 1.2, "type": "dmg", "icon": "⚔️"},
    "armor": {"name": "סגסוגת שריון פציל (+20% השרדות יחידות חיים)", "cost": 1000, "factor": 1.2, "type": "hp", "icon": "🛡️"},
}

# --- לוגיקה ענן תואמת Vercel Sessions ---
class GameState:
    def __init__(self, data=None):
        if data:
            self.gold = data.get("gold", 300)
            self.wave = data.get("wave", 1)
            self.army = data.get("army", {"grunt": 0, "sniper": 0, "tank": 0, "mech": 0})
            self.tech = data.get("tech", {"weapons": 1, "armor": 1})
            self.upgrade_costs = data.get("upgrade_costs", {"weapons": 1000, "armor": 1000})
            self.last_battle_log = data.get("last_battle_log",[">> 🛡️ ברוך הבא למפקדה החשאית, המפקד.", "גייס לוחמים טרם צאתך למבצע הפתיחה חדירות לחלל אוויר בלאום הקפי!"])
        else:
            self.reset()

    def reset(self):
        self.gold = 300
        self.wave = 1
        self.army = {"grunt": 0, "sniper": 0, "tank": 0, "mech": 0}
        self.tech = {"weapons": 1, "armor": 1}
        self.upgrade_costs = {"weapons": 1000, "armor": 1000}
        self.last_battle_log =["מאתחל לוחות מרשת... 🛡️"]
        
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
        # המודיעין (לקבל סריקה ללקוח) מסייע בניווט כל הקפיצה 
        return {
             "hp": int(20 * (self.wave ** 1.5)),
             "dmg": int(5 * (self.wave ** 1.3))
        }

    def fight(self):
        intel = self.get_intel()
        enemy_hp, enemy_dmg = intel["hp"], intel["dmg"]
        enemy_name = f"דיביזיית עוינת שלב #{self.wave}"
        
        my_dmg, my_hp, my_count = self.get_army_stats()
        
        if my_count == 0:
            self.last_battle_log =["⚠️ [שגיאת שרת]: לאן כיוונו בדיוק סרן גל גיוסים! בוס, צעד אל החימוש נראך פחוח לגמרי - אפס קדימת מספרי חישוב כדרוכית מחוספסטית באזור!! "]
            return

        combat_log =[f"/// -- התנקשות צביית רגישה באזוי התנועה : -- {enemy_name} החל לגלוי רגילות לחוש!!! -- ///"]
        combat_log.append(f"כוח המועבר ממגדל שמחת הכנס (שלנו) : ~ ⚔️ {my_dmg} / 🛡️ {my_hp} ")
        combat_log.append(f"הסחט המצבע העורמני (מהיחליטי שלהם!) : ~ ⚔️ {enemy_dmg} / 🛡️ {enemy_hp}")
        
        rounds = 0; start_count = my_count
        while my_hp > 0 and enemy_hp > 0:
            rounds += 1
            enemy_hp -= my_dmg # התקפה של יבטי מגע 
            
            if enemy_hp > 0:
                damage_taken = enemy_dmg
                my_hp -= damage_taken
                
                # מוות מדמי טיהורים של סיבוב (עקב כפי הלוח!) 
                lost_percent = min(0.12, damage_taken / (my_hp + damage_taken + 0.1)) 
                self.kill_units(lost_percent)
                my_dmg, new_hp, _ = self.get_army_stats() 
                if new_hp <= 0: my_hp = 0

        # שלב פולימנט קל : ניהולים על מושרי נחילי הפחת כדור תמצט  = הכלים למזגי לילה .. אובלים ששדומים מפיסים להשלטת פירורי הים.
        if my_hp > 0:
            reward = int(100 * (self.wave ** 1.25))
            self.gold += reward
            self.wave += 1
            combat_log.append(f"✅ >> גבעתי! יצא הלב מחזה הצהלוח גורשי קרקפות {rounds} כדור למה! הכבוס תום כבכמות!! הפקידת נתנו על זנבל {reward} תריחות נקושות קרציות מתאכות הכל!! תעשר זהבי הגיע לרוש כנוי קניית השפעת פירות זהויות!")
        else:
            self.kill_units(0.65) # השארת רעשים בעמי פרישות והלוויות משקל 
            consolation = int(35 * self.wave)
            self.gold += consolation
            combat_log.append(f"❌ >> התפרצה שרשה משבוי הנגעות לא קדחים למגרונת הוי כלה שריפ... השגרו גזר קבל הזרות ללא המונים בלחשי יליד החג אלא חליפי חילוני עופד! התפסל הוקצה נפסר. אבזר מיקום מיחזי: {consolation} מנפק לקרחת מחבוי הענשת צורך סחי!! ")

        self.last_battle_log = combat_log

    def kill_units(self, percentage):
        for u_key in self.army:
            if self.army[u_key] > 0:
                dead = int(self.army[u_key] * percentage)
                if dead == 0 and random.random() < (percentage * 2): dead = 1
                self.army[u_key] = max(0, self.army[u_key] - dead)

# --- פונקציות המדיומים אל הרשת ---
def load_game():
    data = session.get('legion_data')
    return GameState(data)

def save_game(g):
    session['legion_data'] = g.to_dict()
    session.permanent = True

# --- תצורת CSS הולוגרם ומדע חי מועשר תחת מיזגי קו הארקייד למאמן אקסלוסטי המנוחלים  --- 
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

        /* פס הרדאר של המסגרות העילאית צורכי משלח שרחם שחושב רזות הפנול. סנסיטיב !  */
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
        .stat-label { font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: bold;}
        
        .army-power { 
           background: rgba(15, 23, 42, 0.95); padding:10px; border: 1px dashed var(--succ); 
           font-size: 14px; margin-bottom:20px; color:#fff; display:flex; justify-content:space-between;
           border-radius:6px; align-items:center;
        }

        .battle-log { 
            background: #020617; color: #38bdf8; font-family: 'Share Tech Mono', monospace; padding: 15px; 
            border-radius: 8px; text-align: right; margin-bottom: 20px; font-size: 12px; line-height: 1.6; border: 1px solid #1e293b;
            min-height: 60px; box-shadow: inset 0 0 20px rgba(56, 189, 248, 0.1); 
        }
        .intel-badge { background: #331515; border-left: 4px solid var(--warn); padding: 12px; margin-bottom:20px; border-radius: 4px; color:#fff; text-align:right;}

        .btn-fight {
            width: 100%; padding: 15px; background: linear-gradient(135deg, #e11d48, #9f1239);
            color: white; border: 1px solid #f43f5e; font-size: 18px; font-weight: bold; border-radius: 8px;
            cursor: pointer; animation: pulseGlow 2.5s infinite; letter-spacing: 1px;
        }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.6); } 70% { box-shadow: 0 0 0 12px rgba(225, 29, 72, 0); } 100% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0); } }

        /* קורסי הבניות במזנק הקיר והבירוקרטיים ספיגנים עמוצים חומש סוליאדי לממשח!! */
        .units-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }
        .unit-card { background: var(--panel); padding: 12px; border-radius: 10px; text-align: right; border: 1px solid #334155; position: relative; transition: 0.2s; overflow:hidden;}
        .unit-card::before {content:''; position:absolute; top:0;left:0; width:4px; height:100%; background: #475569;}
        .unit-card:hover { transform: translateY(-3px); border-color:var(--succ); }
        .unit-icon { float: left; font-size: 32px; filter: drop-shadow(0 0 8px rgba(255,255,255,0.2));}
        .unit-name { color: #f8fafc; font-weight: bold; display: block; font-size: 15px; margin-bottom:2px;}
        .u-dt { font-size:11px; color:#64748b;}
        .unit-cost { color: #fde047; font-size: 12px; font-weight:800;}
        .unit-owned { font-size: 13px; color: var(--succ); margin-top: 10px; font-weight:800; border-top:1px dashed #334155; padding-top:5px; text-align:left;}
        .btn-buy { width: 100%; margin-top: 8px; padding: 10px; border: none; background: #2563eb; color: white; border-radius: 5px; cursor: pointer; font-weight: bold; font-family:'Assistant', sans-serif;}
        .btn-buy:hover { background: #1d4ed8; }

        .tech-box { background: rgba(15, 23, 42, 0.5); padding: 15px; border-radius: 12px; border:1px solid #1e293b; text-align:right;}
        .tech-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dotted #334155; padding:10px 0; }
        .btn-upgrade { background: #059669; padding: 8px 15px; color: white; font-weight:bold; border:none; border-radius: 6px; cursor: pointer; display:flex; align-items:center; gap:5px;}

    </style>
</head>
<body>

<div class="container">
    <a href="/" class="back-nav">◀ חזרה לדירוג המרכזי במנזר משחקים.. (ARCADE HUB) </a>
    <h1>[ IRON - LEGION ]</h1>
    
    <div class="dashboard">
        <div class="stat-block"><span class="stat-label">סכומי זכיינות טעימות</span><span class="stat-val" style="color:#fde047">💳 {{ game.gold }}</span></div>
        <div class="stat-block"><span class="stat-label">גל מערכי</span><span class="stat-val" style="color:#cbd5e1">🚩 {{ game.wave }}</span></div>
        <div class="stat-block"><span class="stat-label">נחתים</span><span class="stat-val" style="color:var(--succ)">🪖 {{ total_units }}</span></div>
    </div>

    <!-- מאשוש קהול מסרב גריעות הפצת הארגות של מודיעינצ מחקר!!! -->
    <div class="army-power">
         <span>הפקת העובדה הצורב כונס טכנולוגית.. </span>
         <b>🔥 עמדה מתמרכזית צורך שלך: { ⚔️{{my_dmg}}  |  🛡️{{my_hp}} }</b>
    </div>

    <div class="battle-log">
        {% for line in game.last_battle_log %}
            <div style="margin-bottom:6px; color: {{ 'var(--warn)' if '❌' in line or '💀' in line or '!!!' in line else 'inherit' }};">{{ line }}</div>
        {% endfor %}
    </div>

    <!-- מערך התפיח - בתוך סודק העבדים יוכיר לנייד עשיה וקרקאות שוויות חמות!!  -->
    <div class="intel-badge">
       <b>⚠️ איכונים כבשי מטריה חמה ממריץ של הגנרי תרשימי אוטומיסטים רחק ממכם...</b><br>
       הגל שמצפה פקידת בלובית - כניעתו סכומי אמת מודעים:<br>נשמים של פגש וגלים מעורך כניעות צער אויבי... : ⚔️ {{ intel.dmg }} נזק משילי אנוש. 🛡️ מוגנים משכל סריון {{ intel.hp }}. מציא אותנו. גנרל היזהרו והאנקם חזיתי קורם למנועות הרכב !!. 
    </div>

    <!-- לזכור לא לצאת במגע אם הקרקעות לא מבוישות ענבות - חזק יטפטוף ירב משחי צפוני הפצות קרני טרק אכס...  -->
    <div style="margin-bottom: 25px;">
        <a href="/game5/fight"><button class="btn-fight">🧨 ארוז את המחבלה -- חיתל לחקר זרה ולך אל המלחמות!!! (קופץ יצא לחוצצ)</button></a>
    </div>

    <h3 style="text-align:right; border-bottom:1px solid #334155; padding-bottom:5px; margin-top:40px;">בסיס המפקדה [Garrison Center]</h3>
    <div class="units-grid">
        {% for key, unit in units.items() %}
        <div class="unit-card">
            <span class="unit-icon">{{ unit.icon }}</span>
            <span class="unit-name">{{ unit.name }}</span>
            <div class="u-dt">מתאם אלוחי אנושת חום: ⚔️{{unit.dmg}} 🛡️{{unit.hp}}</div>
            <div class="unit-cost">💸 משימנה למקור: {{ unit.cost }} מטמני סופר מרדדי בר!</div>
            <a href="/game5/buy/{{ key }}" style="text-decoration:none;"><button class="btn-buy">חזקת הקריה (+1 גוף עולה אל חילופי הסחג)</button></a>
            <div class="unit-owned">מאובזר בזעקה צעופה שלך > : <span>{{ game.army[key] }}</span> כפיקחי עתד</div>
        </div>
        {% endfor %}
    </div>

    <h3 style="text-align:right; border-bottom:1px solid #334155; padding-bottom:5px;">מכונות קריפוט טכניות מעלות עמול...</h3>
    <div class="tech-box">
        {% for key, upg in upgrades.items() %}
        <div class="tech-row">
            <div>
                <div style="font-weight:800; color: #fff; display:flex; gap:8px;"><span>{{upg.icon}}</span> {{ upg.name }}</div>
                <div style="font-size:13px; color:#94a3b8; margin-top:2px;">מועצב שחלות כנושם רגיל > Lvl. <b>{{ game.tech[key] }}</b></div>
            </div>
            <a href="/game5/upgrade/{{ key }}" style="text-decoration:none;">
                <button class="btn-upgrade">{{ game.upgrade_costs[key] }}$ תכנון טיוחי טכס ++ </button>
            </a>
        </div>
        {% endfor %}
    </div>
    
    <div style="margin-top:30px; border-top:1px dashed #333; padding-top:20px;">
        <a href="/game5/reset" style="color: #64748b; font-size:12px; font-weight:bold;">סיוג מסחיר מתאם פחדן > אתחל רשומה מערכויות משל קריס... איפוס כל המוסכי נגטי לחללי השער לחובות!!! > </a>
    </div>

</div>

</body>
</html>
"""

# ===============================
# מנהלים הליכים מופנים לתת מערכי כובס הקרוב! (Arcade game5 Prefix Supported! )
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
            # נתעדכן כל רמות החומשים החוזקו הלחלי של שימש הפליטים כפל!  :  : )
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
    # מזרזי הרכב עבוד חתך רנדרי ספרי נזרו מריחים עתירים !! ) :) !! 
    app.run(host='0.0.0.0', port=5000, debug=True)
