from flask import Flask, render_template_string, jsonify, request
import json
import maps9
import txt9

app = Flask(__name__)
app.secret_key = 'clover_pixel_engine_x64'

PLAYER_DATA = {"shards": 0, "max_stage_reached": 1}

@app.route('/')
def idx():
    return render_template_string(GAME_HTML, 
                                  maps_json=json.dumps(maps9.generate_maps()),
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
    <title>CLOVER - Pixel Legacy 64</title>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Rubik:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; touch-action: manipulation; }
        body { margin: 0; overflow: hidden; background: #0a0a0c; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 100; 
            background: linear-gradient(135deg, rgba(5,5,10,0.98), rgba(20,25,35,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center; overflow-y:auto;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        h1.title { font-family: 'Press Start 2P', cursive; font-size: clamp(30px, 5vw, 60px); margin:0; text-transform: uppercase;
                   background: -webkit-linear-gradient(#f1c40f, #e74c3c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(4px 4px 0 rgba(241,196,15,0.2)); text-align:center;}
        
        #dev-panel { background: rgba(255,0,0,0.2); border: 2px dashed #f1c40f; padding: 20px; border-radius: 5px; margin-bottom: 20px; display: none; }
        #dev-panel select, #dev-panel button { padding: 8px; font-size: 16px; margin: 5px; font-family: 'Press Start 2P'; cursor: pointer; }

        .info-chest { background: rgba(0,0,0,0.8); border: 4px solid #fff; border-radius: 4px; padding: 20px; max-width: 800px; margin-top: 20px; text-align: right; box-shadow: 6px 6px 0px rgba(255,255,255,0.2); }
        .info-chest h3 { color: var(--gold); margin-top: 0; font-family: 'Press Start 2P'; font-size:14px; line-height:24px;}
        .info-chest ul { list-style: square; padding: 0 20px; }
        .info-chest li { margin-bottom: 12px; font-size: 14px; font-family:'Press Start 2P'; font-size:9px; line-height:20px; }

        .char-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; width: 90%; max-width: 1200px; margin-top:20px; padding-bottom: 50px;}
        .char-card { background: #111; border: 4px solid #333; padding: 15px; border-radius: 0; cursor: pointer; text-align: center; transition: 0.1s; position: relative;}
        .char-card:hover { transform: translateY(-4px); box-shadow: 4px 4px 0 var(--card-color); border-color: white;}
        .char-card h3 { margin: 0 0 10px 0; font-family: 'Press Start 2P'; font-size:16px;}
        .char-card p.char-desc {font-family: 'Rubik'; font-size:14px;}

        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:10; display:flex; flex-direction:column; padding:20px; justify-content:space-between; }
        .glass-panel { background: rgba(0,0,0,0.6); border: 2px solid rgba(255,255,255,0.4); border-radius: 0; padding: 10px; box-shadow: 4px 4px 0 rgba(0,0,0,0.8); }
        
        .mobile-ui { position: absolute; bottom: 20px; width: 100%; left: 0; display: none; pointer-events: none; padding: 0 20px; justify-content: space-between; z-index: 50;}
        .d-pad, .action-btns { display: grid; gap: 10px; pointer-events: auto; }
        .d-pad { grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px; }
        .btn-mob { background: rgba(200,200,200,0.8); border: 4px solid #fff; color: black; font-family:'Press Start 2P'; font-size: 16px; cursor: pointer; }
        .btn-mob:active { background: white; transform: scale(0.95); }
        .action-btns { grid-template-columns: repeat(3, 50px); grid-template-rows: repeat(2, 50px); justify-content: end; }

        .top-right-controls { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; pointer-events: auto;}
        .toggle-btn { padding: 10px; font-family: 'Press Start 2P'; font-size:10px; background: #000; color: white; border: 2px solid #fff; cursor: pointer; box-shadow: 3px 3px 0 #333;}
        .toggle-btn:hover { background: #fff; color:#000; }
        
        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        .stat-bar-container { display: flex; align-items: center; margin-bottom:5px; width:300px; font-family:'Press Start 2P'; font-size:12px;}
        .stat-icon { font-weight:900; margin-left: 10px; width:40px; }
        .bar-out { background: #000; flex-grow: 1; height: 16px; overflow:hidden; border: 2px solid #fff; }
        .bar-in { height:100%; transition: width 0.1s; }
        .hp-bar { background: #e74c3c; } .en-bar { background: #3498db; }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Press Start 2P'; font-size:16px; color:#fff; text-shadow:3px 3px 0 #000;}
        .menu-btn { padding:15px; border:4px solid #fff; background:black; color:white; font-size:20px; font-family:'Press Start 2P'; cursor:pointer; margin-top:20px; transition:0.1s; max-width: 90vw; text-shadow: 2px 2px #555;}
        .menu-btn:hover { background:#fff; color:#000; box-shadow:6px 6px 0px var(--gold); text-shadow:none;}

        kbd { color: var(--gold); border-bottom: 2px solid; padding-bottom:1px; }
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    <div id="dev-panel">
        <h2 id="t-dev-title" style="font-family:'Press Start 2P';font-size:14px;"></h2>
        <select id="dev-stage"> <script>for(let i=1;i<=20;i++) document.write(`<option value="${i}">Stage ${i}</option>`);</script> </select>
        <button id="t-dev-btn" onclick="startMission(HEROES[0], true)"></button>
    </div>

    <h1 class="title" id="t-main-title"></h1>
    <h2 id="t-main-sub" style="margin-bottom:30px; font-family:'Press Start 2P'; font-size:14px; color:var(--gold);"></h2>
    
    <div class="info-chest">
        <h3 id="t-htp-title"></h3> <p id="t-htp-desc" style="white-space: pre-line; margin-bottom: 20px; font-size:13px;"></p>
        <h3 id="t-ctrl-title"></h3> <ul id="t-ctrl-list"></ul>
    </div>
    <div class="char-grid" id="roster"></div>
</div>

<div id="pause-screen" class="screen hidden" style="z-index:9000; background:rgba(0,0,0,0.85);">
    <h1 class="title" id="t-pause" style="margin-bottom: 40px; font-size:30px;"></h1>
    <button class="menu-btn" onclick="togglePause()" id="btn-resume"></button>
    <button class="menu-btn" onclick="location.reload()" id="btn-restart" style="border-color:#e74c3c; color:#e74c3c;"></button>
</div>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="glass-panel" style="direction: ltr; box-shadow:none; background:none; border:none;">
            <div class="stat-bar-container"><span class="stat-icon" style="color:#e74c3c;">HP</span>
                <div class="bar-out"><div class="bar-in hp-bar" id="hp-bar"></div></div> <span id="hp-t" style="margin-left:10px;"></span>
            </div>
            <div class="stat-bar-container"><span class="stat-icon" style="color:#3498db;">EN</span>
                <div class="bar-out"><div class="bar-in en-bar" id="en-bar"></div></div> <span id="en-t" style="margin-left:10px;"></span>
            </div>
        </div>
        
        <div class="glass-panel stage-title" id="stage-info">...</div>
        
        <div class="top-right-controls">
             <button class="toggle-btn" id="t-mobile-toggle" onclick="toggleMobileUI()"></button>
             <button class="toggle-btn" onclick="togglePause()">START / PAUSE</button>
        </div>
    </div>
    
    <div class="mobile-ui" id="mob-ui">
        <div class="d-pad">
            <div></div><button class="btn-mob" ontouchstart="mk('KeyW')" ontouchend="rk('KeyW')">W</button><div></div>
            <button class="btn-mob" ontouchstart="mk('KeyA')" ontouchend="rk('KeyA')">A</button><button class="btn-mob" ontouchstart="mk('KeyS')" ontouchend="rk('KeyS')">S</button><button class="btn-mob" ontouchstart="mk('KeyD')" ontouchend="rk('KeyD')">D</button>
        </div>
        <div class="action-btns">
            <button class="btn-mob" ontouchstart="mk('KeyH')" ontouchend="rk('KeyH')">H</button><button class="btn-mob" ontouchstart="mk('KeyJ')" ontouchend="rk('KeyJ')">J</button><button class="btn-mob" ontouchstart="mk('KeyK')" ontouchend="rk('KeyK')">K</button>
            <button class="btn-mob" ontouchstart="mk('KeyU')" ontouchend="rk('KeyU')">U</button><button class="btn-mob" ontouchstart="mk('KeyI')" ontouchend="rk('KeyI')">I</button><button class="btn-mob" ontouchstart="mk('KeyY')" ontouchend="rk('KeyY')" style="background:var(--gold);color:black;">Y</button>
        </div>
    </div>
</div>

<div id="death-screen" class="screen hidden" style="z-index:9500; background:#0a0a0c;">
    <h1 class="title" id="t-death" style="color:#c0392b; font-size:40px; filter:none; -webkit-text-fill-color:#c0392b;"></h1>
    <h2 style="font-family:'Press Start 2P'; font-size:16px; line-height:30px;"><span id="t-death-sub"></span><br><span id="final-lvl" style="color:var(--gold); font-size:40px;"></span> </h2>
    <button class="menu-btn" onclick="location.reload()" id="btn-retry" style="border-color:#e74c3c; color:#e74c3c;"></button>
</div>

<div id="victory-screen" class="screen hidden" style="z-index:9600; background: #001a0b;">
    <h1 class="title" id="t-vic" style="color:#2ecc71; text-shadow: 4px 4px 0px #000; -webkit-text-fill-color:#2ecc71;"></h1>
    <h2 id="t-vic-sub" style="font-family:'Press Start 2P'; font-size:12px; margin:40px 0;"></h2>
    <button class="menu-btn" onclick="location.href='/'" id="btn-home" style="border-color:#2ecc71; color:#2ecc71;"></button>
</div>

<script>
const MAPS = {{ maps_json | safe }}; const TEXTS = {{ texts | safe }}; const HERO_TEXTS = {{ heroes_texts | safe }};

// Load localized Strings
['t-main-title', 't-main-sub', 't-htp-title', 't-htp-desc', 't-ctrl-title', 't-pause', 'btn-resume', 'btn-restart', 't-death', 't-death-sub', 'btn-retry', 't-vic', 't-vic-sub', 'btn-home', 't-mobile-toggle', 't-dev-title', 't-dev-btn'].forEach(id => { let p = id.replace(/-/g, '_'); if(TEXTS[p]) document.getElementById(id).innerText = TEXTS[p]; else if (id==='t-main-sub') document.getElementById(id).innerText=TEXTS.subtitle_main; else document.getElementById(id).innerText = TEXTS[id.split('-').pop() + "_title"] || id; });

let clist = ""; TEXTS.controls_list.forEach(c => clist += `<li>${c}</li>`); document.getElementById('t-ctrl-list').innerHTML = clist;
if(new URLSearchParams(window.location.search).get('x') === 'v') { document.getElementById('dev-panel').style.display = 'block'; }

// PIXEL ENGINE: Grids defined in rows of characters. (scaled to approx 64px width usually)
const ASSETS = {
   hero: [ ".00000..", "0011100.", "02233200", ".011110.", "00111000", ".00100..", "00...00."], // Generic Base body
   heroC:[ "........", ".00000..", "00223200", ".001100.", "00...00."], // Crouching frame
   skel: [ "..000...", ".01.10..", ".01110..", "..010...", ".01110..", "..0.0..." ], // Standard skull body (melee/shooter)
   jumper: ["........","..010...",".01110..", "0100010."], // low fat thing
   tank:   [ ".00000..", "0111110.", "0140410.", "0111110.", "0101010.", ".01110..", "010.010."], // Big chonky boi
   ninja:  [ ".......0", "....0000", "...04440", "..010010", "..00000."], // fast slicey
   ghost:  [ ".01110..", "0110110.", "0111110.", "0.1.1.0.", "........"], // see-through trailing edges
   miner:  [ "........", "........", "0100010.", "0110110.", ".00100.."], // pops out. (Wait animation: floor debris)
   boss:   [ "000..000", ".040040.", ".004400.", ".044440.", "0.0000.0", ".00..00."], // Massive King Overlord Scale (drawn 2-3x bigger!)
   boss_mad:[ "004..400", ".444444.", ".400004.", ".400004.", "0.4004.0", ".04..40."] // Anger state 
};

function rSprite(ctx, src, x, y, widthScale, facing, C1, C2, extra_y_shift = 0) {
    let raw = ASSETS[src] || ASSETS.skel; 
    let rowNum = raw.length; let colNum = raw[0].length;
    let s_h = (65 / rowNum); let s_w = widthScale / colNum; 
    // Pixel palette map (Colors extracted contextually! Very efficient generic approach)
    let p_c = { '.': null, '0':'#111', '1':C1, '2':C2, '3':'#fff', '4':'#e74c3c' }; 

    ctx.save();
    let ypos = y + extra_y_shift + (src === 'heroC' ? 25 : 0);
    ctx.translate(x + (facing === -1 ? widthScale : 0), ypos); 
    ctx.scale(facing, 1);
    for(let r=0; r<rowNum; r++){
        for(let c=0; c<colNum; c++){
             let char = raw[r][c]; if(!p_c[char]) continue;
             ctx.fillStyle = p_c[char];
             ctx.fillRect(c*s_w, r*s_h, s_w+0.5, s_h+0.5); // Add 0.5 bleeding to fix sub-pixel grid gaps
        }
    }
    ctx.restore();
}

const activeKeys = {};
window.addEventListener('keydown', e => { if(e.code==='Space') e.preventDefault(); if(e.code === 'KeyP' || e.code === 'Escape') togglePause(); activeKeys[e.code]=true; });
window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; }

function mk(c) { activeKeys[c] = true; } function rk(c) { activeKeys[c] = false; }
let isMobileUI = false; function toggleMobileUI() { isMobileUI = !isMobileUI; document.getElementById('mob-ui').style.display = isMobileUI ? 'flex' : 'none'; }

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
        let htxt = HERO_TEXTS[h.id]; let div = document.createElement('div');
        div.className = 'char-card'; div.style.setProperty('--card-color', h.col);
        div.innerHTML = `<h3 style="color:${h.col};">${htxt.name}</h3><p class="char-desc">${htxt.desc}</p>`;
        div.onclick = () => { startMission(h, false); }; box.appendChild(div);
    });
}

const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }); window.dispatchEvent(new Event('resize'));

const STAGE_WIDTH = 3000;
let p_class = null; let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[], drops=[];
let currentMap = MAPS[1]; let globalStage = 1; let f=0; let shakeV=0, camX=0;
let isPaused = false, barrier = null, pipe = null, cloverChest = null, navArrowOpacity = 0;

function doShake(amt){shakeV=amt*4;} 
function togglePause() {
    if(!pl || pl.hp<=0 || globalStage>20) return; 
    isPaused = !isPaused; document.getElementById('pause-screen').classList.toggle('hidden', !isPaused);
    if(!isPaused) { for(let key in activeKeys) activeKeys[key] = false; }
}

class Barrier {
    constructor(x) { this.x = x; this.y = 0; this.w = 40; this.h = canvas.height; this.hp = 200; this.maxHp=200; this.vulnerable = false; }
    draw() {
        ctx.fillStyle = this.vulnerable ? 'rgba(46, 204, 113, 0.5)' : 'rgba(231, 76, 60, 0.5)';
        ctx.fillRect(this.x, this.y, this.w, this.h);
        for(let py=0; py<canvas.height; py+=30) { ctx.fillStyle=(this.vulnerable && f%2===0)?'#2ecc71':'#e74c3c'; ctx.fillRect(this.x + 10, py+(f*2)%30, 20, 15); }
        if(this.vulnerable) { ctx.fillStyle = 'red'; ctx.fillRect(this.x-10, canvas.height/2, 60, 10); ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, canvas.height/2, 60*(this.hp/this.maxHp), 10); }
    }
}

class Pipe {
    constructor(x) { this.w = 100; this.h = 100; this.x = x - this.w - 20; this.y = canvas.height - 80 - this.h; }
    draw() {
        ctx.fillStyle = '#1e8449'; ctx.fillRect(this.x, this.y, this.w, this.h); ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, this.y, this.w+20, 40);
        ctx.fillStyle='rgba(255,255,255,0.2)'; ctx.fillRect(this.x+this.w-30, this.y+40, 10, this.h);
        ctx.fillStyle = 'white'; ctx.font="20px 'Press Start 2P'"; ctx.fillText("↓S", this.x+15, this.y-25);
    }
}

class Drop {
    constructor(x, y, isBoss) { this.x = x; this.y = y; this.w = 20; this.h = 20; this.vy = -5; this.isBoss = isBoss; }
    upd() {
        this.vy += 0.5; this.y += this.vy; let flY = canvas.height-80; if(this.y+this.h > flY) { this.y = flY-this.h; this.vy = 0; }
        if(intersect(this, pl)) {
            if(this.isBoss) { pl.maxHp += 40; pl.maxEn += 40; pl.hp = pl.maxHp; pl.en = pl.maxEn; makeFX(this.x, this.y, 40, '#f1c40f', 'spark'); } 
            else { pl.hp = Math.min(pl.hp + 25, pl.maxHp); makeFX(this.x, this.y, 10, '#2ecc71', 'spark'); }
            return true; 
        } return false;
    }
    draw() {
        ctx.fillStyle = this.isBoss ? '#f1c40f' : '#2ecc71'; ctx.fillRect(this.x, this.y, this.w, this.h);
        ctx.fillStyle = 'white'; ctx.fillText(this.isBoss?"!":"+", this.x+4, this.y+15);
    }
}

class Player {
    constructor(c){
        this.w=40; this.h=65; this.x=100; this.y=0; this.vx=0; this.vy=0;
        this.c = c; this.maxHp=c.maxHp; this.hp=this.maxHp; this.maxEn=c.maxEn; this.en=this.maxEn;
        this.facing = 1; this.grounded = false; this.target = null;
        this.lockKeyTriggered = false; this.atkWait = {}; this.jCount = 0;
        this.iFrames = 0; this.chargeI = 0; this.crouchFlag = false;
    }

    upd() {
        if(this.hp<=0) return;
        this.hp = Math.min(this.hp + this.c.hpRegen, this.maxHp);
        if(this.iFrames > 0) this.iFrames--;

        let isCrouch = kd('KeyS') || kd('ArrowDown');
        let isSprint = kd('ShiftLeft') || kd('ShiftRight');
        let chrgU = kd('KeyU'); let chrgI = kd('KeyI');

        if(isCrouch) { if(!this.crouchFlag) { this.y += 25; this.h = 40; this.crouchFlag = true;} 
        } else { if(this.crouchFlag) { this.y -= 25; this.h = 65; this.crouchFlag = false;} }

        if(chrgI) {
            this.chargeI = Math.min(this.chargeI + 2.5, 200); makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'spark');
        } else if (this.chargeI > 0) {
            let dmg = this.chargeI * 2.5 * this.c.dmgMult; let size = (this.chargeI / 2.5);
            p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+20, dir: this.facing, s:30, dmg:dmg, size: size, color: this.c.pCol, tgt: this.target, shock:true });
            this.vx -= (this.chargeI/15)*this.facing; this.chargeI = 0; doShake(8);
        }

        let applySpeed = this.c.speed;
        if(isSprint) applySpeed *= 1.8;
        if(chrgU || chrgI || isCrouch) applySpeed *= 0.3; 
        
        if(kd('KeyA')){ this.vx-=applySpeed; this.facing=-1; }
        if(kd('KeyD')){ this.vx+=applySpeed; this.facing= 1; }
        
        if((kd('KeyW') || kd('Space')) && !isCrouch) {
            if(!this.jHold) { if(this.jCount < 2) { this.vy = -this.c.jump; this.jCount++; makeFX(this.x+this.w/2, this.y+this.h, 12, '#fff', 'spark'); } this.jHold = true; }
        } else { this.jHold=false;}

        if(chrgU) { this.en = Math.min(this.en + 1.2, this.maxEn); makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'beam');
        } else if (!chrgI) {
            this.sHand('KeyH', '1', 8 * this.c.enCostMult, 12 * this.c.dmgMult, 10);
            this.sHand('KeyJ', '2', 20 * this.c.enCostMult, 30 * this.c.dmgMult, 20);
            this.sHand('KeyK', '3', 45 * this.c.enCostMult, 70 * this.c.dmgMult, 35);
            
            if(kd('KeyY') && !this.atkWait['KeyY']) {
                if(this.en >= this.maxEn) {
                    this.en = 0; // Wipe
                    p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+20, dir: this.facing, s:12, dmg:600*this.c.dmgMult, size: 75, color: '#fff', tgt: this.target, shock:true });
                    this.vx -= 20*this.facing; doShake(12);
                }
                this.atkWait['KeyY'] = true;
            } else if(!kd('KeyY')) { this.atkWait['KeyY'] = false; }
        }

        if(kd('KeyE')){ if(!this.lockKeyTriggered){ this.swLock(); this.lockKeyTriggered=true;} } else {this.lockKeyTriggered=false;}
        if(this.target && this.target.hp <= 0){ this.target = null; this.findBestTarget(); }

        this.vy += 0.6; this.x+=this.vx; this.y+=this.vy; this.vx *= 0.8;
        let leftBnd = (globalStage - 1) * STAGE_WIDTH; if(this.x < leftBnd + 10) { this.x=leftBnd + 10; this.vx=0;} 
        let rightBnd = globalStage * STAGE_WIDTH; if(barrier && this.x + this.w > barrier.x) { this.x = barrier.x - this.w; this.vx = 0; }

        this.physicsFloor();

        if(pipe && intersect(this, pipe) && isCrouch && this.grounded && !this.warp) {
            this.warp=true; pl.iFrames=100; // Warp setup!
            setTimeout(()=>{
                this.hp = Math.min(this.hp + (this.maxHp*0.5), this.maxHp);
                globalStage++; loadStageArea(globalStage); this.warp=false;
            }, 600);
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

    sHand(k,t,cst,dmg,size) {
        if(kd(k)){
            if(!this.atkWait[k]){
                if(this.en >= cst) {
                    this.en -= cst; p_pr.push({ x: this.facing>0? this.x+this.w : this.x, y: this.y+15, dir: this.facing, s:22, dmg:dmg, size: size, color: this.c.pCol, tgt: this.target, shock:false });
                    this.vx -= (cst/5)*this.facing; 
                } this.atkWait[k] = true;
            }
        }else{this.atkWait[k] = false;}
    }

    swLock() { if(this.target) this.target=null; else this.findBestTarget(); }
    findBestTarget() {
        let maxDist = 1400; let trg = null; e_arr.forEach(e => { let d = Math.abs(e.x - this.x); if(d < maxDist && e.x > this.x - 400 && e.x < this.x+1000) { maxDist=d; trg=e; } });
        if(trg) { this.target=trg; doShake(1.5); }
    }

    draw() {
        ctx.save();
        if(this.iFrames > 0 && Math.floor(f / 4) % 2 === 0) ctx.globalAlpha = 0.3;
        // Breathing physics when idle 
        let yPulse = (!this.crouchFlag && this.vx*this.vx < 1 && this.grounded) ? Math.sin(f/8)*2 : 0; 
        rSprite(ctx, this.crouchFlag?'heroC':'hero', this.x, this.y, this.w, this.facing, this.c.pCol, this.c.col, yPulse);

        if(this.chargeI > 0) { ctx.beginPath(); ctx.arc(this.x+this.w/2, this.y+this.h/2, this.chargeI/2.5, 0, Math.PI*2); ctx.fillStyle = this.c.pCol; ctx.globalAlpha = 0.5; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.stroke(); }
        if(this.target){
             let rx = this.target.x + this.target.w/2; let ry = this.target.y+this.target.h/2;
             ctx.globalAlpha=1.0; ctx.strokeStyle='#ff3838'; ctx.lineWidth=2; ctx.beginPath(); ctx.moveTo(this.x+this.w/2, this.y+this.h/2); ctx.lineTo(rx,ry); ctx.stroke(); ctx.beginPath(); ctx.arc(rx,ry, 25+Math.sin(f/4)*5,0,Math.PI*2); ctx.stroke();
        }
        ctx.restore();
    }
}


class Enemy {
    constructor(x, ty) {
        this.x=x; this.ty = ty; this.isAggro = false; 
        
        // Logical Dimensions map based on ty 
        if(ty==='boss'){ this.maxHp=1000 + (globalStage*150); this.w=160; this.h=160; this.s=1.5; this.y = canvas.height-80-this.h; this.isAggro=true; }
        else if(ty==='shooter'){ this.w=40; this.h=50; this.col='#f39c12'; this.s=1.8; this.maxHp = 60 + (globalStage*15);}
        else if(ty==='jumper'){ this.w=35; this.h=45; this.col='#8e44ad'; this.s=1.5; this.maxHp=40+(globalStage*15); }  
        else if(ty==='tank'){ this.w=80; this.h=90; this.col='#7f8c8d'; this.maxHp=(120+(globalStage*30)); this.s=0.6; }
        else if(ty==='ninja'){ this.w=30; this.h=45; this.col='#00cec9'; this.maxHp=30+(globalStage*10); this.s=3.0;}
        else if(ty==='summoner'){ this.w=40; this.h=60; this.col='#341f97'; this.maxHp=50+(globalStage*10); this.s=1.5;}
        else if(ty==='ghost'){ this.w=40; this.h=50; this.maxHp=60+(globalStage*10); this.s=1; this.col='rgba(100,200,255,0.7)'; this.ignoreFloor=true;}
        else if(ty==='sniper'){ this.w=40; this.h=60; this.maxHp=80+(globalStage*15); this.s=1; this.col='#e74c3c'; this.chg=0; }
        else if(ty==='miner'){ this.w=45; this.h=45; this.maxHp=100+(globalStage*20); this.s=2; this.col='#a65c26'; this.hidden=true;}
        else { this.w=40; this.h=50; this.maxHp=60+(globalStage*10); this.s=1.8; this.col='#e74c3c';} // Melee 
        
        this.hp = this.maxHp; this.y = this.ignoreFloor? 200 : canvas.height-120;
        this.shClock = Math.random()*80 + 20; 
        this.facing = -1; // -1 Left default
    }
    
    upd() {
        let dx = pl.x - this.x; let dy = pl.y - this.y; 
        let flY = canvas.height-80;
        this.facing = dx > 0 ? 1 : -1; 
        let dtX = Math.abs(dx);
        
        // AGGRO LOGIC
        if(!this.isAggro) {
            if(dtX < (this.ty==='sniper'?1000:700)) { this.isAggro = true; } 
            else if(!this.hidden && this.ty !== 'ghost' && !this.ignoreFloor) { this.vx = Math.sin(f/30) * this.s; } 
            else { this.vx = 0;}
        }
        
        if(this.isAggro) {
            if(this.ty==='boss') {
               this.shClock--;
               // Smart Master AI Phases: 
               if(this.hp < this.maxHp/2) this.mad = true; 
               if(this.shClock <= 0 && this.vy === 0) {
                   let r = Math.random();
                   if(r < 0.3) { 
                        // The Earthquake Jump Slam!
                        this.vy = -18; this.vx = dx>0? 4:-4; this.doShockOnLand=true;
                        this.shClock = 160; 
                   } else if(r < 0.6) {
                        // Spread Bullet Hell - Stops moving!
                        this.vx=0; 
                        for(let st=-1;st<=1;st+=0.5) pr_arr.push({x:this.x+this.w/2, y:this.y+40, dx:(this.facing*5)+st*4, dy:-5-Math.abs(st*8)});
                        doShake(8); this.shClock = this.mad?90:130;
                   } else {
                        // Pincer moves or Spawns! 
                        if(e_arr.length<6){ e_arr.push(new Enemy(this.x + this.facing*200, 'jumper')); e_arr[e_arr.length-1].isAggro=true; }
                        this.shClock = 100;
                   }
               }
               // Base Chase when not slamming
               if(this.vy===0 && !this.doShockOnLand && this.shClock>30) this.vx = this.facing*(this.s + (this.mad?1:0));
               if(this.doShockOnLand && this.y+this.h >= flY) { 
                    doShake(20); this.doShockOnLand = false; // The Crash Land! 
                    // Release Floor shockwaves ! 
                    pr_arr.push({x:this.x, y:flY-10, dx:-8, dy:0, type:'shock'}); pr_arr.push({x:this.x+this.w, y:flY-10, dx:8, dy:0, type:'shock'}); 
               }
            }
            else if(this.ty === 'melee' || this.ty === 'tank'){
                if(dtX>5) this.vx = this.facing * this.s; 
            } else if(this.ty === 'ninja'){
                this.shClock--; if(this.shClock > 20) { this.vx = this.facing * this.s; } else if(this.shClock > 0) { this.vx = this.facing * 16; } else { this.shClock = Math.random()*50 + 70; } 
            } else if(this.ty === 'shooter'){
                if(dtX > 350) this.vx = this.facing * this.s; else this.vx*=0.6;
                this.shClock--; if(this.shClock<=0) { this.shClock=120; pr_arr.push({x:this.x+this.w/2, y:this.y+20, dx:this.facing*9, dy:0}); }
            } else if(this.ty === 'jumper'){
                 this.vx = this.facing * (this.s+0.2);
                 this.shClock--; if(this.shClock<=0 && this.vy===0){ this.vy = -12; this.shClock=80;} 
            } else if(this.ty === 'summoner') {
                 if(dtX < 500) { this.vx = -this.facing * this.s; } else { this.vx*=0.9; } 
                 this.shClock--;
                 if(this.shClock<=0 && e_arr.length<8) { this.shClock = 300; e_arr.push(new Enemy(this.x, 'jumper')); e_arr[e_arr.length-1].isAggro = true; makeFX(this.x+this.w/2, this.y, 15, '#c8d6e5', 'boom'); }
            } else if(this.ty === 'ghost') {
                // Flies ignoring gravity slowly homing entirely 
                let gAng = Math.atan2(dy, dx);
                this.x += Math.cos(gAng)*this.s*0.9; this.y += Math.sin(gAng)*this.s*0.9; this.vx=0;
            } else if(this.ty === 'sniper') {
                if(dtX > 600) this.vx = this.facing*this.s; else this.vx=0;
                this.chg++; 
                if(this.chg>150){ // Firing logic is drawn via Draw! 
                     pr_arr.push({x:this.x+this.w/2, y:this.y+20, dx:this.facing*25, dy:0, c:'red'}); this.chg=0; doShake(4);
                }
            } else if(this.ty === 'miner') {
                if(this.hidden) {
                   this.vx = 0; this.y = flY + 10;
                   if(dtX < 150) { this.hidden = false; this.vy = -20; makeFX(this.x, flY, 30, '#555', 'boom'); }
                } else {
                   this.vx = this.facing * this.s; 
                   // Digs back in if touches ground for too long! 
                   if(this.vy === 0) { this.shClock--; if(this.shClock<=0){ this.hidden = true; this.shClock=150; } } else { this.shClock=150;}
                }
            }
        }

        // Apply World Constraints (Unless Ghost or Miner burrowed)
        if(!this.ignoreFloor && !this.hidden) {
           this.vy+=0.6; this.y+=this.vy; this.x+=this.vx;
           let leftBnd = (globalStage - 1) * STAGE_WIDTH;
           if(this.x < leftBnd + 10) { this.x=leftBnd + 10; this.vx *= -1; } 
           if(barrier && this.x + this.w > barrier.x) { this.x = barrier.x - this.w; this.vx *= -1; }
           
           let isGEnemy=false; if(this.y+this.h >= flY) { this.y=flY-this.h; this.vy=0; isGEnemy=true;}
           if(!isGEnemy && this.ty !== 'jumper' && this.ty!=='boss'){ 
               let offset_x = (globalStage - 1) * STAGE_WIDTH;
               currentMap.platforms.forEach(pf => {
                  let real_x = pf.x + offset_x; let pFloorY = canvas.height - pf.y_offset;
                  if(this.vy>=0 && this.y+this.h >= pFloorY - 15 && this.y+this.h <= pFloorY + 15 && this.x+this.w > real_x && this.x < real_x+pf.w){
                      this.y = pFloorY-this.h; this.vy=0; isGEnemy=true;
                  }
               });
           }
        }

        if(this.isAggro && intersect(this,pl) && pl.iFrames <= 0){
             pl.hp -= (this.ty === 'boss') ? 30 : (this.ty === 'tank')?20:12; 
             pl.vx = pl.x > this.x ? 12 : -12; pl.vy = -10; pl.iFrames = 45; doShake(3); if(!this.ignoreFloor)this.vx *= 0; 
        }
    }
    
    draw(){
        let pxTy = 'skel'; if(this.ty==='boss')pxTy=(this.mad?'boss_mad':'boss'); else if(['tank','jumper','ninja','ghost','miner'].includes(this.ty))pxTy=this.ty;
        if(this.ty==='ghost') ctx.globalAlpha=0.6 + Math.sin(f/10)*0.3;
        
        let pyMove = (this.vy===0 && Math.abs(this.vx)>1) ? (f%10>5?5:0) : 0; // Quick wobble walk cycle
        if(this.hidden) pyMove=0;

        rSprite(ctx, pxTy, this.x, this.y, this.w, this.facing, this.col, '#fff', pyMove);
        ctx.globalAlpha = 1;

        if(this.ty === 'sniper' && this.chg>50) {
            ctx.strokeStyle = `rgba(255, 0, 0, ${this.chg/150})`; ctx.lineWidth=3; 
            ctx.beginPath(); ctx.moveTo(this.x+(this.facing>0?this.w:0), this.y+20); ctx.lineTo(this.x+(this.facing*2000), this.y+20); ctx.stroke();
        }

        // Draw HUD HP bars only if damaged or boss
        if(this.hp < this.maxHp || this.ty === 'boss'){
            ctx.fillStyle='#111'; ctx.fillRect(this.x, this.y-10, this.w, 5);
            ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.maxHp), 5);
        }
        if(!this.isAggro) { ctx.fillStyle='white'; ctx.font="15px 'Press Start 2P'"; ctx.fillText("?", this.x+(this.w/2)-10, this.y-25); } 
    }
}

class CloverChest {
    constructor(x) { this.x = x; this.w = 120; this.h = 100; this.y = canvas.height - 80 - this.h; this.hp = 800; this.maxHp = 800; }
    draw() {
        ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x, this.y, this.w, this.h); ctx.strokeStyle = '#fff'; ctx.lineWidth=8; ctx.strokeRect(this.x,this.y,this.w,this.h);
        ctx.fillStyle = 'black'; ctx.fillRect(this.x+20, this.y+40, this.w-40, 15);
        ctx.fillStyle = '#f1c40f'; ctx.fillRect(this.x+40, this.y+35, 40, 25);
        ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-15, this.w*(this.hp/this.maxHp), 10);
    }
}

function makeFX(x,y,qty,col,mode) { for(let i=0;i<qty;i++) fx.push({ x:x, y:y, vx:(Math.random()-0.5)*(mode==='boom'?14:6), vy:(mode==='beam')?-(Math.random()*6): (Math.random()-0.5)*(mode==='boom'?14:6), col:col, l: (mode==='spark')?20:30, s: (mode==='boom')?Math.random()*8+6 : 5}); }

function loadStageArea(stageNum) {
    currentMap = MAPS[stageNum > 20 ? 20 : stageNum];
    let stI = document.getElementById('stage-info'); stI.innerText = currentMap.name; stI.style.borderBottom = `5px solid ${currentMap.bg}`; 

    let offset_x = (stageNum - 1) * STAGE_WIDTH;
    e_arr=[]; pr_arr=[]; drops=[]; barrier=null; pipe=null; p_pr=[];
    if(currentMap.is_boss) {
        e_arr.push(new Enemy(offset_x + 2200, 'boss'));
    } else {
        let mQ = 3 + Math.floor(stageNum*1.2); 
        for(let z=0; z<mQ; z++){ let rTy = currentMap.enemies[Math.floor(Math.random() * currentMap.enemies.length)]; e_arr.push(new Enemy(offset_x + 500 + (z * 200), rTy)); }
    }
    if(stageNum % 5 == 0 && stageNum !== 20) { pipe = new Pipe(stageNum * STAGE_WIDTH); } else if (stageNum !== 20) { barrier = new Barrier(stageNum * STAGE_WIDTH - 60); }
}

function startMission(charConfig, devMode = false) {
    p_class = charConfig; globalStage = devMode ? parseInt(document.getElementById('dev-stage').value) : 1; 
    document.getElementById('select-screen').classList.add('hidden'); document.getElementById('ui-layer').classList.remove('hidden');
    pl = new Player(charConfig); if(devMode) { pl.x = (globalStage-1)*STAGE_WIDTH + 100; pl.maxHp=1000; pl.hp=1000; pl.maxEn=1000; pl.en=1000; }
    loadStageArea(globalStage); requestAnimationFrame(sysLoop);
}

function sysLoop() {
    if(isPaused){ requestAnimationFrame(sysLoop); return; }
    f++;
    if(pl.hp<=0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('death-screen').classList.remove('hidden'); document.getElementById('final-lvl').innerText = globalStage; return; }
    pl.upd();
    
    if(e_arr.length === 0) {
        if(barrier) barrier.vulnerable = true;
        if(!barrier && !pipe && !cloverChest) { if(globalStage === 20) { cloverChest = new CloverChest(globalStage * STAGE_WIDTH - 400); } else if(pl.x > globalStage * STAGE_WIDTH) { globalStage++; loadStageArea(globalStage); } }
    }
    let eos = 0; e_arr.forEach(e => { if(Math.abs(e.x - pl.x) < canvas.width*1.5) eos++; });
    navArrowOpacity = (eos === 0 && (barrier || pipe || cloverChest)) ? Math.min(navArrowOpacity + 0.05, 1) : Math.max(navArrowOpacity - 0.05, 0);

    for(let i=e_arr.length-1; i>=0; i--) { 
        let e = e_arr[i]; e.upd(); 
        if(e.hp<=0) { makeFX(e.x+e.w/2,e.y+e.h/2,40,'#ff0055','boom'); drops.push(new Drop(e.x, e.y, e.ty === 'boss')); e_arr.splice(i,1); } 
    }
    if(cloverChest && cloverChest.hp <= 0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('victory-screen').classList.remove('hidden'); return; }
    for(let i=drops.length-1; i>=0; i--) { if(drops[i].upd()) drops.splice(i,1); }
    for(let i=pr_arr.length-1; i>=0; i--) { 
         let b = pr_arr[i]; b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 2, b.c || 'orange', 'spark'); 
         let bxW = b.type==='shock'?40:15;
         if(intersect({x:b.x,y:b.y,w:bxW,h:bxW}, pl)) { if (pl.iFrames <= 0) { pl.hp-= b.type==='shock'?30:15; pl.iFrames=50; pl.vx+= b.dx>0?8:-8; pl.vy=-10; doShake(6); } pr_arr.splice(i,1); continue; }
         if(b.y>canvas.height || b.x<camX || b.x>camX+canvas.width*2) pr_arr.splice(i,1);
    }
    
    for(let i=p_pr.length-1; i>=0; i--) {
        let b = p_pr[i]; 
        if(b.tgt && b.tgt.hp>0){ let tgAng = Math.atan2((b.tgt.y+b.tgt.h/2)-b.y, (b.tgt.x+b.tgt.w/2)-b.x); b.x += Math.cos(tgAng) * b.s; b.y += Math.sin(tgAng) * b.s;
        }else{ b.x += b.dir * b.s;} makeFX(b.x,b.y,2, b.color, 'spark');

        let dflag = false;
        if(cloverChest && intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, cloverChest)) { cloverChest.hp -= b.dmg; makeFX(b.x, b.y, 10, '#fff', 'boom'); dflag=true; doShake(4); } 
        else if(barrier && barrier.vulnerable && intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, barrier)) { barrier.hp -= b.dmg; makeFX(b.x, b.y, 10, '#fff', 'boom'); dflag=true; doShake(3); if(barrier.hp <= 0){barrier = null; doShake(15);} } 
        else {
            for(let j=e_arr.length-1; j>=0; j--){ let te = e_arr[j];
                 if(intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, te)) { te.hp-=b.dmg; makeFX(b.x,b.y,12,b.color,'boom'); dflag=true; doShake(b.shock?10:2); te.vx += b.dir* (b.shock?15:5);
                     if(p_class.id === 'dark'){ pl.hp = Math.min(pl.maxHp, pl.hp+(b.dmg*0.035)); } te.isAggro = true; break;
                 }
            }
        }
        if(dflag || b.y>canvas.height || Math.abs(b.x-pl.x)>3000) {p_pr.splice(i,1);}
    }
    for(let i=fx.length-1; i>=0; i--) { fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--; if(fx[i].l<=0) fx.splice(i,1); }
    
    let cxTar = pl.x - canvas.width/2 + 100; if(cxTar<0) cxTar=0; camX += (cxTar-camX)*0.08; let cm_S_X = camX; let cm_S_Y = 0;
    if(shakeV>0) {cm_S_X+=(Math.random()-0.5)*shakeV; cm_S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.8;} if(shakeV<0.5) shakeV=0;
    
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    ctx.fillStyle='rgba(255,255,255,0.06)'; for(let ds=0;ds<60;ds++) { let pxX = ((ds*319)-(camX*0.1))%canvas.width; if(pxX<0)pxX+=canvas.width; ctx.fillRect(pxX, (ds*7453)%canvas.height, 4, 4); }
    
    ctx.save(); ctx.translate(-cm_S_X, cm_S_Y); 
    
    ctx.fillStyle = currentMap.floor; ctx.fillRect(cm_S_X - 100, canvas.height-80, canvas.width + 400, 300);
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=4; for(let xl=cm_S_X - (cm_S_X % 150); xl < cm_S_X+canvas.width+400; xl+=150){ ctx.beginPath(); ctx.moveTo(xl,canvas.height-80); ctx.lineTo(xl, canvas.height); ctx.stroke(); }

    if(barrier) barrier.draw(); let offset_x = (globalStage - 1) * STAGE_WIDTH;
    currentMap.platforms.forEach(pf => { let real_x = pf.x + offset_x; let pY = canvas.height - pf.y_offset;
         ctx.fillStyle=currentMap.bg; ctx.fillRect(real_x, pY, pf.w, pf.h);
         ctx.fillStyle=currentMap.floor; ctx.fillRect(real_x+5, pY+5, pf.w-10, pf.h-10); 
    });

    if(pipe) pipe.draw(); if(cloverChest) cloverChest.draw(); drops.forEach(d => d.draw()); pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#f1c40f'; pr_arr.forEach(b=>{ if(b.type==='shock') ctx.fillRect(b.x, b.y-20, 20,40); else ctx.fillRect(b.x-5,b.y-5,10,10);});
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.fillRect(b.x-b.size/2,b.y-b.size/2,b.size,b.size);}); fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);}); ctx.globalAlpha=1;
    
    if(navArrowOpacity > 0) { ctx.globalAlpha = navArrowOpacity; ctx.fillStyle = "rgba(255, 255, 255, " + (0.5 + Math.sin(f/8)*0.5) + ")"; ctx.font = "bold 60px 'Press Start 2P'"; ctx.fillText(">", pl.x + 150, canvas.height / 2 - 50); ctx.globalAlpha = 1.0; }
    ctx.restore();
    
    document.getElementById('hp-bar').style.width = Math.max(0,(pl.hp/pl.maxHp)*100)+'%'; document.getElementById('hp-t').innerText = Math.floor(pl.hp)+"/"+pl.maxHp; document.getElementById('en-bar').style.width = Math.max(0,(pl.en/pl.maxEn)*100)+'%'; document.getElementById('en-t').innerText = Math.floor(pl.en)+"/"+pl.maxEn; document.getElementById('lock-hud').style.opacity = pl.target ? 1: 0;
    
    requestAnimationFrame(sysLoop);
}
createSelectMenu();
</script></body></html>
"""
if __name__ == "__main__": app.run(port=5009, debug=True)
