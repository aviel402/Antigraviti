import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = "manager_pro_app11_secret"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 14 # שומר נתוני שחקן

# ===============================
# DATA & NAMES
# ===============================
FIRST_NAMES =["ערן", "מנור", "אוסקר", "מונס", "דיא", "דניאל", "עומר", "שרן", "בירם", "דולב", "יוגב", "ליאור", "דולב", "מוחמד", "אייל", "רוי", "דוד"]
LAST_NAMES =["זהבי", "סולומון", "גלוך", "דבור", "סבע", "פרץ", "אצילי", "ייני", "כיאל", "חזיזה", "אוחיון", "כהן", "אבו פאני", "רביבו", "חמד", "שרי"]
TEAMS_NAMES =["מכבי תל אביב", "מכבי חיפה", "הפועל באר שבע", "בית\"ר ירושלים", "הפועל תל אביב", "מכבי נתניה", "מ.ס אשדוד", "בני סכנין"]
POSITIONS =["GK", "DEF", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD"]
POS_ORDER = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4} 

# ===============================
# LOGIC & CLASSES
# ===============================
class Player:
    def __init__(self, is_gk=False):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.pos = "GK" if is_gk else random.choice(POSITIONS[1:])
        
        base_stats = random.randint(60, 95)
        self.att = base_stats + random.randint(-15, 20)
        self.deny = base_stats + random.randint(-15, 20)
        
        if self.pos == "GK": self.att = random.randint(10, 30); self.deny += 20
        elif self.pos == "FWD": self.att += 20; self.deny = random.randint(20, 50)
        
        self.value = int(((self.att * 0.5) + (self.deny * 0.5)) * 15000) + random.randint(-50000, 200000)
        
    def to_dict(self): return self.__dict__

class Team:
    def __init__(self, name, is_ai=True):
        self.id = str(uuid.uuid4())
        self.name = name; self.is_ai = is_ai
        self.points = 0; self.games_played = 0; self.wins = 0; self.draws = 0; self.losses = 0
        self.goals_for = 0; self.goals_against = 0
        self.budget = 25000000 
        self.formation = "4-4-2"
        self.squad =[Player(is_gk=True)]
        self.squad +=[Player() for _ in range(12)]

    def get_power(self):
        avg_att = sum(p.att for p in self.squad) / max(len(self.squad), 1)
        avg_def = sum(p.deny for p in self.squad) / max(len(self.squad), 1)
        if self.formation == "4-3-3": avg_att *= 1.15 
        if self.formation == "5-4-1": avg_def *= 1.15
        return int(avg_att), int(avg_def)
        
    def get_random_scorer(self):
         fwds_mids =[p for p in self.squad if p.pos in ["FWD", "MID"]]
         if fwds_mids:
             scorer = random.choices(fwds_mids, weights=[3 if p.pos=="FWD" else 1 for p in fwds_mids])[0]
             return scorer.name
         return random.choice(self.squad).name

class League:
    def __init__(self):
        self.teams =[Team(name) for name in TEAMS_NAMES]
        self.my_team_id = self.teams[0].id
        self.teams[0].is_ai = False
        self.week = 1
        self.market = [Player(is_gk=(i==0)) for i in range(7)] 

    def get_team(self, tid):
        return next((t for t in self.teams if t.id == tid), None)

    def play_week(self):
        random.shuffle(self.teams)
        matches =[]
        for i in range(0, len(self.teams), 2):
            matches.append(self.simulate_match(self.teams[i], self.teams[i+1]))
        self.week += 1
        self.market = self.market[2:] + [Player(), Player(is_gk=random.random()>0.8)]
        return matches

    def simulate_match(self, t1, t2):
        p1_att, p1_def = t1.get_power()
        p2_att, p2_def = t2.get_power()
        
        luck1, luck2 = random.uniform(0.7, 1.4), random.uniform(0.7, 1.4)
        raw_1 = max(0, ((p1_att * luck1) - p2_def) / 12)
        raw_2 = max(0, ((p2_att * luck2) - p1_def) / 12)
        
        score1 = int(round(raw_1) + random.randint(0, 1))
        score2 = int(round(raw_2) + random.randint(0, 1))
        
        t1_scorers =[f"{t1.get_random_scorer()} ({random.randint(1, 90)}')" for _ in range(score1)]
        t2_scorers =[f"{t2.get_random_scorer()} ({random.randint(1, 90)}')" for _ in range(score2)]

        t1.games_played += 1; t2.games_played += 1
        t1.goals_for += score1; t1.goals_against += score2
        t2.goals_for += score2; t2.goals_against += score1
        if score1 > score2: t1.points += 3; t1.wins += 1; t2.losses += 1
        elif score2 > score1: t2.points += 3; t2.wins += 1; t1.losses += 1
        else: t1.points += 1; t2.points += 1; t1.draws += 1; t2.draws += 1
            
        return {"t1": t1.name, "s1": score1, "c1": t1_scorers, 
                "t2": t2.name, "s2": score2, "c2": t2_scorers,
                "is_mine": (t1.id == self.my_team_id or t2.id == self.my_team_id)}

# ===============================
# SESSIONS
# ===============================
LEAGUES_DB = {}

def get_game():
    uid = session.get('manager_11_id')
    if not uid or uid not in LEAGUES_DB:
        uid = str(uuid.uuid4())
        session.permanent = True
        session['manager_11_id'] = uid
        LEAGUES_DB[uid] = League()
    return LEAGUES_DB[uid]

# ===============================
# ROUTES
# ===============================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data', methods=['GET'])
def get_data():
    g = get_game()
    my_team = g.get_team(g.my_team_id)
    table = sorted(g.teams, key=lambda t: (t.points, t.goals_for - t.goals_against), reverse=True)
    
    squad_sorted = sorted(my_team.squad, key=lambda p: POS_ORDER.get(p.pos, 5))
    market_sorted = sorted(g.market, key=lambda p: p.value, reverse=True)

    return jsonify({
        "my_team": { "name": my_team.name, "budget": my_team.budget, "formation": my_team.formation, "squad": [p.to_dict() for p in squad_sorted] },
        "table":[ {"pos": i+1, "name": t.name, "pts": t.points, "p": t.games_played, "w":t.wins, "d":t.draws, "l":t.losses, "gd": t.goals_for - t.goals_against} for i, t in enumerate(table)],
        "market":[p.to_dict() for p in market_sorted],
        "week": g.week
    })

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
            if len(my_team.squad) >= 20: return jsonify({"err": "הסגל כבר מוגזם ומלא למקסימום. מותר עד 20 שחקנים."})
            my_team.budget -= target.value
            my_team.squad.append(target)
            g.market.remove(target)
            return jsonify({"msg": f"בוצע! החתמת בהצלחה את {target.name}. ⚽"})
        return jsonify({"err": "תקציב מועדון חסר בשביל העסקה הזו."})

    if action == 'sell':
        target = next((p for p in my_team.squad if p.id == pid), None)
        if target: 
             if len([p for p in my_team.squad if p.pos == "GK"]) < 2 and target.pos == "GK":
                   return jsonify({"err":"חובה להשאיר לפחות שוער אחד פעיל בקבוצה."})
             if len(my_team.squad) > 12: 
                my_team.budget += int(target.value * 0.75)
                my_team.squad.remove(target)
                return jsonify({"msg": f"השחקן {target.name} נמכר! התקציב הועבר לקופה."})
             else: return jsonify({"err": "אין אפשרות לרדת מתחת למינימום סגל חוקי (12)."})
        return jsonify({"err": "פעולה נכשלה"})

    return jsonify({"err": "בקשה לא תקינה"})

# ===============================
# UI & DESIGN (With 'Back' button)
# ===============================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ultimate Manager 11</title>
<style>
:root { --grass: #0a9342; --dark: #074720; --light: #e0f2e9; --accent: #ffea00; --badge:#023020; }
body { margin: 0; background-color: #f4f7f6; font-family: 'Segoe UI', system-ui, sans-serif; color: #222; padding-bottom: 75px; }

/* הוספתי כפתור מובנה ואלגנטי בחלק העליון - לחזרה לפלסק ארקייד */
.arcade-back-btn { background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.4); border-radius: 5px; color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; padding: 5px 10px; display: flex; align-items: center; justify-content: center; transition: 0.2s;}
.arcade-back-btn:hover { background: #fff; color: var(--dark); border-color: #fff; }

.header { background: linear-gradient(135deg, var(--dark) 0%, var(--grass) 100%); color: white; padding: 12px 20px; position: sticky; top:0; z-index:100; box-shadow: 0 4px 12px rgba(0,0,0,0.25); display: flex; justify-content: space-between; align-items: center;}
.team-title { font-weight: 900; font-size: 20px; letter-spacing: 0.5px; display:flex; flex-direction: column; line-height: 1.1; margin-right: 15px;}
.budget { font-family: monospace; font-size: 16px; font-weight: bold; color: var(--accent); background: rgba(0,0,0,0.3); padding: 6px 12px; border-radius: 6px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
.header-right-side { display: flex; align-items: center;}

/* TABS */
.tabs { display: flex; background: #fff; padding: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.tab-btn { flex: 1; background: transparent; color: #555; border: none; font-size: 16px; font-weight: 600; padding: 14px 0; cursor: pointer; border-bottom: 3px solid transparent; transition:0.3s;}
.tab-btn.active { color: var(--grass); border-bottom-color: var(--grass); background: var(--light); }
.tab-btn:hover { background: #fafafa;}

.section { padding: 15px; display: none; animation: fadeIn 0.4s ease; max-width:800px; margin:auto;}
.section.active { display: block; }
@keyframes fadeIn { from { opacity:0; transform: translateY(5px);} to { opacity:1; transform: translateY(0);} }

/* CARDS */
.card { background: white; padding: 15px; margin-bottom: 12px; border-radius: 12px; box-shadow: 0 3px 6px rgba(0,0,0,0.06); display: flex; justify-content: space-between; align-items: center; position:relative; overflow:hidden;}
.pos-tag { position:absolute; left:0; top:0; bottom:0; width:6px; }
.pos-GK { background:#e74c3c;} .pos-DEF { background:#3498db;} .pos-MID { background:#f1c40f;} .pos-FWD { background:#2ecc71;}
.p-info h4 { margin: 0 0 4px 0; font-size: 17px; display:flex; gap:10px; align-items:center; padding-right:10px;}
.p-badge { font-size: 11px; background:#edf2f7; color:#2d3748; padding:3px 8px; border-radius:4px; font-weight:700;}
.p-stats { font-size: 13px; color: #666; margin-right:10px;}
.p-stats b { font-weight:800; }
.b-att { color:#c0392b;} .b-def { color:#2980b9;}
.p-price { font-size:13px; font-weight:bold; color:var(--grass); margin-top:5px; margin-right:10px;}
.action-btn { font-weight:700; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; box-shadow:0 2px 4px rgba(0,0,0,0.2); transition: 0.2s;}
.sell-btn { background: #e74c3c; } .buy-btn { background: #27ae60; }

/* LEAGUE GRID */
.tactics-box { background: #fff; padding:15px; border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom:15px;}
.tactics-box label { font-weight:bold; font-size:14px; margin-bottom:5px; display:block; color:#555;}
select.formation-select { width: 100%; padding: 10px; border-radius: 5px; font-size: 16px; border:1px solid #ccc; background:#f9f9f9; outline:none;}

.table-row { display: grid; grid-template-columns: 25px 2fr 30px 30px 30px 30px 40px; gap:4px; padding: 12px 5px; border-bottom: 1px solid #eee; background: white; font-size: 13px; align-items:center;}
.table-head { background: var(--badge); color: white; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size:12px; border-bottom:none;}
.my-rank { background: var(--light); font-weight: 800; border-right: 4px solid var(--grass); border-left: 4px solid var(--grass);}
.center-t {text-align:center;}

/* BOTTOM PLAY BTN */
.play-week-btn {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: linear-gradient(135deg, #28a745 0%, #208b3a 100%); border: 3px solid rgba(255,255,255,0.4);
    color: white; padding: 15px 50px; border-radius: 40px; text-transform:uppercase; letter-spacing:1px;
    font-size: 18px; font-weight: 900; box-shadow: 0 8px 25px rgba(0,180,60,0.5);
    cursor: pointer; transition: 0.3s; z-index: 200;
}
.play-week-btn:hover { filter: brightness(1.2); } .play-week-btn:active { transform: translateX(-50%) scale(0.94); }

/* MATCHES RESULTS MODAL */
#modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(10,20,15,0.95); z-index: 300; display:none; flex-direction:column; justify-content:flex-start; align-items:center; overflow-y:auto;}
.res-container { width: 100%; max-width:600px; margin-top:20px; display:flex; flex-direction:column; gap:15px;}
.m-card { background: #fff; border-radius:10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); overflow:hidden; }
.m-card.my-match { border:2px solid var(--accent); }
.m-card.win-card { background:#ebfaed; } .m-card.loss-card { background:#fcebeb; }
.m-header { display:flex; justify-content:space-between; background:#222; color:#fff; padding:15px; font-weight:bold; font-size:18px;}
.m-score { background:#111; color:var(--accent); padding:5px 12px; border-radius:5px;}
.m-body { display:flex; padding:12px; justify-content:space-between; background:rgba(0,0,0,0.02); min-height:40px;}
.team-events { flex:1; padding:0 10px; font-size:13px; line-height:1.6;} .event-list-r { text-align:left; color:#c0392b;} .event-list-l { text-align:right; color:#27ae60;}
.modal-close { margin: 30px auto; display:block; padding:12px 50px; background:var(--accent); border:none; color:#000; border-radius:30px; font-size:18px; font-weight:900; cursor:pointer;}
</style>
</head>
<body>

<div class="header">
    <div class="header-right-side">
        <!-- זה כפתור החזרה לעמוד הבית החכם -->
        <a href="/" class="arcade-back-btn">⮜ לכל המשחקים</a>
        <div class="team-title" id="teamName" style="margin-right: 15px;">טוען...</div>
    </div>
    <div class="budget">💸 €<span id="budget">0</span></div>
</div>

<div class="tabs">
    <button class="tab-btn active" onclick="showTab('squad', this)">סגל שחקנים</button>
    <button class="tab-btn" onclick="showTab('market', this)">העברות</button>
    <button class="tab-btn" onclick="showTab('league', this)">טבלה משולבת</button>
</div>

<!-- SECTION SQUAD -->
<div id="squad" class="section active">
    <div class="tactics-box">
        <label>שנה מבנה טקטי של ההרכב:</label>
        <select class="formation-select" onchange="changeTactics(this.value)">
            <option value="4-4-2">4-4-2 : מבנה קלאסי ומאוזן</option>
            <option value="4-3-3">4-3-3 : נטייה התקפית קלה (בונוס לכוח אש)</option>
            <option value="5-4-1">5-4-1 : דגש מובהק על חולית ההגנה</option>
        </select>
    </div>
    <div id="squad-list"></div>
</div>

<!-- SECTION LEAGUE -->
<div id="league" class="section">
    <h3 style="color:var(--dark); margin-top:5px; border-bottom:2px solid #ddd; padding-bottom:5px;"> מחזור ליגה נוכחי: <span id="weekNum">1</span></h3>
    <div class="table-row table-head">
        <div class="center-t">#</div><div>קבוצה</div><div class="center-t" title="נקודות">PTS</div><div class="center-t">P</div><div class="center-t">W</div><div class="center-t">L</div><div class="center-t" title="הפרש שערים">GD</div>
    </div>
    <div id="table-body"></div>
</div>

<!-- SECTION MARKET -->
<div id="market" class="section">
    <div class="tactics-box" style="margin-top:0;">
        <strong>📢 המעקבים בשוק (Scouting Network):</strong> כספי ההעברות קבועים! אלו האופציות לשדרוג הסגל במחזור הנוכחי. השוק יתרענן מדי משחק.
    </div>
    <div id="market-list"></div>
</div>

<button class="play-week-btn" onclick="playWeek()">שחק מחזור ▶️</button>

<div id="modal">
    <div style="text-align:center; padding:20px;">
       <h1 style="color:#fff; margin:0; text-shadow:0 0 10px rgba(0,0,0,0.5); display:inline-block; border-bottom:3px solid var(--accent); padding-bottom:10px;">תוצאות המחזור:</h1>
    </div>
    <div class="res-container" id="results-list"></div>
    <button class="modal-close" onclick="closeModal()">חזור לעמדת האימון</button>
</div>

<script>
const P_CLASSES = {"GK": "pos-GK", "DEF": "pos-DEF", "MID":"pos-MID", "FWD":"pos-FWD"};

function showTab(id, el) {
    document.querySelectorAll('.section').forEach(e => e.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(e => e.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    el.classList.add('active');
}

function renderCard(p, isBuy=false) {
    return `
    <div class="card">
        <div class="pos-tag ${P_CLASSES[p.pos]||""}"></div>
        <div class="p-info">
            <h4><span class="p-badge">${p.pos}</span> ${p.name} </h4>
            <div class="p-stats">התקפה:<b class="b-att"> ${p.att}</b> &nbsp;|&nbsp; הגנה: <b class="b-def"> ${p.deny}</b></div>
            <div class="p-price">💰 ${Number(p.value).toLocaleString()} €</div>
        </div>
        ${isBuy 
          ? `<button class="action-btn buy-btn" onclick="transfer('buy', '${p.id}')">🛒 קנה</button>` 
          : `<button class="action-btn sell-btn" onclick="transfer('sell', '${p.id}')">💶 מכור (75%)</button>`}
    </div>`;
}

function render(data) {
    document.getElementById('teamName').innerText = data.my_team.name;
    document.getElementById('budget').innerText = Number(data.my_team.budget).toLocaleString();
    document.getElementById('weekNum').innerText = data.week;
    
    document.querySelector('.formation-select').value = data.my_team.formation;
    document.getElementById('squad-list').innerHTML = data.my_team.squad.map(p => renderCard(p, false)).join('');
    
    document.getElementById('table-body').innerHTML = data.table.map(t => `
        <div class="table-row ${t.name === data.my_team.name ? 'my-rank' : ''}">
            <div class="center-t" style="color:#aaa;">${t.pos}</div>
            <div style="font-weight:700;">${t.name}</div>
            <div class="center-t" style="font-weight:900; color:var(--dark)">${t.pts}</div>
            <div class="center-t" style="color:#666">${t.p}</div>
            <div class="center-t" style="color:var(--grass); font-weight:bold;">${t.w}</div>
            <div class="center-t" style="color:tomato">${t.l}</div>
            <div class="center-t" dir="ltr" style="font-weight:bold;">${t.gd>0?'+'+t.gd:t.gd}</div>
        </div>
    `).join('');

    document.getElementById('market-list').innerHTML = data.market.map(p => renderCard(p, true)).join('');
}

// URL SAFE API CALL (שמור תחת הדיספאצ'ר כדי לא לגלוש החוצה מהgame11)
async function loadData() {
    const req = await fetch('api/data'); 
    const j = await req.json();
    render(j);
}

async function changeTactics(val) {
    await fetch('api/formation', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({formation:val})
    });
}

async function transfer(act, pid) {
    if(!confirm(act === 'buy' ? 'בטוח שתרצה לקנות את השחקן ולהוציא את התקציב מהמועדון?' : 'השחקן יימכר ויוחזר 75% ממחירו השווי-לקופה. לאשר?')) return;
    const req = await fetch('api/transfer', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action: act, player_id: pid})
    });
    const dat = await req.json();
    if(dat.err) alert('שגיאה: ' + dat.err);
    else { loadData(); }
}

function renderMatchHtml(m) {
     const stC = m.is_mine ? "my-match" : "";
     let bC = ""; 
     if(m.is_mine) {
         if (m.t1 === document.getElementById('teamName').innerText ) {
               bC = m.s1 > m.s2 ? "win-card" : (m.s1<m.s2?"loss-card":"");
         } else {
               bC = m.s2 > m.s1 ? "win-card" : (m.s2<m.s1?"loss-card":"");
         }
     }
     const goalsLeft = m.c1.map(g => `<div>⚽ ${g}</div>`).join('');
     const goalsRight= m.c2.map(g => `<div>${g} ⚽</div>`).join('');

     return `
     <div class="m-card ${stC} ${bC}">
         <div class="m-header">
            <div>${m.t1}</div><div class="m-score">${m.s1} - ${m.s2}</div><div>${m.t2}</div>
         </div>
         <div class="m-body">
            <div class="team-events event-list-l">${goalsLeft}</div>
            <div class="team-events event-list-r">${goalsRight}</div>
         </div>
     </div>`;
}

async function playWeek() {
    const origText = document.querySelector('.play-week-btn').innerText;
    document.querySelector('.play-week-btn').innerText = '⏳ מעבד...';
    
    const req = await fetch('api/play', {method:'POST'});
    const data = await req.json();
    
    const mineIndex = data.findIndex(i => i.is_mine);
    if(mineIndex > 0) { const mw = data.splice(mineIndex, 1)[0]; data.unshift(mw); }
    
    document.getElementById('results-list').innerHTML = data.map(m => renderMatchHtml(m)).join('');
    document.getElementById('modal').style.display = 'flex';
    document.querySelector('.play-week-btn').innerText = origText;
    loadData();
}

function closeModal(){
   document.getElementById('modal').style.display = 'none';
}

loadData();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
