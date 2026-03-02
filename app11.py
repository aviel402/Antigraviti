import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = "manager_pro_app11_secret_final_master"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 14 # שומר למשתמש התחברות קפואה ל14 ימים אליו אישית בלבד (משאר קופות ארקייד.. ) 

# ===============================
# DATA & TEAMS PREFERENCES
# ===============================
FIRST_NAMES =["ערן", "מנור", "אוסקר", "מונס", "דיא", "דניאל", "עומר", "שרן", "בירם", "דולב", "יוגב", "ליאור", "דולב", "מוחמד", "אייל", "רוי", "דוד", "יהב", "שי", "רועי"]
LAST_NAMES =["זהבי", "סולומון", "גלוך", "דבור", "סבע", "פרץ", "אצילי", "ייני", "כיאל", "חזיזה", "אוחיון", "כהן", "אבו פאני", "רביבו", "חמד", "שרי", "עזרא", "גלזר"]

# חברות הקבוצות - מאזניים מקורים! (התחלפות תחת כוונתו שלך בלבד!). 
TEAMS_DB =[
    {"name": "מכבי תל אביב", "primary": "#fcc70e", "secondary": "#051660"},
    {"name": "מכבי חיפה", "primary": "#036531", "secondary": "#ffffff"},
    {"name": "הפועל באר שבע", "primary": "#dd1c20", "secondary": "#ffffff"},
    {"name": "בית\"ר ירושלים", "primary": "#fee411", "secondary": "#010101"},
    {"name": "הפועל תל אביב", "primary": "#e30613", "secondary": "#ffffff"},
    {"name": "מכבי נתניה", "primary": "#fed501", "secondary": "#010101"},
    {"name": "מ.ס אשדוד", "primary": "#ee1b24", "secondary": "#ffed00"},
    {"name": "בני סכנין", "primary": "#ed1c24", "secondary": "#ffffff"},
]
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
        
        base_stats = random.randint(62, 94)
        self.att = base_stats + random.randint(-15, 20)
        self.deny = base_stats + random.randint(-15, 20)
        
        if self.pos == "GK": self.att = random.randint(10, 30); self.deny += 20
        elif self.pos == "FWD": self.att += 20; self.deny = random.randint(20, 50)
        
        self.value = int(((self.att * 0.5) + (self.deny * 0.5)) * 15000) + random.randint(-50000, 200000)
        
    def to_dict(self): return self.__dict__

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
        self.squad =[Player(is_gk=True)]
        self.squad +=[Player() for _ in range(12)]

    def get_power(self):
        avg_att = sum(p.att for p in self.squad) / max(len(self.squad), 1)
        avg_def = sum(p.deny for p in self.squad) / max(len(self.squad), 1)
        if self.formation == "4-3-3": avg_att *= 1.15 
        if self.formation == "5-4-1": avg_def *= 1.15
        return int(avg_att), int(avg_def)
        
    def get_random_scorer(self):
         fwds_mids =[p for p in self.squad if p.pos in["FWD", "MID"]]
         if fwds_mids:
             return random.choices(fwds_mids, weights=[3 if p.pos=="FWD" else 1 for p in fwds_mids])[0].name
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
        raw_1 = max(0, ((p1_att * luck1) - p2_def) / 11)
        raw_2 = max(0, ((p2_att * luck2) - p1_def) / 11)
        
        score1 = int(round(raw_1) + random.randint(0, 1))
        score2 = int(round(raw_2) + random.randint(0, 1))
        
        t1_scorers =[f"{t1.get_random_scorer()} ({random.randint(1, 90)}') " for _ in range(score1)]
        t2_scorers =[f"{t2.get_random_scorer()} ({random.randint(1, 90)}') " for _ in range(score2)]

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
# MEMORY CACHING AND SERVER SESSIONS..
# ===============================
LEAGUES_DB = {}

def get_game():
    uid = session.get('manager_11_pro_key')
    if not uid or uid not in LEAGUES_DB:
        uid = str(uuid.uuid4())
        session.permanent = True
        session['manager_11_pro_key'] = uid
        LEAGUES_DB[uid] = League()
    return LEAGUES_DB[uid]

# ===============================
# ENDPOINTS REST API
# ===============================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

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
        "table":[ {"pos": i+1, "name": t.name, "pts": t.points, "p": t.games_played, "w":t.wins, "d":t.draws, "l":t.losses, "gd": t.goals_for - t.goals_against} for i, t in enumerate(table)],
        "market":[p.to_dict() for p in market_sorted],
        "week": g.week
    })

@app.route('/api/pick_team', methods=['POST'])
def pick_team():
    team_id = request.json.get('team_id')
    get_game().set_player_team(team_id)
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
            if len(my_team.squad) >= 20: return jsonify({"err": "הסגל הגיע לקצה המקסימום (20 מוגבל בקרדיט המועדון)."})
            my_team.budget -= target.value
            my_team.squad.append(target)
            g.market.remove(target)
            return jsonify({"msg": f"כלי תקשורת חותכים : '{target.name}' מאשר התקבל בחיפושי צריף החדשים עבורכם!"})
        return jsonify({"err": "עצר, כי תקציבו מעל המסדר! פחון קודם מהבזקים."})

    if action == 'sell':
        target = next((p for p in my_team.squad if p.id == pid), None)
        if target: 
             if len([p for p in my_team.squad if p.pos == "GK"]) < 2 and target.pos == "GK":
                   return jsonify({"err":"זרוע הגופניים עוצרים פגישה במתנות! אין שוערים לשחק! אי אפשר בלי לחותים שוער.."})
             if len(my_team.squad) > 13: 
                my_team.budget += int(target.value * 0.75)
                my_team.squad.remove(target)
                return jsonify({"msg": "סיום ובינוי חריטי למקום הארגמנטי: הועמדה לסיבוב קרבה הקבל - השאר סוללק.. ! "})
             else: return jsonify({"err": "המנהלי יחדלו לסף התזומת: שמור צוות לחימה 13 שחקנים!"})
        return jsonify({"err": "זכיין נמנר על יתור תקולים."})

    return jsonify({"err": "אי שפיע למחוויות צרות הדגם הפתוחה.. "})

@app.route('/api/restart')
def force_restart():
    session.clear()
    return jsonify({"ok":True})


# ===============================
# UI TEMPLATE עם תקן קישורים מודא למארגים שלנו באמצעות המפלץ url_for הפלסק ! :))
# ===============================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manager PRO XI</title>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
<style>
:root { 
    --p-bg: #121620; 
    --p-panel: rgba(28, 36, 52, 0.95);
    --gold: #d4af37; 
    --grass-alt: #059669; 
    --neon-t: #38bdf8; 
    --txt: #e2e8f0; 
}

body { margin: 0; background: linear-gradient(to top right, #0d1117, #1e293b); color: var(--txt); font-family: 'Assistant', sans-serif; min-height:100vh; padding-bottom: 75px;}
* { box-sizing: border-box;}

.arcade-btn { position: absolute; left: 15px; top:12px; font-weight: bold; font-size: 11px; padding: 6px 12px; background: rgba(0,0,0,0.6); color: white; text-decoration: none; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); transition: 0.3s; z-index:110;}
.arcade-btn:hover { background: #fff; color: #000; }

.header-bar { 
   position: sticky; top:0; z-index:100;
   background: linear-gradient(135deg, rgba(13,24,37,0.9), rgba(16,36,53,1)); 
   border-bottom: 3px solid transparent; 
   box-shadow: 0 4px 15px rgba(0,0,0,0.5); padding: 25px 20px 15px; text-align:right;
   display: flex; justify-content: space-between; align-items:flex-end; backdrop-filter:blur(8px);
}
.hdr-title { font-family: 'Assistant', sans-serif; font-weight: 800; font-size: 24px; color: #fff; margin:0; display:flex; align-items:center; gap:8px;}
.budget-pod { font-family: monospace; font-size: 22px; font-weight:bold; color: var(--gold); background: #0b0e14; padding: 6px 14px; border-radius: 4px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.8); }

/* --- PICK SCREEN עידוק השורשי החיוביות לטפס חסיונת חקירת המארגי ! --- */
#setup-screen { position: absolute; top:0;lef
