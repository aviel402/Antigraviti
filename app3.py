import random
from flask import Flask, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "genesis_space_odyssey_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # שמירת המשחק ל-30 יום!

# ===============================
# בנק אירועי החללית שלנו!
# ===============================
EVENTS =[
    {
        "id": 0, "title": "מטר אסטרואידים סלעי", "desc": "ראדאר המגן מראה ענן סלעי קרח וברזל לפנינו.",
        "choices":[
            {"txt": "הפעל חומות כוח מלאות (20- אנרגיה)", "effect": {"energy": -20}},
            {"txt": "תמרן (קשה), ספוג תפגיעה אם ניכשל (20- מגן)", "effect": {"hull": -20}}
        ]
    },
    {
        "id": 1, "title": "סוחר שוק שחור בגזרה B", "desc": "קפלן של סוחרי פיראטים מתקרב.",
        "choices":[
            {"txt": "רכוש 30 קפסולות מזון (150- קרדיט)", "effect": {"credits": -150, "food": 30}},
            {"txt": "רוקן קבלי כוח תמורת מימון מיוחד (200+ קרדיט, 30- אנרגיה)", "effect": {"credits": 200, "energy": -30}},
            {"txt": "דלג! המשך לשייט קבוע.", "effect": {}}
        ]
    },
    {
        "id": 2, "title": "מוטציה כימית באגף 4", "desc": "קצין חקר מדווח על טחב רעיל שהורס מאגרי מזון תקינים.",
        "choices":[
            {"txt": "השמד כל מדור פגום מיידית כדי להציל את השאר (25- מזון)", "effect": {"food": -25}},
            {"txt": "לחקור, לקרר. ואנחנו חייבים לאכול את השארית... (5 אבדות בצוות מחולות)", "effect": {"crew": -5}},
        ]
    },
    {
        "id": 3, "title": "גילית אות מצוקה צפון כוכבי", "desc": "הנשמעות שרידות במצולות השחקים.",
        "choices":[
            {"txt": "צא לעזור (15- אנרגיה, מקבלים סבירות של פרס כספי של 100+)", "effect": {"energy": -15, "credits": 100}},
            {"txt": "שגרה נוהלית. התעלם (יפיל משקל ומצב רוח אנשיי לחימה..)", "effect": {"credits": -10}} 
        ]
    },
    {
        "id": 4, "title": "סופת לחצים והפגת דלק", "desc": "מהלך הירידות הקפוא של החללית עושה דברים רעים, קפוא שם!",
        "choices":[
            {"txt": "רתק משיכה, תחזק כוון וקור בלוחות נמסים (-150 C. כוח המערכת והמעטפת +10)", "effect": {"credits": -150, "hull": 10}},
            {"txt": "שמרו על קפיאות ונסו לא לנשום מזיקים... מסכי הלב כבו בלובי. (+10 אנרגיה ניחוח דל.)", "effect": {"energy": 10, "food": 5}}, 
        ]
    },
    {
        "id": 5, "title": "קצר בלוחות חכמים פריים B", "desc": "לייזר מילולי מספק צלע חשמלית בחסר סנסורים...",
        "choices":[
             {"txt": "הזעק תתי-הנחתים לחסימות ידניות (-10 גוף חיצוני אבודה אסטרגט... 3 חלילים הלכו למעןנו!)", "effect": {"hull": -10, "crew": -3}},
             {"txt": "שלם מס כבדים רדוד לחומרה רטיבילית חזרוות כוח וטעינות מלאים (-200 כסף קרח +10 נשמור ואנרגיית חימומים)", "effect": {"credits": -200, "energy": 10, "hull": 5}}
        ]
    }
]

# ===============================
# הלוגיקה המשחיתות שלנו ב-State 
# ===============================
class SpaceshipState:
    def __init__(self, data=None):
        if data:
            self.week = data.get("week", 1)
            self.max_weeks = data.get("max_weeks", 20)
            self.crew = data.get("crew", 100)
            self.food = data.get("food", 100)
            self.energy = data.get("energy", 100)
            self.hull = data.get("hull", 100)
            self.credits = data.get("credits", 500)
            self.log = data.get("log", ["קפטן, מסד הנתונים קלט אות מחדש."])
            self.game_over = data.get("game_over", False)
            self.victory = data.get("victory", False)
            self.current_event_id = int(data.get("current_event_id", 0))
        else:
            self.week = 1; self.max_weeks = 20
            self.crew = 100; self.food = 100
            self.energy = 100; self.hull = 100
            self.credits = 500
            self.log =["יומן קפטן. ההרפתקה שולחת מיד קו חיים הופעל!"]
            self.game_over = False; self.victory = False
            self.current_event_id = 0
            self.pick_random_event()

    def to_dict(self):
        return {
            "week": self.week, "max_weeks": self.max_weeks, "crew": self.crew,
            "food": self.food, "energy": self.energy, "hull": self.hull,
            "credits": self.credits, "log": self.log, 
            "game_over": self.game_over, "victory": self.victory, 
            "current_event_id": self.current_event_id
        }

    def pick_random_event(self):
        evt = random.choice(EVENTS)
        self.current_event_id = int(evt['id'])

    def current_event(self):
        for e in EVENTS:
             if e['id'] == self.current_event_id:
                  return e
        return EVENTS[0] # במקרה ומסיבה הזויה האידי לא תואם

    def add_log(self, msg):
        self.log.insert(0, f">[W{self.week}] {msg}")
        if len(self.log) > 4: 
            self.log.pop()

    def consume_resources(self):
        food_con = int(self.crew * 0.15) 
        nrg_con = 8 if self.week > 10 else 5  # כשאתם יותר בטיול החללית קר קשה וארוכה!

        self.food -= food_con
        self.energy -= nrg_con
        
        if self.food < 0:
            starved = abs(self.food)
            self.crew -= starved 
            self.food = 0
            self.add_log(f"התראת רעב עולמית קרטיוויטי !! מחכים מוות בענן שיוט סדון... {-starved} אנשים נפחו את דרכם!")
        if self.energy <= 0:
             self.energy = 0
             self.hull -= 15
             self.add_log("חומת בנקי כביסה ואקום חזירים צוחקו מכבל האנרגיה שהושבת נפסדת מהיסוד כדור חי! אוקריים -15 יציבות")

    def check_status(self):
        if self.hull <= 0:
            self.game_over = True
            self.add_log("פיצוץ!! הכור של מערת הפנטיה רמש, חרדות בנחוצות ליל יטרילי אובדנות - Game over חוסל!")
        elif self.crew <= 0:
            self.game_over = True
            self.add_log("אין שרד מיחיים הטיפות... מערכת זכר הסוף רפאים כלי רפאים רכב חי..")
        elif self.week > self.max_weeks:
            self.victory = True
            self.add_log("שדה הכבונה ניכרו בשקיים אהוו מאדים מתחיל. כל הסקרים ליל סוף הצלה!! ")


# ===============================
# השמירת העוגיה Serverless
# ===============================
def load_ship():
    data = session.get('genesis_data')
    if data: return SpaceshipState(data)
    return None

def save_ship(ship_state):
    session.permanent = True
    session['genesis_data'] = ship_state.to_dict()


# ===============================
# UI & DESIGN (Sci-Fi Neon interface)
# ===============================
TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Genesis Terminal Override</title>
    <link href="                                                           ;display=swap" rel="stylesheet">
    <style>
        :root {
            --n: #00f3ff;   /* חולות הולוגרם ציאיני של מאקוסק תקיעות סרט מסכים רחיק קדוש */
            --alert: #ff003c;
            --success: #39ff14;
            --bg-glass: rgba(0, 15, 30, 0.7);
        }
        body { margin: 0; padding: 20px; background: radial-gradient(circle at 50% 50%, #031526, #01080e 100%); color: var(--n); font-family: 'Share Tech Mono', 'Courier New', monospace; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        
        body::before { content: ""; position: absolute; top:0; left:0; right:0; bottom:0; background-image: linear-gradient(rgba(0,243,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,243,255,0.03) 1px, transparent 1px); background-size: 30px 30px; z-index: -1; }
        .sys-container { width: 100%; max-width: 650px; background: var(--bg-glass); border: 1px solid rgba(0,243,255,0.3); border-radius: 8px; box-shadow: 0 0 15px rgba(0,243,255,0.1); padding: 20px; box-sizing:border-box;}
        
        h1 { font-size: 24px; border-bottom: 2px dashed rgba(0,243,255,0.5); padding-bottom:10px; text-transform:uppercase; margin-top:0;}
        h1::before { content: "SYS.CORE //> "; opacity: 0.6; }
        
        .progress-hud { margin: 15px 0;}
        .trip-label { font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }
        .trip-track { background: #000; height: 10px; border: 1px solid var(--n); position:relative; overflow:hidden;}
        {% set prog = (s.week / s.max_weeks) * 100 %}
        .trip-fill { background: var(--n); height: 100%; width: {{ prog }}%; transition: 0.8s; }
        
        .status-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; margin: 15px 0; border: 1px solid rgba(0, 243, 255, 0.3); background: #01111a; padding: 10px; text-align: center; }
        .gauge-item { display:flex; flex-direction:column; padding: 5px; background:rgba(0,0,0,0.5); border-radius:3px; }
        .g-label { font-size: 11px; opacity:0.7; font-weight:bold; }
        .g-val { font-size: 18px; margin-top: 5px; font-weight: bold; }
        
        {% if s.energy < 25 or s.food < 25 or s.hull < 30 %} .sys-container { animation: warningBlink 1.5s infinite;} @keyframes warningBlink { 50% { box-shadow: 0 0 20px rgba(255,0,60,0.4); border-color: rgba(255,0,60,0.6); } } {% endif %}
        .g-food { color: {% if s.food < 25 %} var(--alert) {% else %} var(--n) {% endif %}; }
        .g-nrg  { color: {% if s.energy < 25 %} var(--alert) {% else %} var(--n) {% endif %}; }
        .g-hull { color: {% if s.hull < 30 %} var(--alert) {% else %} var(--success) {% endif %}; }
        
        .cap-log { background: #00040a; border-right: 3px solid var(--n); color: #ccc; font-size: 12px; min-height: 80px; padding: 10px; margin-bottom: 20px; font-family: monospace; line-height:1.5; text-align: right; box-shadow: inset 0 0 5px rgba(0,243,255,0.1); }
        .screen-ui { background: rgba(0,10,20,0.8); padding: 20px; border: 1px solid rgba(0,243,255,0.4); text-align: right; margin-bottom: 15px; position:relative; border-radius:5px;}
        .desc-text { font-size:15px; color:#fff; line-height: 1.4; margin-bottom:15px;}
        
        /* הכפתורים השקופים עכשיו נושאים עיצוב שמוחזק חזק וללא באג התג "a" בלחיצות תכנוץ Vercel */
        .choices-box { display:flex; flex-direction:column; gap:8px; }
        .opt-btn { 
            display:block; width: 100%; box-sizing:border-box; background: rgba(0,10,25,0.9);
            border: 1px solid rgba(0, 243, 255, 0.5); color: #fff; padding: 15px; font-family: 'Share Tech Mono', sans-serif;
            text-align: right; text-decoration: none; cursor: pointer; transition: 0.2s; font-size:15px; border-radius:3px;
        }
        .opt-btn::before { content: " [>] "; color:var(--n); opacity:0.8; }
        .opt-btn:hover { background: rgba(0, 243, 255, 0.2); border-color: var(--n); padding-right:25px; box-shadow:0 0 10px rgba(0,243,255,0.2);}

        .game-over-ui { background: rgba(255, 0, 60, 0.1); border-color: var(--alert); text-align:center;}
        .victory-ui { background: rgba(57, 255, 20, 0.1); border-color: var(--success); text-align:center;}
        .sys-btn { display:inline-block; margin-top:10px; background:var(--n); color:#000; padding:10px 20px; font-weight:bold; font-size:16px; border:none; cursor:pointer; text-decoration:none; }
        .back-arcade { display:inline-block; text-align:center; text-decoration:none; color:rgba(255,255,255,0.5); margin-top:20px; }
        .back-arcade:hover { color:#fff; text-decoration:underline; }
    </style>
</head>
<body>
   <div class="sys-container">
        <h1>Command Zero _ [M2-T5]</h1>
        
        <div class="progress-hud">
            <div class="trip-label">Voyage Progression: WK[{{s.week}} / {{s.max_weeks}}]</div>
            <div class="trip-track"><div class="trip-fill"></div></div>
        </div>
        
        <!-- בקר סטטיסטי מיוחד חילקו ל 5 -->
        <div class="status-grid">
            <div class="gauge-item"><span class="g-label">CREW.Life</span><span class="g-val">{{s.crew}}</span></div>
            <div class="gauge-item"><span class="g-label">P-ENERGY</span><span class="g-val g-nrg">{{s.energy}}</span></div>
            <div class="gauge-item"><span class="g-label">RATIONS</span><span class="g-val g-food">{{s.food}}</span></div>
            <div class="gauge-item"><span class="g-label">HULL%</span><span class="g-val g-hull">{{s.hull}}%</span></div>
            <div class="gauge-item"><span class="g-label">CREDS-$</span><span class="g-val" style="color:#ffe600">{{s.credits}}</span></div>
        </div>

        <div class="cap-log">
             {% for logline in s.log %}
                 <div style="margin-bottom:5px;">{{ logline }}</div>
             {% endfor %}
        </div>

        {% if s.game_over %}
            <div class="screen-ui game-over-ui">
               <h2 style="color:var(--alert); margin:0;">ALARM // TOTAL LOSS DECLARED</h2>
               <div class="desc-text" style="color:var(--alert)">מערכת הכרובים כשלה מלוחית, הבניה שותקה סופית במסלולה האפרורי. מוות לקיום.</div>
               <a class="sys-btn" style="background:var(--alert);" href="/game3/reset">תפעל לשיחזור זמן נסיגה חליפית <<<</a>
            </div>
        {% elif s.victory %}
             <div class="screen-ui victory-ui">
               <h2 style="color:var(--success); margin:0;">ALL MISSIONS PASSED</h2>
               <div class="desc-text">חיסכון קוברי אנטנות הבליחו ישר כהלכום לחץ קו הסיום – התייצבנו סוללינו ספינת בוס בענני הכתמה נפסד מהיוגה! חיזרו חרסי הארנו. אדום החיוים..</div>
               <a class="sys-btn" style="background:var(--success);" href="/game3/reset">סע להתחיל את העבודה מהתחלת נתיבים... <<<</a>
            </div>
        {% else %}
            <!-- EVENT BOX - מודל בטוח עם Event -->
            <div class="screen-ui">
               <h3 style="color:var(--n); margin-top:0;"> > {{ e_active.title }} </h3>
               <div class="desc-text">{{ e_active.desc }}</div>
               
               <div class="choices-box">
                   {% for choice in e_active.choices %}
                        <a href="/game3/act/{{ loop.index0 }}" class="opt-btn">{{ choice.txt }}</a>
                   {% endfor %}
               </div>
            </div>
        {% endif %}

   </div>
   
   <a href="/" class="back-arcade">⮜ תפריט ההובר למעבד הכנס השאר המשחק של הפוסט Arcade של אני..</a>
</body>
</html>
"""

@app.route('/')
def home():
    ship = load_ship()
    if not ship:
        ship = SpaceshipState()
        save_ship(ship)
        return redirect('/game3/')

    # הבאה במיוחד: העברנו גם את שחרור הפתרון התנאי האקר של רשימה (Events) בפרמטר מאוחד אל טריפטיז.
    e_active = ship.current_event()
    return render_template_string(TEMPLATE, s=ship, e_active=e_active)

@app.route('/act/<int:choice_idx>')
def act(choice_idx):
    s = load_ship()
    if not s or s.game_over or s.victory: 
        return redirect('/game3/')
    
    e_active = s.current_event()
    if choice_idx >= 0 and choice_idx < len(e_active['choices']):
        # איסוף התוצאה למשאב עכשיו מתופעל מהטוחנה. 
        c = e_active['choices'][choice_idx]
        e_calc = c.get('effect', {})
        
        if 'credits' in e_calc: s.credits += e_calc['credits']
        if 'energy' in e_calc: s.energy += e_calc['energy']
        if 'food' in e_calc: s.food += e_calc['food']
        if 'hull' in e_calc: s.hull += e_calc['hull']
        if 'crew' in e_calc: s.crew += e_calc['crew']

        txt = c['txt'].split('(')[0].strip() # גזירה אוטומטי ליפי טקסט יצורה
        s.add_log(f">> רשות המוח החשכה העוברית נגשת אל : [{txt}] פעל !! ")
        
        s.consume_resources()
        s.week += 1
        s.check_status()
        
        if not s.game_over and not s.victory:
            s.pick_random_event()
             
        save_ship(s)

    return redirect('/game3/')

@app.route('/reset')
def reset_g():
    session.pop('genesis_data', None)
    return redirect('/game3/')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
