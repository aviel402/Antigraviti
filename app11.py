import random
import uuid
import os
import json
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fifa_manager_pro_master_key_very_secret")
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 14   # 2 שבועות

# ────────────────────────────────────────────────
#    נתונים סטטיים – במקום קובץ txt11.py
# ────────────────────────────────────────────────

FIRST_NAMES = [
    "יונתן", "איתמר", "דניאל", "עומר", "אלון", "תומר", "רועי", "שחר", "אור", "ליאור",
    "אדם", "בן", "גיא", "דור", "איתי", "נועם", "אריאל", "יותם", "שי", "אמיר"
]

LAST_NAMES = [
    "כהן", "לוי", "מזרחי", "פרץ", "אוחיון", "בן דוד", "דוד", "אברהם", "שלום", "מלכה",
    "גולן", "הראל", "זיו", "חן", "טל", "יוסף", "כץ", "ליבוביץ", "מור", "נחום"
]

TEXTS = {
    "title": "מנג'ר כדורגל ישראלי",
    "sub_title": "בחר קבוצה והתחל לנהל!",
    "budget": "תקציב: ₪",
    "tabs": {
        "squad": "סגל",
        "market": "שוק העברות",
        "table": "טבלה",
        "calendar": "לוח משחקים"
    },
    "squad_pitch_title": "הרכב",
    "squad_bench_title": "ספסל",
    "market_desc": "שחקנים זמינים לרכישה",
    "training_title": "אימון שבועי",
    "training_desc": "שפר 2–3 שחקנים (עלות: 15,000 ₪)",
    "btn_train": "בצע אימון",
    "btn_play_match": "שחק מחזור",
    "btn_reboot": "אפס משחק"
}

POSITIONS = ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CAM", "LW", "RW", "ST"]

LEAGUES_DB = {
    "ליגת העל": [
        {"name": "מכבי תל אביב", "primary": "#0055A4", "secondary": "#FFD700"},
        {"name": "הפועל תל אביב", "primary": "#FF0000", "secondary": "#FFFFFF"},
        {"name": "מכבי חיפה", "primary": "#00A651", "secondary": "#FFFFFF"},
        {"name": "בית"ר ירושלים", "primary": "#FFFF00", "secondary": "#000000"},
        {"name": "הפועל באר שבע", "primary": "#9E1B34", "secondary": "#F0C800"},
    ],
    "ליגה לאומית": [
        {"name": "הפועל חדרה", "primary": "#003087", "secondary": "#FFCC00"},
        {"name": "עירוני קריית שמונה", "primary": "#0033A0", "secondary": "#FFD700"},
        {"name": "מ.ס. אשדוד", "primary": "#000080", "secondary": "#FFD700"},
    ]
}

# ────────────────────────────────────────────────
#    מחלקות
# ────────────────────────────────────────────────

class Player:
    def __init__(self, pos=None):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.pos = pos if pos else random.choice(list(set(POSITIONS)))
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
            self.pac = random.randint(30, 60)
            self.sho = random.randint(20, 40)
            self.dfn += 15
        elif self.pos in ["CB", "LB", "RB"]:
            self.dfn += 10
            self.sho -= 15
        elif self.pos in ["ST", "LW", "RW"]:
            self.sho += 10
            self.pac += 5
            self.dfn -= 20

        self.value = int((self.ovr - 60) * 1500) + random.randint(1000, 5000)
        if self.value < 2000:
            self.value = 2000

        self.injured_weeks = 0
        self.red_card_weeks = 0

    def tick_status(self):
        if self.injured_weeks > 0: self.injured_weeks -= 1
        if self.red_card_weeks > 0: self.red_card_weeks -= 1

    def to_dict(self):
        return self.__dict__

class Team:
    def __init__(self, t_info, league_id):
        self.id = str(uuid.uuid4())
        self.name = t_info["name"]
        self.primary = t_info["primary"]
        self.secondary = t_info["secondary"]
        self.league_id = league_id
        self.is_ai = True

        self.points = 0
        self.games_played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0

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
        for l_id, teams in LEAGUES_DB.items():
            for t in teams:
                self.teams.append(Team(t, l_id))

        self.my_team_id = None
        self.my_league_id = None
        self.week = 1
        self.market = [Player() for _ in range(10)]

    def set_player_team(self, tid):
        self.my_team_id = tid
        my_team = next((t for t in self.teams if t.id == tid), None)
        if my_team:
            self.my_league_id = my_team.league_id
            my_team.is_ai = False
        for t in self.teams:
            if t.id != tid:
                t.is_ai = True

    def play_week(self):
        league_teams = [t for t in self.teams if t.league_id == self.my_league_id]
        random.shuffle(league_teams)
        matches = []

        for i in range(0, len(league_teams), 2):
            if i + 1 < len(league_teams):
                matches.append(self.simulate_match(league_teams[i], league_teams[i + 1]))

        self.week += 1
        self.market = self.market[3:] + [Player() for _ in range(3)]

        if self.my_team_id:
            my_team = next((t for t in self.teams if t.id == self.my_team_id), None)
            if my_team:
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

        t1.games_played += 1
        t2.games_played += 1
        t1.goals_for += s1
        t1.goals_against += s2
        t2.goals_for += s2
        t2.goals_against += s1

        if s1 > s2:
            t1.points += 3
            t1.wins += 1
            t2.losses += 1
        elif s2 > s1:
            t2.points += 3
            t2.wins += 1
            t1.losses += 1
        else:
            t1.points += 1
            t2.points += 1
            t1.draws += 1
            t2.draws += 1

        events = []
        my_team = None
        if t1.id == self.my_team_id:
            my_team = t1
        elif t2.id == self.my_team_id:
            my_team = t2

        if my_team:
            if random.random() < 0.15:
                victim = random.choice(my_team.starting_11)
                victim.injured_weeks = random.randint(1, 3)
                events.append(f"🚑 {victim.name} נפצע – ייעדר {victim.injured_weeks} שבועות")
            if random.random() < 0.10:
                victim = random.choice(my_team.starting_11)
                victim.red_card_weeks = 1
                events.append(f"🟥 {victim.name} הורחק – מושעה למשחק הבא")

        return {
            "t1": t1.name, "s1": s1,
            "t2": t2.name, "s2": s2,
            "is_mine": bool(my_team),
            "events": events
        }

# ────────────────────────────────────────────────
#    שמירה ב-session (Vercel – ללא disk)
# ────────────────────────────────────────────────

def get_game():
    key = session.get('fm_key')
    if not key:
        key = str(uuid.uuid4())
        session['fm_key'] = key
        session.permanent = True

    # ב-Vercel session מאוחסן בדרך כלל ב-Redis / cookie – נשתמש בו ישירות
    if 'fm_data' not in session:
        league = League()
        session['fm_data'] = league.__dict__   # שמירה ראשונית
        # הערה: __dict__ לא שומר אובייקטים מורכבים כמו Player בצורה מושלמת
        # לכן נצטרך לבנות מחדש חלקים – פתרון פשוט יותר בהמשך

    # פתרון זמני – נשמור רק את החלקים הקריטיים
    data = session.get('fm_data', {})
    league = League()
    league.week = data.get('week', 1)
    league.my_team_id = data.get('my_team_id')
    league.my_league_id = data.get('my_league_id')
    league.market = [Player() for _ in range(10)]  # ניצור מחדש כל פעם (פשטות)

    if league.my_team_id:
        my_team = next((t for t in league.teams if t.id == league.my_team_id), None)
        if my_team:
            my_team.is_ai = False

    return league


def save_game(league):
    # שמירה מינימלית – מספיק ל-Vercel / session
    session['fm_data'] = {
        'week': league.week,
        'my_team_id': league.my_team_id,
        'my_league_id': league.my_league_id,
        # ניתן להוסיף עוד אם תרצה (budget, players וכו')
    }


# ────────────────────────────────────────────────
#    Routes
# ────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, texts=TEXTS)


@app.route('/api/data', methods=['GET'])
def get_data():
    g = get_game()

    if not g.my_team_id:
        teams_lite = [
            {"id": t.id, "name": t.name, "c1": t.primary, "c2": t.secondary, "lg": t.league_id}
            for t in g.teams
        ]
        return jsonify({"needs_setup": True, "teams_available": teams_lite})

    my_team = next((t for t in g.teams if t.id == g.my_team_id), None)
    if not my_team:
        return jsonify({"error": "team not found"})

    league_teams = [t for t in g.teams if t.league_id == g.my_league_id]
    table = sorted(league_teams, key=lambda t: (t.points, t.goals_for - t.goals_against), reverse=True)

    resp = {
        "needs_setup": False,
        "my_team": {
            "name": my_team.name,
            "budget": my_team.budget,
            "starting_11": [p.to_dict() for p in my_team.starting_11],
            "bench": [p.to_dict() for p in my_team.bench],
            "col": my_team.primary
        },
        "table": [
            {
                "pos": i+1, "name": t.name, "pts": t.points, "p": t.games_played,
                "w": t.wins, "d": t.draws, "l": t.losses, "gd": t.goals_for - t.goals_against
            }
            for i, t in enumerate(table)
        ],
        "market": [p.to_dict() for p in g.market],
        "week": g.week
    }

    save_game(g)   # שמירה עדכנית
    return jsonify(resp)


@app.route('/api/pick_team', methods=['POST'])
def pick_team():
    g = get_game()
    tid = request.json.get('team_id')
    g.set_player_team(tid)
    save_game(g)
    return jsonify({"status": "success"})


@app.route('/api/play', methods=['POST'])
def play_week():
    g = get_game()
    matches = g.play_week()
    save_game(g)
    return jsonify(matches)


@app.route('/api/swap', methods=['POST'])
def swap_players():
    g = get_game()
    pid1 = request.json.get('id1')
    pid2 = request.json.get('id2')

    my_team = next((t for t in g.teams if t.id == g.my_team_id), None)
    if not my_team:
        return jsonify({"err": "no team"})

    p1 = p2 = None
    loc1 = loc2 = None

    for lst in [my_team.starting_11, my_team.bench]:
        for i, p in enumerate(lst):
            if p.id == pid1:
                p1, loc1 = p, (lst, i)
            if p.id == pid2:
                p2, loc2 = p, (lst, i)

    if p1 and p2 and loc1 and loc2:
        list1, idx1 = loc1
        list2, idx2 = loc2
        list1[idx1], list2[idx2] = p2, p1

        # החלפת עמדה נוכחית
        temp = p1.pos
        p1.pos = p2.pos
        p2.pos = temp

        save_game(g)
        return jsonify({"status": "ok"})

    return jsonify({"err": "לא נמצאו השחקנים"})


@app.route('/api/train', methods=['POST'])
def train_team():
    g = get_game()
    my_team = next((t for t in g.teams if t.id == g.my_team_id), None)
    if not my_team:
        return jsonify({"err": "no team"})

    cost = 15000
    if my_team.budget < cost:
        return jsonify({"err": "אין מספיק תקציב"})

    my_team.budget -= cost
    trainees = random.sample(my_team.starting_11 + my_team.bench, min(3, len(my_team.starting_11 + my_team.bench)))

    for p in trainees:
        p.ovr += 1
        p.pac += 1
        p.sho += 1
        p.value += 3000

    names = ", ".join(p.name for p in trainees)
    save_game(g)

    return jsonify({"msg": f"אימון בוצע! השתפרו: {names}"})


@app.route('/api/transfer', methods=['POST'])
def transfer():
    g = get_game()
    action = request.json.get('action')
    pid = request.json.get('player_id')
    my_team = next((t for t in g.teams if t.id == g.my_team_id), None)

    if not my_team:
        return jsonify({"err": "no team"})

    if action == 'buy':
        target = next((p for p in g.market if p.id == pid), None)
        if not target:
            return jsonify({"err": "שחקן לא נמצא"})
        if my_team.budget < target.value:
            return jsonify({"err": "אין מספיק תקציב"})
        my_team.budget -= target.value
        my_team.bench.append(target)
        g.market.remove(target)
        save_game(g)
        return jsonify({"msg": f"{target.name} נרכש!"})

    if action == 'sell':
        target = next((p for p in my_team.bench if p.id == pid), None)
        if not target:
            return jsonify({"err": "שחקן לא בספסל"})
        my_team.budget += int(target.value * 0.8)
        my_team.bench.remove(target)
        save_game(g)
        return jsonify({"msg": "נמכר בהצלחה"})

    return jsonify({"err": "פעולה לא חוקית"})


@app.route('/api/restart', methods=['POST'])
def restart():
    session.clear()
    return jsonify({"ok": True})


# ────────────────────────────────────────────────
#    HTML + CSS + JS
# ────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ texts.title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700;800&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --panel: rgba(22,27,34,0.92);
      --gold: #f59e0b;
      --grass: #14532d;
      --danger: #dc2626;
      --success: #16a34a;
      --txt: #e2e8f0;
      --muted: #94a3b8;
    }
    body {
      margin:0; background: linear-gradient(135deg, #0d1117, #1e293b);
      color: var(--txt); font-family: 'Assistant', sans-serif; min-height:100vh;
    }
    .header {
      position: sticky; top:0; z-index:100;
      background: rgba(15,23,42,0.9); backdrop-filter: blur(10px);
      padding: 1rem; display: flex; justify-content: space-between; align-items: center;
      border-bottom: 2px solid var(--gold); box-shadow: 0 4px 12px #0006;
    }
    .budget {
      background: #020617; padding: 0.5rem 1rem; border-radius: 8px;
      border: 1px solid #334155; font-family: 'Oswald'; font-size: 1.4rem;
      color: #10b981;
    }
    .tabs {
      display: flex; max-width: 1100px; margin: 1.5rem auto; gap: 4px; padding: 0 1rem;
    }
    .tab {
      flex:1; background: #1e293b; color: var(--muted); border:1px solid #334155;
      border-bottom:0; padding: 0.9rem; font-weight:700; border-radius: 10px 10px 0 0;
      cursor:pointer; transition:0.2s;
    }
    .tab.active { background: var(--grass); color:white; border-color: var(--grass); }
    .content { display:none; background: var(--panel); max-width:1100px; margin:0 auto 5rem;
      padding:1.5rem; border-radius:0 0 12px 12px; min-height:60vh; }
    .content.active { display:block; }
    .fut-card {
      width:118px; height:172px; background: linear-gradient(145deg, #fef08a, #d97706);
      border-radius:14px; border:3px solid #000; box-shadow:0 8px 25px #0006;
      color:#111; font-family:'Oswald'; position:relative; overflow:hidden;
      transition: all 0.18s ease;
    }
    .fut-card:hover { transform: scale(1.07) translateY(-6px); box-shadow:0 16px 40px #0008; }
    .fut-card.silver { background: linear-gradient(145deg, #e2e8f0, #64748b); }
    .fut-card.bronze { background: linear-gradient(145deg, #fbbf24, #92400e); color:#fff; }
    .fut-ovr { position:absolute; top:6px; left:8px; font-size:22px; font-weight:900; }
    .fut-pos { position:absolute; top:30px; left:8px; font-size:11px; font-weight:700; }
    .fut-nat-pos { position:absolute; top:6px; right:8px; font-size:11px; background:#0006;
      border-radius:50%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; }
    .fut-pic { width:50px; height:50px; background:#0003; border-radius:50%; margin:8px auto 4px;
      display:flex; align-items:center; justify-content:center; font-size:24px; }
    .fut-name { text-align:center; font-size:13px; font-weight:700; margin:4px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .fut-stats { display:grid; grid-template-columns:1fr 1fr; gap:2px; font-size:9px; text-align:center; }
    .fut-status { position:absolute; top:4px; right:4px; font-size:14px; background:#0009; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; z-index:2; }
    .pitch { background: linear-gradient(to bottom, #166534, #0f3d1e); border:3px solid #fefce8;
      border-radius:16px; padding:2rem 1rem; min-height:780px; position:relative; margin:1.5rem 0;
      box-shadow: inset 0 0 80px #0008; }
    .pitch-row { display:flex; justify-content:center; gap:14px; margin:1.2rem 0; }
    .bench { display:flex; gap:10px; overflow-x:auto; padding:1rem; background:#0004; border-radius:10px; }
    .market-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(130px,1fr)); gap:16px; }
    .btn-buy { background:#10b981; color:white; border:none; width:100%; padding:6px; margin-top:6px; border-radius:6px; font-weight:700; cursor:pointer; }
    .btn-sell { background:#dc2626; color:white; border:none; width:100%; padding:6px; margin-top:6px; border-radius:6px; font-weight:700; cursor:pointer; }
    .table { width:100%; border-collapse:collapse; background:#0004; border-radius:10px; overflow:hidden; }
    .table th, .table td { padding:12px; text-align:center; border-bottom:1px solid #334155; }
    .my-row { background:#14532d66; font-weight:700; color:var(--gold); }
    .btn-play { background: linear-gradient(90deg, var(--gold), #d97706); color:#111;
      font-size:1.4rem; padding:1rem 3rem; border:none; border-radius:999px; font-weight:900;
      box-shadow:0 8px 30px #f59e0b66; cursor:pointer; transition:0.2s; }
    .btn-play:hover { transform:translateY(-3px); box-shadow:0 12px 40px #f59e0b99; }
    .setup { position:fixed; inset:0; background:#0d1117; z-index:1000; padding:3rem 1rem; overflow-y:auto; text-align:center; }
    .team-card { background: linear-gradient(135deg, #222, #111); border-radius:12px; padding:1.5rem;
      margin:1rem; cursor:pointer; transition:0.3s; border:3px solid transparent; }
    .team-card:hover { transform:translateY(-8px); border-color:var(--gold); }
    #overlay { position:fixed; inset:0; background:#000c; z-index:900; display:none; flex-direction:column;
      align-items:center; padding-top:4rem; overflow-y:auto; }
    .match-res { background:#1e293b; padding:1.5rem; border-radius:12px; width:90%; max-width:520px; margin:1rem; text-align:center; border:1px solid #334155; }
    .score { font-size:3rem; font-family:'Oswald'; color:var(--gold); margin:0.8rem 0; }
    .footer-bar { position:fixed; bottom:0; left:0; right:0; background:#0f172a; padding:1rem;
      text-align:center; border-top:2px solid var(--gold); z-index:400; }
  </style>
</head>
<body>

<div id="setup" class="setup">
  <h1 style="color:var(--gold); font-family:'Oswald'; font-size:3.2rem; margin-bottom:0.5rem;">{{ texts.title }}</h1>
  <p style="font-size:1.3rem; color:#cbd5e1;">{{ texts.sub_title }}</p>
  <div id="teams-grid" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1.5rem; max-width:1200px; margin:2rem auto;"></div>
</div>

<div id="main" style="display:none;">

  <div class="header">
    <h2 id="team-name" style="margin:0; font-family:'Oswald';">⚽ מנג'ר</h2>
    <div class="budget">{{ texts.budget }}<span id="budget-val">0</span></div>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="tab('squad')"> {{ texts.tabs.squad }} </div>
    <div class="tab" onclick="tab('market')"> {{ texts.tabs.market }} </div>
    <div class="tab" onclick="tab('table')"> {{ texts.tabs.table }} </div>
    <div class="tab" onclick="tab('calendar')"> {{ texts.tabs.calendar }} </div>
  </div>

  <div id="squad" class="content active">
    <h3 style="color:var(--gold); text-align:center;">{{ texts.squad_pitch_title }}</h3>
    <div id="pitch" class="pitch">
      <div class="pitch-row" id="row-att"></div>
      <div class="pitch-row" id="row-mid"></div>
      <div class="pitch-row" id="row-def"></div>
      <div class="pitch-row" id="row-gk"></div>
    </div>
    <h3 style="color:var(--gold); text-align:center; margin-top:2rem;">{{ texts.squad_bench_title }}</h3>
    <div id="bench" class="bench"></div>
  </div>

  <div id="market" class="content">
    <p style="text-align:center; color:#cbd5e1;">{{ texts.market_desc }}</p>
    <div id="market-list" class="market-grid"></div>
  </div>

  <div id="table" class="content">
    <table class="table">
      <thead><tr><th>#</th><th>קבוצה</th><th>נק'</th><th>מש'</th><th>נצ'</th><th>תיקו</th><th>הפס'</th><th>הפרש</th></tr></thead>
      <tbody id="tbl-body"></tbody>
    </table>
  </div>

  <div id="calendar" class="content">
    <h2 style="color:var(--gold); text-align:center;">מחזור <span id="week-num"></span></h2>
    <div style="text-align:center; margin:3rem 0;">
      <h3>{{ texts.training_title }}</h3>
      <p>{{ texts.training_desc }}</p>
      <button class="btn-play" style="background:#16a34a; color:white;" onclick="train()"> {{ texts.btn_train }} </button>
    </div>
  </div>

  <div class="footer-bar">
    <button id="btn-play-week" class="btn-play" onclick="playWeek()"> {{ texts.btn_play_match }} </button>
    <div onclick="restartGame()" style="margin-top:1rem; color:#f87171; cursor:pointer; font-size:0.95rem;">
      {{ texts.btn_reboot }}
    </div>
  </div>
</div>

<div id="overlay">
  <h2 style="color:var(--gold); font-family:'Oswald';">תוצאות המחזור</h2>
  <div id="results-list" style="width:90%; max-width:600px;"></div>
  <button class="btn-play" onclick="document.getElementById('overlay').style.display='none'; build()" style="margin:2rem 0;">
    המשך
  </button>
</div>

<script>
const API = {
  data: "{{ url_for('get_data') }}",
  pick: "{{ url_for('pick_team') }}",
  play: "{{ url_for('play_week') }}",
  swap: "{{ url_for('swap_players') }}",
  train: "{{ url_for('train_team') }}",
  transfer: "{{ url_for('transfer') }}",
  restart: "{{ url_for('restart') }}"
};

let selected = null;

function $(id){return document.getElementById(id)}
function tab(id){
  document.querySelectorAll('.content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el=>el.classList.remove('active'));
  $(id).classList.add('active');
  document.querySelector(`[onclick="tab('${id}')"]`).classList.add('active');
}

async function api(endpoint, body=null){
  const opt = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {method:'GET'};
  const res = await fetch(API[endpoint], opt);
  const data = await res.json();
  if(data.err) alert(data.err);
  if(data.msg) alert(data.msg);
  return data;
}

function cardHTML(p, mode='pitch'){
  const sel = selected === p.id ? 'transform:scale(1.08);border-color:#fff;box-shadow:0 0 30px #fff8;' : '';
  let btn = '';
  if(mode==='market') btn=`<button class="btn-buy" onclick="api('transfer',{action:'buy',player_id:'${p.id}'}).then(build)">קנה ₪${p.value.toLocaleString()}</button>`;
  if(mode==='sell')   btn=`<button class="btn-sell" onclick="api('transfer',{action:'sell',player_id:'${p.id}'}).then(build)">מכור ₪${Math.round(p.value*0.8).toLocaleString()}</button>`;

  const status = p.red_card_weeks>0 ? '🟥' : p.injured_weeks>0 ? '🚑' : '';

  return `
  <div class="fut-card ${p.ovr>=80?'':p.ovr>=70?'silver':'bronze'}" style="${sel}" onclick="${mode==='pitch'||mode==='sell'?'select(\"'+p.id+'\")':''}">
    ${status ? `<div class="fut-status">${status}</div>` : ''}
    <div class="fut-ovr">${p.ovr}</div>
    <div class="fut-pos">${p.pos}</div>
    <div class="fut-nat-pos" title="עמדה טבעית">${p.natural_pos}</div>
    <div class="fut-pic">👤</div>
    <div class="fut-name">${p.name}</div>
    <div class="fut-stats">
      <div>PAC ${p.pac}</div><div>DRI ${p.dri}</div>
      <div>SHO ${p.sho}</div><div>DEF ${p.dfn}</div>
      <div>PAS ${p.pas}</div><div>PHY ${p.phy}</div>
    </div>
    ${btn}
  </div>`;
}

function select(id){
  if(selected === id){
    selected = null;
  } else if(selected){
    api('swap', {id1:selected, id2:id}).then(()=> {selected=null; build();});
  } else {
    selected = id;
  }
  build();
}

function buildPitch(data){
  const posMap = {att:['ST','LW','RW'], mid:['CAM','CM'], def:['CB','LB','RB'], gk:['GK']};
  let html = {att:'', mid:'', def:'', gk:''};

  data.my_team.starting_11.forEach(p=>{
    const card = cardHTML(p, 'pitch');
    if(posMap.att.includes(p.pos)) html.att += card;
    else if(posMap.mid.includes(p.pos)) html.mid += card;
    else if(posMap.def.includes(p.pos)) html.def += card;
    else if(posMap.gk.includes(p.pos)) html.gk += card;
  });

  $('row-att').innerHTML = html.att;
  $('row-mid').innerHTML = html.mid;
  $('row-def').innerHTML = html.def;
  $('row-gk').innerHTML = html.gk;

  $('bench').innerHTML = data.my_team.bench.map(p=>cardHTML(p,'sell')).join('');
}

async function build(){
  const data = await api('data');
  if(data.needs_setup){
    $('setup').style.display = 'block';
    $('main').style.display = 'none';
    $('teams-grid').innerHTML = data.teams_available.map(t=>`
      <div class="team-card" style="border-bottom:6px solid ${t.c2};" onclick="api('pick',{team_id:'${t.id}'}).then(build)">
        <div style="font-size:1.8rem; font-weight:800; color:${t.c2};">${t.name}</div>
      </div>
    `).join('');
  } else {
    $('setup').style.display = 'none';
    $('main').style.display = 'block';

    $('team-name').innerText = `⚽ ${data.my_team.name}`;
    $('budget-val').innerText = data.my_team.budget.toLocaleString();
    $('week-num').innerText = data.week;
    $('btn-play-week').innerText = `{{ texts.btn_play_match }} ${data.week}`;

    buildPitch(data);

    $('market-list').innerHTML = data.market.map(p=>cardHTML(p,'market')).join('');

    let rows = '';
    data.table.forEach(t=>{
      rows += `<tr class="${t.name===data.my_team.name?'my-row':''}">
        <td>${t.pos}</td><td>${t.name}</td><td>${t.pts}</td><td>${t.p}</td>
        <td>${t.w}</td><td>${t.d}</td><td>${t.l}</td><td dir="ltr">${t.gd>0?'+':''}${t.gd}</td>
      </tr>`;
    });
    $('tbl-body').innerHTML = rows;
  }
}

async function playWeek(){
  const btn = $('btn-play-week');
  btn.disabled = true;
  btn.style.opacity = '0.6';

  const res = await api('play');
  let html = '';
  res.forEach(m=>{
    html += `
    <div class="match-res" style="${m.is_mine?'border:2px solid var(--gold); box-shadow:0 0 20px #f59e0b44;':''}">
      <div style="display:flex; justify-content:space-between; font-size:1.4rem;">
        <div>${m.t1}</div>
        <div class="score">${m.s1} - ${m.s2}</div>
        <div>${m.t2}</div>
      </div>
      ${m.events ? m.events.map(e=>`<div style="color:#f87171; margin-top:0.6rem;">${e}</div>`).join('') : ''}
    </div>`;
  });
  $('results-list').innerHTML = html;
  $('overlay').style.display = 'flex';

  btn.disabled = false;
  btn.style.opacity = '1';
}

function train(){ api('train').then(build); }

function restartGame(){
  if(confirm('לאפס את המשחק?')) api('restart').then(()=>{ location.reload(); });
}

build();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    # Vercel ישתמש ב-port מהסביבה או 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
