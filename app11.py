import random
import uuid
from flask import Flask, render_template_string, request, jsonify
import txt11 

app = Flask(__name__)

# רשימת עמדות סטנדרטית
POSITIONS = ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CAM", "LW", "RW", "ST"]

def create_player(pos=None):
    """מייצר שחקן חדש כביכול 'נקי' להחזרה כ-dict"""
    p_pos = pos if pos else random.choice(list(set(POSITIONS)))
    name = f"{random.choice(txt11.FIRST_NAMES)} {random.choice(txt11.LAST_NAMES)}"
    base = random.randint(65, 85)
    
    p = {
        "id": str(uuid.uuid4()),
        "name": name,
        "pos": p_pos,
        "natural_pos": p_pos, # עמדה טבעית נשמרת תמיד
        "ovr": base,
        "pac": base + random.randint(-10, 10),
        "sho": base + random.randint(-10, 10),
        "pas": base + random.randint(-10, 10),
        "dri": base + random.randint(-10, 10),
        "dfn": base + random.randint(-10, 10),
        "phy": base + random.randint(-10, 10),
        "value": int((base - 60) * 2000),
        "injured_weeks": 0,
        "red_card_weeks": 0
    }
    return p

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, texts=txt11.TEXTS)

# בגלל שבוורסל אין זיכרון, אנחנו מקבלים את ה-State מהלקוח, מעבדים אותו ומחזירים לו
@app.route('/api/init_game', methods=['GET'])
def init_game():
    # מייצר רשימת קבוצות ראשונית לבחירה
    teams = []
    for l_id, t_list in txt11.LEAGUES_DB.items():
        for t in t_list:
            teams.append({
                "id": str(uuid.uuid4()),
                "name": t["name"],
                "primary": t["primary"],
                "secondary": t["secondary"],
                "league_id": l_id,
                "budget": 100000,
                "points": 0, "gp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0,
                "starting_11": [create_player(p) for p in POSITIONS],
                "bench": [create_player() for _ in range(7)]
            })
    return jsonify({"teams": teams, "market": [create_player() for _ in range(10)]})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    # מקבל את כל מצב הליגה מהדפדפן
    state = request.json
    my_team_id = state['my_team_id']
    teams = state['teams']
    my_league_id = next(t['league_id'] for t in teams if t['id'] == my_team_id)
    
    league_teams = [t for t in teams if t['league_id'] == my_league_id]
    random.shuffle(league_teams)
    
    results = []
    for i in range(0, len(league_teams), 2):
        if i+1 < len(league_teams):
            t1, t2 = league_teams[i], league_teams[i+1]
            
            # סימולציה פשוטה לפי OVR ממוצע
            pow1 = sum(p['ovr'] for p in t1['starting_11']) / 11
            pow2 = sum(p['ovr'] for p in t2['starting_11']) / 11
            
            s1 = max(0, int((pow1 - pow2) / 5) + random.randint(0, 3))
            s2 = max(0, int((pow2 - pow1) / 5) + random.randint(0, 3))
            
            # עדכון טבלה
            t1['gp']+=1; t2['gp']+=1; t1['gf']+=s1; t1['ga']+=s2; t2['gf']+=s2; t2['ga']+=s1
            if s1 > s2: t1['points']+=3; t1['w']+=1; t2['l']+=1
            elif s2 > s1: t2['points']+=3; t2['w']+=1; t1['l']+=1
            else: t1['points']+=1; t2['points']+=1; t1['d']+=1; t2['d']+=1
            
            results.append({"t1": t1['name'], "t2": t2['name'], "s1": s1, "s2": s2})

    return jsonify({"teams": teams, "results": results})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{{ texts.title }}</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; margin: 0; padding: 20px; }
        .card { background: #1e293b; padding: 15px; border-radius: 10px; margin: 10px; border: 1px solid #334155; }
        .fut-card { 
            width: 100px; height: 140px; background: linear-gradient(135deg, #eab308, #ca8a04); 
            border-radius: 8px; color: black; display: inline-block; margin: 5px; position: relative;
            font-size: 12px; text-align: center; vertical-align: top; cursor: pointer;
        }
        .fut-card.selected { outline: 3px solid white; transform: scale(1.05); }
        .nat-pos { position: absolute; top: 5px; right: 5px; font-weight: bold; font-size: 10px; background: rgba(0,0,0,0.1); border-radius: 50%; width: 18px; height: 18px; line-height: 18px; }
        .ovr { font-size: 20px; font-weight: bold; position: absolute; top: 5px; left: 5px; }
        .team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
        button { background: #eab308; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .hidden { display: none; }
    </style>
</head>
<body>

<div id="setup">
    <h1>{{ texts.title }} - בחר קבוצה</h1>
    <div id="team-list" class="team-grid"></div>
</div>

<div id="game" class="hidden">
    <div style="display:flex; justify-content: space-between; align-items: center;">
        <h2 id="team-name"></h2>
        <div id="budget" style="color: #10b981; font-size: 20px;"></div>
    </div>
    
    <div class="card">
        <h3>הרכב פותח</h3>
        <div id="starting-11"></div>
    </div>

    <div class="card">
        <h3>ספסל</h3>
        <div id="bench"></div>
    </div>

    <button onclick="playMatch()">שחק מחזור הבא</button>
    <button onclick="resetGame()" style="background:#ef4444;">אפס משחק</button>
</div>

<script>
let gameState = null;
let selectedId = null;

// טעינה ראשונית - בודק אם יש שמירה ב-LocalStorage
async function init() {
    const saved = localStorage.getItem('fifa_save_v1');
    if (saved) {
        gameState = JSON.parse(saved);
        showGame();
    } else {
        const res = await fetch('/api/init_game');
        const data = await res.json();
        renderSetup(data);
    }
}

function renderSetup(data) {
    const container = document.getElementById('team-list');
    data.teams.forEach(t => {
        const div = document.createElement('div');
        div.className = 'card';
        div.style.borderBottom = `5px solid ${t.secondary}`;
        div.innerHTML = `<h3>${t.name}</h3><button onclick='pickTeam(${JSON.stringify(t)}, ${JSON.stringify(data.teams)})'>בחר</button>`;
        container.appendChild(div);
    });
}

function pickTeam(myTeam, allTeams) {
    gameState = {
        my_team_id: myTeam.id,
        teams: allTeams,
        week: 1,
        market: []
    };
    save();
    showGame();
}

function save() {
    localStorage.setItem('fifa_save_v1', JSON.stringify(gameState));
}

function showGame() {
    document.getElementById('setup').classList.add('hidden');
    document.getElementById('game').classList.remove('hidden');
    renderSquad();
}

function renderSquad() {
    const myTeam = gameState.teams.find(t => t.id === gameState.my_team_id);
    document.getElementById('team-name').innerText = myTeam.name;
    document.getElementById('budget').innerText = "₪" + myTeam.budget.toLocaleString();
    
    const renderP = (p) => `
        <div class="fut-card ${selectedId === p.id ? 'selected' : ''}" onclick="selectPlayer('${p.id}')">
            <div class="ovr">${p.ovr}</div>
            <div class="nat-pos" title="עמדה טבעית">${p.natural_pos}</div>
            <div style="margin-top:40px; font-weight:bold;">${p.name}</div>
            <div style="margin-top:10px;">${p.pos}</div>
        </div>
    `;

    document.getElementById('starting-11').innerHTML = myTeam.starting_11.map(renderP).join('');
    document.getElementById('bench').innerHTML = myTeam.bench.map(renderP).join('');
}

function selectPlayer(id) {
    if (!selectedId) {
        selectedId = id;
    } else {
        if (selectedId !== id) {
            swapPlayers(selectedId, id);
        }
        selectedId = null;
    }
    renderSquad();
}

function swapPlayers(id1, id2) {
    const myTeam = gameState.teams.find(t => t.id === gameState.my_team_id);
    let p1, p2, list1, list2, idx1, idx2;

    [myTeam.starting_11, myTeam.bench].forEach(list => {
        const i1 = list.findIndex(p => p.id === id1);
        if (i1 > -1) { p1 = list[i1]; idx1 = i1; list1 = list; }
        const i2 = list.findIndex(p => p.id === id2);
        if (i2 > -1) { p2 = list[i2]; idx2 = i2; list2 = list; }
    });

    if (p1 && p2) {
        const tempPos = p1.pos;
        p1.pos = p2.pos;
        p2.pos = tempPos;
        list1[idx1] = p2;
        list2[idx2] = p1;
        save();
    }
}

async function playMatch() {
    const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(gameState)
    });
    const data = await res.json();
    gameState.teams = data.teams;
    gameState.week++;
    save();
    alert("המחזור הסתיים! בדוק את הטבלה.");
    renderSquad();
}

function resetGame() {
    if(confirm("בטוח שאתה רוצה לאפס הכל?")) {
        localStorage.removeItem('fifa_save_v1');
        location.reload();
    }
}

init();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
