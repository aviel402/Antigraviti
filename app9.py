from flask import Flask, render_template_string, jsonify, request
import json
import maps9
import txt9

app = Flask(__name__)
app.secret_key = 'clover_10k_marathon'

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
    <title>CLOVER - Long Run</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; touch-action: none; } /* מניעת זום בטלפון */
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        body::before { content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0; 
                       background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.2) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); z-index: 200; background-size: 100% 2px, 3px 100%; pointer-events: none; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 300; 
            background: linear-gradient(135deg, rgba(5,5,10,0.95), rgba(20,20,30,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center; overflow-y:auto;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        h1.title { font-family: 'Righteous', cursive; font-size: clamp(30px, 6vw, 70px); margin:0; text-transform: uppercase; letter-spacing: 2px;
                   background: -webkit-linear-gradient(#f1c40f, #e67e22); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 4px 10px rgba(241,196,15,0.6));}
        
        #dev-panel { background: rgba(255,0,0,0.2); border: 2px solid red; padding: 10px; border-radius: 10px; margin-bottom: 10px; display: none; text-align:center;}
        #dev-panel select, #dev-panel button { padding: 5px; font-size: 14px; margin: 5px; cursor:pointer;}

        .info-chest { background: rgba(0,0,0,0.7); border: 2px solid var(--gold); border-radius: 10px; padding: 15px; max-width: 800px; margin-top: 10px; text-align: right; }
        .info-chest h3 { color: var(--gold); margin-top: 0; font-size: 18px;}
        .info-chest ul { list-style: none; padding: 0; margin:0;}
        .info-chest li { margin-bottom: 5px; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 3px; color:#ddd;}

        .char-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; width: 95%; max-width: 1000px; margin-top:15px; padding-bottom: 30px;}
        .char-card { background: rgba(0,0,0,0.6); border: 2px solid #555; border-bottom-width: 4px; padding: 10px; border-radius: 10px; cursor: pointer; text-align: center; transition: all 0.2s;}
        .char-card:hover { transform: translateY(-3px); border-bottom-width:2px; margin-top:2px; border-color: var(--card-color);}
        .char-card h3 { margin: 0 0 5px 0; font-family: 'Righteous'; font-size: 20px; text-transform:uppercase; text-shadow: 1px 1px #000; }
        
        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:100; display:flex; flex-direction:column; padding:10px; justify-content:space-between; }
        .glass-panel { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 8px; }
        
        /* Mobile UI Override - Smaller, Left D-Pad, Right Actions */
        .mobile-ui { position: absolute; bottom: 10px; width: 100%; left: 0; display: none; pointer-events: none; padding: 0 10px; justify-content: space-between; z-index: 50; opacity: 0.7;}
        .d-pad, .action-btns { display: grid; gap: 5px; pointer-events: auto; }
        .d-pad { grid-template-columns: 45px 45px 45px; grid-template-rows: 45px 45px; justify-content: start;}
        .btn-mob { background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.4); border-radius: 50%; color: white; font-weight: 900; font-size: 16px; cursor: pointer; font-family:'Righteous';}
        .btn-mob:active { background: rgba(255,255,255,0.9); color: black; transform: scale(0.9); }
        .action-btns { grid-template-columns: repeat(3, 45px); grid-template-rows: repeat(2, 45px); justify-content: end; }

        .top-right-controls { display: flex; flex-direction: column; gap: 5px; align-items: flex-end; pointer-events: auto;}
        .toggle-btn { padding: 8px 12px; font-family: 'Righteous'; font-size: 12px; background: rgba(0,0,0,0.7); color: white; border: 1px solid #555; border-radius: 5px; cursor: pointer;}

        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        .stat-bar-container { display: flex; align-items: center; margin-bottom:5px; width:200px; text-shadow:1px 1px black;}
        .stat-icon { font-weight:900; margin-left: 5px; width:30px; font-family:'Righteous'; font-size: 12px;}
        .bar-out { background: rgba(0,0,0,0.7); flex-grow: 1; height: 14px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.5); position:relative; overflow:hidden;}
        .bar-in { height:100%; transition: width 0.1s;}
        .hp-bar { background: #e74c3c; } .en-bar { background: #3498db; }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Righteous'; font-size:18px; color:#fff; text-shadow:0 2px 4px rgba(0,0,0,0.8), 0 0 10px var(--gold);}
        .menu-btn { padding:12px 30px; border:2px solid #fff; border-bottom:4px solid #fff; border-radius:8px; color:white; font-size:18px; font-family:'Righteous'; background:rgba(0,0,0,0.5); cursor:pointer; margin-top:15px; width: 300px; max-width: 80vw;}
        
        #shards-hud { position:absolute; top: 70px; left: 10px; font-family:'Righteous'; font-size: 20px; color: var(--gold); text-shadow: 2px 2px #000; }
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    <div id="dev-panel">
        <h2 id="t-dev-title" style="margin:0 0 10px 0; font-size:16px;"></h2>
        <select id="dev-stage"> <script>for(let i=1;i<=20;i++) document.write(`<option value="${i}">Stage ${i}</option>`);</script> </select>
        <button id="t-dev-btn" onclick="startMission(HEROES[0], true)"></button>
    </div>

    <h1 class="title" id="t-main-title"></h1><h2 id="t-main-sub" style="margin-top:-5px; color:var(--gold); font-size:16px;"></h2>
    
    <div class="info-chest">
        <h3 id="t-htp-title"></h3><p id="t-htp-desc" style="margin-top:5px; white-space: pre-line; line-height:1.3;"></p>
        <h3 id="t-ctrl-title"></h3><ul id="t-ctrl-list" style="display:grid; grid-template-columns: 1fr; gap:5px;"></ul>
    </div>
    <div class="char-grid" id="roster"></div>
</div>

<div id="pause-screen" class="screen hidden">
    <h1 class="title" id="t-pause" style="color:#3498db;"></h1>
    <button class="menu-btn" onclick="togglePause()" id="btn-resume"></button>
    <button class="menu-btn" onclick="location.reload()" id="btn-restart" style="color:#e74c3c; border-color:#e74c3c;"></button>
</div>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="glass-panel" style="direction: ltr; min-width: 220px;">
            <div class="stat-bar-container"><span class="stat-icon" style="color:#e74c3c;">HP</span>
                <div class="bar-out"><div class="bar-in hp-bar" id="hp-bar"></div></div> <span id="hp-t" style="color:#aaa;font-size:10px;margin-left:5px;"></span></div>
            <div class="stat-bar-container"><span class="stat-icon" style="color:#3498db;">EN</span>
                <div class="bar-out"><div class="bar-in en-bar" id="en-bar"></div></div> <span id="en-t" style="color:#aaa;font-size:10px;margin-left:5px;"></span></div>
        </div>
        <div class="glass-panel stage-title" id="stage-info">...</div>
        <div class="top-right-controls">
             <button class="toggle-btn" id="t-mobile-toggle" onclick="toggleMobileUI()"></button>
             <button class="toggle-btn" onclick="togglePause()">⏸ PAUSE</button>
        </div>
    </div>
    
    <div id="shards-hud">💎 0</div>
    
    <!-- מוקטן ומוצמד לשמאל וימין -->
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
            <button class="btn-mob" style="color:#3498db;" ontouchstart="mk('KeyU')" ontouchend="rk('KeyU')">U</button> 
            <button class="btn-mob" ontouchstart="mk('KeyI')" ontouchend="rk('KeyI')">I</button> 
            <button class="btn-mob" style="color:var(--gold);" ontouchstart="mk('KeyY')" ontouchend="rk('KeyY')">Y</button>
        </div>
    </div>
</div>

<div id="death-screen" class="screen hidden" style="z-index:400; background:rgba(40,10,10,0.96)">
    <h1 class="title" id="t-death" style="color:#e74c3c;"></h1>
    <h2><span id="t-death-sub"></span> <span id="final-lvl" style="color:white; padding: 2px 5px; background:#e74c3c; border-radius:5px;"></span> </h2>
    <button class="menu-btn" onclick="location.reload()" id="btn-retry" style="background:#e74c3c; color:#fff; border-color:#e74c3c; margin-top: 20px;"></button>
</div>

<div id="victory-screen" class="screen hidden" style="z-index:500; background: rgba(10,50,20,0.98);">
    <h1 class="title" id="t-vic" style="color:#2ecc71;"></h1>
    <h2 id="t-vic-sub" style="font-size:16px; text-align:center;"></h2>
    <button class="menu-btn" onclick="location.href='/'" id="btn-home" style="background:#2ecc71; border-color:#2ecc71; color:#000;"></button>
</div>

<script>
const MAPS = {{ maps_json | safe }}; const TEXTS = {{ texts | safe }}; const HERO_TEXTS = {{ heroes_texts | safe }};

document.getElementById('t-main-title').innerText = TEXTS.title_main; document.getElementById('t-main-sub').innerText = TEXTS.subtitle_main; document.getElementById('t-htp-title').innerText = TEXTS.how_to_play_title; document.getElementById('t-htp-desc').innerText = TEXTS.how_to_play_desc; document.getElementById('t-ctrl-title').innerText = TEXTS.controls_title; document.getElementById('t-pause').innerText = TEXTS.pause_title; document.getElementById('btn-resume').innerText = TEXTS.btn_resume; document.getElementById('btn-restart').innerText = TEXTS.btn_restart; document.getElementById('t-death').innerText = TEXTS.death_title; document.getElementById('t-death-sub').innerText = "נפלת בשלב: "; document.getElementById('btn-retry').innerText = TEXTS.btn_retry; document.getElementById('t-vic').innerText = TEXTS.victory_title; document.getElementById('t-vic-sub').innerText = TEXTS.victory_sub; document.getElementById('btn-home').innerText = TEXTS.btn_home; document.getElementById('t-mobile-toggle').innerText = TEXTS.mobile_toggle; document.getElementById('t-dev-title').innerText = TEXTS.dev_title; document.getElementById('t-dev-btn').innerText = TEXTS.dev_btn;
let clist = ""; TEXTS.controls_list.forEach(c => clist += `<li>${c}</li>`); document.getElementById('t-ctrl-list').innerHTML = clist;
if(new URLSearchParams(window.location.search).get('x') === 'v') { document.getElementById('dev-panel').style.display = 'block'; }

const activeKeys = {};
window.addEventListener('keydown', e => { 
    if(e.code==='Space') e.preventDefault(); 
    if(e.code === 'KeyP' || e.code === 'Escape') togglePause();
    activeKeys[e.code]=true;
}); window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; } function mk(c){activeKeys[c]=true;} function rk(c){activeKeys[c]=false;}
let isMobUI=false; function toggleMobileUI(){isMobUI=!isMobUI; document.getElementById('mob-ui').style.display=isMobUI?'flex':'none';}
function intersect(a,b){return!(b.x>a.x+a.w || b.x+b.w<a.x || b.y>a.y+a.h || b.y+b.h<a.y);}

const HEROES =[
    { id: 'earth', col: '#2ecc71', maxHp: 180, hpRegen: 0.01, speed: 1.0, jump: 12, maxEn: 100, dmgMult: 1.2, enCostMult: 1, pCol: '#27ae60'},
    { id: 'fire', col: '#e74c3c', maxHp: 80, hpRegen: 0, speed: 1.6, jump: 15, maxEn: 120, dmgMult: 1.8, enCostMult: 1, pCol: '#ff7979'},
    { id: 'water', col: '#3498db', maxHp: 110, hpRegen: 0.15, speed: 1.2, jump: 14, maxEn: 110, dmgMult: 1.0, enCostMult: 1, pCol: '#7ed6df'},
    { id: 'air', col: '#ecf0f1', maxHp: 90, hpRegen: 0, speed: 1.9, jump: 18, maxEn: 100, dmgMult: 0.8, enCostMult: 0.7, pCol: '#c7ecee'},
    { id: 'lightning', col: '#f1c40f', maxHp: 90, hpRegen: 0, speed: 2.2, jump: 14, maxEn: 100, dmgMult: 1.5, enCostMult: 1.5, pCol: '#f9ca24'},
    { id: 'magma', col: '#d35400', maxHp: 160, hpRegen: 0.05, speed: 0.8, jump: 11, maxEn: 100, dmgMult: 1.6, enCostMult: 1.2, pCol: '#eb4d4b'},
    { id: 'light', col: '#ffffb3', maxHp: 100, hpRegen: 0.02, speed: 1.2, jump: 14, maxEn: 300, dmgMult: 0.9, enCostMult: 0.8, pCol: '#fff200'},
    { id: 'dark', col: '#8e44ad', maxHp: 85, hpRegen: 0, speed: 1.4, jump: 14, maxEn: 120, dmgMult: 1.0, enCostMult: 1.0, pCol: '#9b59b6'}
];

function createSelectMenu() {
    let box = document.getElementById('roster');
    HEROES.forEach(h => {
        let ht = HERO_TEXTS[h.id]; let d = document.createElement('div');
        d.className='char-card'; d.style.setProperty('--card-color', h.col);
        d.innerHTML = `<h3 style="color:${h.col};">${ht.name}</h3><div style="font-size:11px;color:#aaa">${ht.desc}</div>`;
        d.onclick=()=>{startMission(h, false);}; box.appendChild(d);
    });
}

const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }); window.dispatchEvent(new Event('resize'));

// -------------------------------------------------------------
function drawRetroSprite(context, tx, ty, w, h, primeCol, t_type, hpRatio, phaseFlag, isFaceRight) {
    context.save(); context.translate(tx, ty); 
    if(!isFaceRight){ context.scale(-1, 1); context.translate(-w, 0); } 

    let bx = 0; let bw = w; 
    context.fillStyle = '#000'; context.fillRect(bx-2, -2, bw+4, h+4); 
    context.fillStyle = primeCol; context.fillRect(bx, 0, bw, h);

    if (t_type === 'player'){
        context.fillStyle = '#34495e'; context.fillRect(bx, h/2, bw, h/2); 
        context.fillStyle = '#fff'; context.fillRect(bx+bw-12, 10, 8, 8); 
        context.fillStyle = primeCol; context.fillRect(bx-4, 8, 8, 20); 
        if(kd('KeyU')){ context.fillStyle='#f1c40f'; context.globalAlpha=0.5; context.beginPath(); context.arc(bw/2, h/2, w+5, 0, Math.PI*2); context.fill(); context.globalAlpha=1; }
    }
    else if(t_type === 'bomber') {
        let inflate = 1.0 + (1-hpRatio)*0.5; context.scale(1, inflate); 
        context.fillStyle='#d35400'; context.fillRect(bx, h/3, bw, h*0.6); 
        context.fillStyle='#000'; context.fillRect(bx+bw/2, 5, 4, 15); 
        context.fillStyle='#e74c3c'; context.fillRect(bx+bw-15, h/2, 12, 8); 
    }
    else if(t_type === 'shield'){
        context.fillStyle = '#7f8c8d'; context.fillRect(bx, 5, bw, h); 
        context.fillStyle = '#ecf0f1'; context.fillRect(bw-8, 0, 15, h+5); 
        context.fillStyle = '#f1c40f'; context.fillRect(bw-4, h/3, 7, 20); 
    }
    else if(t_type === 'ninja'){
        context.fillStyle = '#2c3e50'; context.fillRect(bx, 0, bw, h); 
        context.fillStyle = '#e74c3c'; context.fillRect(bx-4, 12, bw+8, 8); 
        context.fillStyle = '#fff'; context.fillRect(bx+bw-8, 14, 4, 4); 
    }
    else if(t_type === 'flyer'){
        context.fillStyle = '#16a085'; context.beginPath(); context.arc(bw/2, h/2, w/2, 0, Math.PI*2); context.fill();
        context.fillStyle='#ecf0f1'; context.fillRect(bx-15, h/4, 25, 8); context.fillRect(bx-15, h/1.5, 20, 6); 
        if(phaseFlag!==99){ context.fillStyle='#e74c3c'; context.fillRect(bx+bw-12, h/2-6, 12, 12); } // 99 means sleeping
    }
    else if(t_type === 'ghost'){
        context.fillStyle = 'rgba(236, 240, 241, 0.7)'; context.beginPath(); context.arc(bw/2, h/2, w/2, 0, Math.PI*2); context.fill();
        context.fillStyle = '#000'; context.fillRect(bx+bw-12, h/2-5, 6, 6);
    }
    else if(t_type === 'thwomp'){
        context.fillStyle = '#7f8c8d'; context.fillRect(bx, 0, bw, h);
        context.fillStyle = '#2c3e50'; context.fillRect(bx+10, h-10, bw-20, 10); // spikes
        context.fillStyle = '#e74c3c'; context.fillRect(bx+10, 10, 15, 10); context.fillRect(bx+bw-25, 10, 15, 10); // angry eyes
    }
    else if(t_type === 'boss'){
        let color = phaseFlag===1 ? '#e67e22' : phaseFlag===2 ? '#9b59b6' : '#e74c3c'; 
        context.fillStyle = '#2c3e50'; context.fillRect(0,0, w, h);
        context.fillStyle = color; context.fillRect(4,4, w-8, h-8);
        context.fillStyle = '#000'; context.fillRect(w/2, 20, w/2, 20); 
        context.fillStyle = phaseFlag>2 ? '#fff':'red'; context.fillRect(w/2+10, 25, 15,10); 
        context.fillStyle='#f1c40f'; context.fillRect(-10, 0, 30, 25); 
        if(phaseFlag>=2) { context.fillStyle='cyan'; context.fillRect(w/2, h/2, w+30, 8); } 
    }
    else {
        context.fillStyle = primeCol; context.fillRect(bx, 0, bw, h);
        context.fillStyle = '#000'; context.fillRect(bx+bw-12, 12, 8,8);
        if(t_type === 'shooter') { context.fillStyle='#2c3e50'; context.fillRect(bx+bw-4, 25, 18, 6); } 
        if(t_type === 'tank') { context.fillStyle='#95a5a6'; context.fillRect(bx-5, h/3, bw+10, h/2); } 
    }
    context.restore();
}
// -------------------------------------------------------------

let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[], drops=[], coins_arr=[];
let currentMap = MAPS[1]; let globalStage = 1; let f=0; let shakeV=0, camX=0; let shards=0;
let isPaused = false, pipe = null, cloverChest = null;
function doShake(amt){shakeV=amt*5;} 

function togglePause() {
    if(!pl || pl.hp<=0 || globalStage>20) return; 
    isPaused = !isPaused; document.getElementById('pause-screen').classList.toggle('hidden', !isPaused);
    if(!isPaused) for(let k in activeKeys) activeKeys[k] = false; 
}

class Pipe { constructor(x) { this.w = 80; this.h = 100; this.x = x - this.w; this.y = canvas.height - 80 - this.h; }
    draw() {
        ctx.fillStyle = '#27ae60'; ctx.fillRect(this.x, this.y, this.w, this.h); ctx.fillStyle = '#2ecc71'; ctx.fillRect(this.x-10, this.y, this.w+20, 30);
        ctx.strokeStyle = '#000'; ctx.lineWidth=3; ctx.strokeRect(this.x, this.y, this.w, this.h); ctx.strokeRect(this.x-10, this.y, this.w+20, 30);
        ctx.fillStyle = 'white'; ctx.font="20px Arial"; ctx.fillText("⬇ S", this.x+20, this.y-20);
    }
}
class Drop {
    constructor(x,y, isB) { this.x=x; this.y=y; this.w=20; this.h=20; this.vy=-8; this.isB=isB;}
    upd() { this.vy+=0.5; this.y+=this.vy; if(this.y+this.h > canvas.height-80){this.y=canvas.height-80-this.h; this.vy=-this.vy*0.3;}
        if(intersect(this,pl)){
            if(this.isB){pl.maxHp+=25; pl.maxEn+=25; pl.hp=pl.maxHp; pl.en=pl.maxEn; makeFX(this.x,this.y, 25,'#f1c40f','boom');}
            else { pl.hp=Math.min(pl.hp+20, pl.maxHp); makeFX(this.x,this.y, 10,'#2ecc71','spark'); } return true;
        } return false;
    }
    draw() { ctx.fillStyle=this.isB?'#f1c40f':'#2ecc71'; ctx.fillRect(this.x,this.y,this.w,this.h); ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.strokeRect(this.x,this.y,this.w,this.h); ctx.fillStyle='#fff'; ctx.font="16px Arial"; ctx.fillText(this.isB?"★":"♥",this.x+2,this.y+16); }
}
class Coin {
    constructor(x,y){this.x=x; this.y=y; this.w=15; this.h=15;}
    upd(){ if(intersect(this,pl)){ shards+=5; makeFX(this.x,this.y,3,'#f1c40f','spark'); return true; } return false; }
    draw(){ ctx.fillStyle='#f1c40f'; ctx.beginPath(); ctx.arc(this.x+this.w/2, this.y+this.h/2, this.w/2, 0, Math.PI*2); ctx.fill(); ctx.strokeStyle='#fff'; ctx.stroke(); }
}

class Player {
    constructor(c){
        this.w=38; this.h=64; this.x=100; this.y=0; this.vx=0; this.vy=0; this.c = c; this.maxHp=c.maxHp; this.hp=this.maxHp; this.maxEn=c.maxEn; this.en=this.maxEn;
        this.facing = 1; this.grounded = false; this.iFrames = 0; this.chargeI = 0; this.atkWait = {}; this.jCount=0;
    }
    upd() {
        if(this.hp<=0) return; this.hp = Math.min(this.hp+this.c.hpRegen, this.maxHp); if(this.iFrames>0) this.iFrames--;
        
        let crch=kd('KeyS'); let sprt=(kd('ShiftLeft')||kd('ShiftRight')); let chu=kd('KeyU'); let chi=kd('KeyI');
        if(crch && !chi){ if(this.h!==38) {this.y+=26; this.h=38; this.vx*=0.4;} } else { if(this.h!==64) {this.y-=26; this.h=64;} }

        if(chi){ this.chargeI=Math.min(this.chargeI+2, 220); makeFX(this.x+this.w/2, this.y+this.h/2,1,this.c.pCol,'spark'); 
                 if(Math.floor(this.chargeI)%10==0) doShake(0.5); 
        } else if(this.chargeI>0){
            let dmg = this.chargeI * 2.5 * this.c.dmgMult; let s = this.chargeI/2.5;
            p_pr.push({x:this.facing>0?this.x+this.w:this.x-s, y:this.y+20-s/2, dir:this.facing, s:25, dmg:dmg, size:s, color:this.c.pCol, isHoming:true});
            this.vx-=(this.chargeI/8)*this.facing; this.chargeI=0; doShake(5);
        }

        let speed = this.c.speed; if(sprt) speed*=1.8; if(chu || chi || crch) speed*=0.25;
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
                    this.en=0; p_pr.push({x:this.facing>0?this.x+this.w:this.x-100, y:this.y-10, dir:this.facing, s:15, dmg:450*this.c.dmgMult, size:100, color:'#e74c3c', isHoming:true});
                    this.vx -= 18*this.facing; doShake(10);
                } this.atkWait['KeyY']=true; 
            } else if(!kd('KeyY')) this.atkWait['KeyY']=false;
        }

        this.vy+=0.6; this.x+=this.vx; this.y+=this.vy; this.vx*=0.82;
        if(this.x < 10) {this.x=10; this.vx=0;}
        if(this.x+this.w > currentMap.length) {this.x=currentMap.length-this.w; this.vx=0;}

        this.physicsWorld();

        // PIPE LOGIC
        if(pipe && intersect(this,pipe) && crch && this.grounded){
             let aliveEm = 0; e_arr.forEach(e=>{if(Math.abs(e.x-this.x)<800) aliveEm++;});
             if(aliveEm===0) { pl.hp = Math.min(pl.hp+(pl.maxHp*0.3), pl.maxHp); makeFX(this.x,this.y, 40,'#fff','boom'); globalStage++; loadStg(globalStage); }
        }
    }

    physicsWorld() {
        let isG=false; let flY = canvas.height-80; 
        
        // Pits!
        let falling = false;
        currentMap.pits.forEach(p => { if(this.x+this.w/2 > p.x && this.x+this.w/2 < p.x+p.w) falling=true; });
        
        if(!falling && this.y+this.h >= flY){ this.y=flY-this.h; this.vy=0; isG=true; }
        else if(this.y > canvas.height + 200) { this.hp = 0; return; } // Died in pit
        
        // Platforms
        currentMap.platforms.forEach(p => { 
            let pFY = canvas.height-p.y_offset;
            if(this.vy>=0 && this.y+this.h>=pFY-16 && this.y+this.h<=pFY+16 && this.x+this.w>p.x && this.x<p.x+p.w) {this.y=pFY-this.h; this.vy=0; isG=true;}
        });

        // Walls (X-axis blocking)
        currentMap.walls.forEach(w => {
            let wY = flY - w.h;
            if(this.y+this.h > wY && this.x+this.w > w.x && this.x < w.x+50) {
                if(this.vx > 0 && this.x < w.x) { this.x = w.x-this.w; this.vx=0; }
                else if(this.vx < 0 && this.x > w.x) { this.x = w.x+50; this.vx=0; }
            }
        });

        if(isG){this.jCount=0; this.grounded=true;} else this.grounded=false;
    }

    shK(k, t, c, dmg, s){
        if(kd(k)){ if(!this.atkWait[k] && this.en>=c) {
            this.en-=c; p_pr.push({x:this.facing>0?this.x+this.w:this.x, y:this.y+this.h/3, dir:this.facing, s:18, dmg:dmg, size:s, color:this.c.pCol, isHoming:false});
            this.vx -= (c/6)*this.facing; this.atkWait[k]=true;
        } } else this.atkWait[k]=false;
    }

    draw() {
        if(this.iFrames>0 && Math.floor(f/4)%2===0) ctx.globalAlpha=0.4;
        drawRetroSprite(ctx, this.x, this.y, this.w, this.h, this.c.col, 'player', 1.0, 0, this.facing>0);
        if(this.chargeI>0){ ctx.fillStyle=this.c.pCol; ctx.beginPath(); ctx.arc(this.x+this.w/2, this.y+this.h/2, this.chargeI/2.5, 0, Math.PI*2); ctx.fill(); }
        ctx.globalAlpha=1;
    }
}

class Enemy {
    constructor(x, ty) {
        this.ty=ty; this.w=45; this.h=55; this.isAggro=false;
        this.homeX = x; this.x = x; this.y = -100; 
        this.vx=0; this.vy=0; 
        this.s = 2.0; this.stC=120;
        this.maxHp = 60 + (globalStage*25);
        this.c = '#95a5a6'; this.atkWait = 0; 
        
        if(ty==='boss'){ this.maxHp=800+globalStage*150; this.w=90; this.h=110; this.s=1.5;}
        else if(ty==='tank'){ this.w=65; this.h=85; this.maxHp*=3.5; this.s=0.6;}
        else if(ty==='shield'){ this.w=50; this.c='#34495e'; this.maxHp*=2;}
        else if(ty==='bomber'){ this.w=35; this.h=45; this.maxHp*=0.7; this.s=3;}
        else if(ty==='flyer') { this.maxHp*=0.6; this.s=1.5; }
        else if(ty==='ninja') { this.maxHp*=0.8; this.s=3.5; }
        else if(ty==='ghost') { this.maxHp*=0.5; this.s=1.2; }
        else if(ty==='thwomp') { this.w=80; this.h=80; this.maxHp*=5; this.y=50; this.s=0; }
        else if(ty==='shooter'){ this.s=1; this.stC = 120 - Math.min(60, globalStage*2); } 

        this.hp = this.maxHp; this.phase = 1;
    }

    upd() {
        let dx = pl.x - this.x; let isFDir = (dx>0)?1:-1;
        let flY = canvas.height-80; 

        if(this.ty === 'thwomp') {
            if(!this.isAggro && Math.abs(dx) < 100) { this.isAggro=true; this.vy=15; } // drop!
            if(this.isAggro) {
                this.y+=this.vy; if(this.y+this.h >= flY) { this.y=flY-this.h; this.vy=0; doShake(5); this.isAggro=false; this.hp=-999; } // dies after drop
            }
            if(intersect(this, pl)) { pl.hp-=50; pl.iFrames=40; pl.vx=dx<0?15:-15; pl.vy=-10; }
            return;
        }

        if(!this.isAggro){ 
            if(Math.abs(dx)<800) this.isAggro=true; 
            else if(this.ty!=='flyer') this.vx = Math.sin(f/60)*this.s*0.5;
        }
        else {
            if(this.ty==='boss') {
                if(this.hp/this.maxHp < 0.3) this.phase=3; else if(this.hp/this.maxHp < 0.6) this.phase=2;
                let curSp = (this.phase===3)? 3 : (this.phase===2)? 2 : 1.2; this.atkWait--;
                if(this.phase===1) { if(Math.abs(dx)>20) this.vx=isFDir*curSp; }
                else if (this.phase===2) { this.vx = isFDir * curSp; if(this.atkWait<=0 && Math.abs(dx)>150){ this.atkWait=90; pr_arr.push({x:this.x+this.w/2, y:this.y+30, dx:isFDir*10, dy:2, life:180, isHoming:true}); } }
                else if(this.phase===3) { if(this.atkWait>0){ this.vx = isFDir*6; } else { this.vx = isFDir*curSp; } if(f%200===0){ this.atkWait=30; this.vy=-8; makeFX(this.x,this.y,10,'red','boom');} }
            }
            else if (this.ty==='flyer'){ this.x += isFDir * this.s; this.y = pl.y - 150 + Math.sin(f/30)*60; }
            else if (this.ty==='ghost'){ this.x += isFDir*this.s; this.y += (pl.y-this.y)>0?this.s:-this.s; } // ignores gravity
            else if (this.ty==='bomber') { if(Math.abs(dx)<50) this.dieAndExplode(); this.vx = isFDir * this.s; }
            else if(this.ty==='shield' || this.ty==='tank') { this.vx = isFDir * this.s; }
            else if (this.ty==='ninja'){ this.atkWait--; if(this.atkWait>20) this.vx = isFDir*1.5; else if(this.atkWait>0){this.vx=isFDir*12; this.vy=-2; } else this.atkWait=90;}
            else if (this.ty==='shooter') { this.atkWait--; if(Math.abs(dx)>450) this.vx = isFDir*this.s; else this.vx*=0.8;
                 if(this.atkWait<=0) { this.atkWait = this.stC; pr_arr.push({x:this.x+20,y:this.y+20, dx:isFDir*8, dy:0, life:180, isHoming:true});}
            }
            else if (this.ty==='summoner') {
                 if(Math.abs(dx)<600){this.vx = isFDir* -1.2;} else this.vx*=0.8; 
                 this.atkWait--; if(this.atkWait<=0){ this.atkWait=200; e_arr.push(new Enemy(this.x, 'jumper')); e_arr[e_arr.length-1].isAggro=true; }
            }
            else if(this.ty==='jumper') { this.vx=isFDir*1.6; this.atkWait--; if(this.atkWait<=0 && this.y+this.h>=flY-20) {this.vy=-14; this.atkWait=75;}}
            else { this.vx = isFDir*this.s; } 
        }

        if(this.ty!=='ghost' && this.ty!=='flyer') {
            this.vy+=0.6; this.y+=this.vy; this.x+=this.vx;
            let isGe=false; if(this.y+this.h>=flY){this.y=flY-this.h; this.vy=0; isGe=true;}
            
            if(!isGe && this.ty!=='jumper') {
                 currentMap.platforms.forEach(p=>{
                    let py = canvas.height-p.y_offset;
                    if(this.vy>=0 && this.y+this.h>=py-15 && this.y+this.h<=py+15 && this.x+this.w>p.x && this.x<p.x+p.w) {this.y=py-this.h; this.vy=0;}
                 });
            }
            currentMap.walls.forEach(w => {
                let wY = flY - w.h;
                if(this.y+this.h > wY && this.x+this.w > w.x && this.x < w.x+50) {
                    if(this.vx > 0 && this.x < w.x) { this.x = w.x-this.w; this.vx*=-1; }
                    else if(this.vx < 0 && this.x > w.x) { this.x = w.x+50; this.vx*=-1; }
                }
            });
        } else {
            this.x+=this.vx;
        }

        if(this.isAggro && pl.iFrames<=0 && intersect(this, pl)) {
            let dg = (this.ty==='boss')? 30: (this.ty==='tank')? 22 : 12; 
            pl.hp -= dg; pl.vx = dx<0?15:-15; pl.vy=-10; pl.iFrames=50; doShake(3);
        }
    }
    
    dieAndExplode() {
         makeFX(this.x+this.w/2, this.y+this.h/2, 60, '#e67e22', 'boom'); 
         if(intersect({x:this.x-150, y:this.y-150, w:300, h:300}, pl) && pl.iFrames<=0) {
             pl.hp -= 40; pl.iFrames=40; pl.vx = pl.x<this.x?-20:20; pl.vy=-10; doShake(8);
         }
         this.hp = -999; 
    }

    draw() { drawRetroSprite(ctx, this.x, this.y, this.w, this.h, this.c, this.ty, this.hp/this.maxHp, this.isAggro?this.phase:99, pl.x > this.x); 
        ctx.fillStyle='#000'; ctx.fillRect(this.x, this.y-10, this.w,4); ctx.fillStyle='red'; ctx.fillRect(this.x,this.y-10, this.w*(Math.max(0,this.hp)/this.maxHp), 4);
    }
}

class CloverChest {
    constructor(x) { this.x=x; this.y=canvas.height-180; this.w=100; this.h=100; this.hp=600; this.maxHp=600; }
    draw(){ ctx.fillStyle='#f1c40f'; ctx.fillRect(this.x,this.y,this.w,this.h); ctx.fillStyle='#000'; ctx.fillRect(this.x+this.w/2-5, this.y+30, 10,20);
            ctx.strokeStyle='#fff'; ctx.lineWidth=4; ctx.strokeRect(this.x,this.y,this.w,this.h); 
            ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-20, this.w*(this.hp/this.maxHp),10);
            ctx.fillStyle='#fff'; ctx.font="bold 20px Rubik"; ctx.fillText("CLOVER", this.x+10, this.y-35);
    }
}

function makeFX(x,y,q,c,m) { for(let i=0;i<q;i++) fx.push({ x:x, y:y, vx:(Math.random()-0.5)*(m==='boom'?16:4), vy:(m==='beam')?-(Math.random()*8): (Math.random()-0.5)*(m==='boom'?16:4), col:c, l: (m==='spark')?12:20, s: (m==='boom')?Math.random()*6+4 : 3}); }

function loadStg(s_N) {
    let tmap = MAPS[s_N > 20 ? 20 : s_N]; currentMap = tmap;
    document.getElementById('stage-info').innerText = tmap.name; document.getElementById('stage-info').style.boxShadow=`0 0 10px ${tmap.bg}`;
    e_arr=[]; pr_arr=[]; p_pr=[]; drops=[]; coins_arr=[]; pipe=null; cloverChest=null; 

    // Coins
    tmap.coins.forEach(c => coins_arr.push(new Coin(c.x, canvas.height-c.y_offset)));

    // Monsters
    if(tmap.is_boss) { e_arr.push(new Enemy(tmap.length - 800, 'boss')); } 
    else { 
        let ec = 15 + Math.floor(s_N*2); // הרבה מפלצות ל-10,000 פיקסלים
        for(let k=0; k<ec; k++){ 
            let ty=tmap.enemies[Math.floor(Math.random()*tmap.enemies.length)]; 
            e_arr.push(new Enemy(1000 + (k* (tmap.length/ec)), ty)); 
        } 
    }
    
    if(s_N!==20) pipe = new Pipe(tmap.length); 
    else cloverChest = new CloverChest(tmap.length - 500);
}

function startMission(charData, devFlag) {
    p_class = charData; globalStage = devFlag ? parseInt(document.getElementById('dev-stage').value) : 1;
    document.getElementById('select-screen').classList.add('hidden'); document.getElementById('ui-layer').classList.remove('hidden');
    pl = new Player(charData); if(devFlag){pl.maxHp=5000; pl.hp=5000; pl.en=5000; pl.maxEn=5000;}
    loadStg(globalStage); requestAnimationFrame(sysLoop);
}

function sysLoop() {
    if(isPaused){requestAnimationFrame(sysLoop); return; } f++;
    if(pl.hp<=0){ document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('death-screen').classList.remove('hidden'); document.getElementById('final-lvl').innerText=globalStage; return;}

    pl.upd();
    
    for(let i=coins_arr.length-1; i>=0; i--) { if(coins_arr[i].upd()) coins_arr.splice(i,1); }

    for(let i=e_arr.length-1; i>=0; i--) { let e=e_arr[i]; e.upd(); 
        if(e.hp<=0) { if(e.ty==='bomber')e.dieAndExplode(); else {makeFX(e.x+20,e.y+20,30,'#f1c40f','boom'); drops.push(new Drop(e.x,e.y, e.ty==='boss')); } e_arr.splice(i,1); }
    }
    
    if(cloverChest && cloverChest.hp<=0) { document.getElementById('ui-layer').classList.add('hidden'); document.getElementById('victory-screen').classList.remove('hidden'); return; }

    for(let i=drops.length-1; i>=0; i--) { if(drops[i].upd()) drops.splice(i,1); }

    // Enmy Proj (Homing)
    for(let i=pr_arr.length-1; i>=0; i--){ let b=pr_arr[i]; 
         if(b.isHoming && b.life>0){ b.life--; let ta = Math.atan2((pl.y+30)-b.y, (pl.x+15)-b.x); b.dx += Math.cos(ta)*0.5; b.dy += Math.sin(ta)*0.5; }
         b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 1, '#e74c3c', 'spark'); 
         if(intersect({x:b.x,y:b.y,w:10,h:10}, pl)) { if (pl.iFrames<=0) { pl.hp-=18; pl.iFrames=45; pl.vx += b.dx>0?8:-8; doShake(3); } pr_arr.splice(i,1); continue; }
         if(b.y>canvas.height || b.y<0 || Math.abs(b.x-pl.x)>2000) pr_arr.splice(i,1);
    }
    
    for(let i=p_pr.length-1; i>=0; i--){ let b = p_pr[i]; 
        if(b.isHoming){
            let t=null; let md=1500; e_arr.forEach(e=>{let d=Math.abs(e.x-b.x); if(d<md){md=d;t=e;}});
            if(t){let ta = Math.atan2((t.y+20)-b.y, (t.x+20)-b.x); b.x += Math.cos(ta)*b.s; b.y+=Math.sin(ta)*b.s;} else {b.x+=b.dir*b.s;}
        }else{ b.x += b.dir*b.s; }
        makeFX(b.x,b.y,1,b.color,'spark');

        let isDel = false; let projRecHit = {x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size};

        if(cloverChest && intersect(projRecHit, cloverChest)) { cloverChest.hp-=b.dmg; makeFX(b.x, b.y, 5, '#2ecc71', 'boom'); isDel=true; doShake(1.5); } 
        else {
             for(let j=e_arr.length-1; j>=0; j--){ let te = e_arr[j];
                  if(intersect(projRecHit, te)) {
                      let sameDirFacing = (te.x > pl.x) ? (b.dir===1) : (b.dir===-1); 
                      if (te.ty==='shield' && sameDirFacing && b.size < 40){ 
                           b.dir*=-1; pr_arr.push({x:b.x, y:b.y, dx:b.dir*10, dy:0, life:0}); isDel=true; makeFX(b.x, b.y, 15, '#fff', 'spark'); doShake(1); break;
                      } 
                      te.hp-=b.dmg; makeFX(b.x,b.y,8,b.color,'boom'); isDel=true; doShake((b.dmg)/25); te.vx += b.dir*8;
                      if(p_class.id==='dark'){pl.hp=Math.min(pl.maxHp,pl.hp+(b.dmg*0.035));} te.isAggro=true; break;
                  }
             }
        }
        if(isDel || b.y>canvas.height || Math.abs(b.x-pl.x)>1500) p_pr.splice(i,1);
    }

    for(let i=fx.length-1; i>=0; i--) { fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--; if(fx[i].l<=0) fx.splice(i,1); }
    
    let cxT = pl.x - canvas.width/2 + 100; if(cxT<0) cxT=0; camX += (cxT-camX)*0.08; 
    let S_X = camX, S_Y = 0; if(shakeV>0){ S_X+=(Math.random()-0.5)*shakeV; S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.8;} if(shakeV<0.4) shakeV=0;
    
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    ctx.fillStyle='rgba(255,255,255,0.08)'; for(let ds=0;ds<60;ds++) { let pX = ((ds*584)-(camX*0.06))%canvas.width; if(pX<0)pX+=canvas.width; ctx.fillRect(pX,(ds*4113)%canvas.height, 4+(ds%2)*2,4+(ds%2)*2); }
    
    ctx.save(); ctx.translate(-S_X, S_Y); 
    
    let baseFY = canvas.height-80;
    ctx.fillStyle = currentMap.floor; ctx.fillRect(S_X-200, baseFY, canvas.width+500, 300);
    ctx.strokeStyle='rgba(0,0,0,0.6)'; for(let xk=S_X-(S_X%100); xk<S_X+canvas.width+400; xk+=100) { ctx.beginPath(); ctx.moveTo(xk, baseFY); ctx.lineTo(xk, canvas.height); ctx.stroke(); }

    // Pits (Black rectangles over floor)
    currentMap.pits.forEach(p => { ctx.fillStyle='#000'; ctx.fillRect(p.x, baseFY, p.w, 300); });

    // Walls
    currentMap.walls.forEach(w => { ctx.fillStyle=currentMap.floor; ctx.fillRect(w.x, baseFY-w.h, 50, w.h); ctx.strokeStyle='#000'; ctx.strokeRect(w.x, baseFY-w.h, 50, w.h); });

    currentMap.platforms.forEach(p=>{
        let pY = canvas.height-p.y_offset;
        ctx.fillStyle = currentMap.floor; ctx.fillRect(p.x,pY,p.w,p.h);
        ctx.fillStyle='rgba(0,0,0,0.4)'; ctx.fillRect(p.x,pY+p.h-4,p.w,4);
    });

    if(pipe) pipe.draw(); if(cloverChest) cloverChest.draw(); drops.forEach(d=>d.draw()); coins_arr.forEach(c=>c.draw());
    pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#e74c3c'; pr_arr.forEach(b=>{ctx.fillRect(b.x-6,b.y-6,12,12);}); 
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.shadowBlur=15; ctx.shadowColor=b.color; ctx.beginPath(); ctx.arc(b.x,b.y,b.size,0,Math.PI*2); ctx.fill(); ctx.shadowBlur=0;});
    fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);}); ctx.globalAlpha=1;
    
    ctx.restore();
    
    document.getElementById('hp-bar').style.width=Math.max(0,(pl.hp/pl.maxHp)*100)+'%'; document.getElementById('hp-t').innerText=Math.floor(pl.hp)+"/"+pl.maxHp;
    document.getElementById('en-bar').style.width=Math.max(0,(pl.en/pl.maxEn)*100)+'%'; document.getElementById('en-t').innerText=Math.floor(pl.en)+"/"+pl.maxEn;
    document.getElementById('shards-hud').innerText = "💎 " + shards;
    
    requestAnimationFrame(sysLoop);
}

createSelectMenu();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
