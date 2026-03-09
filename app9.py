from flask import Flask, render_template_string, jsonify, request
import json

# מנסים לייבא את קובץ המפות החדש.
try:
    from maps9 import MAPS_CONFIG
except ImportError:
    # אם שוכחים, ייצר משהו כללי לפאלבק (כדי שלא יקרוס השרת)
    print("Warning: maps9.py not found. using fallback flat stages.")
    MAPS_CONFIG = [{"stage": i, "background":"#111", "platforms":[], "enemies":{"walkers": i, "jumpers": 0, "shooters":0, "boss":1 if i%5==0 else 0}} for i in range(1,21)]


app = Flask(__name__)
app.secret_key = 'clover_action_key_v3'

PLAYER_DATA = {
    "shards": 0,
    "max_stage": 1
}

@app.route('/')
def idx():
    # שים לב אנחנו דוחפים את דאטת המפות לפרונט (JSON)
    maps_json_str = json.dumps(MAPS_CONFIG)
    return render_template_string(GAME_HTML, MAPS_DATA=maps_json_str)

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    try:
        data = request.json
        if data and "shards" in data: PLAYER_DATA["shards"] += data.get("shards", 0)
        return jsonify(PLAYER_DATA)
    except: return jsonify({}), 400

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>CLOVER - ROGUELITE EDITION</title>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Orbitron:wght@700&display=swap" rel="stylesheet">
    <style>
        :root { --hp: #e74c3c; --en: #00d2d3; --gl: #f1c40f; }
        * { box-sizing: border-box; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Assistant', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; filter: contrast(1.1); }
        
        .layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events: none; }
        .hidden { display: none !important; opacity: 0; }
        
        /* ---------------- ה-UI הראשי משחק ---------------- */
        #ui-layer { display: flex; flex-direction: column; justify-content: space-between; padding: 20px; z-index: 10; transition: opacity 0.5s; }
        
        .top-hub { display: flex; width: 100%; align-items: flex-end; justify-content: space-between; gap:20px; text-shadow: 2px 2px 4px #000; }
        
        .stats { flex:1; }
        .hud-line { display: flex; justify-content: space-between; font-weight: 800; font-size: 20px; margin-bottom:5px; font-family:'Orbitron',sans-serif; }
        .bar-case { width: 100%; height: 22px; background: rgba(0,0,0,0.5); border: 2px solid #555; border-radius: 4px; box-shadow: 0 5px 10px rgba(0,0,0,0.5); overflow: hidden;}
        .bar-in { height: 100%; transition: width 0.15s cubic-bezier(0.1, 0.7, 1.0, 0.1); }

        .mid-hub { flex: 2; display: flex; flex-direction: column; align-items: center; justify-content: flex-end;}
        .level-stage { text-align: center; margin-bottom: 5px; font-weight:800; letter-spacing: 2px; }
        .stage-box { width: 80%; height: 10px; background: #111; border: 1px solid #777; border-radius:10px; overflow:hidden;}
        
        #game-title-drop {
            position: absolute; top: 20%; left: 50%; transform: translateX(-50%); font-family:'Orbitron',sans-serif;
            font-size: 70px; text-shadow: 0 0 30px rgba(255,255,255,0.8); text-transform: uppercase;
            color: #fff; text-align: center; opacity:0; transition: 0.3s ease; pointer-events: none;
        }

        .controls { 
            direction:ltr; align-self:flex-start; font-size:15px; 
            background: rgba(10,15,30,0.85); border: 2px solid rgba(0,210,211,0.3); padding: 15px 25px; 
            border-radius: 12px; font-weight: 700; color:#ddd;
            box-shadow: 0 4px 15px rgba(0,210,211,0.2); 
        }
        .controls span { color:var(--gl); background:#333; padding: 1px 6px; border-radius:4px; font-family: monospace;}
        
        #lock-on-text { color: #ff4757; text-shadow: 0 0 10px red; opacity: 0; font-weight:800; transition:0.1s;}

        /* ---------------- מסכי תפריטים ---------------- */
        .screen { background: radial-gradient(circle at center, #2f3542 0%, #000 100%); display:flex; flex-direction:column; align-items:center; justify-content:center; pointer-events:auto;}
        h1.neon { font-family: 'Orbitron', sans-serif; font-size: 5rem; text-shadow: 0 0 15px #6c5ce7; color: white; margin-bottom: 5px; }
        .neon-sub { font-size: 1.5rem; letter-spacing: 5px; opacity:0.8; margin-bottom:40px; }
        
        .btn { padding: 15px 40px; border:none; outline:2px solid transparent; background: transparent; cursor: pointer; color: white; 
               border: 3px solid #74b9ff; font-weight: 800; font-size: 20px; transition: 0.2s; font-family: 'Assistant', sans-serif;
               border-radius: 4px; box-shadow: inset 0 0 10px rgba(116,185,255,0); text-transform:uppercase;}
        .btn:hover { background:#74b9ff; color:black; transform: translateY(-5px); box-shadow: 0 15px 30px rgba(116,185,255,0.4); }

        /* גיבורים סלקציה */
        #heroes-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; width: 90%; max-width: 900px; 
            margin-bottom: 40px;
        }
        .hero-card {
            background: rgba(25,25,35,0.9); border: 2px solid rgba(255,255,255,0.1); 
            padding: 20px; border-radius: 15px; text-align: center; cursor: pointer; transition:0.3s;
            position:relative; overflow:hidden;
        }
        .hero-card::after{ content:''; position:absolute; inset:0; border:4px solid transparent; transition:0.3s; border-radius: 15px;}
        .hero-card:hover { transform: translateY(-10px) scale(1.05); }
        .hero-icon { width:60px; height:60px; margin:0 auto 10px; border-radius: 50%; box-shadow: 0 0 20px currentColor;}
        .hero-name { font-weight: 800; font-size: 24px; font-family:'Orbitron',sans-serif; margin-bottom:10px; }
        .hero-desc { font-size: 14px; opacity: 0.8; direction:ltr;}

        /* Unlock Popup */
        #notify-msg { position:fixed; bottom: 25%; left: 50%; transform: translate(-50%, 50px); background:#f1c40f; color:#000; padding:15px 40px; font-weight:800; font-size:24px; opacity:0; pointer-events:none; border-radius:30px; border:4px solid #fff; z-index:99; transition:0.5s ease-out;}
    </style>
</head>
<body>

<div id="ui-layer" class="layer hidden">
    <div class="top-hub">
        <!-- נתוני שחקן HP -->
        <div class="stats" style="direction:ltr;">
            <div class="hud-line"><span style="color:var(--hp)">HP [ <span id="v-hp"></span> ]</span></div>
            <div class="bar-case"><div id="bar-hp" class="bar-in" style="background:linear-gradient(90deg, #e74c3c, #c0392b);"></div></div>
        </div>
        
        <!-- כותרת ושלב (אמצע) -->
        <div class="mid-hub">
            <div class="level-stage" style="color:#dfe6e9">STAGE <span id="v-lvl">1</span> / 20</div>
            <div id="lock-on-text">► TARGET LOCKED ◄</div>
            <div class="stage-box"><div id="bar-stage" style="background:#0984e3; height:100%; width:0%"></div></div>
        </div>

        <!-- נתוני שחקן ENERGY -->
        <div class="stats" style="direction:ltr; text-align:right;">
             <div class="hud-line"><span>[ <span id="v-en"></span> ] ENERGY</span><span style="color:var(--en); display:inline-block; transform: scaleX(-1);">⚡</span></div>
             <div class="bar-case"><div id="bar-en" class="bar-in" style="float:right; background:linear-gradient(-90deg, #00d2d3, #0984e3);"></div></div>
        </div>
    </div>
    
    <div id="game-title-drop">WAVE INCOMING</div>

    <div class="controls">
        <div style="color:rgba(255,255,255,0.6); margin-bottom:5px; text-transform:uppercase;" id="class-indicator">ELEMENT</div>
        <div>Move / Jump : <span>W A D</span></div>
        <div>Shots : <span>H</span> (Weak) <span>J</span> (Medium) <span>K</span> (Heavy)</div>
        <div>Charge Power : Hold <span>U</span></div>
        <div>Lock Auto-Aim: Press <span>E</span></div>
        <div>Ultimate Skill: Press <span>Y</span></div>
    </div>
</div>

<div id="notify-msg">Double Jump Unlocked!</div>

<!-- MAIN MENU / CHAR SELECT -->
<div id="menu-screen" class="screen layer">
    <a href="/" style="position:absolute; top:30px; left:30px; color:#aaa; font-size:18px; text-decoration:none;">◀ יציאה לעמוד ראשי</a>
    <h1 class="neon">CLOVER</h1>
    <div class="neon-sub">THE LEGEND OF ELEMENTS</div>
    <div style="font-size:24px; font-weight:800; margin-bottom: 20px;">בחר אלמנט / Choose Class</div>
    <div id="heroes-grid">
       <!-- נשתל בקוד JS דינמית -->
    </div>
</div>

<div id="death-screen" class="screen layer hidden">
    <h1 style="color:#e84118; font-family:'Orbitron',sans-serif; font-size:80px;">TERMINATED</h1>
    <h2 id="final-stats" style="color:#aaa; font-weight:400; margin-top:20px; font-size:24px;"></h2>
    <div style="margin-top:50px;">
        <button class="btn" style="border-color:#e84118;" onclick="location.reload()">TRY AGAIN</button>
    </div>
</div>

<div id="win-screen" class="screen layer hidden">
    <h1 style="color:#fbc531; font-family:'Orbitron',sans-serif; font-size:80px; text-shadow:0 0 50px gold;">VICTORY</h1>
    <h2>אגדת האלמנטים התממשה</h2>
    <a href="/" class="btn" style="border-color:#fbc531; margin-top:40px; color:white; text-decoration:none;">לחזור להאב משחקים</a>
</div>

<script>
// ---------- דאטה ממפות (PYTHON INJECT) ----------
const RAW_MAPS_JSON = {{ MAPS_DATA | safe }}; 
// במידה ויש שגיאת parse אם הפייטון נופל:
const SERVER_MAPS = (typeof RAW_MAPS_JSON !== "undefined") ? RAW_MAPS_JSON :[];

// ---------------- קונפיג שחקנים / אלמנטים --------------
const HERO_CLASSES = {
    earth:    { name: "EARTH",    desc: "150% HP, Heavy, +Damage",       c:"#27ae60", hpx:1.5, mxE: 100, spd:0.7, jumpMult:0.8, rgb:"39, 174, 96" },
    fire:     { name: "FIRE",     desc: "Fast Regen Energy, Burning DMG",c:"#e74c3c", hpx:1.0, mxE: 100, spd:0.9, jumpMult:1.0, rgb:"231, 76, 60" },
    water:    { name: "WATER",    desc: "150% Energy Max, Smooth jumps", c:"#0097e6", hpx:1.0, mxE: 150, spd:1.0, jumpMult:1.1, rgb:"0, 151, 230" },
    wind:     { name: "WIND",     desc: "Very Fast Movement, Squishy",   c:"#00a8ff", hpx:0.7, mxE: 100, spd:1.5, jumpMult:1.2, rgb:"0, 168, 255" },
    lightning:{ name: "VOLT",     desc: "Quick attacks, Fast recharge",  c:"#fbc531", hpx:0.8, mxE: 120, spd:1.2, jumpMult:1.0, rgb:"251, 197, 49"},
    light:    { name: "LIGHT",    desc: "Heals lightly when moving",     c:"#f5f6fa", hpx:1.1, mxE: 110, spd:1.0, jumpMult:1.0, rgb:"245, 246, 250" },
    dark:     { name: "SHADOW",   desc: "Double Attack Power, Fragile",  c:"#8c7ae6", hpx:0.6, mxE: 90,  spd:1.3, jumpMult:1.0, rgb:"140, 122, 230"},
    magma:    { name: "MAGMA",    desc: "Resilient & Heavy damage hits", c:"#d35400", hpx:1.4, mxE: 80,  spd:0.6, jumpMult:0.8, rgb:"211, 84, 0"}
};

// UI הבנייה לתפריט אפיק משתמש
const gContainer = document.getElementById('heroes-grid');
Object.keys(HERO_CLASSES).forEach(k => {
    let hero = HERO_CLASSES[k];
    let html = `<div class="hero-card" onmouseover="this.style.borderColor='${hero.c}'" onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)'" onclick="launchGame('${k}')">
        <div class="hero-icon" style="color: ${hero.c}; background:${hero.c}"></div>
        <div class="hero-name" style="color: ${hero.c};">${hero.name}</div>
        <div class="hero-desc">${hero.desc}</div>
    </div>`;
    gContainer.innerHTML += html;
});

// ------------- ENGINE --------------
const cvs = document.createElement('canvas'); const ctx = cvs.getContext('2d');
document.body.appendChild(cvs);
function rez() { cvs.width=window.innerWidth; cvs.height=window.innerHeight; ctx.imageSmoothingEnabled = false;}
window.addEventListener('resize', rez); rez();

let state = 'MENU', frame = 0, unlocks={dj:false, super:false, rech:false};
let globalData = { st: 1 };
const G = 0.6; // Gravity
let WORLD_BOUNDS = 10000;
// המרחק של ה"רצפה המדומיינת" שקיימת כגיבוי לתחתית המסך במקרה שנופלים הכל. רצוי לעשות יחסי או 900
function getGroundY() { return cvs.height - 80; }

// input
let KEYMAP = { UP:'KeyW', LEFT:'KeyA', RIGHT:'KeyD', SPACE:'Space', CHARGE:'KeyU', LOCK:'KeyE', S1:'KeyH',S2:'KeyJ',S3:'KeyK',ULT:'KeyY' };
const IK = {};
window.onkeydown=e=> { if(e.code=='Space')e.preventDefault(); IK[e.code]=true; };
window.onkeyup=e=> { IK[e.code]=false; };

let cam={x:0, sx:0}; 
function screenShake(amt) { cam.sx += amt; }

// Entities Array
let P;
let En = []; // אויבים
let Pr =[]; // פגזים השחקן והאויב יחד מופרדים
let Pa =[]; // מערכת חלקיקים לפופ אפ ואקשן גרפיקה
let PLATS =[]; // רצפות המפה הספציפית

// CLASS שחקן גולשי משודרג!
class PlayBoy {
    constructor(cls) {
        let stats = HERO_CLASSES[cls];
        this.baseC = stats.c; this.rgb = stats.rgb;
        this.w = 34; this.h = 60; this.x = 200; this.y = 100; // spawn point 
        
        // Multipliers from chosen Hero Element
        this.maxHp = 100 * stats.hpx; this.hp = this.maxHp;
        this.maxEn = stats.mxE; this.en = this.maxEn;
        this.spdLimit = 1.0 * stats.spd;
        this.jmMult = stats.jumpMult;
        
        // Stats system mechanics inside Hero class check
        this.isDark = (cls === 'dark'); this.isLight = (cls === 'light');
        this.isFire = (cls === 'fire');
        
        this.vx=0; this.vy=0;
        this.fc=1; // facing +1 Right, -1 Left
        this.onFloor=false; this.j=0;
        
        // Lock system improvements!
        this.tg = null; this.tgWait=false; this.lmd=false; // lock mode boolean 
        this.shtDelays={};
    }
    update() {
        if(this.hp <= 0) return;

        // ------------- טיפול בתנועה תחת מצב חצי קופא --------------
        // השדרוג הנדרש "מותר לזוז תחת טעינה!" - אם כי עכשיו לזוז נגזור איטי
        let charging = IK[KEYMAP.CHARGE];
        let acc = charging ? (this.spdLimit * 0.4) : this.spdLimit; 
        
        if (IK[KEYMAP.LEFT]) { this.vx-=acc; this.fc=-1; }
        if (IK[KEYMAP.RIGHT]){ this.vx+=acc; this.fc=1; }
        
        // Auto heal (Light element bonus)
        if(this.isLight && Math.abs(this.vx)>1 && frame%60==0) { this.hp = Math.min(this.hp+1, this.maxHp); }

        // אם במצב טעינה אנו רק מתחמשים, ויורים אפסים. לא יורים במצב זה
        if(charging) {
            let rcSpeed = this.isFire ? 1.0 : 0.6; // Fire charge ultra fast
            this.en = Math.min(this.maxEn, this.en + rcSpeed);
            if(frame%5==0) sSpark(this.x+this.w/2, this.y+this.h, `rgb(${this.rgb})`, 1);
        }
        else {
            // פענוח שלב 15 שיש פתור טעינה לאורך משחק לבד:
            if(unlocks.rech && frame%10==0) this.en = Math.min(this.maxEn, this.en+0.3);

            // Controls הירי המיוחדים 
            this.tryF(KEYMAP.S1, 10, 'WK', 15);
            this.tryF(KEYMAP.S2, 25, 'MD', 35);
            this.tryF(KEYMAP.S3, 40, 'HV', 70);
            if(unlocks.super) this.tryF(KEYMAP.ULT, 100, 'EX', 200);
        }

        // Lock Engine v2 !! System Switch Mode
        if(IK[KEYMAP.LOCK]) {
            if(!this.tgWait){
                this.lmd = !this.lmd; // Toggle auto Mode
                this.tgWait=true;
                if(this.lmd) this.getNxtTg(); else this.tg = null; // מציאת מנעול ראשון או כבוי מוחלט
            }
        } else this.tgWait=false;

        // Auto transition Target -> When enemy dies while in lockMode switch smoothly without double presses! (שדרוג 1 המבוקש)
        if (this.lmd) {
            if(!this.tg || this.tg.hp<=0) this.getNxtTg();
        }
        document.getElementById('lock-on-text').style.opacity = (this.tg && this.lmd) ? 1: 0;
        
        // Physics update (Jumps platform collisions)
        let jumped = false;
        if(IK[KEYMAP.UP]||IK[KEYMAP.SPACE]) {
            if(!this.jmpPrs) {
                let limit = unlocks.dj ? 2 : 1;
                if(this.j < limit) { this.vy = -12 * this.jmMult; this.j++; jumped=true; sDust(this.x, this.y+this.h); }
                this.jmpPrs=true;
            }
        } else this.jmpPrs=false;
        
        let py = this.y;
        this.vy += G;
        this.vx *= 0.85; // חיכוך 
        
        this.x+=this.vx;
        this.y+=this.vy;
        if(this.x<0){this.x=0;this.vx=0;}
        
        // Collisions אלימים רצפה ותחתית + קופסאות הפלטפורמה הסלקטיבית
        this.onFloor=false;
        
        // check plat
        if(this.vy > 0 && !jumped) { // only on way down! (רצפת פלטפורמה אפשר לקפוץ מלמטה לעשות חציה נגישה אליה!)
            for(let p of PLATS) {
                // Was previous Y strictly above it? Meaning real landing condition. Check old bot against top plat
                if(py + this.h <= p.gy + 10 && this.y + this.h >= p.gy) {
                    if(this.x + this.w > p.x && this.x < p.x + p.w) {
                         this.y = p.gy - this.h; this.vy = 0;
                         this.onFloor=true; this.j=0; break;
                    }
                }
            }
        }
        // check floor base global 
        let gf = getGroundY();
        if(this.y + this.h > gf && !this.onFloor) {
            this.y = gf - this.h; this.vy=0; this.onFloor=true; this.j=0;
        }
    }

    tryF(kc, ep, t, bDamg) {
        if(IK[kc]){
            if(!this.shtDelays[kc]) {
                if(this.en>=ep) {
                    this.en -= ep;
                    let push=(ep/10); this.vx-= (this.fc * push); screenShake(push/2);
                    let actualDamg = bDamg * (this.isDark? 1.8: 1.0); // אפקטים יחודי מניעת יתר אבל תכליתי
                    
                    // Creates shot objects: Is 'good' (P for Player source), size relative to dmg
                    Pr.push(new Misl(this.x+(this.fc==1?this.w:0), this.y+this.h/3, this.fc, 'good', actualDamg, this.baseC, this.tg));
                }
                this.shtDelays[kc] = true;
            }
        } else this.shtDelays[kc]=false;
    }
    
    getNxtTg() {
        this.tg = null; let cl=null, bD=1500; // scope limitation to 1.5 screen 
        for(let x of En) {
            let d = Math.abs(x.x - this.x);
            // Ignore guys completely backwards?
            if(d<bD && x.hp>0) { bD=d; cl=x; }
        }
        if(cl) this.tg=cl; 
    }

    draw() {
        ctx.fillStyle = this.baseC;
        if(this.en >= this.maxEn*0.9) {
            ctx.shadowColor = this.baseC; ctx.shadowBlur = 20; 
            // Glowing Aura draw !! JUICE Effect when ready loaded fully energy ! 
            ctx.beginPath(); ctx.ellipse(this.x+this.w/2, this.y+this.h/2, 25+(Math.sin(frame/5)*5), 35, 0,0,Math.PI*2);
            ctx.fillStyle= `rgba(${this.rgb}, 0.3)`; ctx.fill();
        }
        ctx.fillStyle = this.baseC;
        ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.shadowBlur=0;
        // Inner design tech suit view character styling graphic upgrades  
        ctx.fillStyle='#222'; ctx.fillRect(this.x+5, this.y+20, this.w-10, 25);
        
        ctx.fillStyle='#fff';
        ctx.fillRect((this.fc==1? this.x+this.w-8 : this.x+2), this.y+8, 6, 4);

        if(this.tg && this.lmd) {
            let tt = this.tg;
            ctx.strokeStyle='red'; ctx.lineWidth=2;
            let R = 30; // red lock box graphic targeting square frame draw shape  ! 
            ctx.beginPath();
            ctx.moveTo(tt.x-10, tt.y); ctx.lineTo(tt.x-10, tt.y-10); ctx.lineTo(tt.x, tt.y-10); 
            ctx.moveTo(tt.x+tt.w+10, tt.y); ctx.lineTo(tt.x+tt.w+10, tt.y-10); ctx.lineTo(tt.x+tt.w, tt.y-10); 
            ctx.moveTo(tt.x-10, tt.y+tt.h); ctx.lineTo(tt.x-10, tt.y+tt.h+10); ctx.lineTo(tt.x, tt.y+tt.h+10); 
            ctx.moveTo(tt.x+tt.w+10, tt.y+tt.h); ctx.lineTo(tt.x+tt.w+10, tt.y+tt.h+10); ctx.lineTo(tt.x+tt.w, tt.y+tt.h+10); 
            ctx.stroke();

            // Link thread transparent logic wire trace red! 
            ctx.beginPath(); ctx.moveTo(this.x+this.w/2, this.y+20); ctx.lineTo(tt.x+tt.w/2, tt.y+tt.h/2);
            ctx.strokeStyle='rgba(255,50,50,0.2)'; ctx.lineWidth=1; ctx.stroke();
        }
    }
}


class EnemyBase {
    constructor(nx, type, bossMul) {
        this.x=nx; this.hp=30*bossMul; this.type=type;
        this.vx=0; this.vy=0; 
        
        // Type variations Setup. -> jumper , shooter , walker , boss
        if(type=='boss') { this.w=100; this.h=120; this.c='#c0392b'; this.hp*=8; }
        elif (type=='jumper') { this.w=30; this.h=30; this.c='#27ae60'; this.jCooldown=60;}
        elif (type=='shooter'){ this.w=40; this.h=60; this.c='#9b59b6'; this.sCooldown=120;}
        else { this.w=45; this.h=45; this.c='#f39c12'; this.type='walker';} 
        
        this.y=getGroundY()-this.h; this.isBos= (type=='boss'); this.flash=0;
        this.speed= 2 + (bossMul * 0.1) + Math.random()*1; 
        if(type=='walker') this.speed += 0.5; // Walkers run!
        
        this.mHp=this.hp;
    }
    update() {
        let dx= P.x-this.x, ds = Math.abs(dx);
        let moveTries = (dx>0)?1:-1;
        let groundLevelLocal = getGroundY();

        // Platform Support For enemies gravity logic: Only basic falling. not clever navmesh! Just Arcadey
        this.vy += G; 
        this.x+=this.vx; this.y+=this.vy;
        
        // Ground 
        if(this.y+this.h > groundLevelLocal) { this.y=groundLevelLocal-this.h; this.vy=0;}
        
        if (ds<2500) { 
             // Actions Based On Archetypes classes behavior system!!!
             if(this.type=='walker' || this.isBos) {
                  this.vx = moveTries * (this.speed * 0.5); // follow standard 
             }
             if(this.type=='jumper') {
                 if(this.vy===0) this.vx=moveTries*this.speed; 
                 if(this.vy===0 && ds < 400) { this.jCooldown--; if(this.jCooldown<=0){ this.vy=-14; this.vx=moveTries*(this.speed*2.5); this.jCooldown=90;}}
             }
             if(this.type=='shooter') {
                 // stay far
                 if(ds < 350) { this.vx = -moveTries*2; } // backup distance flee retreat logic smart play shooty shoot ! 
                 else if (ds > 400) { this.vx = moveTries*1.5; }
                 else this.vx = 0; // sweet spot! Wait to Shoot!
                 
                 this.sCooldown--;
                 if(this.sCooldown<=0) {
                     this.sCooldown = 80; // delay to shoot next orb payload delivery danger 
                     Pr.push(new Misl(this.x+(dx>0?this.w:0), this.y+10, moveTries, 'bad', (15+(globalData.st*2)), '#fff', null)); 
                 }
             }
             if(this.isBos && ds<500 && Math.random()<0.01 && P.y<this.y) { this.vy = -18; } // massive boss slam Jump ! 
        }

        if(AABB(this, P)) {
            let pd = this.isBos?2:0.8; P.hp -= pd; screenShake(pd*2); 
            let bounce = this.x<P.x?1:-1; this.vx -= bounce*5; P.vx += bounce*6; // physics repulse overlap damage event!! 
            P.vy -=2; sDust(P.x,P.y,'#ff0000');
        }
        if(this.flash>0)this.flash--;
    }
    draw() {
        ctx.fillStyle= this.flash? '#fff': this.c; 
        
        // Jumper is circle visual? Why not! Let's shape geometry 
        if(this.type=='jumper') {
           ctx.beginPath(); ctx.ellipse(this.x+this.w/2, this.y+this.h/2, this.w/2, this.h/2, 0,0,Math.PI*2); ctx.fill(); 
        } else { ctx.fillRect(this.x, this.y, this.w, this.h); }

        if(this.mHp!=this.hp) {
           ctx.fillStyle='#111'; ctx.fillRect(this.x, this.y-10, this.w,4);
           ctx.fillStyle='#f1c40f'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.mHp),4);
        }
        if(this.isBos){ctx.fillStyle='#fff';ctx.font='15px Arial';ctx.fillText("STAGE WARDEN",this.x+10,this.y-15);}
    }
}


class Misl {
    // Projectile constructor physics geometry renderer element core class module!!
    constructor(sx, sy, dirc, allyState, dmgNum, clrTheme, focusObj) {
        this.x=sx; this.y=sy; this.d=dirc; this.f_tgt = focusObj; this.dmg=dmgNum; this.c=clrTheme; 
        
        let scSz = (dmgNum > 70)? 40 : (dmgNum > 20)? 20 : 10; this.sz=scSz; 
        let spd = (dmgNum > 70)? 10 : (dmgNum > 20)? 16 : 22; this.bx = spd*dirc;
        this.by=0; this.isBad=(allyState=='bad'); 
        this.c = this.isBad ? "#ff0000" : this.c;
    }
    update() {
        if(this.f_tgt && !this.isBad && this.f_tgt.hp>0) {
            let cx=this.f_tgt.x+this.f_tgt.w/2, cy=this.f_tgt.y+this.f_tgt.h/2;
            let d_ax=cx-this.x, d_ay=cy-this.y, ang=Math.atan2(d_ay,d_ax); 
            // Turn smoothly factor geometry calculations math
            let spConst = Math.abs(this.bx)>0? Math.abs(this.bx) : 15; 
            this.bx += (Math.cos(ang)*spConst - this.bx)*0.15; 
            this.by += (Math.sin(ang)*spConst - this.by)*0.15;
        }

        this.x+=this.bx; this.y+=this.by;

        if(!this.isBad) {
            for(let o of En) if(AABB(this,{x:o.x,y:o.y,w:o.w,h:o.h})){ 
               o.hp-=this.dmg; this.dmg=0; o.flash=4; screenShake(2); 
               sExplod(o.x+o.w/2, o.y+o.h/2, this.c, this.sz>20?10:4); o.vx += (this.bx>0?3:-3);
               break; 
            }
        } else {
            // enemy bullet 
            if(AABB(this, P)) {
               P.hp-=this.dmg; screenShake(5); this.dmg=0; 
               P.vx+=(this.bx>0?5:-5); sExplod(P.x, P.y, '#e74c3c', 10);
            }
        }
    }
    draw() {
        ctx.fillStyle=this.c; ctx.beginPath(); ctx.arc(this.x,this.y,this.sz/2, 0, Math.PI*2); ctx.fill();
    }
}

// Systems Toolings
function sSpark(x,y,c,ct=1){ for(let i=0;i<ct;i++) Pa.push({x:x,y:y,c:c,sz:3,vy: -2-Math.random()*4, vx:Math.random()-0.5,lf:25}); }
function sExplod(x,y,c,ct){ for(let i=0;i<ct;i++) Pa.push({x:x,y:y,c:c,sz:4+Math.random()*6,vx:(Math.random()-.5)*15,vy:(Math.random()-.5)*15,lf:20});}
function sDust(x,y, c="#95a5a6"){ for(let i=0;i<ct=5;i++) Pa.push({x:x,y:y,c:c,sz:5,vx:(Math.random()-.5)*2,vy:-(Math.random()*3),lf:15}); }
function updPa(){
    for(let i=Pa.length-1; i>=0; i--) { let p=Pa[i]; p.x+=p.vx; p.y+=p.vy; p.vy+=0.3; p.lf--; p.sz*=0.95; if(p.lf<0) Pa.splice(i,1);}
}
function AABB(A,B) { return !(A.x+A.w<B.x || B.x+B.w<A.x || A.y+A.h<B.y || B.y+B.h<A.y);}
// "elif" trick via standard JS if-else trees handled by preprocessors logic. Just chained ifs implemented above natively 

let wfDelay=0, bndMax=2000;
let BGF_COLOR = "#000";

// --------------- STAGE MANAGER BUILD & LOAD מטענים מערכי JSON עשיר ! ---------------
function bldWave() {
    // נתח את ה Stage 
    let conf = SERVER_MAPS.find(o=>o.stage === globalData.st); 
    
    // במידה ושמרת מעל מפה חלופית 
    if(!conf) {
       let idxMapLoop = globalData.st % 20; 
       conf = SERVER_MAPS.find(o=>o.stage === (idxMapLoop==0? 20:idxMapLoop)) || SERVER_MAPS[0];
    }
    
    document.getElementById('v-lvl').innerText = globalData.st;
    msgCenter(conf.enemies.boss ? "⚠ BOSS ⚠" : `STAGE ${globalData.st}`);
    BGF_COLOR = conf.background || '#090a14';

    En = []; PLATS=[];
    
    // Spawn Plats dynamically based on view scale screen 
    if(conf.platforms) {
        let YB = getGroundY(); 
        for(let jb of conf.platforms) {
            PLATS.push( { x: jb.offset_x, gy: YB - jb.height, w: jb.w } );
        }
    }
    
    let wX_SPN = P.x + 800; // where spawn points 
    if(conf.enemies.boss) { En.push(new EnemyBase(wX_SPN, 'boss', globalData.st)); bndMax = wX_SPN+800;}
    else {
        // distribute 
        let ttL = wX_SPN;
        for(let i=0; i<conf.enemies.walkers; i++) { En.push(new EnemyBase(ttL,'walker',globalData.st)); ttL+= 100+Math.random()*100; }
        for(let i=0; i<conf.enemies.shooters;i++) { En.push(new EnemyBase(ttL,'shooter',globalData.st)); ttL+= 200; }
        for(let i=0; i<conf.enemies.jumpers; i++) { En.push(new EnemyBase(ttL,'jumper',globalData.st)); ttL+= 150; }
        bndMax = ttL + 800;
    }
}

// LOOP ! MAIN GAMING FRAME TIME UPDATE PROCESS INTERVAL RENDERS !!!  🚀  🍀 
function lu() {
    if(state!=='PLY')return;
    frame++;
    
    P.update();
    for(let i=En.length-1; i>=0;i--){
       En[i].update(); 
       if(En[i].hp<=0){
          let kD = En[i].isBos? 100 : 5;
          sExplod(En[i].x, En[i].y, En[i].isBos?'gold':'red', En[i].isBos?50:15);
          if(P.isDark) P.hp = Math.min(P.hp+5, P.maxHp); // Vamp bonus trigger dark soul steal passive !
          En.splice(i,1); screenShake(5); 
       }
    }
    for(let i=Pr.length-1; i>=0;i--) { Pr[i].update(); if(Pr[i].dmg<=0 || Pr[i].x > P.x+2000 || Pr[i].y>cvs.height+200 || Pr[i].x< P.x-2000) Pr.splice(i,1); }
    updPa();

    // WIN STAGE RULES !!! => WAVE IS ZERO ENTITY DEAD BODIES ALL GONE CLEAN FIELD CLEARED
    if(En.length==0) {
        if(wfDelay==0) wfDelay = 80; else wfDelay--;
        if(wfDelay==1) {
            // CHECK UPGRADE NOTIFICATION PROGRESS 5-10-15 BOSSS UNLOCKER! !!
            if(globalData.st == 5) pushUpg("⚡ קפיצה כפולה שוחררה!");
            if(globalData.st == 10) { pushUpg("💀 סופר מתקפה ULTIMATE! לחץ Y!"); unlocks.super=true; }
            if(globalData.st == 15) { pushUpg("🔋 הטענת אנרגיה עצמאית קטנה"); unlocks.rech=true; }
            if(globalData.st >= 20) { WINSEQ(); return;} // GAME WIN END ENDLESS FOR NOW UNLESS ADD DLC  

            globalData.st++; P.hp = Math.min(P.maxHp, P.hp + (P.maxHp * 0.2)); 
            bldWave();
            
            fetch('/save',{method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify({shards:globalData.st})});
        }
    }

    if(P.hp<=0) { LOSE(); return; }

    // Renders visual scene matrix drawing contexts HTML elements bridge connectivity logic data views syncing HUD updates UI HTML layout updates !!  
    if(cam.sx>0) {cam.x += (Math.random()-.5)*cam.sx; cam.sx *=0.8; if(cam.sx<0.5)cam.sx=0;}
    let tz = P.x - 250; if(tz<0)tz=0; 
    cam.x += (tz-cam.x)*0.08; 

    // ---- DRAWING GRAPHICS 2D API ---------------- //  
    // Parallax dynamic sky layer paint linear matrix mapping canvas object colors deep background color context gradients filling visual box spaces 
    let grd = ctx.createLinearGradient(0,0, 0,cvs.height); grd.addColorStop(0, BGF_COLOR); grd.addColorStop(1,"#05080e");
    ctx.fillStyle= grd; ctx.fillRect(0,0,cvs.width, cvs.height);
    // Grid retro  Synth Wave Lines Art Background FX 
    ctx.strokeStyle="rgba(100,200,255, 0.05)"; ctx.lineWidth=1;
    for(let lx = -((cam.x*0.1)%40); lx < cvs.width; lx+=40) { ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, cvs.height); ctx.stroke();}
    
    ctx.save(); ctx.translate(-cam.x,0);
    // THE FLOOR SOLID !  // Placed Ground ! 
    ctx.fillStyle="#0A0A0E"; ctx.fillRect(0,getGroundY(), 50000, 400); 
    ctx.fillStyle= P.baseC; ctx.fillRect(0,getGroundY(), 50000, 3); 
    
    // Render selective dynamically PLATFORMS 
    ctx.fillStyle = "#162035"; ctx.strokeStyle = "#4b7bec"; 
    for(let pB of PLATS) { 
        ctx.fillRect(pB.x, pB.gy, pB.w, 40);
        ctx.strokeRect(pB.x, pB.gy, pB.w, 40); 
    }

    P.draw(); for(let o of En) o.draw(); for(let pm of Pr) pm.draw();
    for(let pp of Pa) { ctx.fillStyle=pp.c; ctx.fillRect(pp.x, pp.y, pp.sz, pp.sz); }
    
    ctx.restore();
    syncUI();
    requestAnimationFrame(lu);
}

// Start sequence Game launch initialization code flow app state UI layer bridge connections class mappings HTML injections !!! 
function launchGame(C) { 
   document.getElementById('class-indicator').innerHTML=`◂[ ${HERO_CLASSES[C].name} MODE ] ▸`;
   P = new PlayBoy(C); globalData.st=1; bldWave(); unlocks={dj:(globalData.st>5), super:(globalData.st>10), rech:(globalData.st>15)}; // Safety check 
   document.getElementById('menu-screen').classList.add('hidden');
   document.getElementById('ui-layer').classList.remove('hidden');
   state = 'PLY'; requestAnimationFrame(lu);
}

function msgCenter(txt) {
   let el = document.getElementById('game-title-drop'); el.innerText=txt; 
   el.style.transform = 'translate(-50%, 0) scale(1.5)'; el.style.opacity = 1;
   setTimeout(()=>{ el.style.opacity=0; el.style.transform = 'translate(-50%, -20%) scale(1.0)'; }, 3000);
}
function pushUpg(xT) {
   let T = document.getElementById('notify-msg'); T.innerText = xT; T.style.opacity=1;
   setTimeout(()=>{T.style.opacity=0;}, 4500); if(xT.includes('קפיצה כפול')) unlocks.dj=true;
}

function syncUI() {
    document.getElementById('v-hp').innerText = Math.max(Math.floor(P.hp),0) + " / "+Math.floor(P.maxHp);
    document.getElementById('bar-hp').style.width = Math.max(0,(P.hp/P.maxHp)*100)+"%";
    document.getElementById('v-en').innerText = Math.floor(P.en) + " / "+P.maxEn;
    document.getElementById('bar-en').style.width = (P.en/P.maxEn)*100 + "%";
    document.getElementById('bar-stage').style.width = (globalData.st / 20 * 100)+"%";
}

function LOSE() { 
    state='DIE'; 
    document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('death-screen').classList.remove('hidden');
    document.getElementById('final-stats').innerHTML = `STAGE RECORD REACHED: <span style="color:#fbc531">${globalData.st}</span> / 20`; 
}
function WINSEQ() {
    state='WIN'; document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('win-screen').classList.remove('hidden'); 
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
