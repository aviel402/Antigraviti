import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = "manager_pro_app11_secret_final_master"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7


# ===============================
# DATA
# ===============================

FIRST_NAMES = ["ערן","מנור","אוסקר","דיא","דניאל","עומר","בירם","דולב","יוגב","ליאור","מוחמד","אייל","רוי","דוד","יהב","שי","רועי"]
LAST_NAMES = ["זהבי","סולומון","גלוך","דבור","סבע","פרץ","אצילי","ייני","חזיזה","כהן","אבו פאני","רביבו","חמד","שרי","עזרא","גלזר"]

TEAMS_DB = [
    {"name":"מכבי תל אביב","primary":"#fcc70e","secondary":"#051660"},
    {"name":"מכבי חיפה","primary":"#036531","secondary":"#ffffff"},
    {"name":"הפועל באר שבע","primary":"#dd1c20","secondary":"#ffffff"},
    {"name":"בית\"ר ירושלים","primary":"#fee411","secondary":"#010101"},
    {"name":"הפועל תל אביב","primary":"#e30613","secondary":"#ffffff"},
    {"name":"מכבי נתניה","primary":"#fed501","secondary":"#010101"},
    {"name":"מ.ס אשדוד","primary":"#ee1b24","secondary":"#ffed00"},
    {"name":"בני סכנין","primary":"#ed1c24","secondary":"#ffffff"},
]

POSITIONS = ["GK","DEF","DEF","DEF","MID","MID","MID","FWD","FWD"]
POS_ORDER = {"GK":1,"DEF":2,"MID":3,"FWD":4}


# ===============================
# CLASSES
# ===============================

class Player:
    def __init__(self, is_gk=False):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.pos = "GK" if is_gk else random.choice(POSITIONS[1:])

        base = random.randint(60,90)
        self.att = base + random.randint(-10,15)
        self.deny = base + random.randint(-10,15)

        if self.pos == "GK":
            self.att = random.randint(10,30)
            self.deny += 20
        elif self.pos == "FWD":
            self.att += 20
            self.deny = random.randint(20,50)

        self.value = int((self.att + self.deny) * 12000)

    def to_dict(self):
        return self.__dict__


class Team:
    def __init__(self, info):
        self.id = str(uuid.uuid4())
        self.name = info["name"]
        self.primary = info["primary"]
        self.secondary = info["secondary"]
        self.is_ai = True

        self.points = 0
        self.games_played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0

        self.budget = 30000000
        self.formation = "4-4-2"

        self.squad = [Player(is_gk=True)]
        self.squad += [Player() for _ in range(12)]

    def get_power(self):
        avg_att = sum(p.att for p in self.squad)/len(self.squad)
        avg_def = sum(p.deny for p in self.squad)/len(self.squad)

        if self.formation == "4-3-3":
            avg_att *= 1.1
        if self.formation == "5-4-1":
            avg_def *= 1.1

        return int(avg_att), int(avg_def)

    def random_scorer(self):
        fw = [p for p in self.squad if p.pos in ["FWD","MID"]]
        return random.choice(fw).name if fw else random.choice(self.squad).name


class League:
    def __init__(self):
        self.teams = [Team(t) for t in TEAMS_DB]
        self.my_team_id = None
        self.week = 1
        self.market = [Player(is_gk=(i==0)) for i in range(8)]

    def get_team(self, tid):
        return next((t for t in self.teams if t.id==tid),None)

    def set_player_team(self, tid):
        self.my_team_id = tid
        for t in self.teams:
            t.is_ai = (t.id != tid)

    def simulate_match(self, t1, t2):
        a1,d1 = t1.get_power()
        a2,d2 = t2.get_power()

        s1 = max(0,int(((a1-d2)/15)+random.randint(0,2)))
        s2 = max(0,int(((a2-d1)/15)+random.randint(0,2)))

        t1.games_played+=1
        t2.games_played+=1
        t1.goals_for+=s1; t1.goals_against+=s2
        t2.goals_for+=s2; t2.goals_against+=s1

        if s1>s2:
            t1.points+=3; t1.wins+=1; t2.losses+=1
        elif s2>s1:
            t2.points+=3; t2.wins+=1; t1.losses+=1
        else:
            t1.points+=1; t2.points+=1; t1.draws+=1; t2.draws+=1

        return {"t1":t1.name,"s1":s1,"t2":t2.name,"s2":s2,
                "is_mine":t1.id==self.my_team_id or t2.id==self.my_team_id}

    def play_week(self):
        random.shuffle(self.teams)
        matches=[]
        for i in range(0,len(self.teams),2):
            matches.append(self.simulate_match(self.teams[i],self.teams[i+1]))
        self.week+=1
        self.market = self.market[2:] + [Player(),Player()]
        return matches


LEAGUES_DB = {}

def get_game():
    uid=session.get("manager_key")
    if not uid or uid not in LEAGUES_DB:
        uid=str(uuid.uuid4())
        session["manager_key"]=uid
        LEAGUES_DB[uid]=League()
    return LEAGUES_DB[uid]


# ===============================
# API
# ===============================

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/data")
def data():
    g=get_game()
    if not g.my_team_id:
        return jsonify({
            "needs_setup":True,
            "teams":[{"id":t.id,"name":t.name,"c1":t.primary,"c2":t.secondary} for t in g.teams]
        })

    my=g.get_team(g.my_team_id)
    table=sorted(g.teams,key=lambda t:(t.points,t.goals_for-t.goals_against),reverse=True)

    return jsonify({
        "needs_setup":False,
        "week":g.week,
        "my_team":{
            "name":my.name,
            "budget":my.budget,
            "formation":my.formation,
            "squad":[p.to_dict() for p in my.squad],
            "color":my.primary
        },
        "table":[
            {"pos":i+1,"name":t.name,"pts":t.points,"gd":t.goals_for-t.goals_against}
            for i,t in enumerate(table)
        ],
        "market":[p.to_dict() for p in g.market]
    })


@app.route("/api/pick",methods=["POST"])
def pick():
    get_game().set_player_team(request.json["team_id"])
    return jsonify({"ok":True})


@app.route("/api/play",methods=["POST"])
def play():
    return jsonify(get_game().play_week())


@app.route("/api/formation",methods=["POST"])
def formation():
    g=get_game()
    g.get_team(g.my_team_id).formation=request.json["formation"]
    return jsonify({"ok":True})


@app.route("/api/transfer",methods=["POST"])
def transfer():
    g=get_game()
    my=g.get_team(g.my_team_id)
    pid=request.json["player_id"]
    action=request.json["action"]

    if action=="buy":
        p=next((x for x in g.market if x.id==pid),None)
        if p and my.budget>=p.value:
            my.budget-=p.value
            my.squad.append(p)
            g.market.remove(p)
            return jsonify({"msg":"שחקן נרכש בהצלחה"})
        return jsonify({"err":"אין מספיק תקציב"})

    if action=="sell":
        p=next((x for x in my.squad if x.id==pid),None)
        if p:
            my.budget+=int(p.value*0.75)
            my.squad.remove(p)
            return jsonify({"msg":"שחקן נמכר"})
        return jsonify({"err":"שחקן לא נמצא"})

    return jsonify({"err":"שגיאה"})


# ===============================
# SIMPLE UI
# ===============================

HTML="""
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>Manager PRO XI</title>
<style>
body{background:#0f172a;color:white;font-family:Arial;padding:20px}
button{padding:8px 15px;margin:5px}
.card{background:#1e293b;padding:10px;margin:5px;border-radius:6px}
</style>
</head>
<body>

<h1>Manager PRO XI ⚽</h1>
<div id="app"></div>

<script>
async function load(){
 let r=await fetch("/api/data");
 let d=await r.json();
 let app=document.getElementById("app");

 if(d.needs_setup){
    app.innerHTML="<h2>בחר קבוצה:</h2>";
    d.teams.forEach(t=>{
       app.innerHTML+=`<button onclick="pick('${t.id}')">${t.name}</button>`;
    });
    return;
 }

 app.innerHTML=`
 <h2>${d.my_team.name}</h2>
 <div>תקציב: €${d.my_team.budget.toLocaleString()}</div>
 <button onclick="play()">שחק מחזור</button>
 <h3>טבלה</h3>
 ${d.table.map(t=>`<div>${t.pos}. ${t.name} - ${t.pts} נק'</div>`).join("")}
 <h3>שוק</h3>
 ${d.market.map(p=>`<div class='card'>${p.name} (${p.pos}) - €${p.value.toLocaleString()}
 <button onclick="buy('${p.id}')">קנה</button></div>`).join("")}
 `;
}

async function pick(id){
 await fetch("/api/pick",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({team_id:id})});
 load();
}

async function play(){
 await fetch("/api/play",{method:"POST"});
 load();
}

async function buy(id){
 await fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"buy",player_id:id})});
 load();
}

load();
</script>
</body>
</html>
"""

if __name__=="__main__":
    app.run(debug=True)
