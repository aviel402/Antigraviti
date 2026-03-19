import random
import uuid
import txt11
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = "manager_pro_ultimate_11_key"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7

POSITIONS = ["GK", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD", "FWD"]

# ===============================
# CLASSES & LOGIC
# ===============================
class Player:
    def __init__(self, is_gk=False):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(txt11.FIRST_NAMES)} {random.choice(txt11.LAST_NAMES)[0]}."
        self.pos = "GK" if is_gk else random.choice(["DEF", "MID", "FWD"])
        
        base = random.randint(65, 88)
        self.att = base + random.randint(-10, 15)
        self.deny = base + random.randint(-10, 15)
        
        if self.pos == "GK": self.att = random.randint(15, 30); self.deny += 15
        elif self.pos == "FWD": self.att += 15; self.deny = random.randint(20, 50)
        
        self.rating = int((self.att + self.deny) / 2) if self.pos != "GK" else self.deny
        if self.pos == "FWD": self.rating = int((self.att * 0.8) + (self.deny * 0.2))
        
        # תקציב התחלתי הוא 100,000, לכן מחירים ריאליים למשחק
        self.value = int(self.rating * 500) + random.randint(1000, 5000)
        
        # מערכת אירועים
        self.injury_days = 0
        self.red_card = 0
        
    def to_dict(self): return self.__dict__

class Team:
    def __init__(self, info, league_key):
        self.id = str(uuid.uuid4())
        self.name = info["name"]
        self.primary = info["c1"]
        self.secondary = info["c2"]
        self.league = league_key
        self.is_ai = True
        
        self.pts = 0; self.p = 0; self.w = 0; self.d = 0; self.l = 0
        self.gf = 0; self.ga = 0
        self.budget = 100000 # לפי הבקשה!
        
        self.squad = [Player(is_gk=True) for _ in range(2)]
        self.squad += [Player() for _ in range(14)]
        self.starting_xi = [p.id for p in self.squad[:11]] # מזהי 11 הפותחים

    def get_power(self):
        starters = [p for p in self.squad if p.id in self.starting_xi and p.injury_days == 0 and p.red_card == 0]
        if not starters: return 10, 10
        avg_att = sum(p.att for p in starters) / len(starters)
        avg_def = sum(p.deny for p in starters) / len(starters)
        return avg_att, avg_def

class LeagueGame:
    def __init__(self):
        self.teams = []
        for l_key, l_data in txt11.LEAGUES.items():
            for t_data in l_data["teams"]:
                self.teams.append(Team(t_data, l_key))
                
        self.my_team_id = None
        self.my_league = None
        self.week = 1
        self.market = [Player(is_gk=(i==0)) for i in range(6)]

    def get_team(self, tid):
        return next((t for t in self.teams if t.id == tid), None)

    def play_week(self):
        # משחקים רק בליגה של המשתמש
        league_teams = [t for t in self.teams if t.league == self.my_league]
        random.shuffle(league_teams)
        matches = []
        
        for i in range(0, len(league_teams), 2):
            matches.append(self.simulate_match(league_teams[i], league_teams[i+1]))
            
        self.week += 1
        self.market = [Player(is_gk=(i==0)) for i in range(6)]
        return matches

    def simulate_match(self, t1, t2):
        p1_a, p1_d = t1.get_power()
        p2_a, p2_d = t2.get_power()
        
        s1 = max(0, int(((p1_a * random.uniform(0.8, 1.2)) - p2_d) / 15) + random.randint(0, 1))
        s2 = max(0, int(((p2_a * random.uniform(0.8, 1.2)) - p1_d) / 15) + random.randint(0, 1))
        
        t1.p += 1; t2.p += 1
        t1.gf += s1; t1.ga += s2
        t2.gf += s2; t2.ga += s1
        if s1 > s2: t1.pts += 3; t1.w += 1; t2.l += 1
        elif s2 > s1: t2.pts += 3; t2.w += 1; t1.l += 1
        else: t1.pts += 1; t2.pts += 1; t1.d += 1; t2.d += 1

        # מערכת פציעות וכרטיסים אחרי המשחק
        self.apply_match_events(t1)
        self.apply_match_events(t2)

        return {"t1": t1.name, "s1": s1, "t2": t2.name, "s2": s2, "is_mine": (t1.id == self.my_team_id or t2.id == self.my_team_id)}

    def apply_match_events(self, team):
        for p in team.squad:
            if p.id in team.starting_xi:
                # סיכוי לפציעה (5%)
                if random.random() < 0.05 and p.injury_days == 0:
                    p.injury_days = random.randint(1, 3) # יחמיץ 1-3 שבועות
                # סיכוי לכרטיס אדום (3%)
                if random.random() < 0.03 and p.red_card == 0:
                    p.red_card = 1 # מושעה ממשחק 1
            
            # החלמה
            if p.injury_days > 0 and p.id not in team.starting_xi: p.injury_days -= 1
            if p.red_card > 0 and p.id not in team.starting_xi: p.red_card -= 1

# ===============================
# SERVER MEMORY
# ===============================
DB = {}
def get_game():
    uid = session.get('m11_uuid')
    if not uid or uid not in DB:
        uid = str(uuid.uuid4())
        session.permanent = True
        session['m11_uuid'] = uid
        DB[uid] = LeagueGame()
    return DB[uid]

# ===============================
# ROUTES
# ===============================
@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, t=txt11.TEXTS, lg=txt11.LEAGUES)

@app.route('/api/data', methods=['GET'])
def get_data():
    g = get_game()
    if not g.my_team_id: return jsonify({"needs_setup": True})

    my_team = g.get_team(g.my_team_id)
    league_teams = [t for t in g.teams if t.league == g.my_league]
    table = sorted(league_teams, key=lambda t: (t.pts, t.gf - t.ga), reverse=True)
    
    month_idx = min((g.week - 1) // 4, len(txt11.TEXTS["months"])-1)
    month_name = txt11.TEXTS["months"][month_idx]

    return jsonify({
        "needs_setup": False,
        "team": { 
            "name": my_team.name, "budget": my_team.budget, 
            "squad": [p.to_dict() for p in my_team.squad], 
            "xi": my_team.starting_xi, "col": my_team.primary 
        },
        "table": [{"pos": i+1, "name": t.name, "pts": t.pts, "gd": t.gf - t.ga} for i, t in enumerate(table)],
        "market": [p.to_dict() for p in g.market],
        "calendar": {"week": g.week, "month": month_name}
    })

@app.route('/api/pick_team', methods=['POST'])
def pick_team():
    g = get_game()
    tid = request.json.get('team_id')
    t = g.get_team(tid)
    g.my_team_id = tid
    g.my_league = t.league
    t.is_ai = False
    return jsonify({"ok": True})

@app.route('/api/swap', methods=['POST'])
def swap_player():
    g = get_game()
    t = g.get_team(g.my_team_id)
    pid = request.json.get('pid')
    
    if pid in t.starting_xi:
        t.starting_xi.remove(pid)
    else:
        if len(t.starting_xi) < 11:
            t.starting_xi.append(pid)
        else:
            return jsonify({"err": "ההרכב מלא (11 שחקנים). הוצא שחקן קודם."})
    return jsonify({"ok": True})

@app.route('/api/transfer', methods=['POST'])
def transfer():
    g = get_game(); t = g.get_team(g.my_team_id)
    action = request.json.get('action'); pid = request.json.get('pid')
    
    if action == 'buy':
        p = next((x for x in g.market if x.id == pid), None)
        if p and t.budget >= p.value:
            t.budget -= p.value; t.squad.append(p); g.market.remove(p)
            return jsonify({"msg": "שחקן נרכש בהצלחה!"})
        return jsonify({"err": "אין מספיק תקציב."})
    if action == 'sell':
        p = next((x for x in t.squad if x.id == pid), None)
        if p and len(t.squad) > 13:
            if p.id in t.starting_xi: t.starting_xi.remove(p.id)
            t.budget += int(p.value * 0.8)
            t.squad.remove(p)
            return jsonify({"msg": "שחקן נמכר."})
        return jsonify({"err": "הסגל קטן מדי, לא ניתן למכור."})

@app.route('/api/train', methods=['POST'])
def train():
    g = get_game(); t = g.get_team(g.my_team_id)
    if t.budget >= 15000:
        t.budget -= 15000
        for pid in t.starting_xi:
            p = next((x for x in t.squad if x.id == pid), None)
            if p: p.att += 1; p.deny += 1; p.rating += 1
        return jsonify({"msg": "האימון עבר בהצלחה! השחקנים הפותחים השתפרו."})
    return jsonify({"err": "אין מספיק תקציב לאימון."})

@app.route('/api/play', methods=['POST'])
def play():
    g = get_game(); t = g.get_team(g.my_team_id)
    if len(t.starting_xi) < 11: return jsonify({"err": "חובה להציב 11 שחקנים בהרכב הפותח!"})
    
    for pid in t.starting_xi:
        p = next((x for x in t.squad if x.id == pid), None)
        if p and (p.injury_days > 0 or p.red_card > 0):
            return jsonify({"err": f"השחקן {p.name} פצוע או מורחק! הוצא אותו מההרכב."})
            
    return jsonify(g.play_week())

@app.route('/api/restart')
def restart(): session.clear(); return jsonify({"ok": True})


# ===============================
# HTML / CSS / JS FRONTEND
# ===============================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ t.app_name }}</title>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&display=swap" rel="stylesheet">
<style>
:root { --bg: #0f172a; --panel: #1e293b; --gold: #facc15; --grass: #166534; --text: #f8fafc; }
body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Assistant', sans-serif; padding-bottom: 80px;}
* { box-sizing: border-box; }

.header { position: sticky; top:0; background: #0b0f19; padding: 15px 20px; display:flex; justify-content:space-between; align-items:center; z-index:100; border-bottom:3px solid var(--gold);}
.budget { font-family: monospace; font-size: 20px; color: #10b981; font-weight:bold; background:#000; padding:5px 10px; border-radius:5px;}

/* Setup Screen */
#setup { position:fixed; inset:0; background: var(--bg); z-index:500; display:flex; flex-direction:column; align-items:center; padding-top:50px; overflow-y:auto;}
.league-group { width: 90%; max-width:800px; margin-bottom: 30px;}
.league-title { border-bottom: 2px solid var(--gold); padding-bottom: 5px; margin-bottom: 15px;}
.team-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
.team-btn { padding: 20px 10px; border-radius: 8px; text-align: center; cursor: pointer; border: 2px solid transparent; transition: 0.3s; color:#fff; font-weight:bold;}
.team-btn:hover { transform: scale(1.05); border-color: #fff; }

/* Tabs */
.tabs { display:flex; max-width: 1000px; margin: 20px auto 0; gap:5px; padding:0 10px;}
.tab { flex:1; padding: 12px 5px; background: var(--panel); border:none; color: #94a3b8; font-weight:bold; cursor:pointer; border-radius: 8px 8px 0 0; font-family:inherit;}
.tab.active { background: var(--grass); color: #fff; }

.view { display:none; max-width:1000px; margin: 0 auto; background: var(--panel); padding: 15px; border-radius: 0 0 8px 8px; min-height: 50vh;}
.view.active { display:block; }

/* FIFA Cards */
.card-grid { display: flex; flex-wrap: wrap; gap: 15px; justify-content:center; }
.fifa-card { 
    width: 130px; height: 190px; background: linear-gradient(135deg, #b8860b, #ffd700); 
    border-radius: 10px; position: relative; color: #000; box-shadow: 0 5px 10px rgba(0,0,0,0.5);
    display:flex; flex-direction:column; align-items:center; padding: 10px 5px; cursor:pointer; border:2px solid transparent;
}
.fifa-card.bronze { background: linear-gradient(135deg, #cd7f32, #8b4513); color:#fff;}
.fifa-card.silver { background: linear-gradient(135deg, #c0c0c0, #808080); }
.fifa-card.bench { filter: grayscale(80%); opacity:0.8;}
.fifa-card.selected { border-color: #fff; transform:translateY(-5px); filter:none; opacity:1;}

.c-rtg { position:absolute; top:5px; left:10px; font-size:22px; font-weight:900; }
.c-pos { position:absolute; top:30px; left:12px; font-size:12px; font-weight:bold; }
.c-pic { width:60px; height:60px; background:rgba(255,255,255,0.3); border-radius:50%; margin-top:10px; }
.c-name { font-weight:bold; font-size:14px; margin-top:5px; text-align:center; width:100%; white-space:nowrap; overflow:hidden;}
.c-stats { display:flex; justify-content:space-around; width:100%; border-top:1px solid rgba(0,0,0,0.2); margin-top:auto; padding-top:5px; font-size:12px; font-weight:bold;}
.c-alert { position:absolute; top:-10px; right:-10px; background:red; color:white; border-radius:50%; width:25px; height:25px; display:flex; align-items:center; justify-content:center; font-size:14px; box-shadow:0 0 5px #000;}

/* Pitch */
.pitch { background: var(--grass); border: 2px solid #fff; height: 400px; border-radius: 5px; position:relative; margin-bottom: 20px; display:flex; flex-direction:column; justify-content:space-around; padding:10px;}
.pitch-row { display:flex; justify-content:center; gap:10px; }

/* Action Footer */
.footer { position:fixed; bottom:0; width:100%; background: #0b0f19; padding: 15px; text-align:center; z-index:200;}
.btn-play { background: var(--gold); color:#000; border:none; padding:10px 30px; font-size:18px; font-weight:bold; border-radius:30px; cursor:pointer; font-family:inherit;}

/* Calendar & Training */
.cal-box { background: #0b0f19; padding:20px; border-radius:10px; text-align:center; border:1px solid #334155;}
.cal-month { font-size: 30px; color: var(--gold); font-weight:900; margin-bottom:5px;}
.btn-train { background: #3b82f6; color:white; border:none; padding:15px; border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer; width:100%; margin-top:20px;}

/* Table */
table { width:100%; border-collapse:collapse; text-align:center;}
th, td { padding: 10px; border-bottom: 1px solid #334155;}
th { color: var(--gold); }
.my-row { background: rgba(22, 101, 52, 0.5); font-weight:bold;}

#modal { position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:900; display:none; justify-content:center; align-items:center; flex-direction:column;}
</style>
</head>
<body>

<div id="setup">
    <h1 style="color:var(--gold);">{{ t.setup_title }}</h1>
    <p>{{ t.setup_sub }}</p>
    {% for l_key, l_data in lg.items() %}
    <div class="league-group">
        <h2 class="league-title">{{ l_data.name }}</h2>
        <div class="team-grid">
            {% for team in l_data.teams %}
            <div class="team-btn" style="background: linear-gradient(135deg, {{ team.c1 }}, #000); border-bottom-color:{{ team.c2 }};" 
                 onclick="pickTeam('{{ team.name }}')">
                {{ team.name }}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</div>

<div id="app" style="display:none;">
    <div class="header" id="hdr">
        <h2 style="margin:0;" id="t-name">Team</h2>
        <div class="budget">€<span id="t-budg">0</span></div>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="switchTab('v-pitch', this)">{{ t.tab_pitch }}</button>
        <button class="tab" onclick="switchTab('v-market', this)">{{ t.tab_market }}</button>
        <button class="tab" onclick="switchTab('v-table', this)">{{ t.tab_table }}</button>
        <button class="tab" onclick="switchTab('v-club', this)">{{ t.tab_club }}</button>
    </div>

    <!-- PITCH & SQUAD -->
    <div id="v-pitch" class="view active">
        <div style="text-align:center; color:#94a3b8; font-size:14px; margin-bottom:10px;">לחץ על שחקן מחוץ למגרש כדי להכניס אותו, ועל שחקן במגרש כדי להוציא אותו.</div>
        <div class="pitch" id="pitch-render"></div>
        <h3 style="color:var(--gold);">ספסל / מילואים</h3>
        <div class="card-grid" id="bench-render"></div>
    </div>

    <!-- MARKET -->
    <div id="v-market" class="view">
        <div class="card-grid" id="market-render"></div>
    </div>

    <!-- TABLE -->
    <div id="v-table" class="view">
        <table>
            <thead><tr><th>#</th><th style="text-align:right;">קבוצה</th><th>PTS</th><th>GD</th></tr></thead>
            <tbody id="table-render"></tbody>
        </table>
    </div>

    <!-- CLUB -->
    <div id="v-club" class="view">
        <div class="cal-box">
            <div style="color:#94a3b8;">{{ t.calendar_title }}</div>
            <div class="cal-month" id="cal-month">אוגוסט</div>
            <div style="font-size:18px;">שבוע <span id="cal-week">1</span></div>
        </div>
        <button class="btn-train" onclick="apiCall('train')">{{ t.train_btn }}</button>
        <p style="color:#94a3b8; font-size:12px; text-align:center;">{{ t.train_desc }}</p>
        
        <button onclick="if(confirm('בטוח?')) apiCall('restart')" style="background:transparent; border:1px solid red; color:red; padding:10px; width:100%; margin-top:50px; border-radius:5px;">{{ t.btn_restart }}</button>
    </div>

    <div class="footer">
        <button class="btn-play" onclick="playMatch()">{{ t.btn_play }}</button>
    </div>
</div>

<!-- MATCH MODAL -->
<div id="modal">
    <h1 style="color:#fff; font-size:40px;">תוצאת סיום</h1>
    <div id="m-res" style="font-size:30px; font-weight:bold; color:var(--gold); margin-bottom:30px;"></div>
    <button onclick="closeModal()" style="padding:10px 30px; background:var(--grass); color:white; border:none; border-radius:5px; font-size:20px;">המשך</button>
</div>

<script>
let myTeamName = "";

function switchTab(id, btn) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
}

async function apiCall(ep, payload={}, reload=true) {
    let opts = { method: payload ? 'POST' : 'GET' };
    if(payload && Object.keys(payload).length>0) {
        opts.body = JSON.stringify(payload);
        opts.headers = {'Content-Type': 'application/json'};
    }
    let res = await fetch('/api/'+ep, opts);
    let data = await res.json();
    if(data.err) alert(data.err);
    else if(data.msg) alert(data.msg);
    if(reload) loadData();
    return data;
}

function getCardStyle(rating) {
    if(rating >= 80) return "fifa-card";
    if(rating >= 72) return "fifa-card silver";
    return "fifa-card bronze";
}

function genCard(p, mode) {
    let style = getCardStyle(p.rating);
    let alert = p.red_card > 0 ? `<div class="c-alert">🟥</div>` : p.injury_days > 0 ? `<div class="c-alert">🤕</div>` : "";
    
    let act = "";
    if(mode==="pitch") { act = `onclick="apiCall('swap', {pid:'${p.id}'})"`; }
    if(mode==="bench") { style+=" bench"; act = `onclick="apiCall('swap', {pid:'${p.id}'})"`; }
    if(mode==="market"){ act = `onclick="if(confirm('לקנות ב-${p.value}?')) apiCall('transfer', {action:'buy', pid:'${p.id}'})"`; }
    
    let foot = mode==="market" ? `<div style="font-size:11px; margin-top:5px; color:#10b981;">€${p.value}</div>` : 
               mode==="bench" ? `<div style="font-size:11px; margin-top:5px; color:red;" onclick="event.stopPropagation(); apiCall('transfer',{action:'sell',pid:'${p.id}'})">מכור (€${parseInt(p.value*0.8)})</div>` : "";

    return `
    <div class="${style}" ${act}>
        ${alert}
        <div class="c-rtg">${p.rating}</div>
        <div class="c-pos">${p.pos}</div>
        <div class="c-pic"></div>
        <div class="c-name">${p.name}</div>
        <div class="c-stats">
            <div>⚔️ ${p.att}</div>
            <div>🛡️ ${p.deny}</div>
        </div>
        ${foot}
    </div>`;
}

async function loadData() {
    let res = await fetch('/api/data');
    let data = await res.json();
    
    if(data.needs_setup) {
        document.getElementById('setup').style.display = 'flex';
        document.getElementById('app').style.display = 'none';
        return;
    }
    
    document.getElementById('setup').style.display = 'none';
    document.getElementById('app').style.display = 'block';
    
    let t = data.team;
    myTeamName = t.name;
    document.getElementById('t-name').innerText = t.name;
    document.getElementById('hdr').style.borderBottomColor = t.col;
    document.getElementById('t-budg').innerText = t.budget.toLocaleString();
    
    // סיווג סגל למגרש וספסל
    let xi = t.squad.filter(p => t.xi.includes(p.id));
    let bench = t.squad.filter(p => !t.xi.includes(p.id));
    
    // סידור על המגרש לפי עמדות
    let gk = xi.filter(p=>p.pos==="GK");
    let def = xi.filter(p=>p.pos==="DEF");
    let mid = xi.filter(p=>p.pos==="MID");
    let fwd = xi.filter(p=>p.pos==="FWD");
    
    document.getElementById('pitch-render').innerHTML = `
        <div class="pitch-row">${fwd.map(p=>genCard(p, "pitch")).join('')}</div>
        <div class="pitch-row">${mid.map(p=>genCard(p, "pitch")).join('')}</div>
        <div class="pitch-row">${def.map(p=>genCard(p, "pitch")).join('')}</div>
        <div class="pitch-row">${gk.map(p=>genCard(p, "pitch")).join('')}</div>
    `;
    
    document.getElementById('bench-render').innerHTML = bench.map(p=>genCard(p,"bench")).join('');
    document.getElementById('market-render').innerHTML = data.market.map(p=>genCard(p,"market")).join('');
    
    document.getElementById('table-render').innerHTML = data.table.map(tr => `
        <tr class="${tr.name===t.name?'my-row':''}">
            <td>${tr.pos}</td>
            <td style="text-align:right;">${tr.name}</td>
            <td>${tr.pts}</td>
            <td dir="ltr">${tr.gd>0?'+'+tr.gd:tr.gd}</td>
        </tr>
    `).join('');
    
    document.getElementById('cal-month').innerText = data.calendar.month;
    document.getElementById('cal-week').innerText = data.calendar.week;
}

async function pickTeam(name) {
    let t_id = "";
    // איתור ה-ID לפי שם דורש להעביר נתונים, אז שיניתי את פייתון שיחפש לפי שם.
    // לצורך פשטות: נשלח את שם הקבוצה, בשרת נתקן למצוא לפי שם
    let res = await fetch('/api/pick_team', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({team_id: name}) // We will modify backend to accept name
    });
    loadData();
}

async function playMatch() {
    let data = await apiCall('play', {}, false);
    if(!data || data.err) return; // שגיאת הרכב פצוע
    
    let myMatch = data.find(m => m.is_mine);
    document.getElementById('m-res').innerText = `${myMatch.t1} ${myMatch.s1} - ${myMatch.s2} ${myMatch.t2}`;
    document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
    loadData();
}

// הפעלה ראשונית
loadData();
</script>
</body>
</html>
"""

# עדכון קטן בפייתון כדי שיקבל שם קבוצה במקום ID (יותר קל בממשק)
@app.route('/api/pick_team', methods=['POST'])
def pick_team_override():
    g = get_game()
    t_name = request.json.get('team_id')
    t = next((x for x in g.teams if x.name == t_name), None)
    if t:
        g.my_team_id = t.id
        g.my_league = t.league
        t.is_ai = False
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
