import random
import uuid
import os
import math
from flask import Flask, render_template_string, request, jsonify, session

# הנחה: txt11.py קיים בסביבת העבודה עם TEXTS, FIRST_NAMES, LAST_NAMES, LEAGUES_DB
try:
    import txt11
except ImportError:
    # Fallback למקרה שהקובץ לא קיים, כדי שהקוד ירוץ
    class txt11:
        FIRST_NAMES = ["אבי", "דני", "יוסי", "רועי", "עומר", "ברק", "עידן", "משה", "תומר", "גיא", "אור", "שון"]
        LAST_NAMES = ["כהן", "לוי", "מזרחי", "פרץ", "ביטון", "דוד", "אברהם", "חזן", "גולן", "אוחיון"]
        LEAGUES_DB = {"IL": [{"name": "מכבי תל אביב", "primary": "#ecc918", "secondary": "#051381"},
                             {"name": "מכבי חיפה", "primary": "#008000", "secondary": "#ffffff"},
                             {"name": "הפועל באר שבע", "primary": "#ff0000", "secondary": "#ffffff"},
                             {"name": "בית״ר ירושלים", "primary": "#ffff00", "secondary": "#000000"}]}
        TEXTS = {
            "title": "Manager PRO", "sub_title": "בחר את הקבוצה שלך וצא לדרך!",
            "budget": "תקציב: ₪",
            "tabs": {"squad": "הרכב", "market": "שוק ההעברות", "table": "טבלה", "calendar": "משחקים ואימונים"},
            "squad_pitch_title": "11 הפותחים", "squad_bench_title": "ספסל (לחץ למכירה/חילוף)",
            "market_desc": "רכוש שחקנים לחיזוק הקבוצה. הרשימה מתרעננת כל מחזור.",
            "training_title": "אימון שחקנים", "training_desc": "שפר יכולות של 3 שחקנים אקראיים בעלות של ₪15,000.",
            "btn_train": "אמן קבוצה (₪15K)", "btn_play_match": "שחק מחזור", "btn_reboot": "התחל מחדש"
        }

app = Flask(__name__)
app.secret_key = "fifa_manager_pro_master_key_v2"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7

# מערך 4-3-3 קלאסי
FORMATIONS = ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CAM", "LW", "ST", "RW"]

class Player:
    def __init__(self, pos=None):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(txt11.FIRST_NAMES)} {random.choice(txt11.LAST_NAMES)}"
        
        self.natural_pos = pos if pos else random.choice(list(set(FORMATIONS)))
        # הגיל משפיע על פוטנציאל אימון
        self.age = random.randint(17, 34)
        
        # OVR התחלתי
        if self.age < 21: base = random.randint(60, 75)
        elif self.age > 30: base = random.randint(70, 85)
        else: base = random.randint(65, 88)
        
        self.ovr = base
        self.pac = min(99, max(30, base + random.randint(-15, 12)))
        self.sho = min(99, max(20, base + random.randint(-20, 15)))
        self.pas = min(99, max(40, base + random.randint(-10, 12)))
        self.dri = min(99, max(40, base + random.randint(-10, 15)))
        self.dfn = min(99, max(20, base + random.randint(-20, 15)))
        self.phy = min(99, max(40, base + random.randint(-15, 15)))
        
        # התאמת סטטים לעמדה
        if self.natural_pos == "GK":
            self.pac = random.randint(30, 55); self.sho = random.randint(20, 40)
            self.dfn = min(99, self.dfn + 15)
        elif self.natural_pos in ["CB", "LB", "RB"]:
            self.dfn = min(99, self.dfn + 15); self.sho = max(20, self.sho - 15)
        elif self.natural_pos in ["ST", "LW", "RW"]:
            self.sho = min(99, self.sho + 15); self.pac = min(99, self.pac + 10); self.dfn = max(20, self.dfn - 20)
            
        self.calculate_value()
        
        self.injured_weeks = 0
        self.red_card_weeks = 0
        self.goals = 0

    def calculate_value(self):
        # חישוב ערך אקספוננציאלי: שחקן 85 עולה הרבה יותר משחקן 65
        base_val = 1500 * (1.18 ** max(0, self.ovr - 60))
        # בונוס/עונש גיל
        if self.age < 22: base_val *= 1.3
        elif self.age > 30: base_val *= 0.7
        self.value = int(base_val) + random.randint(500, 2000)
        if self.value < 2000: self.value = 2000

    def tick_status(self):
        if self.injured_weeks > 0: self.injured_weeks -= 1
        if self.red_card_weeks > 0: self.red_card_weeks -= 1

    def train(self):
        if self.ovr >= 99: return False
        growth = 2 if self.age < 23 else 1
        if self.age > 30 and random.random() < 0.5: growth = 0 # שחקנים ותיקים מתקשים להשתפר
        
        if growth > 0:
            self.ovr += growth
            self.pac = min(99, self.pac + growth)
            self.sho = min(99, self.sho + growth)
            self.pas = min(99, self.pas + growth)
            self.calculate_value()
            return True
        return False

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
        
        self.budget = 150000 
        
        self.starting_11 = [Player(pos) for pos in FORMATIONS]
        self.bench = [Player() for _ in range(7)]

    def get_power(self, is_human=False):
        power = 0
        for i, p in enumerate(self.starting_11):
            multiplier = 1.0
            if p.injured_weeks > 0 or p.red_card_weeks > 0:
                multiplier = 0.2  # עונש קשה על שחקן חסר
            elif is_human:
                # בדיקת התאמת עמדה לשחקן האנושי (מבוסס על מיקום במערך 4-3-3)
                expected_pos = FORMATIONS[i]
                if p.natural_pos != expected_pos:
                    if p.natural_pos in ["ST", "LW", "RW"] and expected_pos in ["ST", "LW", "RW"]:
                        multiplier = 0.9 # פגיעה קלה בשינוי עמדת התקפה
                    elif p.natural_pos in ["CB", "LB", "RB"] and expected_pos in ["CB", "LB", "RB"]:
                        multiplier = 0.9
                    else:
                        multiplier = 0.7 # פגיעה קשה בעמדה לא קשורה
            power += (p.ovr * multiplier)
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
        self.market = sorted([Player() for _ in range(12)], key=lambda x: x.ovr, reverse=True)

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
        # ריענון שוק ההעברות - שמירת 4 והגרלת 8 חדשים
        self.market = self.market[:4] + [Player() for _ in range(8)]
        self.market.sort(key=lambda x: x.ovr, reverse=True)
        
        my_team = next(t for t in self.teams if t.id == self.my_team_id)
        for p in my_team.starting_11 + my_team.bench:
            p.tick_status()
            
        return matches

    def generate_scorers(self, team, goals):
        scorers = []
        attackers = [p for p in team.starting_11 if p.natural_pos in ["ST", "LW", "RW", "CAM"]]
        others = [p for p in team.starting_11 if p not in attackers and p.natural_pos != "GK"]
        
        for _ in range(goals):
            pool = attackers * 3 + others # סיכוי גבוה יותר לשחקני התקפה
            if not pool: pool = team.starting_11
            scorer = random.choice(pool)
            scorer.goals += 1
            scorers.append(scorer.name)
        return scorers

    def simulate_match(self, t1, t2):
        p1_pow = t1.get_power(t1.id == self.my_team_id)
        p2_pow = t2.get_power(t2.id == self.my_team_id)
        
        # יתרון ביתיות קל לקבוצה 1
        raw_1 = max(0, ((p1_pow * random.uniform(0.9, 1.3)) - (p2_pow * 0.9)) / 14)
        raw_2 = max(0, ((p2_pow * random.uniform(0.8, 1.2)) - (p1_pow * 0.95)) / 14)
        
        s1 = int(round(raw_1) + (1 if random.random() > 0.8 else 0))
        s2 = int(round(raw_2) + (1 if random.random() > 0.85 else 0))
        
        t1.games_played += 1; t2.games_played += 1
        t1.goals_for += s1; t1.goals_against += s2
        t2.goals_for += s2; t2.goals_against += s1
        
        if s1 > s2: t1.points += 3; t1.wins += 1; t2.losses += 1
        elif s2 > s1: t2.points += 3; t2.wins += 1; t1.losses += 1
        else: t1.points += 1; t2.points += 1; t1.draws += 1; t2.draws += 1
        
        scorers_t1 = self.generate_scorers(t1, s1)
        scorers_t2 = self.generate_scorers(t2, s2)

        events = []
        is_mine = (t1.id == self.my_team_id or t2.id == self.my_team_id)
        if is_mine:
            my_team = t1 if t1.id == self.my_team_id else t2
            # פציעות והרחקות - סיכוי מעט נמוך יותר
            if random.random() < 0.10:
                victim = random.choice([p for p in my_team.starting_11 if p.injured_weeks == 0])
                victim.injured_weeks = random.randint(1, 3)
                events.append(f"🚑 {victim.name} נפצע וייעדר {victim.injured_weeks} שבועות!")
            if random.random() < 0.05:
                victim = random.choice([p for p in my_team.starting_11 if p.red_card_weeks == 0])
                victim.red_card_weeks = 1
                events.append(f"🟥 {victim.name} ספג כרטיס אדום ומושעה מהמשחק הבא!")

        return {
            "t1": t1.name, "s1": s1, "sc1": scorers_t1,
            "t2": t2.name, "s2": s2, "sc2": scorers_t2,
            "is_mine": is_mine,
            "events": events
        }

LEAGUES_DB_STORAGE = {}

def get_game():
    uid = session.get('manager_fifa_11_key')
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
    table = sorted(league_teams, key=lambda t: (t.points, t.goals_for - t.goals_against, t.goals_for), reverse=True)

    return jsonify({
        "needs_setup": False,
        "my_team": { 
            "name": my_team.name, "budget": my_team.budget, 
            "starting_11": [p.to_dict() for p in my_team.starting_11],
            "bench": [p.to_dict() for p in my_team.bench],
            "col": my_team.primary,
            "power": my_team.get_power(True)
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
    idx1 = request.json.get('idx1')
    idx2 = request.json.get('idx2')
    loc1 = request.json.get('loc1') # 'pitch' or 'bench'
    loc2 = request.json.get('loc2')
    
    my_team = next(t for t in g.teams if t.id == g.my_team_id)
    
    list1 = my_team.starting_11 if loc1 == 'pitch' else my_team.bench
    list2 = my_team.starting_11 if loc2 == 'pitch' else my_team.bench

    try:
        idx1, idx2 = int(idx1), int(idx2)
        # החלפת השחקנים עצמם במערכים
        list1[idx1], list2[idx2] = list2[idx2], list1[idx1]
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"err": "שגיאה בביצוע החילוף."})

@app.route('/api/train', methods=['POST'])
def train_team():
    my_team = next(t for t in get_game().teams if t.id == get_game().my_team_id)
    cost = 15000
    if my_team.budget >= cost:
        my_team.budget -= cost
        pool = [p for p in my_team.starting_11 + my_team.bench if p.ovr < 99]
        if not pool:
            return jsonify({"err": "כל השחקנים הגיעו למקסימום פוטנציאל!"})
            
        trainees = random.sample(pool, min(3, len(pool)))
        success_names = []
        for p in trainees:
            if p.train():
                success_names.append(p.name)
        
        if success_names:
            return jsonify({"msg": f"אימון עבר בהצלחה! השתפרו: {', '.join(success_names)}", "type": "success"})
        else:
            return jsonify({"msg": "האימון הסתיים, אך השחקנים עייפים ולא נרשם שיפור משמעותי.", "type": "warning"})
    return jsonify({"err": "אין מספיק תקציב לאימון."})

@app.route('/api/transfer', methods=['POST'])
def transfer():
    g = get_game()
    action = request.json.get('action')
    pid = request.json.get('player_id')
    my_team = next(t for t in g.teams if t.id == g.my_team_id)
    
    if action == 'buy':
        target = next((p for p in g.market if p.id == pid), None)
        if target:
            if my_team.budget >= target.value:
                if len(my_team.bench) >= 15:
                     return jsonify({"err": "הספסל מלא! מכור שחקנים קודם."})
                my_team.budget -= target.value
                my_team.bench.append(target)
                g.market.remove(target)
                return jsonify({"msg": f"החתמת את {target.name} תמורת ₪{target.value:,}!", "type": "success"})
            return jsonify({"err": "אין מספיק תקציב להשלמת ההעברה."})
        return jsonify({"err": "השחקן כבר לא זמין בשוק."})

    if action == 'sell':
        target = next((p for p in my_team.bench if p.id == pid), None)
        if target:
            sell_price = int(target.value * 0.8)
            my_team.budget += sell_price
            my_team.bench.remove(target)
            return jsonify({"msg": f"מכרת את {target.name} תמורת ₪{sell_price:,}.", "type": "info"})
        return jsonify({"err": "ניתן למכור רק שחקנים הנמצאים בספסל."})

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
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;800&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
<style>
:root { 
    --bg-main: #0b0f19; --bg-panel: #151b2b; --gold: #eab308; --gold-glow: rgba(234, 179, 8, 0.4);
    --green: #10b981; --red: #ef4444; --text-light: #f8fafc; --text-muted: #94a3b8;
    --pitch-bg: linear-gradient(0deg, #0e4d25 0%, #166534 50%, #105228 100%);
}
body { margin: 0; background: var(--bg-main); color: var(--text-light); font-family: 'Assistant', sans-serif; padding-bottom: 90px; overflow-x: hidden;}
* { box-sizing: border-box; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-main); }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }

/* Header */
.header-bar { 
    position: sticky; top:0; z-index:100; background: rgba(11, 15, 25, 0.95); padding: 15px 20px; 
    display: flex; justify-content: space-between; align-items:center; backdrop-filter:blur(10px); 
    border-bottom: 2px solid #1e293b; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.team-branding { display: flex; align-items: center; gap: 10px; }
.team-power { background: #1e293b; color: var(--gold); padding: 4px 10px; border-radius: 20px; font-weight: bold; font-family: 'Oswald', sans-serif; font-size: 14px; border: 1px solid #334155;}
.budget-pod { font-family: 'Oswald', sans-serif; font-size: 20px; color: var(--green); background: #020617; padding: 6px 16px; border-radius: 8px; border: 1px solid #1e293b;}

/* Setup Screen */
#setup-screen { position: fixed; inset:0; background: radial-gradient(circle at top, #1e293b, #020617); padding: 60px 20px; z-index:500; text-align:center; overflow-y:auto;}
.grid-teams { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); max-width: 1000px; gap:20px; margin:40px auto; }
.team-option { 
    border-radius:16px; padding:30px 20px; text-align:center; cursor:pointer; 
    border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); background: var(--bg-panel);
}
.team-option:hover { transform: translateY(-10px); border-color: var(--gold); box-shadow: 0 15px 40px var(--gold-glow);}

/* Tabs */
.tabs-tray { display: flex; max-width:1100px; margin: 20px auto 0; gap:8px; padding:0 15px; overflow-x: auto; scrollbar-width: none;}
.tab-b { 
    flex:1; min-width: max-content; background: var(--bg-panel); color: var(--text-muted); 
    border:1px solid #1e293b; border-bottom:0; padding:14px 20px; font-weight:800; font-size:15px; 
    border-radius: 12px 12px 0 0; cursor: pointer; transition:0.3s;
}
.tab-b:hover { color: #fff; background: #1e293b; }
.tab-b.active { color:var(--bg-main); background: var(--gold); border-color:var(--gold); }

.content-box { display: none; background: #0f141e; max-width:1100px; margin: 0 auto; padding:25px; min-height: 500px; border-radius: 0 0 12px 12px; border: 1px solid #1e293b; border-top: none;}
.content-box.active { display:block; animation: fadeIn 0.4s ease-out;}
@keyframes fadeIn { from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:translateY(0);} }

/* FUT CARD STYLE */
.fut-card {
    width: 115px; min-height: 180px; height: auto;
    border-radius: 12px; position: relative; padding: 10px 6px; 
    font-family: 'Oswald', 'Assistant', sans-serif; cursor: pointer; transition: all 0.2s; border: 2px solid transparent;
    display: flex; flex-direction: column; justify-content: flex-start; box-shadow: 0 6px 15px rgba(0,0,0,0.4);
    user-select: none;
}
.card-gold { background: linear-gradient(135deg, #facc15 0%, #a16207 100%); color: #451a03; }
.card-silver { background: linear-gradient(135deg, #e2e8f0, #64748b); color: #0f172a; }
.card-bronze { background: linear-gradient(135deg, #d97706, #78350f); color: #fff; }

.fut-card:hover { transform: translateY(-5px) scale(1.03); }
.fut-card.selected { transform: scale(1.08) translateY(-5px); border-color: #fff; box-shadow: 0 0 25px rgba(255,255,255,0.5); z-index: 20;}

.fut-ovr { position: absolute; top: 6px; left: 8px; font-size: 24px; font-weight: 700; line-height: 1;}
.fut-pos { position: absolute; top: 28px; left: 8px; font-size: 11px; font-weight: 700;}
.fut-nat-pos { position: absolute; top: 6px; right: 6px; font-size: 11px; font-weight: bold; background: rgba(0,0,0,0.3); color: #fff; border-radius: 4px; padding: 2px 5px;}
.fut-age { position: absolute; top: 28px; right: 6px; font-size: 10px; opacity: 0.8;}

.fut-pic { width: 45px; height: 45px; background: rgba(0,0,0,0.15); border-radius: 50%; margin: 15px auto 4px; display:flex; justify-content:center; align-items:flex-end; font-size:26px; overflow:hidden;}

.fut-name { 
    text-align: center; font-size: 13px; font-weight: 800; 
    margin: 8px 0; padding-bottom: 6px; 
    border-bottom: 1px solid rgba(0,0,0,0.2); 
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;
}

.fut-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 3px 6px; font-size: 11px; margin-bottom: 8px; text-align: center; font-weight: 600;}
.fut-status { position: absolute; top:-8px; right:-8px; font-size:16px; background: rgba(0,0,0,0.8); border-radius:50%; width:26px; height:26px; display:flex; justify-content:center; align-items:center; z-index: 5; box-shadow: 0 2px 5px rgba(0,0,0,0.5);}

/* Pitch Layout - CSS Grid Setup for 4-3-3 */
.pitch-container { 
    background: var(--pitch-bg); border: 2px solid rgba(255,255,255,0.2); border-radius: 12px; 
    position: relative; margin-bottom: 25px; padding: 30px 20px;
    min-height: 850px; display: grid; /* הוגדל משמעותית כדי להכיל את התוויות בנוחות */
    grid-template-rows: 1fr 1fr 1fr 1fr;
    grid-template-areas: "att" "mid" "def" "gk";
    box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
    row-gap: 15px;
}
.pitch-container::before { content:''; position:absolute; top:50%; left:0; width:100%; height:2px; background:rgba(255,255,255,0.3); }
.pitch-container::after { content:''; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:140px; height:140px; border:2px solid rgba(255,255,255,0.3); border-radius:50%;}

.pitch-row { display: flex; justify-content: center; align-items: center; gap: 15px; width: 100%; z-index: 2;}
#r-att { grid-area: att; align-items: flex-end;}
#r-mid { grid-area: mid; }
#r-def { grid-area: def; align-items: flex-start;}
#r-gk { grid-area: gk; align-items: flex-end;}

/* 🌟 סגנון חדש לעמדות במגרש 🌟 */
.pitch-slot { display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 2;}
.slot-label {
    font-size: 11px; font-weight: 800; background: rgba(0,0,0,0.85); padding: 4px 12px; 
    border-radius: 20px; z-index: 10; font-family: 'Assistant', sans-serif; letter-spacing: 0.5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.5); text-align: center;
}

.bench-container { display: flex; gap: 12px; overflow-x: auto; padding: 15px; background: var(--bg-panel); border-radius: 12px; border: 1px solid #1e293b;}

/* Buttons & Utils */
.market-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(115px, 1fr)); gap: 15px;}
.act-btn { width:100%; padding:8px 4px; margin-top:auto; border:none; border-radius:6px; font-weight:800; cursor:pointer; font-family:'Assistant'; transition: 0.2s; font-size: 13px;}
.act-btn:active { transform: scale(0.95); }
.buy-btn { background: var(--green); color:white; } .buy-btn:hover{background:#059669;}
.sell-btn { background: var(--red); color:white; } .sell-btn:hover{background:#dc2626;}

.tbl { width:100%; border-collapse:collapse; background: var(--bg-panel); border-radius:12px; overflow:hidden;}
.tbl th { background: #1e293b; padding: 15px; text-align: center; color: var(--text-muted); font-weight: 600;}
.tbl td { padding: 12px 15px; text-align: center; border-bottom: 1px solid #1e293b;}
.tbl tr:last-child td { border-bottom: none;}
.tbl tr:hover { background: rgba(255,255,255,0.02); }
.tr-my { background: rgba(234, 179, 8, 0.08) !important; font-weight:bold; color:var(--gold);}

.flt-wrap { position:fixed; bottom:0; left:0; width:100%; background:rgba(11, 15, 25, 0.95); backdrop-filter:blur(10px); padding:15px; text-align:center; z-index:400; border-top: 1px solid #1e293b;}
.pl-wk { padding:14px 45px; background: var(--gold); color:#000; font-size:22px; border-radius:30px; font-weight:800; border:none; cursor:pointer; box-shadow: 0 0 20px rgba(234, 179, 8, 0.3); transition: 0.3s; font-family:'Oswald';}
.pl-wk:hover { transform: translateY(-3px); box-shadow: 0 0 30px rgba(234, 179, 8, 0.5); }
.pl-wk:disabled { background: #334155; color: #94a3b8; box-shadow: none; cursor: not-allowed; transform: none;}

/* Match Overlay */
#over { position:fixed; inset:0; background:rgba(2, 6, 23, 0.95); backdrop-filter: blur(5px); z-index:900; display:none; flex-direction:column; align-items:center; padding-top:40px; overflow-y:auto;}
.match-card { background:var(--bg-panel); padding:20px; border-radius:16px; width:92%; max-width:600px; margin-bottom:15px; text-align:center; border:1px solid #1e293b;}
.match-score { font-size:36px; font-family:'Oswald'; font-weight:bold; color:var(--gold); margin:10px 0; background: #0f141e; padding: 5px 20px; border-radius: 12px; display:inline-block;}
.scorers { font-size: 13px; color: var(--text-muted); display: flex; justify-content: space-between; margin-top: 5px; }
.scorers div { flex: 1; }
.match-events { font-size:14px; color:var(--red); margin-top:15px; padding-top: 10px; border-top: 1px dashed #334155;}

/* Toast Notifications */
#toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; pointer-events: none;}
.toast { background: #1e293b; color: #fff; padding: 15px 20px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-weight: 600; animation: slideIn 0.3s ease forwards; border-right: 4px solid var(--gold); min-width: 250px;}
.toast.success { border-right-color: var(--green); }
.toast.error { border-right-color: var(--red); }
@keyframes slideIn { from{transform:translateX(100%); opacity:0;} to{transform:translateX(0); opacity:1;} }
@keyframes fadeOut { from{opacity:1;} to{opacity:0;} }
</style>
</head>
<body>

<div id="toast-container"></div>

<div id="setup-screen">
    <h1 style="color:var(--gold); font-size:48px; font-family:'Oswald'; letter-spacing:2px; text-shadow: 0 0 20px rgba(234,179,8,0.3); margin-bottom: 10px;">{{ texts.title }}</h1>
    <p style="font-size: 18px; color: var(--text-muted);">{{ texts.sub_title }}</p>
    <div id="sel-render" class="grid-teams"></div>
</div>

<div id="m-body" style="display:none;">
    <div class="header-bar">
        <div class="team-branding">
            <h2 id="dynN" style="margin:0; font-family:'Oswald'; font-size:24px;"></h2>
            <div class="team-power" id="t-power" title="כוח קבוצה (מושפע מהתאמת עמדות)">OVR 0</div>
        </div>
        <div class="budget-pod">₪ <span id="budget">0</span></div>
    </div>

    <div class="tabs-tray">
        <button class="tab-b active" onclick="goTab('vSqd', this)">{{ texts.tabs.squad }}</button>
        <button class="tab-b" onclick="goTab('vMkt', this)">{{ texts.tabs.market }}</button>
        <button class="tab-b" onclick="goTab('vTbl', this)">{{ texts.tabs.table }}</button>
        <button class="tab-b" onclick="goTab('vCal', this)">{{ texts.tabs.calendar }}</button>
    </div>

    <div class="content-box active" id="vSqd">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <div style="color:var(--gold); font-weight:800; font-size:18px;">{{ texts.squad_pitch_title }}</div>
            <div style="font-size:12px; color:var(--text-muted);">לחץ על שני שחקנים להחלפה ביניהם</div>
        </div>
        
        <div class="pitch-container" id="pitch-ui">
            <div class="pitch-row" id="r-att"></div>
            <div class="pitch-row" id="r-mid"></div>
            <div class="pitch-row" id="r-def"></div>
            <div class="pitch-row" id="r-gk"></div>
        </div>

        <div style="color:var(--gold); margin:20px 0 10px; font-weight:800; font-size:18px;">{{ texts.squad_bench_title }}</div>
        <div class="bench-container" id="bench-ui"></div>
    </div>
    
    <div class="content-box" id="vMkt">
        <p style="color:var(--text-muted); margin-bottom:20px;">{{ texts.market_desc }}</p>
        <div class="market-grid" id="r_mkt"></div>
    </div>
    
    <div class="content-box" id="vTbl">
        <table class="tbl">
             <thead><tr><th>#</th><th>קבוצה</th><th>Pts</th><th>מש'</th><th>נצ'</th><th>תיקו</th><th>הפס'</th><th>הפרש</th></tr></thead>
             <tbody id="r_tbl"></tbody>
        </table>
    </div>

    <div class="content-box" id="vCal">
        <div style="background:var(--bg-panel); padding: 25px; border-radius: 16px; text-align:center; border: 1px solid #1e293b;">
            <h2 style="color:var(--gold); font-family:'Oswald'; font-size:28px; margin:0 0 10px;">מחזור נוכחי: <span id="wwW"></span></h2>
            <p style="color:var(--text-muted);">שחק את המחזור מול הקבוצות האחרות בליגה.</p>
        </div>
        
        <div style="margin-top: 30px; background:var(--bg-panel); padding: 25px; border-radius: 16px; border: 1px solid #1e293b;">
            <h3 style="color:var(--green); margin-top:0;">{{ texts.training_title }} 🏋️</h3>
            <p style="color:var(--text-muted);">{{ texts.training_desc }}</p>
            <button class="pl-wk" style="background:var(--green); color:#fff; font-size:16px; padding:10px 25px; box-shadow:none;" onclick="trainSquad()">{{ texts.btn_train }}</button>
        </div>
    </div>

    <div class="flt-wrap">
        <button class="pl-wk" onclick="pDay(this)" id="btn-play">{{ texts.btn_play_match }}</button>
        <div style="margin-top:12px; cursor:pointer; color:var(--text-muted); font-size:13px; text-decoration:underline;" onclick="reZ()">{{ texts.btn_reboot }}</div>
    </div>
</div>

<div id="over">
    <h2 style="color:var(--gold); font-family:'Oswald'; font-size:40px; margin-bottom: 30px; text-shadow: 0 0 15px rgba(234,179,8,0.5);">תוצאות המחזור</h2>
    <div id="pOverList" style="width:100%; display:flex; flex-direction:column; align-items:center;"></div>
    <button class="pl-wk" onclick="gEl('over').style.display='none'; _runBld();" style="margin-top:20px; margin-bottom:60px;">המשך לניהול</button>
</div>

<script>
let basePath = window.location.pathname;
if (!basePath.endsWith('/')) { basePath += '/'; }

const API = {
   data: basePath + "api/data", pick: basePath + "api/pick_team",
   play: basePath + "api/play", swap: basePath + "api/swap",
   transfer: basePath + "api/transfer", train: basePath + "api/train", restart: basePath + "api/restart"
};

function gEl(id){ return document.getElementById(id); }

function showToast(msg, type='info') {
    const container = gEl('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function goTab(vid, btn) {
    document.querySelectorAll('.content-box').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-b').forEach(x => x.classList.remove('active'));
    gEl(vid).classList.add('active'); btn.classList.add('active');
    window.scrollTo({top:0, behavior:'smooth'});
}

async function fireReq(epKey, payload={}, withLoad=true) {
    let pms = {method: payload ? 'POST' : 'GET'};
    if(payload && Object.keys(payload).length>0){ pms.body=JSON.stringify(payload); pms.headers={'Content-Type':'application/json'}; }
    try {
        let rx = await fetch(API[epKey], pms); 
        let rz = await rx.json();
        if(rz.err) showToast(rz.err, 'error'); 
        else if (rz.msg) showToast(rz.msg, rz.type || 'success');
        if(withLoad) _runBld();
        return rz;
    } catch(e) {
        showToast("שגיאת תקשורת עם השרת", "error");
    }
}

let selPlayer = null; 
function handlePlayerClick(idx, loc) {
    if(!selPlayer) {
        selPlayer = {idx, loc};
        _runBld(); 
    } else {
        if(selPlayer.idx === idx && selPlayer.loc === loc) {
            selPlayer = null; 
            _runBld();
        } else {
            fireReq('swap', {idx1: selPlayer.idx, loc1: selPlayer.loc, idx2: idx, loc2: loc});
            selPlayer = null;
        }
    }
}

function getCardClass(ovr) {
    if(ovr >= 80) return 'fut-card card-gold';
    if(ovr >= 70) return 'fut-card card-silver';
    return 'fut-card card-bronze';
}

function getStatusIcon(p) {
    if(p.red_card_weeks > 0) return `<div class="fut-status">🟥</div>`;
    if(p.injured_weeks > 0) return `<div class="fut-status">🚑</div>`;
    return '';
}

function RPlCard(p, mode, index=null) {
    let isSel = (selPlayer && selPlayer.idx === index && selPlayer.loc === mode);
    let selClass = isSel ? "selected" : "";
    let btn = "";
    
    if(mode === "market") {
        btn = `<button class="act-btn buy-btn" onclick="fireReq('transfer', {action:'buy', player_id:'${p.id}'}, true)">קנה ₪${p.value.toLocaleString()}</button>`;
    } else if(mode === "bench") {
        btn = `<button class="act-btn sell-btn" onclick="event.stopPropagation(); fireReq('transfer', {action:'sell', player_id:'${p.id}'}, true)">מכור ₪${Math.floor(p.value*0.8).toLocaleString()}</button>`;
    }
    
    let onClick = (mode === "pitch" || mode === "bench") ? `onclick="handlePlayerClick(${index}, '${mode}')"` : "";

    return `
    <div style="position:relative; display:flex; flex-direction:column; height:100%;">
        <div class="${getCardClass(p.ovr)} ${selClass}" ${onClick}>
            ${getStatusIcon(p)}
            <div class="fut-ovr">${p.ovr}</div>
            <div class="fut-nat-pos">${p.natural_pos}</div>
            <div class="fut-age">גיל ${p.age}</div>

            <div class="fut-pic">👤</div>
            <div class="fut-name" title="${p.name}">${p.name}</div>
            <div class="fut-stats">
                <div>PAC ${p.pac}</div> <div>DRI ${p.dri}</div>
                <div>SHO ${p.sho}</div> <div>DEF ${p.dfn}</div>
                <div>PAS ${p.pas}</div> <div>PHY ${p.phy}</div>
            </div>
            ${btn}
        </div>
    </div>`;
}

function BldUi(data) {
   gEl('dynN').innerHTML = `⚽ ${data.my_team.name}` ;
   gEl('t-power').innerText = `OVR ${data.my_team.power}`;
   
   const elBudget = gEl('budget');
   const currentB = parseInt(elBudget.innerText.replace(/,/g, '')) || 0;
   if(currentB !== data.my_team.budget) {
       elBudget.innerText = data.my_team.budget.toLocaleString();
       elBudget.style.color = '#fff';
       setTimeout(()=> elBudget.style.color = 'var(--green)', 300);
   }

   gEl('wwW').innerText = data.week;
   gEl('btn-play').innerText = "{{ texts.btn_play_match }} " + data.week;
   
   const s11 = data.my_team.starting_11;
   
   // הגדרות מערך ותוויות למגרש
   const FORMATION = ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CAM", "LW", "ST", "RW"];
   const LABELS = {
       "GK": "שוער (GK)", "LB": "מגן שמאלי (LB)", "CB": "בלם (CB)", "RB": "מגן ימני (RB)",
       "CM": "קשר (CM)", "CAM": "קשר התקפי (CAM)", "LW": "כנף שמאל (LW)", "ST": "חלוץ (ST)", "RW": "כנף ימין (RW)"
   };

   let htmlAtt = "", htmlMid = "", htmlDef = "", htmlGk = "";
   
   s11.forEach((p, i) => {
       let expectedPos = FORMATION[i];
       let labelText = LABELS[expectedPos];
       let isMatch = p.natural_pos === expectedPos;
       let labelColor = isMatch ? "var(--green)" : "var(--red)";

       // עוטף את הכרטיס במשבצת שכוללת תווית עמדה
       let slotHtml = `
       <div class="pitch-slot">
           <div class="slot-label" style="color: ${labelColor}; border: 1px solid ${labelColor};">${labelText}</div>
           ${RPlCard(p, "pitch", i)}
       </div>`;

       if(i >= 8) htmlAtt += slotHtml;
       else if(i >= 5) htmlMid += slotHtml;
       else if(i >= 1) htmlDef += slotHtml;
       else htmlGk += slotHtml;
   });

   gEl('r-att').innerHTML = htmlAtt;
   gEl('r-mid').innerHTML = htmlMid;
   gEl('r-def').innerHTML = htmlDef;
   gEl('r-gk').innerHTML = htmlGk;
   
   gEl('bench-ui').innerHTML = data.my_team.bench.map((p, i) => RPlCard(p, "bench", i)).join('');
   gEl('r_mkt').innerHTML= data.market.map(p => RPlCard(p, "market")).join('');

   gEl('r_tbl').innerHTML= data.table.map(t=>`
      <tr class="${t.name===data.my_team.name?'tr-my':''}">
          <td>${t.pos}</td> 
          <td style="font-weight:bold;">${t.name}</td> 
          <td style="color:var(--gold); font-weight:bold;">${t.pts}</td>
          <td>${t.p}</td> <td>${t.w}</td> <td>${t.d}</td> <td>${t.l}</td>
          <td dir="ltr" style="color:${t.gd>0?'var(--green)':t.gd<0?'var(--red)':''}">${t.gd>0?'+'+t.gd:t.gd}</td>
      </tr>`).join('');
}

async function _runBld() {
   let rx = await fetch(API.data); let js = await rx.json();
   if(js.needs_setup) {
       gEl('setup-screen').style.display = 'block';
       gEl('sel-render').innerHTML = js.teams_available.map(tc=>`
           <div class="team-option" style="background: linear-gradient(145deg, ${tc.c1}22, var(--bg-panel)); border-bottom: 5px solid ${tc.c2};" onclick="fireReq('pick',{team_id:'${tc.id}'})">
              <div style="width:60px; height:60px; background:${tc.c1}; border:3px solid ${tc.c2}; border-radius:50%; margin:0 auto 15px;"></div>
              <div style="font-weight:800; font-size:22px; color:#fff;">${tc.name}</div>
           </div>
       `).join('');
   } else {
       gEl('setup-screen').style.display = 'none'; gEl('m-body').style.display = 'block'; BldUi(js);
   }
}

async function pDay(btn) {
   btn.disabled=true; 
   let originalText = btn.innerText;
   btn.innerText = "משחק מתקיים... ⚽";
   
   let ans = await fireReq('play', {}, false);
   
   gEl('pOverList').innerHTML = ans.map(m=>`
      <div class="match-card" style="${m.is_mine ? 'border:2px solid var(--gold); box-shadow: 0 0 20px rgba(234,179,8,0.15);' : ''}">
          <div style="display:flex; justify-content:space-between; align-items:center; color:#fff;">
             <div style="flex:1; text-align:right; font-size:20px; font-weight:600;">${m.t1}</div>
             <div class="match-score">${m.s1} - ${m.s2}</div>
             <div style="flex:1; text-align:left; font-size:20px; font-weight:600;">${m.t2}</div>
          </div>
          <div class="scorers">
             <div style="text-align:right;">${m.sc1.map(s => `⚽ ${s}`).join('<br>')}</div>
             <div style="text-align:left;">${m.sc2.map(s => `⚽ ${s}`).join('<br>')}</div>
          </div>
          ${m.events && m.events.length > 0 ? '<div class="match-events">' + m.events.map(e => `<div>${e}</div>`).join('') + '</div>' : ''}
      </div>`
   ).join('');

   gEl('over').style.display = 'flex';
   btn.disabled=false; 
   btn.innerText = originalText;
}

function trainSquad() { fireReq('train'); }
function reZ(){ if(confirm('האם אתה בטוח שברצונך למחוק את השמירה ולהתחיל מחדש?')) fireReq('restart'); }

_runBld();
</script>
</body>
</html>
"""
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
