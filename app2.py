import random
import uuid
from flask import Flask, redirect, session
from jinja2 import Environment, BaseLoader

app = Flask(__name__)
# מפתח הצפנה עבור עוגיות ה-Session 
app.secret_key = "rpg_legend_secret_super_key_123"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # שמירה ל-30 יום

# --- HTML TEMPLATE המשודרג עם תמונת הרקע ---
HTML_TEMPLATE_STR = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPG Legends: Golden Forest</title>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Cinzel:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {
            --gold: #FFD700;
            --dark-bg: #0d1117;
            --panel-bg: rgba(30, 34, 42, 0.85);
            --danger: #ff4d4d;
            --safe: #4CAF50;
        }

        body { 
            /* שילוב התמונה background.jpg עם מסך הצללה כדי שהמשחק יבלוט */
            background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.8)), url('/static/background.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-color: #0d0d0f; /* צבע גיבוי למקרה שהתמונה לא נטענה */
            color: #c5c6c7; font-family: 'Assistant', sans-serif; 
            margin: 0; padding: 20px 10px; display: flex; flex-direction: column; 
            align-items: center; min-height: 100vh; overflow-x: hidden;
        }

        /* חלקיקי זהב/עלים מסתובבים ברקע */
        #particles-js { position: fixed; width: 100vw; height: 100vh; top: 0; left: 0; z-index: -1; pointer-events: none;}

        .game-card { 
            background: var(--panel-bg); width: 100%; max-width: 520px; 
            padding: 20px; border-radius: 15px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.8), 0 0 20px rgba(255, 215, 0, 0.1); 
            border: 2px solid #332f1b; position: relative; backdrop-filter: blur(8px);
        }

        h2 { 
            margin: 0 0 15px 0; color: var(--gold); text-align: center; 
            font-family: 'Cinzel', serif; font-size: 28px; text-shadow: 0 2px 10px rgba(255, 215, 0, 0.4); 
            letter-spacing: 2px;
        }

        .stats-grid { 
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; 
            background: rgba(0,0,0,0.6); padding: 12px; border-radius: 10px; 
            margin-bottom: 20px; text-align: center; border: 1px solid #444; 
            font-weight: bold; color: #fff;
            box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
        }

        .stat-box { display: flex; flex-direction: column; align-items: center; justify-content: center; font-size:14px; }
        .stat-icon { font-size: 20px; margin-bottom: 3px; }

        /* פס חיים משודרג */
        .hp-wrapper { width: 100%; grid-column: span 4; margin-top: 5px; }
        .hp-container { 
            background: #222; height: 14px; border-radius: 10px; 
            overflow: hidden; box-shadow: inset 0 2px 5px rgba(0,0,0,0.9); border: 1px solid #555;
        }
        
        {% set hp_percent = (p.hp / p.max_hp) %}
        .hp-fill { 
            height: 100%; width: {{ hp_percent * 100 }}%; 
            transition: width 0.5s cubic-bezier(0.4, 0.0, 0.2, 1); 
            box-shadow: 0 0 10px var(--safe); background-image: linear-gradient(90deg, #1f6b21, #4CAF50);
            {% if hp_percent <= 0.3 %}
            background-image: linear-gradient(90deg, #8b0000, #ff3333); box-shadow: 0 0 15px #ff3333;
            animation: pulse-danger 0.8s infinite alternate;
            {% endif %}
        }
        @keyframes pulse-danger { 0% { opacity: 0.8; } 100% { opacity: 1; filter: brightness(1.5); } }

        /* זירת ההתרחשות */
        .scene { 
            /* הפכנו את הזירה לשקופה קצת כדי שהרקע מאחורה יוסיף עומק! */
            background: linear-gradient(to bottom, {{ bg_color }} 0%, rgba(0,0,0,0.8) 100%); 
            height: 180px; border-radius: 12px; margin-bottom: 20px; 
            position: relative; display: flex; flex-direction: column; justify-content: center; align-items: center; 
            font-size: 65px; text-shadow: 0 5px 15px black; border: 2px solid #524724; 
            box-shadow: inset 0 0 50px rgba(0,0,0,0.9); overflow: hidden;
        }
        
        /* אפקט תזוזת הדמות */
        .scene-icon { animation: float 3s ease-in-out infinite; transition: transform 0.2s; }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        
        /* הנפשת התקפה דרך JS תפעיל קלאס זה */
        .shake-impact { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; color: red;}
        @keyframes shake { 10%, 90% { transform: translate3d(-4px, 0, 0) scale(1.1); } 20%, 80% { transform: translate3d(6px, 0, 0) scale(1.1); } 30%, 50%, 70% { transform: translate3d(-10px, 0, 0) scale(1.1); } 40%, 60% { transform: translate3d(10px, 0, 0) scale(1.1); } }

        .scene-badge { 
            position: absolute; bottom: 10px; font-size: 15px; background: rgba(0,0,0,0.7); 
            padding: 5px 15px; border-radius: 20px; color: var(--gold); border: 1px solid var(--gold); font-weight: bold;
        }
        
        .enemy-hp { position:absolute; top: 10px; width: 80%; }
        
        /* יומן קרב */
        .logs-wrapper {
            background: rgba(0,0,0,0.75); padding: 15px; height: 110px; overflow-y: hidden; 
            border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; 
            display:flex; flex-direction:column-reverse; position: relative;
        }
        .logs-wrapper::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 30px; background: linear-gradient(rgba(0,0,0,1), transparent); pointer-events: none; }
        
        .log-line { margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px dashed #222; font-size: 15px; opacity: 0.8; transition: 0.3s; }
        .log-line:first-child { opacity: 1; font-weight: bold; font-size: 16px; border: none; } 
        
        .log-good { color: #5ce65c; } .log-bad { color: #ff4d4d; } .log-alert { color: var(--gold); } .log-gold { color: #ffeb3b; }

        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        
        /* כפתורים משודרגים כמו שלטי משחק */
        button { 
            background: linear-gradient(to bottom, #2b3344, #181d28); border: 2px solid #4a5c7c; 
            color: #d1d8e0; padding: 15px; font-size: 16px; cursor: pointer; border-radius: 10px; 
            font-weight: 800; text-shadow: 0 1px 3px black; box-shadow: 0 4px 6px rgba(0,0,0,0.5); 
            transition: all 0.15s; position: relative; overflow: hidden; font-family: 'Assistant', sans-serif;
        }
        
        button::before { content:''; position: absolute; top:0;left:-100%; width:50%; height:100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); transform: skewX(-20deg); transition: 0s; }
        button:hover { filter: brightness(1.2); transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.6); }
        button:hover::before { left: 150%; transition: 0.6s ease; }
        button:active { transform: translateY(2px); box-shadow: 0 2px 4px rgba(0,0,0,0.6); }

        .combat-btn { background: linear-gradient(to bottom, #591919, #360b0b); border-color: #ff4d4d; color: #ffb3b3;}
        .heal-btn { background: linear-gradient(to bottom, #1d4d1d, #0b2b0b); border-color: #4CAF50; color: #b3ffb3;}
        .shop-btn { background: linear-gradient(to bottom, #4d4013, #2b2308); border-color: var(--gold); color: #fffde0;}
        .travel-btn { background: linear-gradient(to bottom, #1a3b40, #0a1f22); border-color: #4df;}

        a.back-menu { display:block; margin-top: 20px; color: #bbb; font-size: 14px; text-decoration:none; text-align: center; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 10px;}
        a.back-menu:hover { color: var(--gold); text-shadow: 0 0 10px var(--gold); background: rgba(0,0,0,0.8); }
        
        /* Flash Red overlay upon hit */
        .flash-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: red; opacity: 0; pointer-events: none; z-index: 100; transition: opacity 0.5s; }
        .flash-active { animation: hit-flash 0.3s forwards; }
        @keyframes hit-flash { 0% {opacity:0.4;} 100% {opacity:0;} }
    </style>
</head>
<body>
    <div class="flash-overlay" id="flash-screen"></div>

    <div class="game-card">
        <h2>יער הזהב וממלכת הצללים</h2>
        <div class="stats-grid">
            <div class="stat-box"><span class="stat-icon">⭐</span> {{ p.level }} רמה</div>
            <div class="stat-box"><span class="stat-icon">💰</span> {{ p.gold }}ג</div>
            <div class="stat-box"><span class="stat-icon">⚔️</span> {{ p.damage }} כוח</div>
            <div class="stat-box"><span class="stat-icon">🧪</span> {{ p.potions }} ש"ח</div>
            
            <div class="hp-wrapper">
                <div style="font-size:12px; margin-bottom:3px; display:flex; justify-content:space-between">
                    <span style="color:#ff6666">❤️ {{ p.hp }}/{{ p.max_hp }} ({{ p.xp }}/{{ p.next_level_xp }} XP)</span>
                </div>
                <div class="hp-container"><div class="hp-fill"></div></div>
            </div>
        </div>

        <div class="scene">
            <div class="scene-icon" id="target-icon">{{ emoji_icon }}</div>
            {% if p.in_combat and p.current_enemy %}
            <div class="hp-container enemy-hp"><div class="hp-fill" style="background-image:linear-gradient(90deg, #aa0000, #ff4d4d); box-shadow:none; width:{{(p.current_enemy.hp / p.current_enemy.max_hp)*100}}%;"></div></div>
            {% endif %}
            <div class="scene-badge">{{ location_name }}</div>
        </div>

        <div class="logs-wrapper" id="logs-box">
            {% for log in p.logs %}
                {% set log_class = "" %}
                {% if "נפגעת" in log or "איבדת" in log or "חסר" in log or "מכה אנושה" in log %} {% set log_class = "log-bad" %}
                {% elif "זהב" in log and ("גרם" in log or "+" in log) %} {% set log_class = "log-gold" %}
                {% elif "שיקוי" in log or "שודרג" in log or "ניצחון" in log or "רמה" in log or "הצלחת" in log %} {% set log_class = "log-good" %}
                {% elif "מארב פתע" in log %} {% set log_class = "log-alert" %}
                {% endif %}
                <div class="log-line {{ log_class }}">{{ log }}</div>
            {% endfor %}
        </div>

        <div class="actions">
            {% if p.hp <= 0 %}
                <button data-act="death" data-url="/game2/restart" style="grid-column: span 2; background: #660000; border-color: red;">☠️ מסעך הסתיים. לחץ להתחלה חדשה</button>
            {% elif p.in_combat %}
                <button class="combat-btn" data-act="attack" data-url="/game2/action/attack">⚔️ תקיפת חרב</button>
                <button class="heal-btn" data-act="heal" data-url="/game2/action/heal">🧪 שתיית שיקוי</button>
                <button style="grid-column: span 2;" data-act="run" data-url="/game2/action/flee">🏃 נסיגה פחדנית חזרה (-זהב)</button>
            {% elif p.location == 'town' %}
                <button class="travel-btn" data-act="travel" data-url="/game2/travel/forest">🌲 היכנס ליער הזהב</button>
                <button class="travel-btn" style="border-color: #aa00ff" data-act="travel" data-url="/game2/travel/cave">🦇 מערת אופל הצללים</button>
                <button class="shop-btn" data-act="coin" data-url="/game2/shop/buy_potion">🧪 שיקוי חיים (30ג)</button>
                <button class="shop-btn" data-act="upgrade" data-url="/game2/shop/upgrade_weapon">⚔️ רכישת כוח ({{ p.weapon_level * 60 }}ג)</button>
                <button class="heal-btn" style="grid-column: span 2;" data-act="heal" data-url="/game2/action/inn">🏨 שינה מלאה בפונדק (20ג)</button>
            {% elif p.location == 'forest' or p.location == 'cave' %}
                <button class="combat-btn" data-act="search" data-url="/game2/action/explore" style="grid-column: span 2;">🔍 סייר במעמקים</button>
                <button data-act="travel" data-url="/game2/travel/town" style="grid-column: span 2;">🏠 חזור אל העיר</button>
            {% endif %}
        </div>
    </div>
    <a href="/" class="back-menu">⮜ חזרה לארקייד הראשי </a>

    <!-- מערכת סאונדים, ויזואליה והשהייה אלגנטית! -->
    <script>
        const AContext = window.AudioContext || window.webkitAudioContext;
        const ctx = new AContext();
        
        function playSfx(type) {
            if (ctx.state === 'suspended') ctx.resume();
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            
            const now = ctx.currentTime;
            if (type === 'slash') { 
                o.type = 'sawtooth'; o.frequency.setValueAtTime(150, now);
                o.frequency.exponentialRampToValueAtTime(10, now + 0.1);
                g.gain.setValueAtTime(0.5, now); g.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
                o.start(now); o.stop(now + 0.1);
            } else if (type === 'hit') { 
                o.type = 'square'; o.frequency.setValueAtTime(60, now);
                o.frequency.exponentialRampToValueAtTime(20, now + 0.3);
                g.gain.setValueAtTime(0.6, now); g.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
                o.start(now); o.stop(now + 0.3);
            } else if (type === 'heal' || type === 'upgrade') { 
                o.type = 'sine'; o.frequency.setValueAtTime(400, now);
                o.frequency.linearRampToValueAtTime(800, now + 0.2);
                g.gain.setValueAtTime(0.3, now); g.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
                o.start(now); o.stop(now + 0.3);
            } else if (type === 'coin') { 
                o.type = 'sine'; o.frequency.setValueAtTime(1000, now);
                g.gain.setValueAtTime(0.3, now); g.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
                o.start(now); o.stop(now + 0.1);
            } else { 
                o.type = 'triangle'; o.frequency.setValueAtTime(800, now);
                g.gain.setValueAtTime(0.1, now); g.gain.linearRampToValueAtTime(0.01, now + 0.05);
                o.start(now); o.stop(now + 0.05);
            }
        }

        window.onload = () => {
            const actTriggered = sessionStorage.getItem("trigger_action");
            const sceneIcon = document.getElementById("target-icon");
            const lastLog = `{{ p.logs[0] if p.logs else '' }}`;

            if(actTriggered) { 
                if(actTriggered === "attack") { 
                    playSfx('slash'); 
                    sceneIcon.classList.add("shake-impact"); 
                }
                if(actTriggered === "heal") { playSfx('heal'); }
                if(actTriggered === "coin" || actTriggered === "upgrade") { playSfx('coin'); }
                sessionStorage.removeItem("trigger_action");
            }
            
            if (lastLog.includes("נפגעת") && lastLog.includes("חיים")) {
                setTimeout(() => {
                    playSfx('hit');
                    document.getElementById("flash-screen").classList.add("flash-active");
                }, 100);
            }
        };

        document.querySelectorAll('button[data-url]').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault(); 
                const url = btn.getAttribute('data-url');
                const actionName = btn.getAttribute('data-act');
                
                playSfx(actionName);
                if(actionName === 'attack') document.getElementById("target-icon").classList.add("shake-impact");

                sessionStorage.setItem("trigger_action", actionName);
                setTimeout(() => window.location.href = url, 200);
            };
        });
    </script>
</body>
</html>
"""

jinja_env = Environment(loader=BaseLoader())
game_template = jinja_env.from_string(HTML_TEMPLATE_STR)

# --- MODELS מורשת יער הזהב המשופרת ---
class Enemy:
    def __init__(self, name, level, hp=None):
        self.name = name; self.level = level; 
        self.max_hp = 25 + (level * 15) 
        self.hp = hp if hp is not None else self.max_hp
        self.damage = 5 + (level * 4)
        self.xp_reward = 25 * level
        self.gold_reward = random.randint(15, 40) * level
        
    def to_dict(self): return {"name": self.name, "level": self.level, "hp": self.hp}
    @classmethod
    def from_dict(cls, data):
        if not data: return None
        return cls(data["name"], data["level"], data["hp"])

class Player:
    def __init__(self, data=None):
        if data:
            self.id = data.get("id", str(uuid.uuid4()))
            self.hp = data.get("hp", 100); self.max_hp = data.get("max_hp", 100)
            self.level = data.get("level", 1); self.xp = data.get("xp", 0); self.next_level_xp = data.get("next_level_xp", 100)
            self.gold = data.get("gold", 50); self.damage = data.get("damage", 20); self.potions = data.get("potions", 3)
            self.location = data.get("location", "town"); self.in_combat = data.get("in_combat", False)
            self.current_enemy = Enemy.from_dict(data.get("current_enemy"))
            self.weapon_level = data.get("weapon_level", 1)
            self.logs = data.get("logs",["🛡️ ברוכים הבאים. האגדה של 'יער הזהב' חוזרת לחיים."])
        else:
            self.id = str(uuid.uuid4()); self.hp = 100; self.max_hp = 100; self.level = 1
            self.xp = 0; self.next_level_xp = 100; self.gold = 50
            self.damage = 20; self.potions = 3; self.location = "town"
            self.in_combat = False; self.current_enemy = None
            self.weapon_level = 1; self.logs =["🛡️ אגדת יער הזהב המקורית חוזרת... התחמש והכן עצמך!"]

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
            if self.hp >= self.max_hp: return self.add_log("אין צורך, החיים שלך מלאים לחלוטין!")
            heal_amount = 40 + (self.level * 10) 
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.potions -= 1
            self.add_log(f"קנית {heal_amount} חיים משיקוי! (נותרו: {self.potions} 🧪)")
        else: self.add_log("אין לך מספיק שיקויים בכלל... חזור לחנות המקומית!")

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.level += 1; self.xp -= self.next_level_xp; self.next_level_xp = int(self.next_level_xp * 1.5)
            self.max_hp += 20; self.hp = self.max_hp; self.damage += 8
            self.add_log(f"⭐ השתדרגת! רמה חדשה ({self.level}). החיים והכוח שוקמו.")
        else:
            self.add_log(f"+ צברת {amount} ניסיון מהקרב.")

# --- Session Management  ---
def load_player():
    data = session.get('rpg_legend_v3') 
    if data: return Player(data)
    return None

def save_player(player):
    session.permanent = True
    session['rpg_legend_v3'] = player.to_dict()

# --- ROUTES ---

@app.route('/')
def home():
    p = load_player()
    if not p:
        p = Player(); save_player(p)
        return redirect('/game2/')  

    # הגדרנו צבעים שקופים ל-rgba כדי שהתמונה רקע תשתלב בפנים!
    bg_color = "rgba(61, 45, 11, 0.4)"; icon = "🏰"; loc_name = "העיר המרכזית - מסחר ובטחה"
    if p.in_combat and p.current_enemy:
        bg_color = "rgba(54, 22, 22, 0.5)"; 
        ei = "🐕" if "כלב" in p.current_enemy.name else "🐻" if "דוב" in p.current_enemy.name else "🐅" if "נמר" in p.current_enemy.name else "🦁" if "אריה" in p.current_enemy.name else "🐘" if "פיל" in p.current_enemy.name else "👿"
        icon = f"{ei}"
        loc_name = f"{p.current_enemy.name} הופיע! מפלצת רמה {p.current_enemy.level}"
    elif p.location == "forest":
        bg_color = "rgba(22, 53, 32, 0.5)"; icon = "🍂🌳"; loc_name = "אמצע היער של קדם (חיות טבע)"
    elif p.location == "cave":
        bg_color = "rgba(23, 15, 46, 0.5)"; icon = "🌫️⛰️"; loc_name = "מערת אדון החיות - חושך טוטאלי"

    save_player(p)
    return game_template.render(p=p, bg_color=bg_color, emoji_icon=icon, location_name=loc_name)

@app.route('/restart')
def restart():
    session.pop('rpg_legend_v3', None)
    return redirect('/game2/')

@app.route('/travel/<destination>')
def travel(destination):
    p = load_player()
    if not p or p.hp <= 0 or p.in_combat: return redirect('/game2/')
    
    if destination in {"town", "forest", "cave"}:
        if destination == "cave" and p.level < 4:
            p.add_log("שומר המערה: 'חזור! חיות בפנים יהרגו אותך! (נדרש רמה 4+) ⛔")
        else:
            p.location = destination
            p.add_log(f"הגעת אל: {destination}.")
    save_player(p); return redirect('/game2/')

@app.route('/shop/<action>')
def shop(action):
    p = load_player()
    if not p or p.location != "town": return redirect('/game2/')

    if action == "buy_potion":
        if p.gold >= 30: p.gold -= 30; p.potions += 1; p.add_log("רכשת מילוי שיקוי 🧪 למסע.")
        else: p.add_log("הסוחר קופץ. חסר לך זהב. (צריך 30ג).")
    elif action == "upgrade_weapon":
        cost = p.weapon_level * 60
        if p.gold >= cost:
            p.gold -= cost; p.damage += 15; p.weapon_level += 1
            p.add_log(f"רכשת שידרוג כוח! (כוח התקפה עלה ל-{p.damage}).")
        else: p.add_log(f"חסר מספיק זהב, השידרוג עולה ({cost}ג).")
    save_player(p); return redirect('/game2/')

@app.route('/action/<act>')
def perform_action(act):
    p = load_player()
    if not p: return redirect('/game2/')
    
    if p.hp <= 0: return redirect('/game2/')

    if act == "explore" and not p.in_combat:
        if random.random() > 0.60: p.add_log("אתה מהלך בזהירות בתוך השטח, ולפתע הכל דומם... אין זכר לאיש.")
        else: start_combat(p)

    elif act == "attack" and p.in_combat: handle_combat_round(p)

    elif act == "heal":
        if p.potions > 0: p.heal(); 
        if p.in_combat: enemy_turn(p)

    elif act == "flee" and p.in_combat:
        loss = int(p.gold * 0.20)
        p.gold -= loss; p.in_combat = False; p.current_enemy = None; p.location = "town"
        p.add_log(f"ברחת בעור שיניך וחזרת העירה בבכי. עמלת בדרך לאבד {-loss}גרם זהב.")

    elif act == "inn" and p.location == "town":
        if p.gold >= 20: 
            p.gold -= 20; p.hp = p.max_hp
            p.add_log("התארחת בחדר של ראש העיר, הבריאות הוחזרה לחיים למקסימום. 💤")
        else: p.add_log("צריך עוד טיפה זהב! (עולה 20ג) חסר לך מספיק זהב.")

    save_player(p); return redirect('/game2/')

def start_combat(p):
    forest_animals =[("כלב טועה נושך", 1), ("דוב היער האכזרי", 2), ("נמר מסוות בין עצים", 3)]
    cave_demons =[("אריה הרים מתורף", 4), ("פיל מוזהב מטין כבד (בוס שומר)", 6), ("שד מערות אלפא אכזרי", 8)]
    
    choice = random.choice(forest_animals) if p.location == "forest" else random.choice(cave_demons)
    if choice[1] >= 6 and p.level < 5: choice = ("עטלף קרנבל ענקי טרף", 5) 

    p.current_enemy = Enemy(choice[0], choice[1]); p.in_combat = True
    p.add_log(f"⚠️ הרגשת סכנה גדולה! {p.current_enemy.name} יוצא למתקפה עליך.")

def handle_combat_round(p):
    e = p.current_enemy
    miss_chance = random.random()
    if miss_chance > 0.90:
        p.add_log(f"מכתך עברה מעל ראשו! {e.name} התחמק מהחרב.")
    else:
        is_crit = random.random() > 0.70
        dmg = int(p.damage * 1.5) if is_crit else p.damage
        e.hp -= dmg
        p.add_log(f"הורדת {dmg} נזק מדמם במכת מחץ אנושה!" if is_crit else f"התקפתך חדרה דרך הפרווה, גרמת {-dmg} לחיים שלו.")

    if e.hp <= 0:
        p.in_combat = False; p.gold += e.gold_reward; 
        p.add_log(f"הצלחת להכניע את {e.name}! 🏆 חיטטת ומצאת +{e.gold_reward} גרם זהב! מדהים.")
        p.gain_xp(e.xp_reward)
        p.current_enemy = None
    else: enemy_turn(p)

def enemy_turn(p):
    if p.hp <= 0: return 
    
    if random.random() > 0.85: p.add_log(f"בלימה יפה! ברחת בזמן מתנופף והשבץ לא הגיע, התחמקת מנזק.")
    else:
        base_dmg = p.current_enemy.damage
        reduction = p.level * 2 
        final_dmg = max(1, base_dmg - reduction)
        dmg = final_dmg + random.randint(-2, 3)
        p.hp -= dmg
        p.add_log(f"ספגת מכה קשה! נפגעת ואתה איבדת {dmg} נקודות חיים. הזהר!!")
        
    if p.hp <= 0:p.hp = 0; p.in_combat = False; p.add_log("☠️ מסך העיניים שלך רועד לאיטו והחשכה משיגה... אבוד במעבה 'יער הזהב'.")

if __name__ == '__main__':app.run(port=5000, debug=True)
