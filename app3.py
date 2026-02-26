import random
from flask import Flask, render_template_string, redirect, session

app = Flask(__name__)
# שימוש במפתח הצפנה משופר והגדרות חיי session
app.secret_key = "genesis_space_odyssey_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 יום שמירה של משחק לחזור לחללית!

# ===============================
# GLOBAL EVENT DATA (STATICS)
# ===============================
# שומרים אירועים בחוץ, כך שבעוגיה יישמר רק המזהה שלו ולא כל הטקסטים שלו
EVENTS =[
    {
        "id": 0, "title": "מטר אסטרואידים סלעי", "desc": "ראדאר המגן מראה ענן סלעי קרח וברזל לפנינו.",
        "choices":[
            {"txt": "הפעל חומות כוח מלאות (20- אנרגיה)", "effect": {"energy": -20}},
            {"txt": "תמרן (קשה), ספוג תפגיעה אם ניכשל (20- חוזק גוף)", "effect": {"hull": -20}}
        ]
    },
    {
        "id": 1, "title": "סוחר שוק שחור בגזרה B", "desc": "קפלן של משמידי מערכות התקרב לספינה.",
        "choices":[
            {"txt": "רכוש 30 קפסולות מזון (150- קרדיט)", "effect": {"credits": -150, "food": 30}},
            {"txt": "רוקן קבלי כוח אל החללית שלו למכירה (+200 קרדיט, 30- אנרגיה)", "effect": {"credits": 200, "energy": -30}},
            {"txt": "העלם מעין חום (דלג)", "effect": {}}
        ]
    },
    {
        "id": 2, "title": "מוטציה ורטיקאלית באגף 4", "desc": "קצין חקר מדווח על טחב רעיל שהורס מאגרי מזון תקינים.",
        "choices":[
            {"txt": "השמד כל מדור פגום מיידית (25- מזון)", "effect": {"food": -25}},
            {"txt": "לסנן לאכול תקין! יש תחלואה בצמחים... (5- אבדות בצוות)", "effect": {"crew": -5}},
        ]
    },
    {
        "id": 3, "title": "גלית אות מצוקה צפון כוכבי", "desc": "נלקח תדר נקי מזריקה - לטפל בהם?",
        "choices":[
            {"txt": "צא לעזור - פותח לינק סוחר ושימרונג נכסים (15- אנרגיה, 100+ קרדיט)", "effect": {"energy": -15, "credits": 100}},
            {"txt": "שגרה נוהלית. התעלם (יגרום לרעשי גוונים באנשי צוות)", "effect": {"credits": -10}} 
        ]
    },
    {
        "id": 4, "title": "דממת תקשורת וחוסר רגיעה", "desc": "מהלך הירידות הקפוא של החללית עושה דברים רעים במנועי שיחול, צריך מוסכמה חקרית שנתית:",
        "choices":[
            {"txt": "רתק תחזוקה. עצור הפחתות אנרגיה לפרק ופועלי השגחה (150- קרדיט, 10+ כוח מתאר)", "effect": {"credits": -150, "hull": 10}},
            {"txt": "כיבוי מסע נוף יומנוח לשיא משאבות הלב", "effect": {"energy": 10, "food": 5}}, 
        ]
    },
    {
        "id": 5, "title": "קצר בלוחות מולקולארים", "desc": "פאנל C ניזוק במהלך שיח חליף נחקר עולמות!",
        "choices":[
             {"txt": "חמש סירת כבישה ידנית - צוות נופל למרכבים עקב הקפצה חייה.. (-10 חוזק גוף,-3 איבוד כנפיות)", "effect": {"hull": -10, "crew": -3}},
             {"txt": "שלם מעבדים מרכיבים אוטומאטית דרך הקונסול מנופחים משמירת מטבע(-200 C, שלמות חזרות+10%)", "effect": {"credits": -200, "energy": +10, "hull": +5}}
        ]
    }
]

# ===============================
# MODEL / LOGIC CLASS
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
            self.log = data.get("log", ["קפטן, מסד הנתונים מוכן."])
            self.game_over = data.get("game_over", False)
            self.victory = data.get("victory", False)
            self.current_event_id = data.get("current_event_id", 0)
        else:
            self.week = 1; self.max_weeks = 20
            self.crew = 100; self.food = 100
            self.energy = 100; self.hull = 100
            self.credits = 500
            self.log =["יומן כוכבים הפעל. חללית יצאה משיוט האב."]
            self.game_over = False; self.victory = False
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
        # לא מריצים קובץ שלם, רק מצביעים לקורס האנרגיה ב ID המערכת הקטנה למעלה
        evt = random.choice(EVENTS)
        self.current_event_id = evt['id']

    def current_event(self):
        for e in EVENTS:
             if e['id'] == self.current_event_id:
                  return e
        return EVENTS[0]

    def add_log(self, msg):
        self.log.insert(0, f"> [W{self.week}] {msg}")
        if len(self.log) > 4: 
            self.log.pop()

    def consume_resources(self):
        food_con = int(self.crew * 0.15) 
        nrg_con = 8 if self.week > 10 else 5  # המרחק למאדים מתקרר, האנרגיה מתבזבזת כפול מעל לחצי המשחק

        self.food -= food_con
        self.energy -= nrg_con
        
        # התראות היעלמות ונפילת עניבה (הענקת עונשי מכנסיות רזות או פגע אוויר חללי):
        if self.food < 0:
            starved = abs(self.food)
            self.crew -= starved 
            self.food = 0
            self.add_log(f"התראת מזון!! הצוות איבד כוח.. {starved} תושבים נפחו חיות רחמנא יסמן..")
        if self.energy <= 0:
             self.energy = 0
             self.hull -= 15
             self.add_log("חומת פליטי אויר נפגמה מחשב תקיעות אנרגיה נכנע לחומצות ואקום ה-0 כבידתו!! (-15)")

    def check_status(self):
        if self.hull <= 0:
            self.game_over = True
            self.add_log("!!! פיצוץ קריטי בכור הגרעין. לא שרדו !!!")
        elif self.crew <= 0:
            self.game_over = True
            self.add_log("אין פעולות סדירות גולמות ביחתי, אנחנו פחחות מוחיט מן המתכת, קופה רותחת סבת כבד דם של חייל משגות. הספינה יתומה..")
        elif self.week > self.max_weeks:
            self.victory = True
            self.add_log("ברוכים הבאים - אור קסיופה. הבסנו תדחיית תור החיים... מאדים אנחנו שם.")

# ===============================
# SESSION MANAGEMENT FUNC
# ===============================
def load_ship():
    data = session.get('genesis_data')
    if data: return SpaceshipState(data)
    return None

def save_ship(ship_state):
    session.permanent = True
    session['genesis_data'] = ship_state.to_dict()


# ===============================
# CSS / TEMPLATE (Cyberpunk Space Terminal UI)
# ===============================
TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Genesis UI Interface</title>
    <!-- שימוש בפונט חללי כדי לשבור את צבעי הכלי אבחנה -->
    <link href="                                                           &display=swap" rel="stylesheet">
    <style>
        :root {
            --n: #00f3ff;   /* נאיון סייאנולוג'יה קבוע */
            --alert: #ff003c;
            --success: #39ff14;
            --bg-glass: rgba(0, 15, 30, 0.7);
        }

        body { 
            margin: 0; padding: 20px; 
            background: radial-gradient(circle at 50% 50%, #031526, #01080e 100%);
            color: var(--n);
            font-family: 'Share Tech Mono', 'Courier New', monospace;
            display: flex; flex-direction: column; align-items: center; min-height: 100vh;
        }

        /* גריד הרקע הספק מיכניקי תסמונות החללי המורחב לחות */
        body::before {
             content: ""; position: absolute; top:0; left:0; right:0; bottom:0;
             background-image: 
                 linear-gradient(rgba(0,243,255,0.03) 1px, transparent 1px),
                 linear-gradient(90deg, rgba(0,243,255,0.03) 1px, transparent 1px);
             background-size: 30px 30px; z-index: -1;
        }

        .sys-container {
            width: 100%; max-width: 650px; background: var(--bg-glass); border: 1px solid rgba(0,243,255,0.3);
            border-radius: 8px; box-shadow: 0 0 15px rgba(0,243,255,0.1); padding: 20px;
        }

        h1 { font-size: 26px; border-bottom: 2px dashed rgba(0,243,255,0.5); padding-bottom:10px; text-transform:uppercase; margin-top:0;}
        h1::before { content: "TERMINAL \\> "; opacity: 0.6; }

        /* קוו מידת הזמן הנשף החשוב - Mars Trip Bar */
        .progress-hud { margin: 15px 0;}
        .trip-label { font-size: 14px; text-transform: uppercase; letter-spacing: 2px; }
        .trip-track { background: #000; height: 12px; border: 1px solid var(--n); box-shadow: 0 0 5px var(--n) inset; margin-top: 5px;}
        {% set prog = (s.week / s.max_weeks) * 100 %}
        .trip-fill { background: var(--n); height: 100%; width: {{ prog }}%; transition: 0.8s; box-shadow: 0 0 10px var(--n); }

        /* מערכת כפתורי המערכים התצוגה המחשמלת הזרמית! (סטטוס לולאות שונות בסדרי הקבוצות */
        .status-grid { 
             display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 15px; margin-bottom: 25px; 
             border: 1px solid #00f3ff55; background: #01111a; padding: 10px; text-align: center;
        }
        .gauge-item { font-size: 12px; opacity:0.8; display:flex; flex-direction:column; padding: 5px; }
        .g-val { font-size: 18px; margin-top: 4px; font-weight: bold; opacity:1;}
        
        /* אזעקות למדי תגובה בצוק הרמה החרב במצב חרא אסטרואטאי!!! (פחות מ-25 מאדומים וזוהר פתע אלאורום חסימי.) */
        {% if s.energy < 25 or s.food < 25 or s.hull < 30 %}
             .sys-container { animation: warningBlink 3s infinite;}
        {% endif %}
        
        .g-food { color: {% if s.food < 25 %} var(--alert) {% else %} var(--n) {% endif %}; }
        .g-nrg  { color: {% if s.energy < 25 %} var(--alert) {% else %} var(--n) {% endif %}; }
        .g-hull { color: {% if s.hull < 30 %} var(--alert) {% else %} var(--success) {% endif %}; }
        
        /* טייפקאסטר הפקודה - עט סלטי פקודה לחוקרי הטיווח בספסל לכתם */
        .cap-log { 
            background: #00040a; border-left: 3px solid var(--n);
            color: #ccc; font-size: 13px; height: 80px; padding: 10px; overflow-y:auto; 
            margin-bottom: 20px; font-family: monospace; display:flex; flex-direction:column-reverse;
            text-align: right; box-shadow: inset 0 0 5px rgba(0,243,255,0.1);
        }

        .screen-ui { background: #000; padding: 20px; border: 1px dotted rgba(0,243,255,0.4); text-align: center; margin-bottom: 15px; }
        
        /* ממשח הכושר והעיקוף המפעיליים פנינים - בחירות הסבר פשוט ומחורבן ומשם ניקוד מהמשפט פועל מיוצבים בהסדר המטבלאי */
        .desc { font-size:16px; margin: 15px 0; color: #fff;}
        .opt-btn { 
             display:block; width: 100%; margin:8px 0; background: transparent;
             border: 1px solid rgba(0, 243, 255, 0.4); color: #fff; padding: 15px; text-align: right; font-family: monospace; font-size: 15px; cursor: pointer; transition: 0.2s; position:relative; overflow:hidden;
        }
        .opt-btn:hover { background: rgba(0, 243, 255, 0.1); border-color: var(--n); padding-right: 25px; }
        .opt-btn::before { content: " [EXE] "; opacity:0.6; color: var(--n);}
        
        /* END AND GO OVER OVER LATE UI ENDER GAME: פשוט שינצוות לחגגו. דברים בקרחת החק */
        .fatal { border-color: var(--alert); background: rgba(255, 0, 60, 0.1);}
        .fatal .desc { color: var(--alert); }
        .victo { border-color: var(--success); background: rgba(57, 255, 20, 0.05); }
        .btn-restart { display: inline-block; background: var(--n); color:#000; border:none; padding:12px 20px; margin-top:20px; cursor:pointer; font-weight:bold; font-family:inherit;}
        .home-l { text-align: center; color: rgba(255,255,255,0.4); font-size:11px; text-decoration:none; display:block; margin-top: 30px;}
        .home-l:hover {color:#fff;}
    </style>
</head>
<body>
   <div class="sys-container">
        <h1>System Override. Genesis.</h1>

        <div class="progress-hud">
            <div class="trip-label">Orbit >> Mars Vector[ Week {{s.week}} / {{s.max_weeks}} ]</div>
            <div class="trip-track"><div class="trip-fill"></div></div>
        </div>

        <!-- קירות קלימייג המצבת שחוק השוקעת כפיש דלת - צמתו אמוז קווטאר גולח ינכוש -->
        <div class="status-grid">
            <div class="gauge-item"><span>CREW</span> <span class="g-val">{{s.crew}}</span></div>
            <div class="gauge-item"><span>PWR.CORE</span> <span class="g-val g-nrg">{{s.energy}}</span></div>
            <div class="gauge-item"><span>ORG.FOOD</span> <span class="g-val g-food">{{s.food}}</span></div>
            <div class="gauge-item"><span>HULL-DEF</span> <span class="g-val g-hull">{{s.hull}}%</span></div>
            <div class="gauge-item"><span>G-CREDITS</span> <span class="g-val" style="color:#ffe600">{{s.credits}}</span></div>
        </div>

        <div class="cap-log">
             {% for line in s.log %}
                 <div style="margin-bottom:4px">{{line}}</div>
             {% endfor %}
        </div>

        {% if s.game_over %}
            <div class="screen-ui fatal">
               <h2 style="color:var(--alert); margin-top:0;">SYSTEM FAILURE ALARM: DEAD HULL! 💀 </h2>
               <div class="desc">את הירח הזה הם רצו, אך הפחד ניצח, כל החללית הוכתרה שנית לפגישות צבועי פשעים בבריח הרמונס בחדים מתחת שחף. מות אכזור! .</div>
               <a href="/game3/reset"><button class="btn-restart">Initialize RE-ROLL Protocol > </button></a>
            </div>
        {% elif s.victory %}
            <div class="screen-ui victo">
               <h2 style="color:var(--success); margin-top:0;">WELCOME. COLONY VECTOR ZERO ARRIVAL. 🎉 </h2>
               <div class="desc">נבואתינו הבת גבינות, ניצוליה צבאי, האור התחדל בחשיות סורקות של שדיי הגחשים המרתוייד סולח מהחץ הקור מארץ ישראל! מוצא משחקי צומות הליטוס! </div>
               <a href="/game3/reset"><button class="btn-restart" style="background:var(--success)">ENTER PREV JOURNEY > </button></a>
            </div>
        {% else %}
            {% set cevt = s.current_event() %}
            <div class="screen-ui">
               <div style="font-weight:bold; letter-spacing:1px; margin-bottom:5px; border-bottom:1px dotted #333; padding-bottom:5px;">/// AWAITING COMM.LOG_ORDER. ID-{{cevt.id}} ///</div>
               <div class="desc" style="color:var(--n);"> {{ cevt.title }} </div>
               <div style="color:#999; font-size:14px; margin-bottom: 20px;"> >> {{ cevt.desc }}</div>

               <div style="text-align: right;">
               {% for idx in range(cevt.choices|length) %}
                    <a href="/game3/act/{{ idx }}" style="text-decoration:none;">
                       <button class="opt-btn"> {{ cevt.choices[idx].txt }}</button>
                    </a>
               {% endfor %}
               </div>
            </div>
        {% endif %}

   </div>
   
   <a class="home-l" href="/"><< Exit Comm_port >></a>
</body>
</html>
"""


# ===============================
# APP ROUTES FOR 'GENESIS' ARCH
# ===============================
@app.route('/')
def home():
    ship = load_ship()
    if not ship:
        ship = SpaceshipState()
        save_ship(ship)
        return redirect('/game3/')

    save_ship(ship)
    return render_template_string(TEMPLATE, s=ship)

@app.route('/act/<int:choice_idx>')
def act(choice_idx):
    s = load_ship()
    if not s or s.game_over or s.victory: return redirect('/game3/')
    
    evt = s.current_event()
    if choice_idx < 0 or choice_idx >= len(evt['choices']):
        return redirect('/game3/') # כניסה סרק במקור התג לוח מניב האורדן 
        
    c = evt['choices'][choice_idx]
    e_calc = c.get('effect', {})
    
    # מיכום פענוחי העמדה הפוליסיות
    if 'credits' in e_calc: s.credits += e_calc['credits']
    if 'energy' in e_calc: s.energy += e_calc['energy']
    if 'food' in e_calc: s.food += e_calc['food']
    if 'hull' in e_calc: s.hull += e_calc['hull']
    if 'crew' in e_calc: s.crew += e_calc['crew']

    s.add_log(f"הוראה עובדה חברת המנגנון :: בוצע: '{c['txt'].split('(')[0]}'.")

    # משאבים משמשעים צריכת זעווה מסוף ימיים
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
    # מפעילים לבדיקת רק קטע דלת פשוט ברץ הלייבי המטבי על אוקרציות מחובן
    app.run(port=5000, debug=True)
