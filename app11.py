import random
import uuid
import os
from flask import Flask, render_template_string, request, jsonify, session, url_for
import txt11  # וודא שהקובץ txt11.py נמצא באותה תיקייה

app = Flask(__name__)
app.secret_key = "fifa_manager_pro_master_key"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7

POSITIONS = ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CAM", "LW", "RW", "ST"]

class Player:
    def __init__(self, pos=None):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(txt11.FIRST_NAMES)} {random.choice(txt11.LAST_NAMES)}"
        
        # עמדה נוכחית (יכולה להשתנות בחילופים)
        self.pos = pos if pos else random.choice(list(set(POSITIONS)))
        # עמדה טבעית (נשארת קבועה תמיד)
        self.natural_pos = self.pos 
        
        base = random.randint(65, 88)
        self.ovr = base
        self.pac = base + random.randint(-15, 10)
        self.sho = base + random.randint(-20, 10)
        self.pas = base + random.randint(-10, 10)
        self.dri = base + random.randint(-10, 10)
        self.dfn = base + random.randint(-20, 10)
        self.phy = base + random.randint(-10, 15)
        
        if self.pos == "GK":
            self.pac = random.randint(30, 60); self.sho = random.randint(20, 40)
            self.dfn += 15
        elif self.pos in ["CB", "LB", "RB"]:
            self.dfn += 10; self.sho -= 15
        elif self.pos in ["ST", "LW", "RW"]:
            self.sho += 10; self.pac += 5; self.dfn -= 20
            
        self.value = int((self.ovr - 60) * 1500) + random.randint(1000, 5000)
        if self.value < 2000: self.value = 2000
        
        self.injured_weeks = 0
        self.red_card_weeks = 0

    def tick_status(self):
        if self.injured_weeks > 0: self.injured_weeks -= 1
        if self.red_card_weeks > 0: self.red_card_weeks -= 1

    def to_dict(self): return self.__dict__

class Team:
    def __init__(self, t_info, league_id):
        self.id = str(uuid.uuid4())
        self.name = t_info["name"]
        self.primary = t_info["primary"]
        self.secondary = t_info["secondary"]
        self.league_id = league_id
        self.is_ai = True
        
        self.points = 0; self.games_played = 0; self.wins = 0; self.draws = 0; self.losses = 0
        self.goals_for = 0; self.goals_against = 0
        
        self.budget = 100000 
        
        self.starting_11 = [Player(pos) for pos in POSITIONS]
        self.bench = [Player() for _ in range(7)]

    def get_power(self):
        power = 0
        for p in self.starting_11:
            if p.injured_weeks > 0 or p.red_card_weeks > 0:
                power += (p.ovr * 0.3) 
            else:
                power += p.ovr
        return int(power / 11)

class League:
    def __init__(self):
        self.teams = []
        for l_id, teams in txt11.LEAGUES_DB.items():
            for t in teams:
                self.teams.append(Team(t, l_id))
                
        self.my_team_id = None
        self.my_league_id = None
        self.week = 1
        self.market = [Player() for _ in range(10)]

    def set_player_team(self, tid):
        self.my_team_id = tid
        my_team = next((t for t in self.teams if t.id == tid), None)
        self.my_league_id = my_team.league_id
        for t in self.teams: t.is_ai = (t.id != tid)

    def play_week(self):
        league_teams = [t for t in self.teams if t.league_id == self.my_league_id]
        random.shuffle(league_teams)
        matches = []
        
        for i in range(0, len(league_teams), 2):
            if i+1 < len(league_teams):
                matches.append(self.simulate_match(league_teams[i], league_teams[i+1]))
        
        self.week += 1
        self.market = self.market[3:] + [Player() for _ in range(3)]
        
        my_team = next(t for t in self.teams if t.id == self.my_team_id)
        for p in my_team.starting_11 + my_team.bench:
            p.tick_status()
            
        return matches

    def simulate_match(self, t1, t2):
        p1_pow = t1.get_power()
        p2_pow = t2.get_power()
        
        raw_1 = max(0, ((p1_pow * random.uniform(0.8, 1.2)) - (p2_pow * 0.9)) / 15)
        raw_2 = max(0, ((p2_pow * random.uniform(0.8, 1.2)) - (p1_pow * 0.9)) / 15)
        
        s1 = int(round(raw_1) + random.randint(0, 1))
        s2 = int(round(raw_2) + random.randint(0, 1))
        
        t1.games_played += 1; t2.games_played += 1
        t1.goals_for += s1; t1.goals_against += s2
        t2.goals_for += s2; t2.goals_against += s1
        if s1 > s2: t1.points += 3; t1.wins += 1; t2.losses += 1
        elif s2 > s1: t2.points += 3; t2.wins += 1; t1.losses += 1
        else: t1.points += 1; t2.points += 1; t1.draws += 1; t2.draws += 1
        
        events = []
        if t1.id == self.my_team_id or t2.id == self.my_team_id:
            my_team = t1 if t1.id == self.my_team_id else t2
            if random.random() < 0.15:
                victim = random.choice(my_team.starting_11)
                victim.injured_weeks = random.randint(1, 3)
                events.append(f"🚑 {victim.name} נפצע וייעדר {victim.injured_weeks} שבועות!")
            if random.random() < 0.10:
                victim = random.choice(my_team.starting_11)
                victim.red_card_weeks = 1
                events.append(f"🟥 {victim.name} קיבל אדום ומושעה מהמשחק הבא!")

        return {
            "t1": t1.name, "s1": s1,
            "t2": t2.name, "s2": s2,
            "is_mine": (t1.id == self.my_team_id or t2.id == self.my_team_id),
            "events": events
        }

# משתנה גלובלי לאיחסון הליגות (בזכרון ה-RAM של השרת)
LEAGUES_DB_STORAGE = {}

def get_game():
    uid = session.get('manager_fifa_11_key')
    # אם אין סשן או שהשרת עבר ריסטרט והמידע נמחק
    if not uid or uid not in LEAGUES_DB_STORAGE:
        uid = str(uuid.uuid4())
        session.permanent = True
        session['manager_fifa_11_key'] = uid
        LEAGUES_DB_STORAGE[uid] = League()
    return LEAGUES_DB_STORAGE[uid]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, texts=txt11.TEXTS)

@app.route('/api/data', methods=['GET'])
def get_data():
    g = get_game()
    if not g.my_team_id:
        teams_lite = [{"id": t.id, "name": t.name, "c1": t.primary, "c2": t.secondary, "lg": t.league_id} for t in g.teams]
        return jsonify({"needs_setup": True, "teams_available": teams_lite})

    my_team = next(t for t in g.teams if t.id == g.my_team_id)
    league_teams = [t for t in g.teams if t.league_id == g.my_league_id]
    table = sorted(league_teams, key=lambda t: (t.points, t.goals_for - t.goals_against), reverse=True)

    return jsonify({
        "needs_setup": False,
        "my_team": { 
            "name": my_team.name, "budget": my_team.budget, 
            "starting_11": [p.to_dict() for p in my_team.starting_11],
            "bench": [p.to_dict() for p in my_team.bench],
            "col": my_team.primary 
        },
        "table": [{"pos": i+1, "name": t.name, "pts": t.points, "p": t.games_played, "w":t.wins, "d":t.draws, "l":t.losses, "gd": t.goals_for - t.goals_against} for i, t in enumerate(table)],
        "market": [p.to_dict() for p in g.market],
        "week": g.week
    })

@app.route('/api/pick_team', methods=['POST'])
def pick_team():
    get_game().set_player_team(request.json.get('team_id'))
    return jsonify({"status": "success"})

@app.route('/api/play', methods=['POST'])
def play_week():
    return jsonify(get_game().play_week())

@app.route('/api/swap', methods=['POST'])
def swap_players():
    g = get_game()
    pid1 = request.json.get('id1')
    pid2 = request.json.get('id2')
    my_team = next(t for t in g.teams if t.id == g.my_team_id)
    
    p1, p2 = None, None
    idx1, list1 = -1, None
    idx2, list2 = -1, None
    
    for i, p in enumerate(my_team.starting_11):
        if p.id == pid1: p1, idx1, list1 = p, i, my_team.starting_11
        if p.id == pid2: p2, idx2, list2 = p, i, my_team.starting_11
    for i, p in enumerate(my_team.bench):
        if p.id == pid1: p1, idx1, list1 = p, i, my_team.bench
        if p.id == pid2: p2, idx2, list2 = p, i, my_team.bench
        
    if p1 and p2:
        list1[idx1] = p2
        list2[idx2] = p1
        # החלפת עמדות במגרש (אבל העמדה הטבעית נשארת איתם)
        temp_pos = p1.pos
        p1.pos = p2.pos
        p2.pos = temp_pos
        return jsonify({"status": "ok"})
    return jsonify({"err": "שגיאה בהחלפה"})

@app.route('/api/train', methods=['POST'])
def train_team():
    my_team = next(t for t in get_game().teams if t.id == get_game().my_team_id)
    cost = 15000
    if my_team.budget >= cost:
        my_team.budget -= cost
        trainees = random.sample(my_team.starting_11 + my_team.bench, min(3, len(my_team.starting_11 + my_team.bench)))
        for p in trainees:
            p.ovr += 1; p.pac += 1; p.sho += 1
            p.value += 3000
        names = ", ".join([p.name for p in trainees])
        return jsonify({"msg": f"האימון עבר בהצלחה! השחקנים הבאים השתפרו: {names}"})
    return jsonify({"err": "אין מספיק תקציב לאימון."})

@app.route('/api/transfer', methods=['POST'])
def transfer():
    g = get_game()
    action = request.json.get('action')
    pid = request.json.get('player_id')
    my_team = next(t for t in g.teams if t.id == g.my_team_id)
    
    if action == 'buy':
        target = next((p for p in g.market if p.id == pid), None)
        if target and my_team.budget >= target.value:
            my_team.budget -= target.value
            my_team.bench.append(target)
            g.market.remove(target)
            return jsonify({"msg": f"{target.name} נרכש בהצלחה והצטרף לספסל!"})
        return jsonify({"err": "אין מספיק תקציב."})

    if action == 'sell':
        target = next((p for p in my_team.bench if p.id == pid), None)
        if target:
            my_team.budget += int(target.value * 0.8)
            my_team.bench.remove(target)
            return jsonify({"msg": "השחקן נמכר."})
        return jsonify({"err": "ניתן למכור רק שחקנים מהספסל."})

    return jsonify({"err": "פעולה לא חוקית."})

@app.route('/api/restart')
def force_restart():
    session.clear()
    return jsonify({"ok":True})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ texts.title }}</title>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
<style>
:root { 
    --p-bg: #121620; --p-panel: rgba(28, 36, 52, 0.95); --gold: #eab308; 
    --silver: #cbd5e1; --bronze: #d97706; --grass: #166534; --txt: #f8fafc; 
}
body { margin: 0; background: linear-gradient(to top right, #0f172a, #1e293b); color: var(--txt); font-family: 'Assistant', sans-serif; padding-bottom: 80px;}
* { box-sizing: border-box; }

.header-bar { position: sticky; top:0; z-index:100; background: rgba(15,23,42,0.9); padding: 20px; display: flex; justify-content: space-between; align-items:center; backdrop-filter:blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.5); border-bottom: 2px solid var(--gold);}
.budget-pod { font-family: 'Oswald', sans-serif; font-size: 22px; color: #10b981; background: #020617; padding: 5px 15px; border-radius: 8px; border: 1px solid #334155;}

/* Setup Screen */
#setup-screen { position: absolute; inset:0; background: #0f172a; padding: 40px 20px; z-index:500; text-align:center; overflow-y:auto;}
.grid-teams { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); max-width: 1000px; gap:20px; margin:30px auto; }
.team-option { border-radius:12px; padding:20px; text-align:center; cursor:pointer; border:2px solid transparent; box-shadow: 0 5px 15px rgba(0,0,0,0.5); transition: 0.3s; background: var(--p-panel);}
.team-option:hover { transform: translateY(-5px); border-color: var(--gold);}

/* Tabs */
.tabs-tray { display: flex; max-width:1000px; margin: 20px auto 0; gap:5px; padding:0 10px;}
.tab-b { flex:1; background: #1e293b; color: #94a3b8; border:1px solid #334155; border-bottom:0; padding:12px; font-weight:800; font-size:15px; border-radius: 8px 8px 0 0; cursor: pointer; transition:0.3s;}
.tab-b.active { color:#fff; background: var(--grass); border-color:var(--grass);}

.content-box { display: none; background: rgba(30,41,59,0.5); max-width:1000px; margin: 0 auto; padding:20px; min-height: 500px; border-radius: 0 0 8px 8px;}
.content-box.active { display:block; animation: fadeIn 0.3s;}
@keyframes fadeIn { from{opacity:0;} to{opacity:1;} }

/* FIFA FUT CARD STYLE */
.fut-card {
    width: 110px; height: 165px; background: linear-gradient(135deg, #facc15 0%, #ca8a04 100%);
    border-radius: 10px; position: relative; padding: 5px; color: #451a03; font-family: 'Oswald', sans-serif;
    box-shadow: 0 5px 10px rgba(0,0,0,0.5); cursor: pointer; transition: 0.2s; border: 3px solid transparent;
}
.fut-card.silver { background: linear-gradient(135deg, #e2e8f0, #94a3b8); color: #0f172a;}
.fut-card.bronze { background: linear-gradient(135deg, #d97706, #92400e); color: #fff;}
.fut-card:hover { transform: scale(1.05); }
.fut-card.selected { transform: scale(1.1); border-color: #fff; box-shadow: 0 0 20px #fff; z-index: 10;}

.fut-ovr { position: absolute; top: 3px; left: 6px; font-size: 20px; font-weight: bold; line-height: 1;}
.fut-pos { position: absolute; top: 24px; left: 6px; font-size: 10px; font-weight: bold;}
/* עמדה טבעית - חדש */
.fut-nat-pos { position: absolute; top: 3px; right: 6px; font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.2); border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(0,0,0,0.1);}

.fut-pic { width: 45px; height: 45px; background: rgba(0,0,0,0.1); border-radius: 50%; margin: 5px auto 0; display:flex; justify-content:center; align-items:center; font-size:20px;}
.fut-name { text-align: center; font-size: 12px; font-weight: bold; margin-top: 5px; border-bottom: 1px solid rgba(0,0,0,0.2); padding-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.fut-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 2px; font-size: 9px; margin-top: 3px; text-align: center; line-height: 1.2;}
.fut-status { position: absolute; top:3px; right:3px; font-size:12px; background: rgba(0,0,0,0.7); border-radius:50%; width:20px; height:20px; display:flex; justify-content:center; align-items:center; z-index: 5;}

/* Pitch Layout */
.pitch-container { 
    background: var(--grass); border: 2px solid #fff; border-radius: 10px; 
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 20px 0; min-height: 700px; position: relative; margin-bottom: 20px; overflow:hidden;
}
.pitch-container::before { content:''; position:absolute; top:50%; left:0; width:100%; height:2px; background:rgba(255,255,255,0.4); z-index: 1; }
.pitch-container::after { content:''; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:120px; height:120px; border:2px solid rgba(255,255,255,0.4); border-radius:50%; z-index: 1;}

.pitch-row { display: flex; justify-content: center; align-items: center; gap: 15px; width: 100%; z-index: 2; position: relative;}

.bench-container { display: flex; gap: 10px; overflow-x: auto; padding: 15px; background: rgba(0,0,0,0.4); border-radius: 8px;}

/* Market & Utils */
.market-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 15px;}
.buy-btn, .sell-btn { width:100%; padding:5px; margin-top:5px; border:none; border-radius:4px; font-weight:bold; cursor:pointer;}
.buy-btn { background: #10b981; color:white; } .sell-btn { background: #ef4444; color:white; }

.tbl { width:100%; border-collapse:collapse; background: rgba(0,0,0,0.5); border-radius:8px;}
.tbl th, .tbl td { padding: 12px; text-align: center; border-bottom: 1px solid #334155;}
.tr-my { background: rgba(22, 101, 52, 0.4); font-weight:bold; color:var(--gold);}

.flt-wrap { position:fixed; bottom:0; left:0; width:100%; background:#0f172a; padding:15px; text-align:center; z-index:400; border-top: 1px solid var(--gold);}
.pl-wk { padding:12px 40px; background: var(--gold); color:#000; font-size:20px; border-radius:30px; font-weight:900; border:none; cursor:pointer; box-shadow: 0 0 10px rgba(234, 179, 8, 0.5);}

/* Overlay */
#over { position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:900; display:none; flex-direction:column; align-items:center; padding-top:50px; overflow-y:auto;}
.match-card { background:#1e293b; padding:20px; border-radius:10px; width:90%; max-width:500px; margin-bottom:15px; text-align:center; border:1px solid #334155;}
.match-score { font-size:32px; font-family:'Oswald'; font-weight:bold; color:var(--gold); margin:10px 0;}
.match-events { font-size:14px; color:#f87171; margin-top:10px;}
</style>
</head>
<body>

<div id="setup-screen">
    <h1 style="color:var(--gold); font-size:40px; font-family:'Oswald'; letter-spacing:2px;">{{ texts.title }}</h1>
    <p>{{ texts.sub_title }}</p>
    <div id="sel-render" class="grid-teams"></div>
</div>

<div id="m-body" style="display:none;">
    <div class="header-bar">
        <h2 id="dynN" style="margin:0; font-family:'Oswald';"></h2>
        <div class="budget-pod">{{ texts.budget }}<span id="budget">0</span></div>
    </div>

    <div class="tabs-tray">
        <button class="tab-b active" onclick="goTab('vSqd', this)">{{ texts.tabs.squad }}</button>
        <button class="tab-b" onclick="goTab('vMkt', this)">{{ texts.tabs.market }}</button>
        <button class="tab-b" onclick="goTab('vTbl', this)">{{ texts.tabs.table }}</button>
        <button class="tab-b" onclick="goTab('vCal', this)">{{ texts.tabs.calendar }}</button>
    </div>

    <div class="content-box active" id="vSqd">
        <div style="color:var(--gold); margin-bottom:10px; font-weight:bold;">{{ texts.squad_pitch_title }}</div>
        
        <div class="pitch-container" id="pitch-ui">
            <div class="pitch-row" id="row-att"></div>
            <div class="pitch-row" id="row-mid"></div>
            <div class="pitch-row" id="row-def"></div>
            <div class="pitch-row" id="row-gk"></div>
        </div>

        <div style="color:var(--gold); margin:10px 0; font-weight:bold;">{{ texts.squad_bench_title }}</div>
        <div class="bench-container" id="bench-ui"></div>
    </div>
    
    <div class="content-box" id="vMkt">
        <p>{{ texts.market_desc }}</p>
        <div class="market-grid" id="r_mkt"></div>
    </div>
    
    <div class="content-box" id="vTbl">
        <table class="tbl">
             <thead><tr><th>מקום</th><th>קבוצה</th><th>Pts</th><th>מש'</th><th>נצ'</th><th>הפס'</th><th>הפרש</th></tr></thead>
             <tbody id="r_tbl"></tbody>
        </table>
    </div>

    <div class="content-box" id="vCal">
        <h2 style="color:var(--gold);">מחזור נוכחי: <span id="wwW"></span></h2>
        <hr style="border-color:#334155;">
        <h3>{{ texts.training_title }}</h3>
        <p>{{ texts.training_desc }}</p>
        <button class="pl-wk" style="background:#10b981; color:#fff;" onclick="trainSquad()">{{ texts.btn_train }}</button>
    </div>

    <div class="flt-wrap">
        <button class="pl-wk" onclick="pDay(this)" id="btn-play">{{ texts.btn_play_match }}</button>
        <div style="margin-top:10px; cursor:pointer; color:#ef4444; font-size:12px;" onclick="reZ()">{{ texts.btn_reboot }}</div>
    </div>
</div>

<div id="over">
    <h2 style="color:var(--gold); font-family:'Oswald';">תוצאות המחזור</h2>
    <div id="pOverList" style="width:100%; display:flex; flex-direction:column; align-items:center;"></div>
    <button class="pl-wk" onclick="gEl('over').style.display='none'; _runBld();" style="margin-top:20px; margin-bottom:50px;">המשך לניהול</button>
</div>

<script>
const API = {
   data: "{{ url_for('get_data') }}", pick: "{{ url_for('pick_team') }}",
   play: "{{ url_for('play_week') }}", swap: "{{ url_for('swap_players') }}",
   transfer: "{{ url_for('transfer') }}", train: "{{ url_for('train_team') }}",
   restart: "{{ url_for('force_restart') }}"
};

function gEl(id){ return document.getElementById(id); }

function goTab(vid, btn) {
    document.querySelectorAll('.content-box').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-b').forEach(x => x.classList.remove('active'));
    gEl(vid).classList.add('active'); btn.classList.add('active');
}

async function fireReq(epKey, payload={}, withLoad=true) {
    let pms = {method: payload ? 'POST' : 'GET'};
    if(payload && Object.keys(payload).length>0){ pms.body=JSON.stringify(payload); pms.headers={'Content-Type':'application/json'}; }
    let rx = await fetch(API[epKey], pms); let rz = await rx.json();
    if(rz.err) alert(rz.err); else if (rz.msg) alert(rz.msg);
    if(withLoad) _runBld();
    return rz;
}

let selectedPlayerId = null;
function selectPlayer(id) {
    if(!selectedPlayerId) {
        selectedPlayerId = id;
        _runBld();
    } else {
        if(selectedPlayerId !== id) {
            fireReq('swap', {id1: selectedPlayerId, id2: id});
        }
        selectedPlayerId = null;
    }
}

function getCardClass(ovr) {
    if(ovr >= 80) return 'fut-card';
    if(ovr >= 70) return 'fut-card silver';
    return 'fut-card bronze';
}

function getStatusIcon(p) {
    if(p.red_card_weeks > 0) return `<div class="fut-status">🟥</div>`;
    if(p.injured_weeks > 0) return `<div class="fut-status">🚑</div>`;
    return '';
}

function RPlCard(p, mode="pitch") {
    let selClass = selectedPlayerId === p.id ? "selected" : "";
    let btn = "";
    if(mode === "market") btn = `<button class="buy-btn" onclick="fireReq('transfer', {action:'buy', player_id:'${p.id}'}, true)">קנה ₪${p.value.toLocaleString()}</button>`;
    if(mode === "bench_sell") btn = `<button class="sell-btn" onclick="fireReq('transfer', {action:'sell', player_id:'${p.id}'}, true)">מכור ₪${Math.floor(p.value*0.8).toLocaleString()}</button>`;
    
    let onClick = (mode==="pitch" || mode==="bench_sell") ? `onclick="selectPlayer('${p.id}')"` : "";

    return `
    <div class="${getCardClass(p.ovr)} ${selClass}" ${onClick}>
        ${getStatusIcon(p)}
        <div class="fut-ovr">${p.ovr}</div>
        <div class="fut-pos">${p.pos}</div>
        
        <div class="fut-nat-pos" title="עמדה מקורית">${p.natural_pos}</div>

        <div class="fut-pic">👤</div>
        <div class="fut-name">${p.name}</div>
        <div class="fut-stats">
            <div>PAC ${p.pac}</div> <div>DRI ${p.dri}</div>
            <div>SHO ${p.sho}</div> <div>DEF ${p.dfn}</div>
            <div>PAS ${p.pas}</div> <div>PHY ${p.phy}</div>
        </div>
        ${btn}
    </div>`;
}

function BldUi(data) {
   gEl('dynN').innerHTML = `⚽ ${data.my_team.name}` ;
   gEl('budget').innerText = data.my_team.budget.toLocaleString();
   gEl('wwW').innerText = data.week;
   gEl('btn-play').innerText = "{{ texts.btn_play_match }} " + data.week;
   
   let htmlAtt = "", htmlMid = "", htmlDef = "", htmlGk = "";
   
   data.my_team.starting_11.forEach(p => {
       let card = RPlCard(p, "pitch");
       if(["ST", "LW", "RW"].includes(p.pos)) htmlAtt += card;
       else if(["CAM", "CM", "CDM", "LM", "RM"].includes(p.pos)) htmlMid += card;
       else if(["CB", "LB", "RB"].includes(p.pos)) htmlDef += card;
       else if(p.pos === "GK") htmlGk += card;
   });

   gEl('row-att').innerHTML = htmlAtt;
   gEl('row-mid').innerHTML = htmlMid;
   gEl('row-def').innerHTML = htmlDef;
   gEl('row-gk').innerHTML = htmlGk;
   
   gEl('bench-ui').innerHTML = data.my_team.bench.map(p => RPlCard(p, "bench_sell")).join('');
   gEl('r_mkt').innerHTML= data.market.map(p => RPlCard(p, "market")).join('');

   gEl('r_tbl').innerHTML= data.table.map(t=>`
      <tr class="${t.name===data.my_team.name?'tr-my':''}">
          <td>${t.pos}</td> <td>${t.name}</td> <td>${t.pts}</td>
          <td>${t.p}</td> <td>${t.w}</td> <td>${t.l}</td>
          <td dir="ltr">${t.gd>0?'+'+t.gd:t.gd}</td>
      </tr>`).join('');
}

async function _runBld() {
   let rx = await fetch(API.data); let js = await rx.json();
   if(js.needs_setup) {
       gEl('setup-screen').style.display = 'block';
       gEl('sel-render').innerHTML = js.teams_available.map(tc=>`
           <div class="team-option" style="background: linear-gradient(135deg, ${tc.c1}, #111); border-bottom: 5px solid ${tc.c2};" onclick="fireReq('pick',{team_id:'${tc.id}'})">
              <div style="font-weight:900; font-size:24px; color:${tc.c2}">${tc.name}</div>
           </div>
       `).join('');
   } else {
       gEl('setup-screen').style.display = 'none'; gEl('m-body').style.display = 'block'; BldUi(js);
   }
}

async function pDay(btn) {
   btn.disabled=true; btn.style.opacity="0.5";
   let ans = await fireReq('play', {}, false);
   
   gEl('pOverList').innerHTML = ans.map(m=>`
      <div class="match-card" style="${m.is_mine ? 'border-color:var(--gold); box-shadow: 0 0 15px rgba(234,179,8,0.2);' : ''}">
          <div style="display:flex; justify-content:space-between; align-items:center; color:#fff;">
             <div style="flex:1; text-align:right; font-size:18px;">${m.t1}</div>
             <div class="match-score">${m.s1} - ${m.s2}</div>
             <div style="flex:1; text-align:left; font-size:18px;">${m.t2}</div>
          </div>
          ${m.events ? m.events.map(e => `<div class="match-events">${e}</div>`).join('') : ''}
      </div>`
   ).join('');

   gEl('over').style.display = 'flex';
   btn.disabled=false; btn.style.opacity="1";
}

function trainSquad() { fireReq('train'); }
function reZ(){ if(confirm('{{ texts.btn_reboot }}?')) fireReq('restart'); }

_runBld();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    # השתמש ב-debug=False כדי למנוע ריסטארטים של השרת שמוחקים את המידע מהזכרון
    app.run(host='0.0.0.0', port=5000)
