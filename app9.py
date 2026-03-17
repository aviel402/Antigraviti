from flask import Flask, render_template_string, jsonify, request
import json
import maps9
import txt9

app = Flask(__name__)
app.secret_key = 'clover_epic_rpg_edition'

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
    <title>CLOVER 64x BIT - Overture</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; touch-action: manipulation; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        /* CRT Effect Overlays */
        body::before { content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0; 
                       background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.2) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); z-index: 200; background-size: 100% 2px, 3px 100%; pointer-events: none; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 300; 
            background: linear-gradient(135deg, rgba(5,5,10,0.95), rgba(20,20,30,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center; overflow-y:auto;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        h1.title { font-family: 'Righteous', cursive; font-size: clamp(40px, 8vw, 80px); margin:0; text-transform: uppercase; letter-spacing: 2px;
                   background: -webkit-linear-gradient(#f1c40f, #e67e22); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 4px 15px rgba(241,196,15,0.6));}
        
        #dev-panel { background: rgba(255,0,0,0.2); border: 2px solid red; padding: 15px; border-radius: 10px; margin-bottom: 20px; display: none; text-align:center;}
        #dev-panel select, #dev-panel button { padding: 10px; font-size: 16px; margin: 5px; font-family: 'Rubik'; cursor:pointer;}

        .info-chest { background: rgba(0,0,0,0.7); border: 2px solid var(--gold); border-radius: 10px; padding: 20px; max-width: 800px; margin-top: 20px; text-align: right; box-shadow: inset 0 0 15px rgba(241,196,15,0.1); }
        .info-chest h3 { color: var(--gold); margin-top: 0; }
        .info-chest ul { list-style: none; padding: 0; }
        .info-chest li { margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; color:#ddd;}

        .char-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 15px; width: 95%; max-width: 1200px; margin-top:20px; padding-bottom: 50px;}
        .char-card { background: rgba(0,0,0,0.6); border: 2px solid #555; border-bottom-width: 6px; padding: 15px; border-radius: 12px; cursor: pointer; text-align: center; transition: all 0.2s; position: relative;}
        .char-card:hover { transform: translateY(-5px); border-bottom-width:2px; margin-top:4px; box-shadow: 0 0px 25px rgba(0,0,0,0.8); border-color: var(--card-color);}
        .char-card h3 { margin: 0 0 5px 0; font-family: 'Righteous'; font-size: 24px; text-transform:uppercase; text-shadow: 2px 2px #000; }
        
        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:100; display:flex; flex-direction:column; padding:20px; justify-content:space-between; }
        .glass-panel { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; border-bottom: 3px solid rgba(255,255,255,0.1); }
        
        /* Mobile System Override */
        .mobile-ui { position: absolute; bottom: 20px; width: 100%; left: 0; display: none; pointer-events: none; padding: 0 20px; justify-content: space-between; z-index: 50;}
        .d-pad, .action-btns { display: grid; gap: 10px; pointer-events: auto; }
        .d-pad { grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px; }
        .btn-mob { background: rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4); border-radius: 12px; color: white; font-weight: 900; font-size: 18px; cursor: pointer; font-family:'Righteous';}
        .btn-mob:active { background: rgba(255,255,255,0.9); color: black; transform: scale(0.9); }
        .action-btns { grid-template-columns: repeat(3, 55px); grid-template-rows: repeat(2, 55px); justify-content: end; }

        .top-right-controls { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; pointer-events: auto;}
        .toggle-btn { padding: 10px 18px; font-family: 'Righteous'; font-size: 14px; font-weight:bold; background: rgba(0,0,0,0.7); color: white; border: 2px solid #555; border-radius: 8px; cursor: pointer; transition: 0.3s; }
        .toggle-btn:hover { background: #fff; color: #000; border-color: #fff;}

        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        .stat-bar-container { display: flex; align-items: center; margin-bottom:5px; width:280px; text-shadow:1px 1px black;}
        .stat-icon { font-weight:900; margin-left: 10px; width:50px; font-family:'Righteous'; font-size: 14px; letter-spacing: 1px;}
        .bar-out { background: rgba(0,0,0,0.7); flex-grow: 1; height: 18px; border-radius: 5px; border: 2px solid rgba(255,255,255,0.5); position:relative; overflow:hidden;}
        .bar-in { height:100%; transition: width 0.1s;}
        .hp-bar { background: #e74c3c; box-shadow: inset 0 5px 0 rgba(255,255,255,0.3); }
        .en-bar { background: #3498db; box-shadow: inset 0 5px 0 rgba(255,255,255,0.3); }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Righteous'; font-size:24px; color:#fff; text-shadow:0 2px 4px rgba(0,0,0,0.8), 0 0 10px var(--gold);}
        .menu-btn { padding:15px 40px; border:2px solid #fff; border-bottom:6px solid #fff; border-radius:8px; color:white; font-size:20px; font-family:'Righteous'; font-weight:900; background:rgba(0,0,0,0.5); cursor:pointer; margin-top:20px; transition:0.2s; width: 350px; max-width: 90vw;}
        .menu-btn:hover { border-bottom-width:2px; transform:translateY(4px); background:#fff; color:#000; box-shadow:0 0 20px #fff;}
        .menu-btn:active{ background:#f1c40f;}
        
        kbd { background: #333; color: #f1c40f; padding: 2px 6px; border-radius: 4px; border-bottom: 3px solid #111; font-weight: bold; margin:0 3px;}
        #stage-alert { position: absolute; top:40%; left:50%; transform: translate(-50%, -50%); font-family:'Righteous'; font-size: 8vw; opacity:0; text-shadow: 5px 5px 0px #000, 0 0 20px var(--gold); text-align:center; z-index: 100;}
    </style>
</head>
<body>

<!-- מסך בוררים דמויי רעפים וארט צבעים ! -->
<div id="select-screen" class="screen">
    <div id="dev-panel">
        <h2 id="t-dev-title"></h2>
        <select id="dev-stage"> <script>for(let i=1;i<=20;i++) document.write(`<option value="${i}">Level Start -> Stage ${i}</option>`);</script> </select>
        <button id="t-dev-btn" onclick="startMission(HEROES[0], true)"></button>
    </div>

    <h1 class="title" id="t-main-title"></h1><h2 id="t-main-sub" style="margin-top:-10px; color:var(--gold); font-style:italic;"></h2>
    
    <div class="info-chest">
        <h3 id="t-htp-title"></h3><p id="t-htp-desc" style="white-space: pre-line; line-height:1.5;"></p>
        <h3 id="t-ctrl-title"></h3><ul id="t-ctrl-list" style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;"></ul>
    </div>
    <div class="char-grid" id="roster"></div>
</div>

<div id="pause-screen" class="screen hidden" style="background: rgba(10, 15, 25, 0.95);">
    <h1 class="title" id="t-pause" style="filter: hue-rotate(180deg); margin-bottom: 20px; letter-spacing:5px;"></h1>
    <button class="menu-btn" onclick="togglePause()" id="btn-resume"></button>
    <button class="menu-btn" onclick="location.reload()" id="btn-restart" style="color:#e74c3c; border-color:#e74c3c; background: rgba(50,0,0,0.5);"></button>
</div>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="glass-panel" style="direction: ltr; min-width: 320px;">
            <div class="stat-bar-container"><span class="stat-icon" style="color:#e74c3c;">HP</span>
                <div class="bar-out"><div class="bar-in hp-bar" id="hp-bar"></div></div> <span id="hp-t" style="color:#aaa;font-size:10px;margin-left:5px;"></span></div>
            <div class="stat-bar-container"><span class="stat-icon" style="color:#3498db;">EN</span>
                <div class="bar-out"><div class="bar-in en-bar" id="en-bar"></div></div> <span id="en-t" style="color:#aaa;font-size:10px;margin-left:5px;"></span></div>
        </div>
        <div class="glass-panel stage-title" id="stage-info">...</div>
        
        <div class="top-right-controls">
             <button class="toggle-btn" id="t-mobile-toggle" onclick="toggleMobileUI()" style="border-color:#3498db;"></button>
             <button class="toggle-btn" onclick="togglePause()">⏸ PAUSE <kbd>ESC</kbd></button>
        </div>
    </div>
    
    <div id="stage-alert"></div>
    
    <div class="mobile-ui" id="mob-ui">
        <div class="d-pad"><div></div><button class="btn-mob" ontouchstart="mk('KeyW')" ontouchend="rk('KeyW')">W</button><div></div>
            <button class="btn-mob" ontouchstart="mk('KeyA')" ontouchend="rk('KeyA')">A</button> <button class="btn-mob" ontouchstart="mk('KeyS')" ontouchend="rk('KeyS')">S</button> <button class="btn-mob" ontouchstart="mk('KeyD')" ontouchend="rk('KeyD')">D</button></div>
        <div class="action-btns"><button class="btn-mob" ontouchstart="mk('KeyH')" ontouchend="rk('KeyH')">H</button> <button class="btn-mob" ontouchstart="mk('KeyJ')" ontouchend="rk('KeyJ')">J</button> <button class="btn-mob" ontouchstart="mk('KeyK')" ontouchend="rk('KeyK')">K</button> <button class="btn-mob" style="color:#3498db;" ontouchstart="mk('KeyU')" ontouchend="rk('KeyU')">U</button> <button class="btn-mob" ontouchstart="mk('KeyI')" ontouchend="rk('KeyI')">I</button> <button class="btn-mob" style="color:var(--gold);" ontouchstart="mk('KeyY')" ontouchend="rk('KeyY')">Y</button></div>
    </div>
</div>

<div id="death-screen" class="screen hidden" style="z-index:400; background:rgba(40,10,10,0.96)">
    <h1 class="title" id="t-death" style="color:#e74c3c; filter:drop-shadow(0 0 10px red);"></h1>
    <h2 style="font-size:26px;"><span id="t-death-sub"></span> <span id="final-lvl" style="color:white; padding: 4px 10px; background:#e74c3c; border-radius:5px;"></span> </h2>
    <button class="menu-btn" onclick="location.reload()" id="btn-retry" style="background:#e74c3c; color:#fff; border-color:#e74c3c; margin-top: 40px;"></button>
</div>

<div id="victory-screen" class="screen hidden" style="z-index:500; background: rgba(10,50,20,0.98);">
    <h1 class="title" id="t-vic" style="color:#2ecc71; text-shadow: 0 0 30px #2ecc71;"></h1>
    <h2 id="t-vic-sub" style="font-size:18px; line-height:1.6; max-width: 600px; text-align:center;"></h2>
    <button class="menu-btn" onclick="location.href='/'" id="btn-home" style="background:#2ecc71; border-color:#2ecc71; color:#000; font-weight:900; margin-top:50px;"></button>
</div>

<script>
// --- CORE AND PAYLOAD EXTRACTION ---
const MAPS = {{ maps_json | safe }}; const TEXTS = {{ texts | safe }}; const HERO_TEXTS = {{ heroes_texts | safe }};

// Set DOM Localizations using parsed variables
document.getElementById('t-main-title').innerText = TEXTS.title_main; document.getElementById('t-main-sub').innerText = TEXTS.subtitle_main; document.getElementById('t-htp-title').innerText = TEXTS.how_to_play_title; document.getElementById('t-htp-desc').innerText = TEXTS.how_to_play_desc; document.getElementById('t-ctrl-title').innerText = TEXTS.controls_title; document.getElementById('t-pause').innerText = TEXTS.pause_title; document.getElementById('btn-resume').innerText = TEXTS.btn_resume; document.getElementById('btn-restart').innerText = TEXTS.btn_restart; document.getElementById('t-death').innerText = TEXTS.death_title; document.getElementById('t-death-sub').innerText = TEXTS.death_sub; document.getElementById('btn-retry').innerText = TEXTS.btn_retry; document.getElementById('t-vic').innerText = TEXTS.victory_title; document.getElementById('t-vic-sub').innerText = TEXTS.victory_sub; document.getElementById('btn-home').innerText = TEXTS.btn_home; document.getElementById('t-mobile-toggle').innerText = TEXTS.mobile_toggle; document.getElementById('t-dev-title').innerText = TEXTS.dev_title; document.getElementById('t-dev-btn').innerText = TEXTS.dev_btn;
let clist = ""; TEXTS.controls_list.forEach(c => clist += `<li>${c}</li>`); document.getElementById('t-ctrl-list').innerHTML = clist;
if(new URLSearchParams(window.location.search).get('x') === 'v') { document.getElementById('dev-panel').style.display = 'block'; }

// INPUT SYSTEM & HELPER TOOLS! 
const activeKeys = {};
window.addEventListener('keydown', e => { 
    if(e.code==='Space') e.preventDefault(); 
    if(e.code === 'KeyP' || e.code === 'Escape') togglePause();
    activeKeys[e.code]=true;
}); window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; } function mk(c){activeKeys[c]=true;} function rk(c){activeKeys[c]=false;}
let isMobUI=false; function toggleMobileUI(){isMobUI=!isMobUI; document.getElementById('mob-ui').style.display=isMobUI?'flex':'none';}
function intersect(a,b){return!(b.x>a.x+a.w || b.x+b.w<a.x || b.y>a.y+a.h || b.y+b.h<a.y);}
function mapNum(v,min1,max1,min2,max2){return min2+(v-min1)*(max2-min2)/(max1-min1);}

// Classes 
const HEROES =[
    { id: 'earth', col: '#2ecc71', maxHp: 180, hpRegen: 0.01, speed: 0.9, jump: 12, maxEn: 100, dmgMult: 1.2, enCostMult: 1, pCol: '#27ae60'},
    { id: 'fire', col: '#e74c3c', maxHp: 80, hpRegen: 0, speed: 1.6, jump: 15, maxEn: 120, dmgMult: 1.8, enCostMult: 1, pCol: '#ff7979'},
    { id: 'water', col: '#3498db', maxHp: 110, hpRegen: 0.15, speed: 1.1, jump: 14, maxEn: 110, dmgMult: 1.0, enCostMult: 1, pCol: '#7ed6df'},
    { id: 'air', col: '#ecf0f1', maxHp: 90, hpRegen: 0, speed: 1.9, jump: 18, maxEn: 100, dmgMult: 0.8, enCostMult: 0.7, pCol: '#c7ecee'},
    { id: 'lightning', col: '#f1c40f', maxHp: 90, hpRegen: 0, speed: 2.2, jump: 14, maxEn: 100, dmgMult: 1.5, enCostMult: 1.5, pCol: '#f9ca24'},
    { id: 'magma', col: '#d35400', maxHp: 160, hpRegen: 0.05, speed: 0.7, jump: 11, maxEn: 100, dmgMult: 1.6, enCostMult: 1.2, pCol: '#eb4d4b'},
    { id: 'light', col: '#ffffb3', maxHp: 100, hpRegen: 0.02, speed: 1.0, jump: 14, maxEn: 300, dmgMult: 0.9, enCostMult: 0.8, pCol: '#fff200'},
    { id: 'dark', col: '#8e44ad', maxHp: 85, hpRegen: 0, speed: 1.3, jump: 14, maxEn: 120, dmgMult: 1.0, enCostMult: 1.0, pCol: '#9b59b6'}
];

function createSelectMenu() {
    let box = document.getElementById('roster');
    HEROES.forEach(h => {
        let ht = HERO_TEXTS[h.id]; let d = document.createElement('div');
        d.className='char-card'; d.style.setProperty('--card-color', h.col);
        d.innerHTML = `<h3 style="color:${h.col};">${ht.name}</h3><div style="font-size:12px;color:#aaa">${ht.desc}</div>`;
        d.onclick=()=>{startMission(h, false);}; box.appendChild(d);
    });
}

// Global Core Config 
const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }); window.dispatchEvent(new Event('resize'));

// -------------------------------------------------------------
// === PIXEL ART RENDERER MAGIC 16 BIT === 
// -------------------------------------------------------------
function drawRetroSprite(context, tx, ty, w, h, primeCol, t_type, hpRatio, phaseFlag, isFaceRight) {
    context.save(); context.translate(tx, ty); 
    if(!isFaceRight){ context.scale(-1, 1); context.translate(-w, 0); } // Flip magic for symmetry

    let bx = 0; let bw = w; 
    let headR = 8;
    // Base Frame
    context.fillStyle = '#000'; context.fillRect(bx-2, -2, bw+4, h+4); // Core dark border! 
    context.fillStyle = primeCol; context.fillRect(bx, 0, bw, h);

    if (t_type === 'player'){
        context.fillStyle = '#34495e'; context.fillRect(bx, h/2, bw, h/2); // pants
        context.fillStyle = '#fff'; context.fillRect(bx+bw-12, 10, 8, 8); // main visor 
        context.fillStyle = primeCol; context.fillRect(bx-4, 8, 8, 20); // Backpack logic tank
        if(kd('KeyU')){ context.fillStyle='#f1c40f'; context.globalAlpha=0.6; context.beginPath(); context.arc(bw/2, h/2, w+10, 0, Math.PI*2); context.fill(); context.globalAlpha=1; }
    }
    else if(t_type === 'bomber') {
        let inflate = 1.0 + (1-hpRatio)*0.5; // grows when hit!!
        context.scale(1, inflate); 
        context.fillStyle='#d35400'; context.fillRect(bx, h/3, bw, h*0.6); // roundish
        context.fillStyle='#000'; context.fillRect(bx+bw/2, 5, 4, 15); // bomb fuse line
        context.fillStyle='#e74c3c'; context.fillRect(bx+bw-15, h/2, 12, 8); // Angry eye 
    }
    else if(t_type === 'shield'){
        context.fillStyle = '#7f8c8d'; context.fillRect(bx, 5, bw, h); // grey body
        // HUGE Front White Shield !! 
        context.fillStyle = '#ecf0f1'; context.fillRect(bw-8, 0, 15, h+5); 
        context.fillStyle = '#f1c40f'; context.fillRect(bw-4, h/3, 7, 20); // cross icon  
    }
    else if(t_type === 'ninja'){
        context.fillStyle = '#2c3e50'; context.fillRect(bx, 0, bw, h); 
        context.fillStyle = '#e74c3c'; context.fillRect(bx-4, 12, bw+8, 8); // red ribbon 
        context.fillStyle = '#fff'; context.fillRect(bx+bw-8, 14, 4, 4); // single eye peak
    }
    else if(t_type === 'flyer'){
        context.fillStyle = '#16a085'; context.beginPath(); context.arc(bw/2, h/2, w/2, 0, Math.PI*2); context.fill();
        context.fillStyle='#ecf0f1'; context.fillRect(bx-15, h/4, 25, 8); context.fillRect(bx-15, h/1.5, 20, 6); // jetpack wings!
        context.fillStyle='#e74c3c'; context.fillRect(bx+bw-12, h/2-6, 12, 12); // single cyborg eye
    }
    else if(t_type === 'boss'){
        let color = phaseFlag===1 ? '#e67e22' : phaseFlag===2 ? '#9b59b6' : '#e74c3c'; // Rage change
        context.fillStyle = '#2c3e50'; context.fillRect(0,0, w, h);
        context.fillStyle = color; context.fillRect(4,4, w-8, h-8);
        context.fillStyle = '#000'; context.fillRect(w/2, 20, w/2, 20); // evil mask
        context.fillStyle = phaseFlag>2 ? '#fff':'red'; context.fillRect(w/2+10, 25, 15,10); // eye pupil 
        // Pauldrons shoulder
        context.fillStyle='#f1c40f'; context.fillRect(-10, 0, 30, 25); 
        if(phaseFlag>=2) { context.fillStyle='cyan'; context.fillRect(w/2, h/2, w+30, 8); } // laser sword active
    }
    else {
        // generic enemies melee/shooter/tank
        context.fillStyle = primeCol; context.fillRect(bx, 0, bw, h);
        context.fillStyle = '#000'; context.fillRect(bx+bw-12, 12, 8,8);
        if(t_type === 'shooter') { context.fillStyle='#2c3e50'; context.fillRect(bx+bw-4, 25, 18, 6); } // holds gun tube! 
        if(t_type === 'tank') { context.fillStyle='#95a5a6'; context.fillRect(bx-5, h/3, bw+10, h/2); } // massive armored plate belt 
    }

    context.restore();
}
// -------------------------------------------------------------

const STAGE_WIDTH = 3000;
let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[], drops=[];
let currentMap = MAPS[1]; let globalStage = 1; let f=0; let shakeV=0, camX=0;
let isPaused = false, barrier = null, pipe = null, cloverChest = null;
let navArrowOpacity = 0; function doShake(amt){shakeV=amt*5;} 

function togglePause() {
    if(!pl || pl.hp<=0 || globalStage>20) return; 
    isPaused = !isPaused; document.getElementById('pause-screen').classList.toggle('hidden', !isPaused);
    if(!isPaused) for(let k in activeKeys) activeKeys[k] = false; 
}

class Barrier {
    constructor(x) { this.x = x; this.y = 0; this.w = 50; this.h = canvas.height; this.hp = 250; this.maxHp=250; this.v = false; }
    draw() {
        ctx.fillStyle = this.v ? 'rgba(46, 204, 113, 0.6)' : 'rgba(231, 76, 60, 0.4)'; ctx.fillRect(this.x, 0, this.w, this.h);
        ctx.strokeStyle=this.v ? '#fff':'red'; ctx.lineWidth=3; ctx.strokeRect(this.x+20, 0, 5, this.h);
        if(this.v){ ctx.fillStyle='red'; ctx.fillRect(this.x-10, canvas.height/2, 60,10); ctx.fillStyle='#2ecc71'; ctx.fillRect(this.x-10, canvas.height/2, 60*(this.hp/this.maxHp),10); }
    }
}
class Pipe { constructor(x) { this.w = 80; this.h = 100; this.x = x - this.w - 50; this.y = canvas.height - 80 - this.h; }
    draw() {
        ctx.fillStyle = '#27ae60'; ctx.fillRect(this.x, this.y, this.w, this.h); ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, this.y, this.w+20, 30);
        ctx.strokeStyle = '#000'; ctx.lineWidth=3; ctx.strokeRect(this.x, this.y, this.w, this.h); ctx.strokeRect(this.x-10, this.y, this.w+20, 30);
        ctx.fillStyle = 'white'; ctx.font="24px Righteous"; ctx.fillText("➔⬇➔", this.x, this.y-20);
    }
}
class Drop {
    constructor(x,y, isB) { this.x=x; this.y=y; this.w=24; this.h=24; this.vy=-8; this.isB=isB;}
    upd() { this.vy+=0.5; this.y+=this.vy; if(this.y+this.h > canvas.height-80){this.y=canvas.height-80-this.h; this.vy=-this.vy*0.3;}
        if(intersect(this,pl)){
            if(this.isB){pl.maxHp+=25; pl.maxEn+=25; pl.hp=pl.maxHp; pl.en=pl.maxEn; makeFX(this.x,this.y, 25,'#f1c40f','boom');}
            else { pl.hp=Math.min(pl.hp+20, pl.maxHp); makeFX(this.x,this.y, 10,'#2ecc71','spark'); } return true;
        } return false;
    }
    draw() { ctx.fillStyle=this.isB?'#f1c40f':'#2ecc71'; ctx.fillRect(this.x,this.y,this.w,this.h); ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.strokeRect(this.x,this.y,this.w,this.h); ctx.fillStyle='#fff'; ctx.font="20px Arial"; ctx.fillText(this.isB?"★":"♥",this.x+2,this.y+20); }
}

class Player {
    constructor(c){
        this.w=38; this.h=64; this.x=100; this.y=0; this.vx=0; this.vy=0; this.c = c; this.maxHp=c.maxHp; this.hp=this.maxHp; this.maxEn=c.maxEn; this.en=this.maxEn;
        this.facing = 1; this.grounded = false; this.target = null; this.iFrames = 0; this.chargeI = 0; this.atkWait = {}; this.jCount=0;
    }
    upd() {
        if(this.hp<=0) return; this.hp = Math.min(this.hp+this.c.hpRegen, this.maxHp); if(this.iFrames>0) this.iFrames--;
        
        let crch=kd('KeyS'); let sprt=(kd('ShiftLeft')||kd('ShiftRight')); let chu=kd('KeyU'); let chi=kd('KeyI');
        if(crch && !chi){ if(this.h!==38) {this.y+=26; this.h=38; this.vx*=0.4;} } else { if(this.h!==64) {this.y-=26; this.h=64;} }

        if(chi){ this.chargeI=Math.min(this.chargeI+2, 220); makeFX(this.x+this.w/2, this.y+this.h/2,1,this.c.pCol,'spark'); 
                 if(Math.floor(this.chargeI)%10==0) doShake(0.5); 
        } else if(this.chargeI>0){
            let dmg = this.chargeI * 2.5 * this.c.dmgMult; let s = this.chargeI/2.5;
            p_pr.push({x:this.facing>0?this.x+this.w:this.x-s, y:this.y+20-s/2, dir:this.facing, s:25, dmg:dmg, size:s, color:this.c.pCol, tgt:this.target});
            this.vx-=(this.chargeI/8)*this.facing; this.chargeI=0; doShake(5);
        }

        let speed = this.c.speed; if(sprt) speed*=2; if(chu || chi || crch) speed*=0.25;
        if(sprt && this.grounded && f%6===0 && (kd('KeyA')||kd('KeyD'))) makeFX(this.x+10,this.y+this.h, 2, '#777','spark');

        if(kd('KeyA')){this.vx-=speed; this.facing=-1;} if(kd('KeyD')){this.vx+=speed; this.facing=1;}
        if((kd('KeyW')||kd('Space')) && !crch){ if(!this.jHold && this.jCount<2){this.vy=-this.c.jump; this.jCount++; makeFX(this.x+15,this.y+this.h, 6, '#fff','spark'); this.jHold=true;} } else {this.jHold=false;}

        if(chu){ this.en = Math.min(this.en+1.5, this.maxEn); makeFX(this.x+this.w/2,this.y+this.h/2,1,'#ecf0f1','beam');} 
        else if(!chi) {
            this.shK('KeyH','1',8*this.c.enCostMult, 15*this.c.dmgMult, 12);
            this.shK('KeyJ','2',20*this.c.enCostMult, 35*this.c.dmgMult, 20);
            this.shK('KeyK','3',45*this.c.enCostMult, 80*this.c.dmgMult, 32);
            if(kd('KeyY')&&!this.atkWait['KeyY']) {
                if(this.en >= this.maxEn-2){
                    this.en=0; p_pr.push({x:this.facing>0?this.x+this.w:this.x-100, y:this.y-10, dir:this.facing, s:15, dmg:450*this.c.dmgMult, size:100, color:'#e74c3c', tgt:this.target});
                    this.vx -= 18*this.facing; doShake(10);
                } this.atkWait['KeyY']=true; 
            } else if(!kd('KeyY')) this.atkWait['KeyY']=false;
        }

        if(kd('KeyE')){if(!this.LTrig){this.swLck(); this.LTrig=true;}}else this.LTrig=false;
        if(this.target && this.target.hp<=0){this.target=null; this.getBestTrg();}

        this.vy+=0.6; this.x+=this.vx; this.y+=this.vy; this.vx*=0.82;
        let leftB = (globalStage-1)*STAGE_WIDTH; if(this.x < leftB+10) {this.x=leftB+10; this.vx=0;}
        if(barrier && this.x+this.w > barrier.x) {this.x=barrier.x-this.w; this.vx=0;}
        
        let isG=false; let flY=canvas.height-80; if(this.y+this.h>=flY){this.y=flY-this.h; this.vy=0; isG=true;} 
        else {
            currentMap.platforms.forEach(p => { let r_x=p.x+leftB; let pFY = canvas.height-p.y_offset;
                if(this.vy>=0 && this.y+this.h>=pFY-16 && this.y+this.h<=pFY+16 && this.x+this.w>r_x && this.x<r_x+p.w) {this.y=pFY-this.h; this.vy=0; isG=true;}
            });
        }
        if(isG){this.jCount=0; this.grounded=true;} else this.grounded=false;
        
        // C- PIPE ENTRANCE TRIGGER
        if(pipe && intersect(this,pipe) && crch && isG){
             pl.hp = Math.min(pl.hp+(pl.maxHp*0.3), pl.maxHp); 
             makeFX(this.x,this.y, 40,'#fff','boom'); globalStage++; loadStg(globalStage);
        }
    }

    shK(k, t, c, dmg, s){
        if(kd(k)){ if(!this.atkWait[k] && this.en>=c) {
            this.en-=c; p_pr.push({x:this.facing>0?this.x+this.w:this.x, y:this.y+this.h/3, dir:this.facing, s:18, dmg:dmg, size:s, color:this.c.pCol, tgt:this.target});
            this.vx -= (c/6)*this.facing; this.atkWait[k]=true;
        } } else this.atkWait[k]=false;
    }

    swLck(){if(this.target) this.target=null; else this.getBestTrg();}
    getBestTrg() { let md=1600; let trg=null; e_arr.forEach(e=>{let d=Math.abs(e.x-this.x); if(d<md && e.x>this.x-600 && e.x<this.x+1000){md=d; trg=e;}}); if(trg){this.target=trg; doShake(1.5);} }

    draw() {
        if(this.iFrames>0 && Math.floor(f/4)%2===0) ctx.globalAlpha=0.4;
        drawRetroSprite(ctx, this.x, this.y, this.w, this.h, this.c.col, 'player', 1.0, 0, this.facing>0);

        if(this.chargeI>0){ ctx.fillStyle=this.c.pCol; ctx.beginPath(); ctx.arc(this.x+this.w/2, this.y+this.h/2, this.chargeI/2.5, 0, Math.PI*2); ctx.fill(); }
        
        if(this.target) {
            let tx=this.target.x+this.target.w/2; let ty=this.target.y+this.target.h/2;
            ctx.strokeStyle='#e74c3c'; ctx.lineWidth=3; ctx.beginPath(); ctx.arc(tx,ty,35+Math.sin(f/4)*5, 0, Math.PI*2); ctx.stroke();
            ctx.setLineDash([5,5]); ctx.beginPath(); ctx.moveTo(this.x+this.w/2, this.y+this.h/2); ctx.lineTo(tx,ty); ctx.stroke(); ctx.setLineDash([]);
        }
        ctx.globalAlpha=1;
    }
}

class Enemy {
    constructor(x, ty) {
        this.ty=ty; this.w=45; this.h=55; this.isAggro=false;
        this.homeX = x; this.x = x; this.y = -100; // Drops from sky init.
        this.vx=0; this.vy=0; 
        let dif = (globalStage * 0.1); // difficulty multi

        this.s = 2.0; this.stC=120;
        this.maxHp = 60 + (globalStage*25);
        this.c = '#95a5a6'; this.atkWait = 0; 
        
        // SPECIAL STATS!
        if(ty==='boss'){ this.maxHp=800+globalStage*150; this.w=90; this.h=110; this.s=1.5;}
        else if(ty==='tank'){ this.w=65; this.h=85; this.maxHp*=3.5; this.s=0.6;}
        else if(ty==='shield'){ this.w=50; this.c='#34495e'; this.maxHp*=2;}
        else if(ty==='bomber'){ this.w=35; this.h=45; this.maxHp*=0.7; this.s=3;}
        else if(ty==='flyer') { this.maxHp*=0.6; this.s=1.5; }
        else if(ty==='ninja') { this.maxHp*=0.8; this.s=3; }
        else if(ty==='shooter'){ this.s=1; this.stC = 120 - Math.min(60, globalStage*2); } // shoot faster 

        this.hp = this.maxHp;
        this.phase = 1;
    }

    upd() {
        let dx = pl.x - this.x; let isFDir = (dx>0)?1:-1;
        let flY = canvas.height-80; 

        if(!this.isAggro){ if(Math.abs(dx)<800) this.isAggro=true; else this.vx = Math.sin(f/60)*this.s*0.5;}
        else {
            // ADVANCED AI PER TYPE! 
            if(this.ty==='boss') {
                if(this.hp/this.maxHp < 0.3) this.phase=3; else if(this.hp/this.maxHp < 0.6) this.phase=2;
                
                let curSp = (this.phase===3)? 3 : (this.phase===2)? 2 : 1.2;
                this.atkWait--;

                if(this.phase===1) { if(Math.abs(dx)>20) this.vx=isFDir*curSp; }
                else if (this.phase===2) { 
                    this.vx = isFDir * curSp; 
                    if(this.atkWait<=0 && Math.abs(dx)>150){ 
                         this.atkWait=90; pr_arr.push({x:this.x+this.w/2, y:this.y+30, dx:isFDir*10, dy:2});
                    }
                }
                else if(this.phase===3) { // Frenzy! 
                    if(this.atkWait>0){ this.vx = isFDir*6; } else { this.vx = isFDir*curSp; }
                    if(f%200===0){ this.atkWait=30; this.vy=-8; makeFX(this.x,this.y,10,'red','boom');}
                }
            }
            else if (this.ty==='flyer'){
                this.x += isFDir * this.s; 
                this.y = pl.y - 150 + Math.sin(f/30)*60; // tracks above player height mostly!
            }
            else if (this.ty==='bomber') {
                if(Math.abs(dx)<50) this.dieAndExplode(); // Pop mechanism
                this.vx = isFDir * this.s; 
            }
            else if(this.ty==='shield' || this.ty==='tank') { this.vx = isFDir * this.s; }
            else if (this.ty==='ninja'){ this.atkWait--; if(this.atkWait>20) this.vx = isFDir*1.5; else if(this.atkWait>0){this.vx=isFDir*12; this.vy=-2; } else this.atkWait=90;}
            else if (this.ty==='shooter') { this.atkWait--; if(Math.abs(dx)>450) this.vx = isFDir*this.s; else this.vx*=0.8;
                 if(this.atkWait<=0) { this.atkWait = this.stC; pr_arr.push({x:this.x+20,y:this.y+20, dx:isFDir*10, dy:0});}
            }
            else if (this.ty==='summoner') {
                 if(Math.abs(dx)<600){this.vx = isFDir* -1.2;} else this.vx*=0.8; // reverse dir 
                 this.atkWait--; if(this.atkWait<=0){ this.atkWait=200; e_arr.push(new Enemy(this.x, 'jumper')); e_arr[e_arr.length-1].isAggro=true; }
            }
            else if(this.ty==='jumper') { this.vx=isFDir*1.6; this.atkWait--; if(this.atkWait<=0 && this.y+this.h>=flY-20) {this.vy=-14; this.atkWait=75;}}
            else { this.vx = isFDir*this.s; } // standard melee
        }

        this.x+=this.vx; 
        let lBnd = (globalStage-1)*STAGE_WIDTH; if(this.x < lBnd+20) {this.x=lBnd+20; this.vx*=-1;}
        if(barrier && this.x+this.w > barrier.x-10){ this.x=barrier.x-10-this.w; this.vx*=-1;}

        if(this.ty!=='flyer') {
            this.vy+=0.6; this.y+=this.vy; 
            let isGe=false; if(this.y+this.h>=flY){this.y=flY-this.h; this.vy=0; isGe=true;}
            
            if(!isGe && this.ty!=='jumper') {
                 currentMap.platforms.forEach(p=>{
                    let px = p.x+lBnd; let py = canvas.height-p.y_offset;
                    if(this.vy>=0 && this.y+this.h>=py-15 && this.y+this.h<=py+15 && this.x+this.w>px && this.x<px+p.w) {this.y=py-this.h; this.vy=0;}
                 });
            }
        }

        // --- Damage output engine --- 
        if(this.isAggro && pl.iFrames<=0 && intersect(this, pl)) {
            let dg = (this.ty==='boss')? 30: (this.ty==='tank')? 22 : 12; 
            pl.hp -= dg; pl.vx = dx<0?15:-15; pl.vy=-10; pl.iFrames=50; doShake(3);
        }
    }
    
    dieAndExplode() {
         // Bomber big AOE radius mechanic 
         makeFX(this.x+this.w/2, this.y+this.h/2, 60, '#e67e22', 'boom'); 
         if(intersect({x:this.x-150, y:this.y-150, w:300, h:300}, pl) && pl.iFrames<=0) {
             pl.hp -= 40; pl.iFrames=40; pl.vx = pl.x<this.x?-20:20; pl.vy=-10; doShake(8);
         }
         this.hp = -999; 
    }

    draw() { drawRetroSprite(ctx, this.x, this.y, this.w, this.h, this.c, this.ty, this.hp/this.maxHp, this.phase, pl.x > this.x); 
        ctx.fillStyle='#000'; ctx.fillRect(this.x, this.y-10, this.w,4); ctx.fillStyle='red'; ctx.fillRect(this.x,this.y-10, this.w*(Math.max(0,this.hp)/this.maxHp), 4);
    }
}

class CloverChest {
    constructor(x) { this.x=x; this.y=canvas.height-180; this.w=100; this.h=100; this.hp=600; this.maxHp=600; }
    draw(){ ctx.fillStyle='#f1c40f'; ctx.fillRect(this.x,this.y,this.w,this.h); ctx.fillStyle='#000'; ctx.fillRect(this.x+this.w/2-5, this.y+30, 10,20);
            ctx.strokeStyle='#fff'; ctx.lineWidth=4; ctx.strokeRect(this.x,this.y,this.w,this.h); 
            ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-20, this.w*(this.hp/this.maxHp),10);
            ctx.fillStyle='#fff'; ctx.font="bold 26px Rubik"; ctx.fillText("ULTIMATE CHEST", this.x-25, this.y-35);
    }
}

function makeFX(x,y,q,c,m) { for(let i=0;i<q;i++) fx.push({ x:x, y:y, vx:(Math.random()-0.5)*(m==='boom'?16:4), vy:(m==='beam')?-(Math.random()*8): (Math.random()-0.5)*(m==='boom'?16:4), col:c, l: (m==='spark')?12:20, s: (m==='boom')?Math.random()*10+5 : 4}); }

// CORE INITIALIZATION LOOP !! 
function loadStg(s_N) {
    let tmap = MAPS[s_N > 20 ? 20 : s_N]; currentMap = tmap;
    document.getElementById('stage-info').innerText = tmap.name; document.getElementById('stage-info').style.boxShadow=`0 0 10px ${tmap.bg}`;
    let sbx = document.getElementById('stage-alert'); sbx.innerText = tmap.is_boss ? "AREA SECURED" : "FIGHT ON!"; 
    if(s_N%5===0 && s_N!==20) sbx.innerText = "CHALLENGE MET!"; 
    sbx.style.opacity = 1; setTimeout(()=>{ sbx.style.opacity=0 }, 2500);

    let offset_x = (s_N - 1) * STAGE_WIDTH;
    e_arr=[]; pr_arr=[]; p_pr=[]; drops=[]; barrier=null; pipe=null; cloverChest=null; 

    // Monster Gen Code Matrix !
    if(tmap.is_boss) { e_arr.push(new Enemy(offset_x + 2200, 'boss')); } 
    else { let ec = 3 + Math.floor(s_N*0.8); 
           for(let k=0; k<ec; k++){ let ty=tmap.enemies[Math.floor(Math.random()*tmap.enemies.length)]; e_arr.push(new Enemy(offset_x+600+(k*280), ty)); } 
    }
    
    // Physical checkings items.
    if(s_N % 5 == 0 && s_N!==20) pipe = new Pipe(s_N * STAGE_WIDTH); 
    else if (s_N !== 20) barrier = new Barrier(s_N * STAGE_WIDTH - 60);
}

function startMission(charData, devFlag) {
    p_class = charData;
    globalStage = devFlag ? parseInt(document.getElementById('dev-stage').value) : 1;
    document.getElementById('select-screen').classList.add('hidden'); document.getElementById('ui-layer').classList.remove('hidden');
    pl = new Player(charData); if(devFlag){pl.maxHp=5000; pl.hp=5000; pl.en=5000; pl.maxEn=5000; pl.x = (globalStage-1)*STAGE_WIDTH+100;}
    loadStg(globalStage); requestAnimationFrame(sysLoop);
}

// --------------------- ENGINE --------------------------- // 
function sysLoop() {
    if(isPaused){requestAnimationFrame(sysLoop); return; }
    f++;
    if(pl.hp<=0){ document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('death-screen').classList.remove('hidden'); document.getElementById('final-lvl').innerText=globalStage; return;}

    pl.upd();
    if(e_arr.length===0 && barrier){ barrier.v=true; }
    if(e_arr.length===0 && !barrier && !pipe && !cloverChest) {
        if(globalStage===20){ cloverChest=new CloverChest(globalStage*STAGE_WIDTH - 400);} else if(pl.x>globalStage*STAGE_WIDTH){globalStage++; loadStg(globalStage);}
    }

    navArrowOpacity = (e_arr.length===0 && (barrier||pipe||cloverChest))? Math.min(navArrowOpacity+0.05, 1) : Math.max(navArrowOpacity-0.05, 0);

    // AI LOOPS O(N) 
    for(let i=e_arr.length-1; i>=0; i--) { let e=e_arr[i]; e.upd(); 
        if(e.hp<=0) { if(e.ty==='bomber')e.dieAndExplode(); else {makeFX(e.x+20,e.y+20,30,'#f1c40f','boom'); drops.push(new Drop(e.x,e.y, e.ty==='boss')); } e_arr.splice(i,1); }
    }
    
    // Check winner
    if(cloverChest && cloverChest.hp<=0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('victory-screen').classList.remove('hidden'); return; }

    for(let i=drops.length-1; i>=0; i--) { if(drops[i].upd()) drops.splice(i,1); }

    // Enmy Pr 
    for(let i=pr_arr.length-1; i>=0; i--){ let b=pr_arr[i]; b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 1, '#fff', 'spark'); 
         if(intersect({x:b.x,y:b.y,w:8,h:8}, pl)) { if (pl.iFrames<=0) { pl.hp-=18; pl.iFrames=45; pl.vx += b.dx>0?8:-8; doShake(3); } pr_arr.splice(i,1); continue; }
         if(b.y>canvas.height || b.x<camX || b.x>camX+canvas.width*2) pr_arr.splice(i,1);
    }
    
    // Play Pr Collision + Smart Shields Matrix !
    for(let i=p_pr.length-1; i>=0; i--){ let b = p_pr[i]; 
        if(b.tgt && b.tgt.hp>0){let ta = Math.atan2((b.tgt.y+20)-b.y, (b.tgt.x+20)-b.x); b.x += Math.cos(ta)*b.s; b.y+=Math.sin(ta)*b.s; }else{ b.x += b.dir*b.s; }
        makeFX(b.x,b.y,1,b.color,'spark');

        let isDel = false; let projRecHit = {x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size};

        if(cloverChest && intersect(projRecHit, cloverChest)) { cloverChest.hp-=b.dmg; makeFX(b.x, b.y, 5, '#2ecc71', 'boom'); isDel=true; doShake(1.5); } 
        else if(barrier && barrier.v && intersect(projRecHit, barrier)){ barrier.hp-=b.dmg; makeFX(b.x, b.y, 3,'red','boom'); isDel=true; if(barrier.hp<=0) barrier=null;} 
        else {
             for(let j=e_arr.length-1; j>=0; j--){ let te = e_arr[j];
                  if(intersect(projRecHit, te)) {
                      // ====== FRONT SHIELD MECHANIC DEVIATION BLOCK ========
                      let sameDirFacing = (te.x > pl.x) ? (b.dir===1) : (b.dir===-1); 
                      if (te.ty==='shield' && sameDirFacing && b.size < 40){ // normal sizes get BLOCKED ! Ult ignores shield.
                           b.dir*=-1; // Ricochet effect ! 
                           pr_arr.push({x:b.x, y:b.y, dx:b.dir*15, dy:0}); // reflect it back!! 
                           isDel=true; makeFX(b.x, b.y, 15, '#fff', 'spark'); doShake(1); break;
                      } 

                      // Normal Hits Process 
                      te.hp-=b.dmg; makeFX(b.x,b.y,8,b.color,'boom'); isDel=true; doShake((b.dmg)/25); te.vx += b.dir*12;
                      if(p_class.id==='dark'){pl.hp=Math.min(pl.maxHp,pl.hp+(b.dmg*0.035));} te.isAggro=true; break;
                  }
             }
        }
        if(isDel || b.y>canvas.height || Math.abs(b.x-pl.x)>3000) p_pr.splice(i,1);
    }

    for(let i=fx.length-1; i>=0; i--) { fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--; if(fx[i].l<=0) fx.splice(i,1); }
    
    // View Transform Smooth Algorithm ...
    let cxT = pl.x - canvas.width/2 + 100; if(cxT<0) cxT=0; camX += (cxT-camX)*0.08; 
    let S_X = camX, S_Y = 0; if(shakeV>0){ S_X+=(Math.random()-0.5)*shakeV; S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.8;} if(shakeV<0.4) shakeV=0;
    
    // ====== THE CANVAS DRAW RENDERS OVERRIDE ==== !!!
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    // Draw far stars logic ..
    ctx.fillStyle='rgba(255,255,255,0.08)'; for(let ds=0;ds<60;ds++) { let pX = ((ds*584)-(camX*0.06))%canvas.width; if(pX<0)pX+=canvas.width; ctx.fillRect(pX,(ds*4113)%canvas.height, 4+(ds%2)*2,4+(ds%2)*2); }
    
    ctx.save(); ctx.translate(-S_X, S_Y); 
    
    // Core Bottom base layout mapping.
    let baseFY = canvas.height-80;
    ctx.fillStyle = currentMap.floor; ctx.fillRect(S_X-200, baseFY, canvas.width+500, 300);
    ctx.strokeStyle='rgba(0,0,0,0.6)'; for(let xk=S_X-(S_X%100); xk<S_X+canvas.width+400; xk+=100) { ctx.beginPath(); ctx.moveTo(xk, baseFY); ctx.lineTo(xk, canvas.height); ctx.stroke(); }

    let pFOffset = (globalStage-1)*STAGE_WIDTH;
    currentMap.platforms.forEach(p=>{
        let p_X = p.x+pFOffset; let pY = canvas.height-p.y_offset;
        ctx.fillStyle = currentMap.floor; ctx.fillRect(p_X,pY,p.w,p.h);
        ctx.fillStyle='rgba(0,0,0,0.4)'; ctx.fillRect(p_X,pY+p.h-4,p.w,4);
    });

    if(barrier) barrier.draw(); if(pipe) pipe.draw(); if(cloverChest) cloverChest.draw(); drops.forEach(d=>d.draw());
    pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#f1c40f'; pr_arr.forEach(b=>{ctx.fillRect(b.x-6,b.y-6,12,12);}); // draw evil square bullets  
    
    // Magic Beams of users logic!! 
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.shadowBlur=15; ctx.shadowColor=b.color; ctx.beginPath(); ctx.arc(b.x,b.y,b.size,0,Math.PI*2); ctx.fill(); ctx.shadowBlur=0;});
    fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);}); ctx.globalAlpha=1;
    
    // Navigation 
    if(navArrowOpacity>0) { ctx.globalAlpha=navArrowOpacity; ctx.fillStyle="rgba(255, 255, 255, " + (0.5+Math.sin(f/10)*0.5) + ")"; ctx.font="80px Righteous"; ctx.fillText("FORWARD >", pl.x+200, canvas.height/2); ctx.globalAlpha=1.0; }

    ctx.restore();
    
    // Data sync string builders (Lightweight UI dom logic without Reflow blocking!!!)
    document.getElementById('hp-bar').style.width=Math.max(0,(pl.hp/pl.maxHp)*100)+'%'; document.getElementById('hp-t').innerText=Math.floor(pl.hp)+"/"+pl.maxHp;
    document.getElementById('en-bar').style.width=Math.max(0,(pl.en/pl.maxEn)*100)+'%'; document.getElementById('en-t').innerText=Math.floor(pl.en)+"/"+pl.maxEn;
    
    requestAnimationFrame(sysLoop);
}

createSelectMenu();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
