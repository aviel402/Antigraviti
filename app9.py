from flask import Flask, render_template_string, jsonify, request
import json
import maps9
import txt9

app = Flask(__name__)
app.secret_key = 'clover_master_v8_final_world'

PLAYER_DATA = {"shards": 0, "max_stage_reached": 1}

@app.route('/')
def idx():
    game_maps = maps9.generate_maps()
    return render_template_string(GAME_HTML, 
                                  maps_json=json.dumps(game_maps),
                                  texts=json.dumps(txt9.TEXTS),
                                  heroes_texts=json.dumps(txt9.HERO_TEXTS))

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    try:
        data = request.json
        PLAYER_DATA["shards"] += data.get("shards", 0)
        if data.get("stage", 1) > PLAYER_DATA["max_stage_reached"]:
            PLAYER_DATA["max_stage_reached"] = data.get("stage", 1)
        return jsonify(PLAYER_DATA)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CLOVER - World</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; touch-action: manipulation; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 100; 
            background: linear-gradient(135deg, rgba(5,5,10,0.95), rgba(20,20,30,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center; overflow-y:auto;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        h1.title { font-family: 'Righteous', cursive; font-size: clamp(40px, 8vw, 80px); margin:0; text-transform: uppercase;
                   background: -webkit-linear-gradient(#f1c40f, #e67e22); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 0px 20px rgba(241,196,15,0.4));}
        
        /* Debug Menu */
        #dev-panel { background: rgba(255,0,0,0.2); border: 2px solid red; padding: 20px; border-radius: 10px; margin-bottom: 20px; display: none; }
        #dev-panel select, #dev-panel button { padding: 10px; font-size: 16px; margin: 5px; font-family: 'Rubik'; }

        /* Chest Info Panel */
        .info-chest { background: rgba(0,0,0,0.7); border: 2px solid var(--gold); border-radius: 10px; padding: 20px; max-width: 800px; margin-top: 20px; text-align: right; box-shadow: 0 0 15px rgba(241,196,15,0.3); }
        .info-chest h3 { color: var(--gold); margin-top: 0; }
        .info-chest ul { list-style: none; padding: 0; }
        .info-chest li { margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #333; padding-bottom: 5px;}

        .char-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; width: 90%; max-width: 1200px; margin-top:20px; padding-bottom: 50px;}
        .char-card { background: rgba(0,0,0,0.5); border: 2px solid #555; padding: 15px; border-radius: 12px; cursor: pointer; text-align: center; transition: 0.3s; }
        .char-card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.5); border-color: var(--card-color);}
        .char-card h3 { margin: 0 0 5px 0; font-family: 'Righteous'; }
        
        /* UI Layer */
        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:10; display:flex; flex-direction:column; padding:20px; justify-content:space-between; }
        .glass-panel { background: rgba(255,255,255,0.05); backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 10px; }
        
        /* Mobile Controls */
        .mobile-ui { position: absolute; bottom: 20px; width: 100%; left: 0; display: none; pointer-events: none; padding: 0 20px; justify-content: space-between; z-index: 50;}
        .d-pad, .action-btns { display: grid; gap: 10px; pointer-events: auto; }
        .d-pad { grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px; }
        .btn-mob { background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.5); border-radius: 50%; color: white; font-weight: bold; font-size: 20px; cursor: pointer; backdrop-filter: blur(5px); }
        .btn-mob:active { background: rgba(255,255,255,0.5); transform: scale(0.9); }
        .action-btns { grid-template-columns: repeat(3, 50px); grid-template-rows: repeat(2, 50px); justify-content: end; }

        .top-right-controls { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; pointer-events: auto;}
        .toggle-btn { padding: 8px 15px; font-family: 'Rubik'; background: #333; color: white; border: 1px solid #777; border-radius: 5px; cursor: pointer; }
        
        /* Top HUD */
        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        .stat-bar-container { display: flex; align-items: center; margin-bottom:5px; width:250px;}
        .stat-icon { font-weight:900; margin-left: 10px; width:40px; font-size: 12px;}
        .bar-out { background: rgba(0,0,0,0.7); flex-grow: 1; height: 18px; border-radius: 10px; overflow:hidden; border: 1px solid rgba(255,255,255,0.2); }
        .bar-in { height:100%; transition: width 0.1s; }
        .hp-bar { background: #e74c3c; box-shadow: 0 0 10px #e74c3c; }
        .en-bar { background: #3498db; box-shadow: 0 0 10px #3498db; }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Righteous'; font-size:20px; color:#fff; text-shadow:0 0 10px cyan;}
        .menu-btn { padding:15px 40px; border:2px solid #fff; border-radius:8px; color:white; font-size:24px; font-family:'Righteous'; background:transparent; cursor:pointer; margin-top:20px; text-transform:uppercase; transition:0.3s; width: 350px; max-width: 90vw;}
        .menu-btn:hover { background:#fff; color:#000; box-shadow:0 0 20px #fff; transform: scale(1.05);}
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    
    <div id="dev-panel">
        <h2 id="t-dev-title"></h2>
        <select id="dev-stage">
            <script>for(let i=1;i<=20;i++) document.write(`<option value="${i}">Stage ${i}</option>`);</script>
        </select>
        <button id="t-dev-btn" onclick="startMission(HEROES[0], true)"></button>
    </div>

    <h1 class="title" id="t-main-title"></h1>
    <h2 id="t-main-sub" style="margin:0; color:var(--gold);"></h2>
    
    <div class="info-chest">
        <h3 id="t-htp-title"></h3>
        <p id="t-htp-desc" style="font-size: 14px; white-space: pre-line;"></p>
        <h3 id="t-ctrl-title"></h3>
        <ul id="t-ctrl-list"></ul>
    </div>

    <div class="char-grid" id="roster"></div>
</div>

<div id="pause-screen" class="screen hidden" style="z-index:9000;">
    <h1 class="title" id="t-pause" style="color:#3498db; margin-bottom: 20px;"></h1>
    <button class="menu-btn" onclick="togglePause()" id="btn-resume"></button>
    <button class="menu-btn" onclick="location.reload()" id="btn-restart" style="background:#e74c3c; border-color:#e74c3c;"></button>
</div>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="glass-panel" style="direction: ltr;">
            <div class="stat-bar-container">
                <span class="stat-icon" style="color:#e74c3c;">HP <span id="hp-t"></span></span>
                <div class="bar-out"><div class="bar-in hp-bar" id="hp-bar"></div></div>
            </div>
            <div class="stat-bar-container">
                <span class="stat-icon" style="color:#3498db;">EN <span id="en-t"></span></span>
                <div class="bar-out"><div class="bar-in en-bar" id="en-bar"></div></div>
            </div>
        </div>
        
        <div class="glass-panel stage-title" id="stage-info">...</div>
        
        <div class="top-right-controls">
             <button class="toggle-btn" id="t-mobile-toggle" onclick="toggleMobileUI()"></button>
             <button class="toggle-btn" onclick="togglePause()">⏸ PAUSE</button>
        </div>
    </div>
    
    <!-- Mobile Controls -->
    <div class="mobile-ui" id="mob-ui">
        <div class="d-pad">
            <div></div><button class="btn-mob" ontouchstart="mk('KeyW')" ontouchend="rk('KeyW')">W</button><div></div>
            <button class="btn-mob" ontouchstart="mk('KeyA')" ontouchend="rk('KeyA')">A</button>
            <button class="btn-mob" ontouchstart="mk('KeyS')" ontouchend="rk('KeyS')">S</button>
            <button class="btn-mob" ontouchstart="mk('KeyD')" ontouchend="rk('KeyD')">D</button>
        </div>
        <div class="action-btns">
            <button class="btn-mob" ontouchstart="mk('KeyH')" ontouchend="rk('KeyH')">H</button>
            <button class="btn-mob" ontouchstart="mk('KeyJ')" ontouchend="rk('KeyJ')">J</button>
            <button class="btn-mob" ontouchstart="mk('KeyK')" ontouchend="rk('KeyK')">K</button>
            <button class="btn-mob" ontouchstart="mk('KeyU')" ontouchend="rk('KeyU')">U</button>
            <button class="btn-mob" ontouchstart="mk('KeyI')" ontouchend="rk('KeyI')">I</button>
            <button class="btn-mob" ontouchstart="mk('KeyY')" ontouchend="rk('KeyY')" style="background:var(--gold);color:black;">Y</button>
        </div>
    </div>
</div>

<div id="death-screen" class="screen hidden" style="z-index:9500;">
    <h1 class="title" id="t-death" style="color:#c0392b;"></h1>
    <h2><span id="t-death-sub"></span> <span id="final-lvl" style="color:var(--gold);"></span> </h2>
    <button class="menu-btn" onclick="location.reload()" id="btn-retry" style="background:#e74c3c;"></button>
</div>

<div id="victory-screen" class="screen hidden" style="z-index:9600; background: rgba(10,40,10,0.95);">
    <h1 class="title" id="t-vic" style="color:#2ecc71;"></h1>
    <h2 id="t-vic-sub"></h2>
    <button class="menu-btn" onclick="location.href='/'" id="btn-home" style="background:#2ecc71; border-color:#2ecc71; color:#000;"></button>
</div>

<script>
const MAPS = {{ maps_json | safe }};
const TEXTS = {{ texts | safe }};
const HERO_TEXTS = {{ heroes_texts | safe }};

// --- טעינת טקסטים ---
document.getElementById('t-main-title').innerText = TEXTS.title_main;
document.getElementById('t-main-sub').innerText = TEXTS.subtitle_main;
document.getElementById('t-htp-title').innerText = TEXTS.how_to_play_title;
document.getElementById('t-htp-desc').innerText = TEXTS.how_to_play_desc;
document.getElementById('t-ctrl-title').innerText = TEXTS.controls_title;
document.getElementById('t-pause').innerText = TEXTS.pause_title;
document.getElementById('btn-resume').innerText = TEXTS.btn_resume;
document.getElementById('btn-restart').innerText = TEXTS.btn_restart;
document.getElementById('t-death').innerText = TEXTS.death_title;
document.getElementById('t-death-sub').innerText = TEXTS.death_sub;
document.getElementById('btn-retry').innerText = TEXTS.btn_retry;
document.getElementById('t-vic').innerText = TEXTS.victory_title;
document.getElementById('t-vic-sub').innerText = TEXTS.victory_sub;
document.getElementById('btn-home').innerText = TEXTS.btn_home;
document.getElementById('t-mobile-toggle').innerText = TEXTS.mobile_toggle;
document.getElementById('t-dev-title').innerText = TEXTS.dev_title;
document.getElementById('t-dev-btn').innerText = TEXTS.dev_btn;

let clist = "";
TEXTS.controls_list.forEach(c => clist += `<li>${c}</li>`);
document.getElementById('t-ctrl-list').innerHTML = clist;

// בדוק האם עברנו x=v
if(new URLSearchParams(window.location.search).get('x') === 'v') {
    document.getElementById('dev-panel').style.display = 'block';
}

// --- מקשים ---
const activeKeys = {};
window.addEventListener('keydown', e => { 
    if(e.code==='Space') e.preventDefault(); 
    if(e.code === 'KeyP' || e.code === 'Escape') togglePause();
    activeKeys[e.code]=true;
});
window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; }

// Mobile handlers
function mk(c) { activeKeys[c] = true; }
function rk(c) { activeKeys[c] = false; }
let isMobileUI = false;
function toggleMobileUI() {
    isMobileUI = !isMobileUI;
    document.getElementById('mob-ui').style.display = isMobileUI ? 'flex' : 'none';
}

function intersect(a,b){return!(b.x>a.x+a.w || b.x+b.w<a.x || b.y>a.y+a.h || b.y+b.h<a.y);}

const HEROES =[
    { id: 'earth', col: '#2ecc71', maxHp: 180, hpRegen: 0.01, speed: 0.8, jump: 13, maxEn: 100, dmgMult: 1.2, enCostMult: 1, pCol: '#27ae60'},
    { id: 'fire', col: '#e74c3c', maxHp: 80, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.8, enCostMult: 1, pCol: '#ff7979'},
    { id: 'water', col: '#3498db', maxHp: 110, hpRegen: 0.15, speed: 1.0, jump: 14, maxEn: 110, dmgMult: 1.0, enCostMult: 1, pCol: '#7ed6df'},
    { id: 'air', col: '#ecf0f1', maxHp: 90, hpRegen: 0, speed: 1.6, jump: 16, maxEn: 100, dmgMult: 0.8, enCostMult: 0.7, pCol: '#c7ecee'},
    { id: 'lightning', col: '#f1c40f', maxHp: 90, hpRegen: 0, speed: 2.0, jump: 13, maxEn: 100, dmgMult: 1.5, enCostMult: 1.5, pCol: '#f9ca24'},
    { id: 'magma', col: '#d35400', maxHp: 150, hpRegen: 0.05, speed: 0.6, jump: 11, maxEn: 100, dmgMult: 1.6, enCostMult: 1.2, pCol: '#eb4d4b'},
    { id: 'light', col: '#ffffb3', maxHp: 100, hpRegen: 0.02, speed: 1.0, jump: 14, maxEn: 300, dmgMult: 0.9, enCostMult: 0.8, pCol: '#fff200'},
    { id: 'dark', col: '#8e44ad', maxHp: 85, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.0, enCostMult: 1.0, pCol: '#9b59b6'}
];

function createSelectMenu() {
    let box = document.getElementById('roster');
    HEROES.forEach(h => {
        let htxt = HERO_TEXTS[h.id];
        let div = document.createElement('div');
        div.className = 'char-card'; div.style.setProperty('--card-color', h.col);
        div.innerHTML = `<h3 style="color:${h.col};">${htxt.name}</h3><div class="char-desc">${htxt.desc}</div>`;
        div.onclick = () => { startMission(h, false); }
        box.appendChild(div);
    });
}

const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }); window.dispatchEvent(new Event('resize'));

const STAGE_WIDTH = 3000;
let p_class = null; let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[], drops=[];
let currentMap = MAPS[1]; let globalStage = 1; let f=0; let shakeV=0, camX=0;
let isPaused = false; 
let barrier = null; // מודל מחסום שביר
let pipe = null; // צינור מעבר מריו
let cloverChest = null;
let navArrowOpacity = 0;

function doShake(amt){shakeV=amt*4;} 

function togglePause() {
    if(!pl || pl.hp<=0 || globalStage>20) return; 
    isPaused = !isPaused;
    document.getElementById('pause-screen').classList.toggle('hidden', !isPaused);
    if(!isPaused) { for(let key in activeKeys) activeKeys[key] = false; }
}

class Barrier {
    constructor(x) { this.x = x; this.y = 0; this.w = 40; this.h = canvas.height; this.hp = 200; this.maxHp=200; this.vulnerable = false; }
    draw() {
        ctx.fillStyle = this.vulnerable ? 'rgba(46, 204, 113, 0.5)' : 'rgba(231, 76, 60, 0.5)';
        ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.fillStyle = this.vulnerable ? '#2ecc71' : '#e74c3c';
        ctx.fillRect(this.x + 15, this.y, 10, this.h);
        if(this.vulnerable) {
            ctx.fillStyle = 'red'; ctx.fillRect(this.x-10, canvas.height/2, 60, 10);
            ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, canvas.height/2, 60*(this.hp/this.maxHp), 10);
        }
    }
}

class Pipe {
    constructor(x) { 
        this.w = 80; this.h = 100; 
        this.x = x - this.w - 50; 
        this.y = canvas.height - 80 - this.h; 
    }
    draw() {
        ctx.fillStyle = '#27ae60'; ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, this.y, this.w+20, 30);
        ctx.strokeStyle = '#000'; ctx.lineWidth=3; 
        ctx.strokeRect(this.x, this.y, this.w, this.h); ctx.strokeRect(this.x-10, this.y, this.w+20, 30);
        ctx.fillStyle = 'white'; ctx.font="20px Arial"; ctx.fillText("⬇ S", this.x+20, this.y-20);
    }
}

class Drop {
    constructor(x, y, isBoss) {
        this.x = x; this.y = y; this.w = 20; this.h = 20; this.vy = -5;
        this.isBoss = isBoss;
    }
    upd() {
        this.vy += 0.5; this.y += this.vy;
        let flY = canvas.height-80;
        if(this.y+this.h > flY) { this.y = flY-this.h; this.vy = 0; }
        if(intersect(this, pl)) {
            if(this.isBoss) {
                pl.maxHp += 20; pl.maxEn += 20; pl.hp = pl.maxHp; pl.en = pl.maxEn;
                makeFX(this.x, this.y, 20, '#f1c40f', 'spark');
            } else {
                pl.hp = Math.min(pl.hp + 25, pl.maxHp);
                makeFX(this.x, this.y, 10, '#2ecc71', 'spark');
            }
            return true; 
        }
        return false;
    }
    draw() {
        ctx.fillStyle = this.isBoss ? '#f1c40f' : '#2ecc71'; ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.strokeStyle = '#fff'; ctx.strokeRect(this.x, this.y, this.w, this.h);
        ctx.fillStyle = 'white'; ctx.fillText(this.isBoss?"★":"+", this.x+5, this.y+15);
    }
}

class Player {
    constructor(c){
        this.w=35; this.h=65; this.x=100; this.y=0; this.vx=0; this.vy=0;
        this.c = c; this.maxHp=c.maxHp; this.hp=this.maxHp; this.maxEn=c.maxEn; this.en=this.maxEn;
        this.facing = 1; this.grounded = false; this.target = null;
        this.lockKeyTriggered = false; this.atkWait = {}; this.jCount = 0;
        this.iFrames = 0; this.chargeI = 0; 
    }

    upd() {
        if(this.hp<=0) return;
        this.hp = Math.min(this.hp + this.c.hpRegen, this.maxHp);
        if(this.iFrames > 0) this.iFrames--;

        let isCrouch = kd('KeyS') || kd('ArrowDown');
        let isSprint = kd('ShiftLeft') || kd('ShiftRight');
        let chrgU = kd('KeyU');
        let chrgI = kd('KeyI');

        // גודל דמות לפי התכופפות
        if(isCrouch) {
            if(this.h !== 40) { this.y += 25; this.h = 40; } // כיווץ מטה
        } else {
            if(this.h !== 65) { this.y -= 25; this.h = 65; } // עמידה
        }

        // --- מכת הסופר I (הולך לאט, מושפע צבע, ללא עלות) ---
        if(chrgI) {
            this.chargeI = Math.min(this.chargeI + 2, 200); 
            makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'spark');
        } else if (this.chargeI > 0) {
            let dmg = this.chargeI * 2 * this.c.dmgMult;
            let size = (this.chargeI / 3);
            p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+20, dir: this.facing, s:25, dmg:dmg, size: size, color: this.c.pCol, tgt: this.target });
            this.vx -= (this.chargeI/10)*this.facing; this.chargeI = 0; doShake(5);
        }

        // --- תנועה ---
        let applySpeed = this.c.speed;
        if(isSprint) applySpeed *= 1.8;
        if(chrgU || chrgI || isCrouch) applySpeed *= 0.3; // האטה בזמן טעינות או כריעה
        
        if(kd('KeyA')){ this.vx-=applySpeed; this.facing=-1; }
        if(kd('KeyD')){ this.vx+=applySpeed; this.facing= 1; }
        
        if((kd('KeyW') || kd('Space')) && !isCrouch) {
            if(!this.jHold) {
                if(this.jCount < 2) { this.vy = -this.c.jump; this.jCount++; makeFX(this.x+this.w/2, this.y+this.h, 6, '#fff', 'spark'); }
                this.jHold = true;
            }
        } else { this.jHold=false;}

        // --- יריות ---
        if(chrgU) {
            this.en = Math.min(this.en + 1.2, this.maxEn);
            makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'beam');
        } else if (!chrgI) {
            this.sHand('KeyH', '1', 8 * this.c.enCostMult, 12 * this.c.dmgMult, 8);
            this.sHand('KeyJ', '2', 20 * this.c.enCostMult, 30 * this.c.dmgMult, 15);
            this.sHand('KeyK', '3', 45 * this.c.enCostMult, 70 * this.c.dmgMult, 25);
            
            // Y: עולה 100% מהאנרגיה במדויק
            if(kd('KeyY') && !this.atkWait['KeyY']) {
                if(this.en >= this.maxEn) {
                    this.en = 0; // מרוקן הכל
                    p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+20, dir: this.facing, s:12, dmg:400*this.c.dmgMult, size: 60, color: this.c.pCol, tgt: this.target });
                    this.vx -= 15*this.facing; doShake(8);
                }
                this.atkWait['KeyY'] = true;
            } else if(!kd('KeyY')) { this.atkWait['KeyY'] = false; }
        }

        if(kd('KeyE')){ if(!this.lockKeyTriggered){ this.swLock(); this.lockKeyTriggered=true;} } else {this.lockKeyTriggered=false;}
        if(this.target && this.target.hp <= 0){ this.target = null; this.findBestTarget(); }

        this.vy += 0.6; this.x+=this.vx; this.y+=this.vy; this.vx *= 0.8;
        
        // גבולות מפה שמאלה וימינה
        let leftBnd = (globalStage - 1) * STAGE_WIDTH; 
        if(this.x < leftBnd + 10) { this.x=leftBnd + 10; this.vx=0;} 
        
        let rightBnd = globalStage * STAGE_WIDTH;
        if(barrier && this.x + this.w > barrier.x) { this.x = barrier.x - this.w; this.vx = 0; }

        this.physicsFloor();

        // --- בדיקת כניסה לצינור ---
        if(pipe && intersect(this, pipe) && isCrouch && this.grounded) {
            this.hp = Math.min(this.hp + (this.maxHp*0.5), this.maxHp);
            globalStage++;
            loadStageArea(globalStage);
        }
    }

    physicsFloor() {
        let isG=false; let floor_lvl = canvas.height-80;
        if(this.y+this.h >= floor_lvl){ this.y = floor_lvl-this.h; this.vy=0; isG=true; } else {
            let offset_x = (globalStage - 1) * STAGE_WIDTH;
            currentMap.platforms.forEach(pf => {
               let real_x = pf.x + offset_x; let pFloorY = canvas.height - pf.y_offset;
               if(this.vy>=0 && this.y+this.h >= pFloorY - 14 && this.y+this.h <= pFloorY + 14 && this.x+this.w > real_x && this.x < real_x+pf.w){
                   this.y = pFloorY-this.h; this.vy=0; isG=true;
               }
            });
        }
        if(isG){this.jCount=0; this.grounded=true;} else{this.grounded=false;}
    }

    sHand(k,t,cost,dmg,size) {
        if(kd(k)){
            if(!this.atkWait[k]){
                if(this.en >= cost) {
                    this.en -= cost;
                    p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+20, dir: this.facing, s:(t==='1')?18:15, dmg:dmg, size: size * (this.c.id==='magma'? 1.8:1), color: this.c.pCol, tgt: this.target });
                    this.vx -= (cost/5)*this.facing; 
                }
                this.atkWait[k] = true;
            }
        }else{this.atkWait[k] = false;}
    }

    swLock() { if(this.target) this.target=null; else this.findBestTarget(); }
    findBestTarget() {
        let maxDist = 1400; let trg = null;
        e_arr.forEach(e => { let d = Math.abs(e.x - this.x); if(d < maxDist && e.x > this.x - 400 && e.x < this.x+1000) { maxDist=d; trg=e; } });
        if(trg) { this.target=trg; doShake(1.5); }
    }

    draw() {
        ctx.save(); ctx.translate(this.x, this.y);
        if(this.iFrames > 0 && Math.floor(f / 4) % 2 === 0) ctx.globalAlpha = 0.3;

        ctx.fillStyle = this.c.col; 
        if(this.en > 90) { ctx.shadowBlur = 15; ctx.shadowColor = this.c.col; }
        ctx.fillRect(0,0,this.w,this.h); ctx.shadowBlur = 0;
        ctx.fillStyle='rgba(255,255,255,0.8)'; 
        if(this.facing>0) ctx.fillRect(this.w-4, 0, 4, this.h); else ctx.fillRect(0,0,4,this.h);

        if(this.chargeI > 0) {
            ctx.beginPath(); ctx.arc(this.w/2, this.h/2, this.chargeI/2.5, 0, Math.PI*2);
            ctx.fillStyle = this.c.pCol; ctx.globalAlpha = 0.5; ctx.fill();
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); ctx.globalAlpha = 1.0;
        }

        if(this.target){
             let rx = this.target.x + this.target.w/2 - this.x; let ry = this.target.y+this.target.h/2 - this.y;
             ctx.strokeStyle='#ff3838'; ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(this.w/2, this.h/2); ctx.lineTo(rx,ry); ctx.stroke();
             ctx.beginPath(); ctx.arc(rx,ry, 25+Math.sin(f/4)*5,0,Math.PI*2); ctx.stroke();
        }
        ctx.globalAlpha = 1.0; ctx.restore();
    }
}

class Enemy {
    constructor(x, ty) {
        this.x=x; this.y=10; this.ty = ty; this.homeX = x; this.isAggro = false; 
        this.w = 40; this.h=50; this.vx=0; this.vy=0; 
        this.maxHp = 40 + (globalStage*15); this.s = 2; this.stateT = 100;
        
        if(ty==='boss'){ this.maxHp *= 18; this.w=120; this.h=120; this.s=1;}
        else if(ty==='shooter'){ this.col = '#f39c12'; this.s=1.5;}
        else if(ty==='jumper'){ this.col = '#8e44ad'; this.s=1.3; }  
        else if(ty==='tank'){ this.col='#7f8c8d'; this.w=60; this.h=75; this.maxHp*=3; this.s=0.5; }
        else if(ty==='ninja'){ this.col='#00cec9'; this.w=30; this.h=45; this.maxHp*=0.6; this.s=2.5; this.stateT=80;}
        else if(ty==='summoner'){ this.col='#341f97'; this.w=40; this.h=60; this.maxHp*=0.9; this.s=1.2;}
        else { this.col = '#c23616'; } 
        
        this.hp = this.maxHp; this.shClock = Math.random()*80 + 20; 
    }
    upd() {
        let dx = pl.x - this.x; let flY = canvas.height-80;
        if(!this.isAggro) {
            if(Math.abs(dx) < 700) { this.isAggro = true; } else { this.vx = Math.sin(f/40) * this.s * 0.5; }
        }
        if(this.isAggro) {
            if(this.ty === 'melee' || this.ty === 'boss' || this.ty === 'tank'){
                if(Math.abs(dx)>2) this.vx = dx>0? this.s:-this.s;
                if(this.ty==='boss' && Math.random()<0.02 && e_arr.length<5) { e_arr.push(new Enemy(this.x, 'jumper')); e_arr[e_arr.length-1].isAggro = true;}
            } else if(this.ty === 'ninja'){
                this.stateT--;
                if(this.stateT > 20) { this.vx = dx>0? this.s:-this.s; } else if(this.stateT > 0) { this.vx = dx>0? 13:-13; } else { this.stateT = Math.random()*60 + 90; } 
            } else if(this.ty === 'shooter'){
                if(Math.abs(dx) > 350) this.vx = dx>0? this.s:-this.s; else this.vx*=0.6;
                this.shClock--; if(this.shClock<=0) { this.shClock=120; pr_arr.push({x:this.x+20, y:this.y+20, dx:dx>0?8:-8, dy:0}); }
            } else if(this.ty === 'jumper'){
                 this.vx = dx>0? this.s+0.2 : -(this.s+0.2);
                 this.shClock--; if(this.shClock<=0 && this.y+this.h>=flY){ this.vy = -10; this.shClock=90;} 
            } else if(this.ty === 'summoner') {
                 if(Math.abs(dx) < 600) { this.vx = dx>0 ? -this.s : this.s; } else { this.vx*=0.9; } 
                 this.shClock--;
                 if(this.shClock<=0 && e_arr.length<8) {
                     this.shClock = 250; e_arr.push(new Enemy(this.x+50, 'melee')); e_arr[e_arr.length-1].isAggro = true;
                     makeFX(this.x+50, this.y, 15, '#c8d6e5', 'boom');
                 }
            }
        }
        this.vy+=0.6; this.y+=this.vy; this.x+=this.vx;
        
        let leftBnd = (globalStage - 1) * STAGE_WIDTH;
        if(this.x < leftBnd + 10) { this.x=leftBnd + 10; this.vx *= -1; } 
        if(barrier && this.x + this.w > barrier.x) { this.x = barrier.x - this.w; this.vx *= -1; }
        
        let isGEnemy=false; if(this.y+this.h >= flY) { this.y=flY-this.h; this.vy=0; isGEnemy=true;}
        if(!isGEnemy && this.ty !== 'jumper'){ 
            let offset_x = (globalStage - 1) * STAGE_WIDTH;
            currentMap.platforms.forEach(pf => {
               let real_x = pf.x + offset_x; let pFloorY = canvas.height - pf.y_offset;
               if(this.vy>=0 && this.y+this.h >= pFloorY - 15 && this.y+this.h <= pFloorY + 15 && this.x+this.w > real_x && this.x < real_x+pf.w){
                   this.y = pFloorY-this.h; this.vy=0; isGEnemy=true;
               }
            });
        }
        
        if(this.isAggro && intersect(this,pl) && pl.iFrames <= 0){
             pl.hp -= (this.ty === 'boss' || this.ty === 'tank') ? 22 : 12; 
             pl.vx = dx<0 ? 12 : -12; pl.vy = -8; pl.iFrames = 45; doShake(2.5); this.vx *= 0; 
        }
    }
    draw(){
        ctx.fillStyle = this.col; ctx.fillRect(this.x,this.y,this.w,this.h);
        if(this.ty==='tank') { ctx.fillStyle='black'; ctx.fillRect(this.x+5,this.y+5, this.w-10, 10); } 
        if(this.ty==='ninja'){ ctx.fillStyle='red'; ctx.fillRect(this.x, this.y+8, this.w, 5); } 
        if(this.ty==='summoner') { ctx.fillStyle='cyan'; ctx.beginPath(); ctx.arc(this.x+20,this.y-10,8,0,Math.PI*2); ctx.fill();} 
        ctx.fillStyle='#111'; ctx.fillRect(this.x, this.y-10, this.w, 5); ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.maxHp), 5);
        if(!this.isAggro) { ctx.fillStyle = 'white'; ctx.fillText("Zzz", this.x+10, this.y-20); } else { ctx.fillStyle='white'; let fw = pl.x > this.x ? this.w-12 : 4;  ctx.fillRect(this.x+fw, this.y+8, 8,8); ctx.fillStyle='black'; ctx.fillRect(this.x+fw+2, this.y+10,4,4); }
    }
}

class CloverChest {
    constructor(x) { this.x = x; this.y = canvas.height - 80 - 80; this.w = 80; this.h = 80; this.hp = 500; this.maxHp = 500; }
    draw() {
        ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.strokeStyle = '#f1c40f'; ctx.lineWidth=5; ctx.strokeRect(this.x,this.y,this.w,this.h);
        ctx.fillStyle = '#fff'; ctx.font="20px Arial"; ctx.fillText("CLOVER", this.x+5, this.y-20);
        ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.maxHp), 5);
    }
}

function makeFX(x,y,qty,col,mode) { for(let i=0;i<qty;i++) fx.push({ x:x, y:y, vx:(Math.random()-0.5)*(mode==='boom'?12:4), vy:(mode==='beam')?-(Math.random()*6): (Math.random()-0.5)*(mode==='boom'?12:4), col:col, l: (mode==='spark')?15:25, s: (mode==='boom')?Math.random()*6+4 : 3}); }

function loadStageArea(stageNum) {
    currentMap = MAPS[stageNum > 20 ? 20 : stageNum];
    let stI = document.getElementById('stage-info'); stI.innerText = currentMap.name;
    stI.style.border = `2px solid ${currentMap.bg}`; stI.style.boxShadow = `0 0 10px ${currentMap.bg}`;

    let offset_x = (stageNum - 1) * STAGE_WIDTH;
    e_arr=[]; pr_arr=[]; drops=[]; barrier=null; pipe=null; p_pr=[];

    if(currentMap.is_boss) {
        e_arr.push(new Enemy(offset_x + 2000, 'boss'));
    } else {
        let mQ = 3 + Math.floor(stageNum/1.5); 
        for(let z=0; z<mQ; z++){
            let rTy = currentMap.enemies[Math.floor(Math.random() * currentMap.enemies.length)];
            e_arr.push(new Enemy(offset_x + 500 + (z * 350), rTy));
        }
    }
    
    // קביעת מחסום או צינור
    if(stageNum % 5 == 0 && stageNum !== 20) {
        pipe = new Pipe(stageNum * STAGE_WIDTH);
    } else if (stageNum !== 20) {
        barrier = new Barrier(stageNum * STAGE_WIDTH - 40);
    }
}

function startMission(charConfig, devMode = false) {
    p_class = charConfig;
    if(devMode) {
        globalStage = parseInt(document.getElementById('dev-stage').value);
    } else {
        globalStage = 1; 
    }
    document.getElementById('select-screen').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    pl = new Player(charConfig); 
    
    if(devMode) { pl.x = (globalStage-1)*STAGE_WIDTH + 100; pl.maxHp=999; pl.hp=999; pl.maxEn=999; pl.en=999; }
    
    loadStageArea(globalStage); 
    requestAnimationFrame(sysLoop);
}

function sysLoop() {
    if(isPaused){ requestAnimationFrame(sysLoop); return; }
    f++;
    if(pl.hp<=0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('death-screen').classList.remove('hidden'); document.getElementById('final-lvl').innerText = globalStage; return; }
    
    pl.upd();
    
    // מעבר לעולם הבא (שבירת מחסום)
    if(e_arr.length === 0) {
        if(barrier) barrier.vulnerable = true;
        
        if(!barrier && !pipe && !cloverChest) {
            if(globalStage === 20) { cloverChest = new CloverChest(globalStage * STAGE_WIDTH - 300); }
            else if(pl.x > globalStage * STAGE_WIDTH) { globalStage++; loadStageArea(globalStage); }
        }
    }

    // ציור חץ ניווט אם כולם במסך מתו
    let enemiesOnScreen = 0;
    e_arr.forEach(e => { if(Math.abs(e.x - pl.x) < canvas.width) enemiesOnScreen++; });
    navArrowOpacity = (enemiesOnScreen === 0 && (barrier || pipe || cloverChest)) ? Math.min(navArrowOpacity + 0.05, 1) : Math.max(navArrowOpacity - 0.05, 0);

    for(let i=e_arr.length-1; i>=0; i--) { 
        let e = e_arr[i]; e.upd(); 
        if(e.hp<=0) { makeFX(e.x+20,e.y+20,30,'#27ae60','boom'); drops.push(new Drop(e.x, e.y, e.ty === 'boss')); e_arr.splice(i,1); } 
    }

    if(cloverChest && cloverChest.hp <= 0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('victory-screen').classList.remove('hidden'); return; }

    for(let i=drops.length-1; i>=0; i--) { if(drops[i].upd()) drops.splice(i,1); }

    for(let i=pr_arr.length-1; i>=0; i--) { 
         let b = pr_arr[i]; b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 1, 'orange', 'spark'); 
         if(intersect({x:b.x,y:b.y,w:8,h:8}, pl)) { if (pl.iFrames <= 0) { pl.hp-=15; pl.iFrames = 45; pl.vx += b.dx > 0 ? 5 : -5; doShake(3); } pr_arr.splice(i,1); continue; }
         if(b.y>canvas.height || b.x<camX || b.x>camX+canvas.width*2) pr_arr.splice(i,1);
    }
    
    for(let i=p_pr.length-1; i>=0; i--) {
        let b = p_pr[i]; 
        if(b.tgt && b.tgt.hp>0){ let tgAng = Math.atan2((b.tgt.y+b.tgt.h/2)-b.y, (b.tgt.x+b.tgt.w/2)-b.x); b.x += Math.cos(tgAng) * b.s; b.y += Math.sin(tgAng) * b.s;
        }else{ b.x += b.dir * b.s;}
        makeFX(b.x,b.y,2, b.color, 'spark');

        let dflag = false;
        if(cloverChest && intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, cloverChest)) {
            cloverChest.hp -= b.dmg; makeFX(b.x, b.y, 8, '#2ecc71', 'boom'); dflag=true; doShake(2);
        } else if(barrier && barrier.vulnerable && intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, barrier)) {
            barrier.hp -= b.dmg; makeFX(b.x, b.y, 5, '#2ecc71', 'boom'); dflag=true; doShake(1);
            if(barrier.hp <= 0) barrier = null; // נשבר!
        } else {
            for(let j=e_arr.length-1; j>=0; j--){
                 let te = e_arr[j];
                 if(intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, te)) {
                     te.hp-=b.dmg; makeFX(b.x,b.y,8,b.color,'boom'); dflag=true; doShake((b.dmg)/20); te.vx += b.dir*6;
                     if(p_class.id === 'dark'){ pl.hp = Math.min(pl.maxHp, pl.hp+(b.dmg*0.025)); } te.isAggro = true; break;
                 }
            }
        }
        if(dflag || b.y>canvas.height || Math.abs(b.x-pl.x)>2500) {p_pr.splice(i,1);}
    }

    for(let i=fx.length-1; i>=0; i--) { fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--; if(fx[i].l<=0) fx.splice(i,1); }
    
    let cxTar = pl.x - canvas.width/2 + 100; if(cxTar<0) cxTar=0; camX += (cxTar-camX)*0.08; let cm_S_X = camX; let cm_S_Y = 0;
    if(shakeV>0) {cm_S_X+=(Math.random()-0.5)*shakeV; cm_S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.8;} if(shakeV<0.5) shakeV=0;
    
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    ctx.fillStyle='rgba(255,255,255,0.06)'; 
    for(let ds=0;ds<60;ds++) { let pxX = ((ds*319)-(camX*0.1))%canvas.width; if(pxX<0)pxX+=canvas.width; ctx.beginPath(); ctx.arc(pxX, (ds*7453)%canvas.height, 2+ds%3, 0,7); ctx.fill();}
    
    ctx.save(); ctx.translate(-cm_S_X, cm_S_Y); 
    
    ctx.fillStyle = currentMap.floor; ctx.fillRect(cm_S_X - 100, canvas.height-80, canvas.width + 400, 300);
    ctx.strokeStyle='rgba(0,0,0,0.4)'; for(let xl=cm_S_X - (cm_S_X % 120); xl < cm_S_X+canvas.width+400; xl+=120){ ctx.beginPath(); ctx.moveTo(xl,canvas.height-80); ctx.lineTo(xl, canvas.height); ctx.stroke(); }

    let offset_x = (globalStage - 1) * STAGE_WIDTH;
    currentMap.platforms.forEach(pf => {
         let real_x = pf.x + offset_x; let pY = canvas.height - pf.y_offset;
         ctx.fillStyle=currentMap.bg; ctx.shadowBlur=10; ctx.shadowColor=currentMap.floor; ctx.fillRect(real_x, pY, pf.w, pf.h); ctx.shadowBlur=0; 
         ctx.fillStyle=currentMap.floor; ctx.fillRect(real_x+3, pY+3, pf.w-6, pf.h-6); 
    });

    if(barrier) barrier.draw();
    if(pipe) pipe.draw();
    if(cloverChest) cloverChest.draw();
    drops.forEach(d => d.draw());
    pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#f39c12'; pr_arr.forEach(b=>{ctx.fillRect(b.x-4,b.y-4,8,8);});
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.beginPath(); ctx.arc(b.x,b.y,b.size,0,Math.PI*2); ctx.fill();});
    fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);}); ctx.globalAlpha=1;
    
    // ציור החץ
    if(navArrowOpacity > 0) {
        ctx.globalAlpha = navArrowOpacity;
        ctx.fillStyle = "rgba(255, 255, 255, " + (0.5 + Math.sin(f/10)*0.5) + ")";
        ctx.font = "bold 60px Arial";
        ctx.fillText("➔", pl.x + 150, canvas.height / 2);
        ctx.globalAlpha = 1.0;
    }

    ctx.restore();
    
    document.getElementById('hp-bar').style.width = Math.max(0,(pl.hp/pl.maxHp)*100)+'%';
    document.getElementById('hp-t').innerText = Math.floor(pl.hp)+"/"+pl.maxHp;
    document.getElementById('en-bar').style.width = Math.max(0,(pl.en/pl.maxEn)*100)+'%';
    document.getElementById('en-t').innerText = Math.floor(pl.en)+"/"+pl.maxEn;
    
    requestAnimationFrame(sysLoop);
}

createSelectMenu();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
