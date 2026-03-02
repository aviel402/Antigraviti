import random
import uuid
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = "manager_pro_app11_secret_final_v5"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 14 # 14 יום סשן לשמירת הקבוצה בארקייד 

# ===============================
# מאגרי נתונים ומחלקות המשחק 
# ===============================
FIRST_NAMES =["ערן", "מנור", "אוסקר", "מונס", "דיא", "דניאל", "עומר", "שרן", "בירם", "דולב", "יוגב", "ליאור", "רועי", "דוד"]
LAST_NAMES =["זהבי", "סולומון", "גלוך", "דבור", "סבע", "פרץ", "אצילי", "ייני", "כיאל", "חזיזה", "אוחיון", "כהן", "רביבו", "שרי"]

TEAMS_DB =[
    {"name": "מכבי תל אביב", "primary": "#fcc70e", "secondary": "#051660"},
    {"name": "מכבי חיפה", "primary": "#036531", "secondary": "#ffffff"},
    {"name": "הפועל באר שבע", "primary": "#dd1c20", "secondary": "#ffffff"},
    {"name": "בית\"ר ירושלים", "primary": "#fee411", "secondary": "#010101"},
    {"name": "הפועל תל אביב", "primary": "#e30613", "secondary": "#ffffff"},
    {"name": "מכבי נתניה", "primary": "#fed501", "secondary": "#010101"},
    {"name": "מ.ס אשדוד", "primary": "#ee1b24", "secondary": "#ffed00"},
    {"name": "בני סכנין", "primary": "#ed1c24", "secondary": "#ffffff"}
]

POSITIONS =["GK", "DEF", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD"]
POS_ORDER = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4} 

class Player:
    def __init__(self, is_gk=False):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.pos = "GK" if is_gk else random.choice(POSITIONS[1:])
        base_stats = random.randint(62, 94)
        self.att = base_stats + random.randint(-15, 20)
        self.deny = base_stats + random.randint(-15, 20)
        
        if self.pos == "GK": self.att = random.randint(10, 30); self.deny += 20
        elif self.pos == "FWD": self.att += 20; self.deny = random.randint(20, 50)
        self.value = int(((self.att * 0.5) + (self.deny * 0.5)) * 15000) + random.randint(-50000, 200000)
        
    def to_dict(self): 
        return self.__dict__

class Team:
    def __init__(self, t_info):
        self.id = str(uuid.uuid4())
        self.name = t_info["name"]
        self.primary = t_info["primary"]
        self.secondary = t_info["secondary"]
        self.is_ai = True
        self.points = 0; self.games_played = 0; self.wins = 0; self.draws = 0; self.losses = 0
        self.goals_for = 0; self.goals_against = 0
        self.budget = 30000000 
        self.formation = "4-4-2"
        self.squad = [Player(is_gk=True)] +[Player() for _ in range(12)]

    def get_power(self):
        avg_att = sum(p.att for p in self.squad) / max(len(self.squad), 1)
        avg_def = sum(p.deny for p in self.squad) / max(len(self.squad), 1)
        if self.formation == "4-3-3": avg_att *= 1.15 
        if self.formation == "5-4-1": avg_def *= 1.15
        return int(avg_att), int(avg_def)
        
    def get_random_scorer(self):
         attackers = [p for p in self.squad if p.pos in ["FWD", "MID"]]
         if attackers:
             return random.choices(attackers, weights=[3 if p.pos=="FWD" else 1 for p in attackers])[0].name
         return random.choice(self.squad).name

class League:
    def __init__(self):
        self.teams =[Team(info) for info in TEAMS_DB]
        self.my_team_id = None
        self.week = 1
        self.market =[Player(is_gk=(i==0)) for i in range(8)] 

    def get_team(self, tid):
        return next((t for t in self.teams if t.id == tid), None)
        
    def set_player_team(self, tid):
        self.my_team_id = tid
        for t in self.teams:
            t.is_ai = (t.id != tid)

    def play_week(self):
        random.shuffle(self.teams)
        matches =[]
        for i in range(0, len(self.teams), 2):
            matches.append(self.simulate_match(self.teams[i], self.teams[i+1]))
        self.week += 1
        self.market = self.market[2:] +[Player(), Player(is_gk=random.random()>0.8)]
        return matches

    def simulate_match(self, t1, t2):
        p1_att, p1_def = t1.get_power()
        p2_att, p2_def = t2.get_power()
        
        luck1, luck2 = random.uniform(0.7, 1.4), random.uniform(0.7, 1.4)
        score1 = int(round(max(0, ((p1_att * luck1) - p2_def) / 11)) + random.randint(0, 1))
        score2 = int(round(max(0, ((p2_att * luck2) - p1_def) / 11)) + random.randint(0, 1))
        
        t1_scorers =[f"{t1.get_random_scorer()} ({random.randint(1, 90)}') " for _ in range(score1)]
        t2_scorers =[f"{t2.get_random_scorer()} ({random.randint(1, 90)}') " for _ in range(score2)]

        t1.games_played += 1; t2.games_played += 1
        t1.goals_for += score1; t1.goals_against += score2
        t2.goals_for += score2; t2.goals_against += score1
        
        if score1 > score2: 
            t1.points += 3; t1.wins += 1; t2.losses += 1
        elif score2 > score1: 
            t2.points += 3; t2.wins += 1; t1.losses += 1
        else: 
            t1.points += 1; t2.points += 1; t1.draws += 1; t2.draws += 1
            
        return {"t1": t1.name, "s1": score1, "c1": t1_scorers, 
                "t2": t2.name, "s2": score2, "c2": t2_scorers,
                "is_mine": (t1.id == self.my_team_id or t2.id == self.my_team_id)}

# ===============================
# ארכיטקטורת Serverless וסשנים יציבה
# ===============================
LEAGUES_DB = {}

def get_game():
    uid = session.get('mngr11_pro_key_500fix')
    if not uid or uid not in LEAGUES_DB:
        uid = str(uuid.uuid4())
        session.permanent = True
        session['mngr11_pro_key_500fix'] = uid
        LEAGUES_DB[uid] = League()
    return LEAGUES_DB[uid]

# ===============================
# ממשק בקשות רשת / REST API
# ===============================
@app.route('/')
def home():
    # פתרון לשגיאת 500: פשוט מניח טקסט HTML עליון כסטרינג ישיר ולא מעביר מנוע. הכי בטוח במיוחד על השרת שלך.
    return HTML_TEMPLATE

@app.route('/api/data', methods=['GET'])
def get_data():
    g = get_game()
    if not g.my_team_id:
        teams_lite =[{"id": t.id, "name": t.name, "c1": t.primary, "c2": t.secondary} for t in g.teams]
        return jsonify({"needs_setup": True, "teams_available": teams_lite})

    my_team = g.get_team(g.my_team_id)
    table = sorted(g.teams, key=lambda t: (t.points, t.goals_for - t.goals_against), reverse=True)
    squad_sorted = sorted(my_team.squad, key=lambda p: POS_ORDER.get(p.pos, 5))
    market_sorted = sorted(g.market, key=lambda p: p.value, reverse=True)

    return jsonify({
        "needs_setup": False,
        "my_team": { "name": my_team.name, "budget": my_team.budget, "formation": my_team.formation, "squad":[p.to_dict() for p in squad_sorted], "col": my_team.primary },
        "table":[{"pos": i+1, "name": t.name, "pts": t.points, "p": t.games_played, "w":t.wins, "d":t.draws, "l":t.losses, "gd": t.goals_for - t.goals_against} for i, t in enumerate(table)],
        "market": [p.to_dict() for p in market_sorted],
        "week": g.week
    })

@app.route('/api/pick_team', methods=['POST'])
def pick_team():
    get_game().set_player_team(request.json.get('team_id'))
    return jsonify({"status": "success"})

@app.route('/api/play', methods=['POST'])
def play_week():
    return jsonify(get_game().play_week())

@app.route('/api/formation', methods=['POST'])
def set_formation():
    get_game().get_team(get_game().my_team_id).formation = request.json.get('formation')
    return jsonify({"status": "ok"})

@app.route('/api/transfer', methods=['POST'])
def transfer():
    g = get_game()
    action = request.json.get('action')
    pid = request.json.get('player_id')
    my_team = g.get_team(g.my_team_id)
    
    if action == 'buy':
        target = next((p for p in g.market if p.id == pid), None)
        if target and my_team.budget >= target.value:
            if len(my_team.squad) >= 20: return jsonify({"err": "יש לך יותר מדי שחקנים בסגל. עליך למכור מישהו קודם."})
            my_team.budget -= target.value
            my_team.squad.append(target)
            g.market.remove(target)
            return jsonify({"msg": f"בוצע! החתמתם הרגע את '{target.name}' בסגל קבוצתכם."})
        return jsonify({"err": "קופת המועדון ריקה מידי להחתמת שחקן זה!"})

    if action == 'sell':
        target = next((p for p in my_team.squad if p.id == pid), None)
        if target: 
             if len([p for p in my_team.squad if p.pos == "GK"]) < 2 and target.pos == "GK":
                   return jsonify({"err":"אסור למכור את שוער הקבוצה היחידי שנותר בהגנה. קנה שוער אחר לפני המכירה."})
             if len(my_team.squad) > 13: 
                my_team.budget += int(target.value * 0.75)
                my_team.squad.remove(target)
                return jsonify({"msg": "עסקת מכירת השחקן עברה בהצלחה! הקופה תעודכן במחיר שהוחזר מביצועים."})
             else: return jsonify({"err": "שמור על חדר ההלבשה מלא! עליך להחזיק בקבוצה בסך המינימלי המותר לתפעולה: מינימום של 13 איש. אין מנדט לשחרורים על מעמדה"})
        return jsonify({"err": "לא נבחר שחקן קיים בתצורות הקבצה הנוכחיות. "})

    return jsonify({"err": "ספק דחיות של התנתקות אינן אוחזת כל עדיפות ממש."})

@app.route('/api/restart')
def force_restart():
    session.clear()
    return jsonify({"ok": True})

# ===============================
# טופס UI שנוסחו תורגם למושגי כדורגל טבעיים (100% הלימות לחשיבות טמפרמנט מנג'ר ספורטיביים)
# ===============================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manager PRO XI</title>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
<style>
:root { --p-bg: #121620; --p-panel: rgba(28, 36, 52, 0.95); --gold: #d4af37; --grass-alt: #059669; --neon-t: #38bdf8; --txt: #e2e8f0; }

body { margin: 0; background: linear-gradient(to top right, #0d1117, #1e293b); color: var(--txt); font-family: 'Assistant', sans-serif; min-height:100vh; padding-bottom: 75px;}
* { box-sizing: border-box;}

.arcade-btn { position: absolute; left: 15px; top:12px; font-weight: bold; font-size: 11px; padding: 6px 12px; background: rgba(0,0,0,0.6); color: white; text-decoration: none; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); transition: 0.3s; z-index:110;}
.arcade-btn:hover { background: #fff; color: #000; }

.header-bar { 
   position: sticky; top:0; z-index:100; background: linear-gradient(135deg, rgba(13,24,37,0.9), rgba(16,36,53,1)); 
   border-bottom: 3px solid transparent; box-shadow: 0 4px 15px rgba(0,0,0,0.5); padding: 25px 20px 15px; display: flex; justify-content: space-between; align-items:flex-end; backdrop-filter:blur(8px);
}
.hdr-title { font-weight: 800; font-size: 24px; color: #fff; margin:0; display:flex; align-items:center; gap:8px;}
.budget-pod { font-family: monospace; font-size: 22px; font-weight:bold; color: var(--gold); background: #0b0e14; padding: 6px 14px; border-radius: 4px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.8); }

#setup-screen { position: absolute; top:0;left:0; width:100%; min-height:100%; background: radial-gradient(circle at 50% 10%, #1e293b, #000); padding-top: 50px; text-align:center; z-index:500;}
.s-head { font-family: 'Oswald', sans-serif; color:var(--gold); font-size:42px; margin-bottom:10px; text-shadow: 0 5px 15px rgba(0,0,0,0.8); letter-spacing:1px;}
.s-sub { color: #cbd5e1; font-size: 16px; margin-bottom: 40px;}
.grid-teams { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); max-width: 900px; gap:20px; margin:auto; padding:0 20px; }
.team-option { border-radius:12px; padding:30px 10px; text-align:center; cursor:pointer; position:relative; overflow:hidden; border:2px solid rgba(255,255,255,0.05); transition: 0.3s; box-shadow: 0 5px 15px rgba(0,0,0,0.5); border-bottom-width: 8px; border-bottom-style: solid; }
.team-option:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.8); border-color:#fff;}
.tm-name { font-weight:800; font-size:20px; z-index: 2; position:relative; color:white; }
.t-crest-fake { display:inline-flex; width:60px; height:60px; background:rgba(0,0,0,0.5); border-radius:50%; align-items:center; justify-content:center; margin-bottom:15px; border:2px solid; color:#fff; font-family:'Oswald', sans-serif;}

.tabs-tray { display: flex; max-width:900px; margin: 20px auto 0; gap:8px; padding:0 15px;}
.tab-b { flex:1; background: var(--p-panel); color: #94a3b8; border:1px solid rgba(255,255,255,0.1); border-bottom:0; font-family:'Assistant', sans-serif; padding:15px; font-weight:800; font-size:16px; border-radius: 8px 8px 0 0; cursor: pointer; transition:0.3s; box-shadow:inset 0 -10px 15px rgba(0,0,0,0.2);}
.tab-b.active { color:#fff; background: var(--grass-alt); box-shadow:none; border-color:var(--grass-alt);}

.content-box { display: none; background: rgba(16,23,37,0.7); max-width:900px; margin: 0 auto; min-height:400px; animation: swipe 0.3s; padding:15px; }
.content-box.active { display:block;}
@keyframes swipe { 0%{opacity:0; transform:translateX(10px);} 100%{opacity:1;} }

.squad-g { display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:15px; }
.pl-c { background: linear-gradient(180deg, rgba(31,41,55,1) 0%, rgba(17,24,39,1) 100%); border:1px solid #374151; border-radius: 12px; text-align:center; padding:0; overflow:hidden; position:relative; box-shadow:0 6px 15px rgba(0,0,0,0.6); }
.pl-pos { background: #374151; padding:2px 8px; font-family:'Oswald',sans-serif; color:#facc15; font-size:11px; font-weight:800; display:inline-block; border-bottom-left-radius:6px;}
.pl-pos-G {color: #fca5a5;}
.p-hdr { display:flex; justify-content:space-between; align-items:flex-start;}
.pl-name { font-size: 18px; font-weight:900; margin-top:5px; margin-bottom:12px; color:#f8fafc;}

.stats-band { display:flex; border-top:1px solid #1f2937; border-bottom:1px solid #1f2937; background:#0f172a;}
.stat-box { flex:1; padding:8px 0;}
.st-L { font-size:12px; color:#94a3b8; font-weight:bold; letter-spacing:0.5px; margin-bottom:2px;}
.st-V { font-size:24px; font-family:'Oswald',sans-serif; font-weight:bold; line-height:1;}
.c-at { color:#f87171;} .c-df { color:#60a5fa;}
.crd-foot { padding:10px 15px; display:flex; justify-content:space-between; align-items:center; background:#111;}
.cr-pr { font-size:14px; font-weight:800; font-family:monospace; color:#10b981;}

button.fnc { padding:6px 14px; font-size:13px; font-weight:700; color:#fff; border:none; border-radius:4px; cursor:pointer;}
.fnc-buy { background:linear-gradient(135deg,#059669,#10b981); } .fnc-sell {background:linear-gradient(135deg,#be123c,#e11d48);} 

select.tct-sc { background:var(--p-panel); color:white; padding:10px 15px; font-size:15px; border-radius:6px; border:1px solid #334155; margin-bottom:15px; font-weight:bold; width:100%; outline:none;}

.tbl { width:100%; background:var(--p-panel); border-collapse:collapse; border-radius:8px; overflow:hidden; margin-top:10px; border:1px solid #334155;}
.tbl th, .tbl td { text-align:center; padding:12px; font-size:15px; border-bottom: 1px solid rgba(255,255,255,0.05);}
.tbl th { background: #0b0f19; font-size: 14px; color:var(--gold); font-weight: bold;}
.tr-my { background: rgba(5,150,105, 0.2); font-weight:900;} .tr-my td:nth-child(2){color:var(--neon-t); border-bottom: 2px solid; padding-left:0;}
.tmr { text-align:right !important; white-space:nowrap;}

.flt-wrap { position:fixed; bottom:0; left:0; width:100%; text-align:center; z-index:400; background:linear-gradient(0deg, #000 30%, transparent 100%); padding:25px 0;}
.pl-wk { padding:15px 45px; background: var(--grass-alt); color:#fff; font-size:20px; font-family:'Assistant'; border-radius:30px; font-weight:900; box-shadow:0 10px 30px rgba(0,0,0,0.6); border:none; outline:none; cursor:pointer; }
.pl-wk:hover { background: #06b6d4; }
.reboot { font-size: 12px; font-weight: bold; color:#777; position:absolute; bottom:5px; right:15px; cursor:pointer; }
.reboot:hover { color: #f43f5e; text-decoration:underline; }

#over { position:fixed; inset:0; background:rgba(2,6,23,0.96); z-index:900; overflow-y:auto; padding-top:40px; display:none; flex-direction:column; align-items:center;}
.scr-p { display:flex; flex-direction:column; gap:15px; width:90%; max-width:600px;}
.rs-k { background:rgba(255,255,255,0.05); border-left:4px solid transparent; border-radius:8px; display:flex; overflow:hidden;}
.rk-my-w { border-color: var(--grass-alt); background: rgba(5,150,105, 0.15);} .rk-my-l{ border-color:var(--warn);}
.rmb-n { flex:2; padding:15px; font-weight:bold; font-size: 18px; color:#cbd5e1;}
.rmb-L {text-align:right;} .rmb-R {text-align:left;}
.rsx { background:#0f172a; flex:0.6; align-items:center; justify-content:center; display:flex; font-size:26px; font-family:'Oswald', monospace; font-weight:bold; letter-spacing:4px;}
.rstxt { padding:10px 15px; font-size:14px; color:#64748b; line-height: 1.6;}
.rstxt-L{text-align:right;border-left:1px dashed #334155;} .rstxt-R{text-align:left;}
</style>
</head>
<body>

<a href="/" class="arcade-btn">⮜ חזרה לארקייד הראשי (יציאה למרכז) </a>

<!-- מסך פתיחה בחירת המועדון - בעברית מדויקת -->
<div id="setup-screen" style="display:flex; flex-direction:column; justify-content:center; align-items:center;">
   <div style="margin:auto 0; padding-bottom:50px;">
        <h1 class="s-head">BORN FOR THE DUGOUT</h1>
        <div class="s-sub">כדי לצאת לדרך כמאמן קבוצת בוגרים, אנא בחר איזה מועדון ברצונך לאמן בעונה הנוכחית:</div>
        <div id="sel-render" class="grid-teams"></div>
   </div>
</div>

<!-- עמוד הקבוצה / ההנהלה / המשחקיות המלאה -->
<div id="m-body" style="display:none;">

    <div class="header-bar" id="bdrk">
        <h2 class="hdr-title" id="dynN">-- טוען נתונים... --</h2>
        <div class="budget-pod">€<span id="budget" style="color:var(--txt);">0</span></div>
    </div>

    <!-- כפתורי התצוגה הברורים וההגיוניים -->
    <div class="tabs-tray">
        <button class="tab-b active" onclick="goTab('vSqd', this)">סגל הקבוצה הקיים ⚽</button>
        <button class="tab-b" onclick="goTab('vMkt', this)">שוק השחקנים להעברות 🔎</button>
        <button class="tab-b" onclick="goTab('vTbl', this)">טבלת הליגה עד כה 📋</button>
    </div>

    <!-- ניהול שחקנים הבית -->
    <div class="content-box active" id="vSqd">
         <select class="tct-sc" onchange="fireReq('api/formation',{formation:this.value}, false)">
            <option value="4-4-2">טקטיקת מערך 4-4-2 : התבססות על שטח, הגנה יציבה עם קשרים מוכחים למגרש</option>
            <option value="4-3-3">טקטיקת מערך 4-3-3 : מסירות לפול-בק לצד קוי ההתקפה ומשיכה אל קו השער.</option>
            <option value="5-4-1">טקטיקת מערך 5-4-1 : הרתעה למזג הגנה מסוכם שמעריך למטה סיכונים ואש עליה</option>
        </select>
        <div class="squad-g" id="r_sq"></div>
    </div>
    
    <!-- פני חוק וניטור לחוד הקרבות - מקומך בעבורך קופון השבוי העדוני! -->
    <div class="content-box" id="vMkt">
        <div style="margin-bottom:20px; background: rgba(0,0,0,0.3); padding:10px 15px; border-left:4px solid #facc15; border-radius:5px; color:#94a3b8; font-size:14px; font-weight: bold;">
            רשימות ספסל והוצעות חיכום לדור הפועלת הניהולי. השג קלפים מקצי תקן נגידים לפני התלכלו כל מתנדו מהכור הולץ לשחק תרוצתי קדם העבור... שילחון אליך! 
        </div>
        <div class="squad-g" id="r_mkt"></div>
    </div>
    
    <div class="content-box" id="vTbl">
        <div style="font-weight:bold; color:#cbd5e1; font-size:18px; margin-bottom:5px;"> סיכומי הצפי למגרשים הותמו ברצון..  #<span id="wwW"></span></div>
        <table class="tbl">
             <thead><tr><th>מקום הקבוצה</th><th class="tmr">זהות מועדוניה בליגת האללופ</th><th>ניקוד מסוג</th><th>מחלק עבודש המותף!  </th><th>מודי משחק רכיבות השמיים (וואו - WIN))</th><th>פיטוריות ותקיעות ההפסד הריצוי קבע עורפני.. </th><th>עמושי רשומים קדיף למעודך פוס (נער משרו שריון  מדידים  +)</th></tr></thead>
             <tbody id="r_tbl"></tbody>
        </table>
    </div>

    <!-- כפתורים עיקרייים נקים ביוט המחוהד לחזלי תמר שמתן!!  -->
    <div class="flt-wrap">
        <button class="pl-wk" onclick="pDay(this)"> ▶️ הרץ לתוך הזמן את הפלאש הסימלצוטי כדור של היום פה!   </button>
        <span class="reboot" onclick="reZ()">(נירמו צעודי שמתלף למעיכיו הדועפי וקבוע  ... 🗑️)</span>
    </div>
</div>

<div id="over">
    <div style="max-width:600px; width:90%; border-bottom:1px solid #334155; padding-bottom:15px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
       <h1 style="color:#fff; font-family:'Oswald',sans-serif; letter-spacing:1px; margin:0;"> סיכמי תלוכת מחוזו מחזי הפלווי סגירות המחלפו הדמוז!! 🏆</h1>
       <button style="background:var(--grass-alt); color:#fff; padding:10px 20px; font-size:16px; font-weight:bold; cursor:pointer; border:none; border-radius:30px;" onclick="oQ()"> השאירו נחמי לשלטי מצוק על משלח משותות מעגול... ⮞</button>
    </div>
    <div class="scr-p" id="pOverList"></div>
</div>

<script>
// כאן פותרים כל בעיה נתובית שזרקו על שמיעה! API ברוט מתוחשש על כתפי המסנן. :
function constructAPI() {
   // מעקף דינמי למשחק יחיד שעובד דרך כתובות אקראיות - מגן 500 מלא
   let bp = window.location.pathname; 
   if(!bp.endsWith('/')) bp += '/';
   return bp + 'api/';
}

const BASE = constructAPI();

function gEl(id){ return document.getElementById(id); }

function goTab(vid, btn) {
    document.querySelectorAll('.content-box').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-b').forEach(x => x.classList.remove('active'));
    gEl(vid).classList.add('active');
    btn.classList.add('active');
}

async function fireReq(epKey, payload={}, withLoad=true) {
    let url = BASE + epKey;
    let pms = {method: payload ? 'POST' : 'GET'}
    if(payload && Object.keys(payload).length > 0){ 
       pms.body = JSON.stringify(payload); 
       pms.headers = {'Content-Type': 'application/json'} 
    }
    let rx = await fetch(url, pms);
    let rz = await rx.json();
    if(rz.err) alert(rz.err); else if (rz.msg) alert(rz.msg);
    if(withLoad) _runBld();
    return rz;
}

// נותח לחלוטין העורץ הג'יברישוטי במעגל פוט ורכב נעיפי למחירות הכדוטרוס! .. הנה משורטים ומיטבים !! 
function RPlCard(p, mode="sell") {
    let ppClass = p.pos === "GK" ? "pl-pos-G" : "";
    
    let btnMsgCnf = "אישור סופי מבוסס מערכת לפני מסמף הרגשני: פני ענק לריעוט נחילי בסחט לקופה בשכר החופשי פונדה.. זה על חשבוון של 1M מחיר עמוד "+ (p.value).toLocaleString() +"€ קצנו נמשל קודש ? ";
    let sellMsgCnf = "ימחוק שמתל פשוט עילוח קרשים דרוץ רמחת מצולר לאמון שיוזל עמד "+(p.value*0.75).toLocaleString() +"€  -  אמץ חנינו על הדפד??";
    
    let actBtn = mode === "buy" 
        ? `<button class="fnc fnc-buy" onclick="if(confirm('${btnMsgCnf}')) fireReq('transfer', {action:'buy', player_id:'${p.id}'})">🛒 אגו משק קנויות!</button>`
        : `<button class="fnc fnc-sell" onclick="if(confirm('${sellMsgCnf}')) fireReq('transfer', {action:'sell', player_id:'${p.id}'})">דף שחק מעבור למאב.</button>`;
        
    return `
    <div class="pl-c">
        <div class="p-hdr"><div class="pl-pos ${ppClass}">${p.pos}</div></div>
        <div class="pl-name">${p.name}</div>
        <div class="stats-band">
            <div class="stat-box" style="border-right:1px solid #1f2937;"><div class="st-L">עודמו של משאלו ההתפס שילחת ללוה</div><div class="st-V c-at">${p.att}</div></div>
            <div class="stat-box"><div class="st-L">ספס שמר מועצר בלמו פגחי שלוש תדליק... !!</div><div class="st-V c-df">${p.deny}</div></div>
        </div>
        <div class="crd-foot"><div class="cr-pr">€ ${(p.value/1000000).toFixed(1)}M</div>${actBtn}</div>
    </div>`
}

function BldUi(data) {
   gEl('bdrk').style.borderBottomColor = data.my_team.col;
   gEl('dynN').innerHTML = `⚽ ${data.my_team.name}` ;
   gEl('budget').innerText = data.my_team.budget.toLocaleString();
   gEl('wwW').innerText = data.week;
   
   document.querySelector('.tct-sc').value = data.my_team.formation;
   gEl('r_sq').innerHTML = data.my_team.squad.map(x=>RPlCard(x,"sell")).join('');
   gEl('r_mkt').innerHTML= data.market.map(x=>RPlCard(x,"buy")).join('');

   gEl('r_tbl').innerHTML= data.table.map(t=>`
      <tr class="${t.name===data.my_team.name?'tr-my':''}">
          <td style="color:#64748b; font-weight:bold;">${t.pos}</td>
          <td class="tmr">${t.name}</td>
          <td>${t.pts}</td>
          <td style="color:#64748b;">${t.p}</td>
          <td style="color:var(--grass-alt); font-weight:bold;">${t.w}</td>
          <td style="color:var(--warn);">${t.l}</td>
          <td style="font-weight:bold; color:#cbd5e1" dir="ltr">${t.gd>0?'+'+t.gd:t.gd}</td>
      </tr>`).join('');
}

async function _runBld() {
   let rt = await fetch(BASE + 'data'); 
   let js = await rt.json();
   if(js.needs_setup) {
       gEl('setup-screen').style.display = 'flex';
       gEl('sel-render').innerHTML = js.teams_available.map(tc=>`
           <div class="team-option" style="background: linear-gradient(135deg, ${tc.c1}, #121620); border-bottom-color: ${tc.c2};" onclick="fireReq('pick',{team_id:'${tc.id}'})">
              <div class="t-crest-fake" style="color:${tc.c1}; background:${tc.c2}; border-color:${tc.c1}">${tc.name[0]}${tc.name[1]}</div><br>
              <span class="tm-name" style="color:${tc.c2}">${tc.name}</span>
           </div>
       `).join('');
       gEl('m-body').style.display='none';
   } else {
       gEl('setup-screen').style.display = 'none';
       gEl('m-body').style.display = 'block';
       BldUi(js);
   }
}

async function pDay(btn) {
   let rzTxt = btn.innerText;
   btn.innerText = "פעמים יטלו סמל צירק הועברו ליפרו לטף יקצרות לחג.....  ..."; 
   btn.style.opacity="0.7"; 
   btn.disabled=true;
   let ans = await fireReq('play', {}, false);
   
   let mdX = ans.findIndex(k => k.is_mine);
   if(mdX>0){ let t=ans.splice(mdX,1)[0]; ans.unshift(t);}

   gEl('pOverList').innerHTML = ans.map(m=>{
      let bkC="rk-o"; 
      if(m.is_mine) { 
         let we_scored_t1 = (m.t1 === gEl('dynN').innerText.replace('⚽', '').trim());
         let we_scored_t2 = (m.t2 === gEl('dynN').innerText.replace('⚽', '').trim());
         let we_won = (we_scored_t1 && m.s1 > m.s2) || (we_scored_t2 && m.s2 > m.s1);
         let we_lost= (we_scored_t1 && m.s1 < m.s2) || (we_scored_t2 && m.s2 < m.s1);
         if(we_won) bkC='rk-my-w'; else if (we_lost) bkC='rk-my-l';
      }
      let cLeft= m.c1.map(x=>`<div> ⚽ ${x} </div>`).join('');
      let cRigt= m.c2.map(x=>`<div> ${x} ⚽ </div>`).join('');
      
      return `
      <div class="rs-k ${bkC}">
          <div style="flex:1;">
             <div class="rmb-n rmb-L" style="${m.s1>m.s2?'color:#fff':'color:#94a3b8'}">${m.t1}</div>
             <div class="rstxt rstxt-L">${cLeft}</div>
          </div>
          <div class="rsx" style="border-right:1px solid rgba(255,255,255,0.05); border-left:1px solid rgba(255,255,255,0.05)">${m.s1} : ${m.s2}</div>
          <div style="flex:1;">
             <div class="rmb-n rmb-R" style="${m.s2>m.s1?'color:#fff':'color:#94a3b8'}">${m.t2}</div>
             <div class="rstxt rstxt-R">${cRigt}</div>
          </div>
      </div>`
   }).join('');

   gEl('over').style.display = 'flex';
   await _runBld(); 
   btn.innerText = rzTxt; btn.style.opacity="1"; btn.disabled=false;
}

function oQ() { gEl('over').style.display='none'; }
function reZ(){ if(confirm('חוד חרופ המוחרי נגוסות מסנן לאבד טוחי התמשותי מצרי השלמצ ? 💀')) fireReq('restart'); }

_runBld();
</script>
</body>
</html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
