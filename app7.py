import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

# נניח שזה app7 בתשתית שלך (PROXIMA)
app = Flask(__name__)
app.secret_key = 'hebrew_commander_full_fix_v12' 

# ==========================================
# 🛰️ נתוני התחנה והאויבים עם הופעה ויזואלית
# ==========================================

SECTORS = {
    "N": {"name": "האנגר צפוני", "defense": 100, "max_def": 100},
    "S": {"name": "כור דרומי",   "defense": 100, "max_def": 100},
    "E": {"name": "מעבדות מזרח", "defense": 100, "max_def": 100},
    "W": {"name": "נשקייה מערב", "defense": 100, "max_def": 100},
    "CORE": {"name": "ליבת הפיקוד", "defense": 1000, "max_def": 1000} 
}

# הוספתי "icon" לאפיון הויזואלי במסך השליטה!
ALIENS = [
    {"name": "רחפן עוקץ", "dmg": 5, "speed": 1, "icon": "🛸"},
    {"name": "משחית כבד", "dmg": 15, "speed": 2, "icon": "👾"},
    {"name": "מלכת הכוורת", "dmg": 30, "speed": 1, "icon": "🦂"}
]

# ==========================================
# ⚙️ מנוע המשחק
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "energy": 100, "max_energy": 100,
                "oxygen": 100, "max_oxygen": 100,
                "day": 1,
                "sectors": SECTORS.copy(),
                "enemies": [],
                "log": [{"text": "התחנה חוברה מחדש. חיישני התנועה פעילים.", "type": "sys"}]
            }
        else:
            self.state = state

    def log(self, t, type="sys"): 
        self.state["log"].append({"text": t, "type": type})

    def spawn_wave(self):
        count = random.randint(1, min(self.state["day"], 4)) # מקסימום 4 מפלצות מוגרלות
        for _ in range(count):
            loc = random.choice(["N", "S", "E", "W"])
            base = random.choice(ALIENS)
            enemy = {
                "id": str(uuid.uuid4())[:8],
                "name": base["name"],
                "dmg": base["dmg"],
                "hp": 20 + (self.state["day"] * 5),
                "loc": loc,
                "icon": base["icon"]
            }
            self.state["enemies"].append(enemy)
            sector_name = self.state["sectors"][loc]["name"]
            self.log(f"⚠️ איום חדש: {enemy['name']} הופיע ב-{sector_name}!", "danger")

    def next_turn(self):
        s = self.state
        s["energy"] = min(s["energy"] + 15, s["max_energy"])  # שופר מעט לתת חופש פעולה
        s["oxygen"] -= 4
        
        if s["oxygen"] <= 0:
            self.log("❌ אזל החמצן לחלוטין. התחנה נכנעה לריק.", "danger")
            return "dead"

        # אויבים תוקפים
        alive = []
        for e in s["enemies"]:
            loc = e["loc"]
            sec = s["sectors"][loc]
            
            # אם החדר נפרץ (הגנה 0) - האויב מתקדם לליבה
            if sec["defense"] <= 0 and loc != "CORE":
                self.log(f"🚨 שער {sec['name']} נפרץ! פולשים מתקדמים לליבה.", "danger")
                e["loc"] = "CORE"
                sec["defense"] = 0
            
            # נזק לחדר הנוכחי (או לליבה)
            target = s["sectors"][e["loc"]]
            target["defense"] -= e["dmg"]
            
            # מערכת הגנה פסיבית גורמת נזק קל לאויבים השוהים בחדרים מבצעיים (לא בליבה)
            if target["defense"] > 0 and e["loc"] != "CORE":
                e["hp"] -= 5 
            
            if target["defense"] <= 0 and e["loc"] == "CORE":
                return "dead"
            
            if e["hp"] > 0:
                alive.append(e)
            else:
                self.log(f"🔫 ההגנה האוטומטית טיפלה ב-{e['name']}.", "sys")

        s["enemies"] = alive
        
        # סיכוי לגל חדש (קשוח יותר ככל שמתקדמים בימים)
        if random.random() < 0.35 + (s["day"] * 0.05):
            self.spawn_wave()

        return "ok"

    def action_fire(self, loc):
        if self.state["energy"] >= 25:
            self.state["energy"] -= 25
            hits = 0
            survivors = []
            for e in self.state["enemies"]:
                if e["loc"] == loc:
                    e["hp"] -= 40 # כח תקיפה רגיל
                    hits += 1
                    if e["hp"] > 0: 
                        survivors.append(e)
                    else: 
                        self.log(f"🎯 ירי מדויק השמיד את {e['name']}!", "success")
                else:
                    survivors.append(e)
            self.state["enemies"] = survivors
            
            sec_name = self.state["sectors"][loc]["name"]
            if hits == 0: self.log(f"ירית באגף {sec_name} על אזור ריק. שטח נקי.", "sys")
        else:
            self.log("⚡ לא ניתן לבצע תקיפה! יש צורך ב-25 חשמל.", "danger")

    # 🔥 נשק יום הדין
    def action_emp(self):
        if self.state["energy"] >= 80:
            self.state["energy"] -= 80
            survivors = []
            for e in self.state["enemies"]:
                e["hp"] -= 50
                if e["hp"] > 0: survivors.append(e)
            
            if len(self.state["enemies"]) > len(survivors):
                self.log(f"💥 גל EMP רב עוצמה ריסק מספר אויבים בכל התחנה!", "success")
            else:
                self.log(f"💥 גל ה-EMP פגע בכולם והחליש את הרגישויות שלהם.", "info")
            self.state["enemies"] = survivors
        else:
            self.log("⚡ סירנות! אנרגיית רשת ל-EMP נמוכה! דרושים 80 כוח.", "danger")


    def action_repair(self, loc):
        if self.state["energy"] >= 20:
            self.state["energy"] -= 20
            # מוסיף הגנה לחדר
            target = self.state["sectors"][loc]
            target["defense"] = min(target["defense"] + 60, target["max_def"])
            self.log(f"🔧 חוליות חירום ביצרו את ה-{target['name']}.", "info")
        else:
            self.log("⚡ חסרה אנרגיה למערכות התיקון! (20 נדרש)", "danger")

    def action_ventilate(self):
        if self.state["energy"] >= 30:
            self.state["energy"] -= 30
            self.state["oxygen"] = min(self.state["oxygen"] + 45, 100)
            self.log("💨 שאיבת אוויר בוצעה: אספקת חמצן רעננה להמשך הליבה.", "success")
        else:
            self.log("⚡ מנועי האוויר משותקים, אין חשמל (30 דרוש).", "danger")

    def action_wait(self):
        self.log("⏳ כוננות צבירה מופעלת... מחוללי מתח מטעינים המון אנרגיה.", "info")


# ==========================================
# SERVER API (מתואם לחנות הארקיד שלך!)
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML)

# הכתובת היא כעת רק 'update' עבור Dispatcher Middleware יחסית 
@app.route("/update", methods=["POST"])
def update_game():
    d = request.json
    try: 
        eng = Engine(session.get("game_cmd_prox"))
    except: 
        eng = Engine(None)

    act = d.get("action")
    target = d.get("target") 

    status = "ok"

    if act == "reset":
        eng = Engine(None)
    elif act == "fire":
        eng.action_fire(target)
        status = eng.next_turn()
    elif act == "repair":
        eng.action_repair(target)
        status = eng.next_turn()
    elif act == "vent":
        eng.action_ventilate()
        status = eng.next_turn()
    elif act == "wait":
        eng.action_wait()
        # בוסט לאנרגיה מוגבר במתנה בטוחה:
        eng.state["energy"] = min(eng.state["energy"] + 15, eng.state["max_energy"]) 
        status = eng.next_turn()
    elif act == "emp":
        eng.action_emp()
        status = eng.next_turn()

    # יצירת מרווח זמן לשחקן לנשום בתור ה1 הראשון
    if act == "init" and eng.state["day"] == 1 and not eng.state["enemies"]:
        pass # לא עושים כלום ב-init, רק שולבים UI

    # דיווח הפסד נקי למשחקון
    if status == "dead":
        session["game_cmd_prox"] = None # איפוס לאחר מוות
        return jsonify({"dead": True, "day": eng.state["day"]})

    # קידום "לילה לחצי לילה" ימי המשחק
    if random.random() < 0.15: 
        eng.state["day"] += 1
        eng.log(f"☀️ שחר זורח. סיום סימולציה מחזור {eng.state['day']-1}, רמת הסכנה עלתה!", "danger")

    # שימור מצב
    session["game_cmd_prox"] = eng.state
    
    return jsonify({
        "stats": {
            "energy": eng.state["energy"],
            "oxy": eng.state["oxygen"],
            "day": eng.state["day"],
            "core": eng.state["sectors"]["CORE"]["defense"]
        },
        "sectors": eng.state["sectors"],
        "enemies": eng.state["enemies"],  # <<< זהו הסוד הגדול שעובר כעת לדפדפן להציג אוייבים!
        "log": eng.state["log"][-20:] # חותכים את אורך הטקסט שהלוג מראה כדי לא לשקולט שרת 
    })


# ==========================================
# FRONTEND - המסך הטקטי! 
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PROXIMA STATION - COMMANDER</title>
<style>
    :root { --main: #00f3ff; --alert: #ff004c; --bg: #07090f; }
    
    body { background: var(--bg); color: var(--main); font-family: monospace; margin: 0; height: 100vh; display: flex; flex-direction: column; overflow:hidden;}
    
    /* המסך רועד כשהחיים בסכנה */
    .screen-shake { animation: shake 0.5s; }
    @keyframes shake {
      0% { transform: translate(1px, 1px) rotate(0deg); }
      10% { transform: translate(-1px, -2px) rotate(-1deg); }
      30% { transform: translate(3px, 2px) rotate(0deg); }
      50% { transform: translate(-1px, -1px) rotate(1deg); }
      100% { transform: translate(0, 0) rotate(0deg); }
    }
    
    /* מזהיר על סוף עולם החמצן - אדמומיות באוויר */
    body.low-oxygen::before {
        content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle, transparent 30%, rgba(255, 0, 50, 0.4) 100%);
        pointer-events: none; z-index: 1000; animation: blink_danger 2s infinite;
    }
    
    /* חלוקת לוחות הבקרה העליון */
    .hud { 
        background: #0d121c; padding: 15px; border-bottom: 2px solid var(--main); 
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 0 30px rgba(0, 243, 255, 0.15); z-index: 10;
    }
    .bar-box { width: 130px; text-align: center; font-size: 15px; font-weight: bold;}
    .bar { height: 14px; background: #222; margin-top: 5px; border:1px solid #444; border-radius:3px; overflow:hidden;}
    .fill { height: 100%; transition: width 0.3s; width: 100%; }
    
    .hud-title {text-align:center;}
    
    /* MAP - GRID התחנה עצמה */
    .station { 
        flex: 1; display: grid; position: relative;
        grid-template-areas: 
            ". N ."
            "W C E"
            ". S .";
        gap: 20px; align-items: center; justify-content: center;
        background: radial-gradient(ellipse at center, #111a28 0%, var(--bg) 80%);
    }
    
    .room {
        width: 150px; height: 120px;
        background: rgba(10,25,45,0.85); border: 2px solid #23426e; border-radius: 8px;
        display: flex; flex-direction: column; justify-content: space-between; padding: 10px;
        text-align: center; transition: all 0.3s; position: relative; box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    .room:hover { border-color: var(--main); box-shadow: 0 0 15px var(--main); transform: scale(1.05); z-index: 5;}
    
    .r-n { grid-area: N; }  .r-s { grid-area: S; }  
    .r-e { grid-area: E; }  .r-w { grid-area: W; } 
    .r-c { grid-area: C; border-color: gold; height: 140px; width: 170px; background: rgba(50,40,0,0.6);}

    /* שכבות הויזואל - מפלצות מתרוצצות בפנים החדרים */
    .alien-layer {
        position: absolute; top: 30px; left: 5px; right: 5px; bottom: 35px;
        display: flex; flex-wrap: wrap; justify-content: center; align-content: center;
        gap: 5px; font-size: 22px; filter: drop-shadow(2px 2px 2px #000);
        pointer-events: none; /* כדי שהאמוגים לא יבלוקי לחיצות על הכפתור */
    }
    .floating-alien { animation: floatAlien 1s infinite alternate ease-in-out;}
    @keyframes floatAlien { from {transform: translateY(-2px);} to {transform: translateY(2px);} }
    

    /* מתג וכפתורים */
    .hp-strip { height: 6px; background: #333; margin-top: auto; margin-bottom: 8px; border-radius:2px;}
    .hp-val { height: 100%; background: #0f0; width: 100%; transition: 0.4s;}
    
    .action-row {display:flex; gap: 4px; z-index:2;}
    .btn { 
        flex: 1; border: none; padding: 6px 0; border-radius:4px;
        font-family: inherit; font-weight: bold; cursor: pointer; color: white; transition: 0.1s;
    }
    .btn-fire { background: #b01515; } .btn-fire:hover {background: #d42222;}
    .btn-fix { background: #065ca8; } .btn-fix:hover {background: #147ce3;}
    .btn-fire:active, .btn-fix:active { transform:scale(0.9);}
    
    .danger-glow { animation: blink_danger 1s infinite; border-color: var(--alert); background: rgba(80,0,10, 0.8);}
    @keyframes blink_danger { 50% { box-shadow: 0 0 30px var(--alert); } }

    /* הקומה של המסכים */
    .bottom-panel { height: 200px; background: #080c14; border-top: 2px solid #23426e; display: grid; grid-template-columns: 2fr 1fr; z-index:10;}
    .logs { padding: 15px; overflow-y: auto; font-size: 13px; line-height:1.6; border-left: 2px solid #23426e;
            box-shadow: inset 0 0 30px #000; display:flex; flex-direction: column-reverse; /* הטריק שהגוללים הפוך החדש מודגש */
    }
    .log-line { margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1px dotted rgba(255,255,255,0.1); opacity:0.8;}
    .log-line:first-child { opacity:1; text-shadow: 0 0 5px currentColor; font-weight:bold;} /* הודעה הכי מעודכנת הציעה קשקוש קונטרסית*/
    
    .sys-controls { padding: 15px; display: flex; flex-direction: column; gap: 10px; justify-content: center; }
    .big-btn { padding: 12px; background: #13243d; border: 1px solid var(--main); border-radius:5px; color: var(--main); font-family: inherit; font-weight:bold; cursor: pointer;}
    .big-btn:hover { background: var(--main); color: #000; box-shadow:0 0 15px var(--main);}
    
    .emp-btn {border-color: #d112b1; color: #ff3dfb; box-shadow: inset 0 0 10px #ff3dfb; animation: neon 2s infinite;}
    .emp-btn:hover {background: #ff3dfb; color: #fff;}
    @keyframes neon { 50% { box-shadow: inset 0 0 20px #ff3dfb; } }

    .btn-reset { margin-top: auto; padding: 4px; font-size:11px; background: none; border:1px dotted red; color: red; cursor:pointer;}
    .btn-reset:hover {background:red; color:white;}
    
    .back-btn {position: absolute; top:10px; left:10px; color:#fff; text-decoration:none; font-size:12px; border:1px solid #fff; padding:3px 8px; z-index: 100;}
    
    .sys { color: #8eb3ff; } .danger { color: #ff477e; } .success { color: #2ce852; } .info { color: #fcc919; }

</style>
</head>
<body>
<!-- לכיוון לתשתיות היכל המשחקים בחוץ! -->
<a href="/" class="back-btn">🔙 ארקייד HUB</a>

<div class="hud">
    <div class="bar-box">
        ⚡ מתח כוח: <span id="txt-en">100</span>
        <div class="bar"><div id="bar-en" class="fill" style="background:#00f3ff"></div></div>
    </div>
    <div class="hud-title">
        <h2 style="margin:0; letter-spacing:4px; text-shadow:0 0 10px var(--main);">PROXIMA STATION</h2>
        <div style="font-size:13px; color:#7d96bb;">יום פריסה: <span id="day-val" style="color:white;font-weight:bold;font-size:16px;">1</span> | ליבת חסינות: <span id="txt-core">1000</span></div>
    </div>
    <div class="bar-box">
        💨 יתרת חמצן: <span id="txt-ox">100</span>
        <div class="bar"><div id="bar-ox" class="fill" style="background:#2ce852"></div></div>
    </div>
</div>

<div class="station">
    <!-- North -->
    <div class="room r-n" id="room-N">
        <div style="font-weight:bold; text-shadow:1px 1px 0 #000;">האנגר פלוטוניום (צ)</div>
        <div class="alien-layer" id="aliens-N"></div>
        <div class="hp-strip"><div class="hp-val" id="hp-N"></div></div>
        <div class="action-row">
            <button class="btn btn-fire" onclick="act('fire', 'N')">🔥 תקיפה(25)</button>
            <button class="btn btn-fix" onclick="act('repair', 'N')">🔧 שיקום(20)</button>
        </div>
    </div>

    <!-- West -->
    <div class="room r-w" id="room-W">
        <div style="font-weight:bold; text-shadow:1px 1px 0 #000;">נשקיית סיבים (מ)</div>
        <div class="alien-layer" id="aliens-W"></div>
        <div class="hp-strip"><div class="hp-val" id="hp-W"></div></div>
        <div class="action-row">
            <button class="btn btn-fire" onclick="act('fire', 'W')">🔥 תקיפה(25)</button>
            <button class="btn btn-fix" onclick="act('repair', 'W')">🔧 שיקום(20)</button>
        </div>
    </div>

    <!-- CORE (HEART OF THE STATION) -->
    <div class="room r-c" id="room-CORE" title="מרכז בקרה - אל תיתן להם להגיע הנה!">
        <div style="color:gold; font-size:18px; font-weight:900; letter-spacing:1px; margin-bottom:5px;">ליבת פיקוד רגישה</div>
        <!-- פה מגיע פקוד ה-ALIEN אם פורצים למרכז -->
        <div class="alien-layer" id="aliens-CORE" style="font-size:32px;"></div> 
        <div style="font-size:25px; margin:auto; z-index:1; opacity:0.3; animation:pulse 4s infinite;">☢️</div>
        <div class="hp-strip" style="background:#000;"><div class="hp-val" id="hp-CORE" style="background:gold"></div></div>
    </div>

    <!-- East -->
    <div class="room r-e" id="room-E">
        <div style="font-weight:bold; text-shadow:1px 1px 0 #000;">מפרץ עגינה (מז)</div>
        <div class="alien-layer" id="aliens-E"></div>
        <div class="hp-strip"><div class="hp-val" id="hp-E"></div></div>
         <div class="action-row">
            <button class="btn btn-fire" onclick="act('fire', 'E')">🔥 תקיפה(25)</button>
            <button class="btn btn-fix" onclick="act('repair', 'E')">🔧 שיקום(20)</button>
        </div>
    </div>

    <!-- South -->
    <div class="room r-s" id="room-S">
        <div style="font-weight:bold; text-shadow:1px 1px 0 #000;">ליטיום סיילס (ד)</div>
        <div class="alien-layer" id="aliens-S"></div>
        <div class="hp-strip"><div class="hp-val" id="hp-S"></div></div>
        <div class="action-row">
            <button class="btn btn-fire" onclick="act('fire', 'S')">🔥 תקיפה(25)</button>
            <button class="btn btn-fix" onclick="act('repair', 'S')">🔧 שיקום(20)</button>
        </div>
    </div>
</div>

<div class="bottom-panel">
    <!-- LOG TERMINAL -->
    <div class="logs" id="logbox"></div>
    
    <!-- CENTRAL BUTTON CONTROLS -->
    <div class="sys-controls">
        <button class="big-btn emp-btn" onclick="act('emp')" title="מכת חרמש הפוגעת בכל אזור המשחק מול האויבים כולם">💥 גל השמד T.E.S.L.A (-80⚡)</button>
        <button class="big-btn" onclick="act('vent')" style="border-color:#2ce852; color:#2ce852;">💨 מזגן שדה אוויר / העלאת O2 (-30⚡)</button>
        <button class="big-btn" onclick="act('wait')" style="border-style:dashed;">⏳ הסתר והשקט! (-אגירת מתח לזמן מגן)</button>
        <button class="btn-reset" onclick="act('reset')">⏻ איפוס שרתי מערכה בסיסי (REBOOT)</button>
    </div>
</div>

<script>
    // הURL התיאורתי הדינאמי לHUB המשותף. מובנה כדי לעבוד במיקור צד! 
    const API = "update"; 

    // מתקן זיכרון להקראת CORE שעברה 
    let previousCoreDefense = 1000;

    async function act(action, target=null) {
        try {
            let res = await fetch(API, {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action:action, target:target})
            });
            let d = await res.json();

            // === במקרה מוות טראגי של הקונסולה ====== 
            if (d.dead) {
                // הרעד מסך מוגבר רציני
                document.body.classList.add("screen-shake"); 
                document.body.style.animationIterationCount = "15"; 
                document.body.classList.add("low-oxygen"); // סאבים הכל באדום חצי שקוף דכאוני.
                
                setTimeout(() => {
                    alert("!! נטרול התראת צוללת! משחקי ההישרדות הסתיימו. \\nהמפלים קרסו לאט לאט באזוב מלח. שרדתם פולשות זרועו במישור משך מחזורי " + d.day + " ימים פליאודים!.");
                    location.reload(); // רענון מהקונסולה הניטש 
                }, 300);
                return;
            }

            // עדכון משאבים ותיאורי מחסה (Bars Setup) 
            updateBar('en', d.stats.energy);
            updateBar('ox', d.stats.oxy);
            document.getElementById('day-val').innerText = d.stats.day;
            document.getElementById('txt-core').innerText = d.stats.core;
            
            // טעינה וויזואל קונוס מובהק בחוסר חמצן !
            if(d.stats.oxy < 30) document.body.classList.add("low-oxygen");
            else document.body.classList.remove("low-oxygen");

            // --- ריקוד ושפירת שייקינג --- מסננת CORE כדי שהליבה יראה "אוכל טיל".
            if (d.stats.core < previousCoreDefense) {
                document.body.classList.remove("screen-shake");
                void document.body.offsetWidth; // הטריק המזוהף לדרוך אנימציה בכוח דפדפני !! 
                document.body.classList.add("screen-shake");
            }
            previousCoreDefense = d.stats.core; // איוף אחסוני המועט
            
            
            //  === ויזואליה של המפות הקרקעות של פליט המכמים  ==== 
            // 1. ראשית נרוקן את החייזרים מהלוחות: 
            const dirs = ['N','S','E','W', 'CORE'];
            dirs.forEach(k => {
               document.getElementById(`aliens-${k}`).innerHTML = ''; 
            });

            // 2. כעת נשתול אותם סרוצים ויש משיקים קבצות במודים: 
            d.enemies.forEach(e => {
                let theDiv = document.getElementById(`aliens-${e.loc}`);
                if (theDiv) {
                   // עניק ציפה מרטיפה אסתטית מפלסטיינט.   
                   theDiv.innerHTML += `<span class="floating-alien" title="${e.name} (פציע בקווי מתח תאימות סמיות עד רמות כפול ${Math.floor(e.hp)} שורד)" style="cursor:help;">${e.icon}</span>`;
                }
            });


            // == מדדים וכוננות סוג המרכב ופילוג מגבלת שולי כוח =====
            for (let k in d.sectors) {
                let sec = d.sectors[k];
                let elHp = document.getElementById("hp-"+k);
                let pct = (sec.defense / sec.max_def) * 100;
                
                if(elHp) elHp.style.width = pct + "%";
                
                // שינוי צבעי הסכך. אם כורה זה איום מסומן, שיוף לאנחנו רעים! 
                let roomEl = document.getElementById("room-"+k);
                if (pct < 40 && pct > 0) {
                     if(k!=="CORE") elHp.style.backgroundColor = "red";
                     else elHp.style.backgroundColor = "orange";
                     roomEl.classList.add("danger-glow");
                } 
                else if(pct <= 0) { 
                    elHp.style.backgroundColor = "#222"; 
                    roomEl.style.opacity = "0.4"; // חדר הרוס / תקיף ליבה טרונית טועית לחלוקה כפרי
                    roomEl.classList.remove("danger-glow");
                }
                else {
                    if (k === "CORE") elHp.style.backgroundColor = "gold";
                    else elHp.style.backgroundColor = "var(--main)"; // גוף חי רלוונטי
                    
                    roomEl.style.opacity = "1";
                    roomEl.classList.remove("danger-glow");
                }
            }


            // יורד הLOG ים לקודים שיישאו את כל הסחריץ: (Flex reverse helps to render lines to top instead appends downside limits bounds).
            let lb = document.getElementById("logbox");
            lb.innerHTML = "";
            let latests = d.log.reverse(); 
            latests.forEach(l => {
                lb.innerHTML += `<div class="log-line ${l.type}"> [sys@terminal~]# ${l.text}</div>`;
            });

        } catch(e) { console.error("חיבור אבד לרפסודה!", e); }
    }


    function updateBar(id, val) {
        document.getElementById("txt-"+id).innerText = val + "%";
        document.getElementById("bar-"+id).style.width = Math.min(val,100) + "%"; // חריץ על חריגות מקרא אופי לא עובר מאה בפאן UI
        
        let bb = document.getElementById("bar-"+id);
        if(val <= 30) bb.style.backgroundColor = "var(--alert)";
        else bb.style.backgroundColor = id === 'en' ? 'var(--main)' : '#2ce852'; // ציבוץ מקורי דשא 
    }
    
    // קלרד תמוני מסד.
    window.onload = () => { act('init'); };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5007, debug=True)
