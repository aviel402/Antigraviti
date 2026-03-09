from flask import Flask, render_template_string, jsonify, request
import json
import maps9  # הייבוא של קובץ המפות החדש שיצרנו!

app = Flask(__name__)
app.secret_key = 'clover_fixed_key_v3_indie'

PLAYER_DATA = {"shards": 0, "max_stage_reached": 1}

@app.route('/')
def idx():
    # שליפת המפות והמרתן למחרוזת שנוכל להזריק כמשתנה JS ב-HTML
    game_maps = maps9.generate_maps()
    return render_template_string(GAME_HTML, maps_json=json.dumps(game_maps))

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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Origins</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 100; 
            background: linear-gradient(135deg, rgba(5,5,10,0.95), rgba(20,20,30,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        /* Titles & UI Typography */
        h1.title { font-family: 'Righteous', cursive; font-size: 80px; margin:0; text-transform: uppercase;
                   background: -webkit-linear-gradient(#f1c40f, #e67e22); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 0px 20px rgba(241,196,15,0.4));}
        
        /* Character Select Screen */
        .char-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; width: 80%; max-width: 1200px; margin-top:30px; }
        .char-card { background: rgba(0,0,0,0.5); border: 2px solid #555; padding: 20px; border-radius: 12px; cursor: pointer; text-align: center; transition: 0.3s; position: relative; overflow: hidden; }
        .char-card:hover { transform: translateY(-10px); box-shadow: 0 10px 20px rgba(0,0,0,0.5); border-color: var(--card-color);}
        .char-card h3 { margin-bottom: 5px; font-family: 'Righteous'; letter-spacing:1px; }
        .char-desc { font-size: 13px; color: #ccc; margin-top: 10px; line-height: 1.4; }
        
        /* In-game HUD - Glassmorphism style */
        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:10; display:flex; flex-direction:column; padding:20px; justify-content:space-between; }
        .glass-panel { background: rgba(255,255,255,0.05); backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; }
        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        
        /* Stats */
        .stat-bar-container { display: flex; align-items: center; margin-bottom:8px; width:300px;}
        .stat-icon { font-weight:900; margin-left: 10px; width:40px;}
        .bar-out { background: rgba(0,0,0,0.7); flex-grow: 1; height: 22px; border-radius: 20px; overflow:hidden; border: 2px solid rgba(255,255,255,0.2); }
        .bar-in { height:100%; transition: width 0.15s; position:relative; overflow:hidden;}
        /* Add glow to inner bar */
        .bar-in::after { content:""; position:absolute; top:0;left:0; right:0; height:5px; background:rgba(255,255,255,0.4); border-radius:20px; }

        .hp-bar { background: #e74c3c; box-shadow: 0 0 10px #e74c3c; }
        .en-bar { background: #3498db; box-shadow: 0 0 10px #3498db; }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Righteous'; font-size:24px; color:#fff; text-shadow:0 0 10px cyan;}

        .controls { align-self:flex-start; pointer-events: auto;}
        kbd { background: #111; border: 1px solid #444; border-bottom:3px solid #555; border-radius:4px; padding: 2px 8px; font-weight: bold; color:var(--gold);}

        /* On Screen Notifications */
        #stage-alert { position: absolute; top:40%; left:50%; transform: translate(-50%, -50%); font-family:'Righteous'; font-size: 70px; opacity:0; text-shadow: 0 0 20px cyan; letter-spacing:5px;}
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    <h1 class="title">BATTLE HUB</h1>
    <h2>בחר את השליט שלך</h2>
    <div class="char-grid" id="roster">
        <!-- Javascript fills this -->
    </div>
</div>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="glass-panel" style="direction: ltr; min-width:350px;">
            <div class="stat-bar-container">
                <span class="stat-icon" style="color:#e74c3c;">HP <span id="hp-t" style="font-size:12px;color:#aaa"></span></span>
                <div class="bar-out"><div class="bar-in hp-bar" id="hp-bar"></div></div>
            </div>
            <div class="stat-bar-container">
                <span class="stat-icon" style="color:#3498db;">EN <span id="en-t" style="font-size:12px;color:#aaa"></span></span>
                <div class="bar-out"><div class="bar-in en-bar" id="en-bar"></div></div>
            </div>
        </div>
        
        <div class="glass-panel stage-title" id="stage-info">STAGE 1: FORESTS</div>
        
        <div class="glass-panel" style="font-size:20px; color:#ff3b3b; font-family:'Righteous'; letter-spacing:2px; font-weight:900;" id="lock-hud">TARGET LOCKED E</div>
    </div>
    
    <div id="stage-alert">FIGHT!</div>

    <div class="glass-panel controls">
        <div><kbd>W</kbd> <kbd>A</kbd> <kbd>D</kbd> - זוז וקפוץ</div>
        <div><kbd>H</kbd> <kbd>J</kbd> <kbd>K</kbd> - סוגי ירייה  |  <kbd>Y</kbd> מיוחד (שלב 10)</div>
        <div><kbd>U</kbd> החזק - טען כוח (תזוזה איטית וספיגת אויר)</div>
        <div><kbd>E</kbd> כוונת אוטומטית נעילה - (מחליף אוטומטית בירוטוי!)</div>
    </div>
</div>

<div id="death-screen" class="screen hidden">
    <h1 class="title" style="color:#c0392b; -webkit-text-fill-color:unset; text-shadow:none;">SYSTEM FAILURE</h1>
    <h2>מתת בשלב <span id="final-lvl" style="color:red;"></span>. הגל איכשהו הצליח לשרוד...</h2>
    <button onclick="location.reload()" style="padding:15px 30px; background:red; border:none; border-radius:8px; color:white; font-size:20px; font-family:'Rubik'; font-weight:900; cursor:pointer;">RESTART SYSTEM</button>
</div>


<script>
// Maps JSON loaded from Server Side Python File securely.
const MAPS = {{ maps_json | safe }};

// Keys setup
const activeKeys = {};
window.addEventListener('keydown', e => { if(e.code==='Space') e.preventDefault(); activeKeys[e.code]=true;});
window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; }

// Heroes Definitions (Classes)
const HEROES =[
    { id: 'earth', name: 'אדמה', col: '#2ecc71', maxHp: 180, hpRegen: 0.01, speed: 0.7, jump: 12, maxEn: 100, dmgMult: 1.2, enCostMult: 1, pCol: '#27ae60', desc:'חיים כמעט בלתי נגמרים ומכה כואבת, אבל זז מאוד לאט.'},
    { id: 'fire', name: 'אש', col: '#e74c3c', maxHp: 80, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.8, enCostMult: 1, pCol: '#ff7979', desc:'עשוי מזכוכית. זז ממש מהיר ושורף אויבים עם בונוס נזק מטורף.'},
    { id: 'water', name: 'מים', col: '#3498db', maxHp: 110, hpRegen: 0.1, speed: 1.0, jump: 14, maxEn: 110, dmgMult: 1.0, enCostMult: 1, pCol: '#7ed6df', desc:'הממוצע המושלם. מתרפא באופן טבעי ומחדש חיים מהר יחסית בזמן הליכה.'},
    { id: 'air', name: 'אוויר', col: '#ecf0f1', maxHp: 90, hpRegen: 0, speed: 1.6, jump: 16, maxEn: 100, dmgMult: 0.8, enCostMult: 0.7, pCol: '#c7ecee', desc:'ריחוף גבוה מעל פלטפורמות, יכולות התחמקות נדירות - פגיעה נמוכה במטרות.'},
    { id: 'lightning', name: 'ברק', col: '#f1c40f', maxHp: 90, hpRegen: 0, speed: 2.0, jump: 13, maxEn: 100, dmgMult: 1.5, enCostMult: 1.5, pCol: '#f9ca24', desc:'טיל מבוזר במסך. עף מצד לצד מהר, נזק ענק אבל אנרגיה מתרוקנת מהר מאד.'},
    { id: 'magma', name: 'לבה', col: '#d35400', maxHp: 150, hpRegen: 0.05, speed: 0.6, jump: 11, maxEn: 100, dmgMult: 1.6, enCostMult: 1.2, pCol: '#eb4d4b', desc:'יוריות בגודל כדור הארץ - מוחצות כל דבר מסביב בזכות משקולת הנזק הכבד שלהם.'},
    { id: 'light', name: 'אור', col: '#ffffb3', maxHp: 100, hpRegen: 0.02, speed: 1.0, jump: 14, maxEn: 300, dmgMult: 0.9, enCostMult: 0.8, pCol: '#fff200', desc:'אנרגיה אין סופית. מחזיק מחסניות התקפה אדירות שיכולות לעצור יחידות ענקיות מבלי להיטען מחדש.'},
    { id: 'dark', name: 'חושך', col: '#8e44ad', maxHp: 85, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.0, enCostMult: 1.0, pCol: '#9b59b6', desc:'צייד אפל לילה אמיתי - *LIFESTEAL*: מקבל חיים עם כל כדור שהוא תוקע בגוף האויבים.'}
];

// Initialize Selection
function createSelectMenu() {
    let box = document.getElementById('roster');
    HEROES.forEach(h => {
        let div = document.createElement('div');
        div.className = 'char-card';
        div.style.setProperty('--card-color', h.col);
        div.innerHTML = `<h3 style="color:${h.col}; font-size:28px">${h.name}</h3><div class="char-desc">${h.desc}</div>`;
        div.onclick = () => { startMission(h); }
        box.appendChild(div);
    });
}

const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
function res() { canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }
window.addEventListener('resize',res); res();

// GAME VARIABLES
let p_class = null; let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[];
let currentMap = MAPS[1];
let wave = 1; let f=0; let shakeV=0, camX=0;

// HELPERS
function intersect(a,b){return!(b.x>a.x+a.w || b.x+b.w<a.x || b.y>a.y+a.h || b.y+b.h<a.y);}
function doShake(amt){shakeV=amt*3;}

// PLAYER LOGIC
class Player {
    constructor(c){
        this.w=35; this.h=65;
        this.x=200; this.y=0; this.vx=0; this.vy=0;
        this.c = c; // Save class stats
        this.maxHp=c.maxHp; this.hp=this.maxHp;
        this.maxEn=c.maxEn; this.en=this.maxEn;
        
        this.facing = 1; this.grounded = false; this.target = null;
        this.lockKeyTriggered = false; this.atkWait = {}; this.jCount = 0;
    }

    upd() {
        if(this.hp<=0) return;
        this.hp = Math.min(this.hp + this.c.hpRegen, this.maxHp);
        let chrg = kd('KeyU');
        
        // --- 1. MOVEMENT ---
        // NEW FEATURE: Allow slow walk and fast dash left right even when U pressed
        let applySpeed = this.c.speed;
        if(chrg) applySpeed *= 0.5; // Moving is slow while holding charge
        
        if(kd('KeyA')){ this.vx-=applySpeed; this.facing=-1; }
        if(kd('KeyD')){ this.vx+=applySpeed; this.facing= 1; }
        
        // Double jump rules + Jump Key Handler
        if(kd('KeyW') || kd('Space')) {
            if(!this.jHold) {
                if(this.jCount < 2) { 
                    this.vy = -this.c.jump; this.jCount++;
                    makeFX(this.x+this.w/2, this.y+this.h, 6, '#fff', 'spark');
                }
                this.jHold = true;
            }
        } else { this.jHold=false;}

        // --- 2. COMBAT ACTIONS ---
        if(chrg) {
            this.en = Math.min(this.en + 1.2, this.maxEn);
            makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'beam');
        } else {
            // Cannot shoot when charging
            this.sHand('KeyH', '1', 8 * this.c.enCostMult, 12 * this.c.dmgMult, 8);
            this.sHand('KeyJ', '2', 20 * this.c.enCostMult, 30 * this.c.dmgMult, 15);
            this.sHand('KeyK', '3', 45 * this.c.enCostMult, 70 * this.c.dmgMult, 25);
            this.sHand('KeyY', 'u', 100 * this.c.enCostMult, 250 * this.c.dmgMult, 50); // ultimate 
        }

        // --- 3. AUTO LOCKON FEATURE ---
        if(kd('KeyE')){
            if(!this.lockKeyTriggered){ this.swLock(); this.lockKeyTriggered=true;}
        } else {this.lockKeyTriggered=false;}

        // Check Target validation & Auto Switch
        if(this.target && this.target.hp <= 0){
             // CURRENT TARGET DEAD - Immediately find closest remaining enemy instead of null!
             this.target = null;
             this.findBestTarget();
        }

        // --- PHYSICS ---
        this.vy += 0.6; this.x+=this.vx; this.y+=this.vy; this.vx *= 0.8;
        if(this.x < 0){this.x=0; this.vx=0;}
        
        // Ground Math - Main floor at Canvas H - 80. + Checking maps Platforms.
        let isG=false; let floor_lvl = canvas.height-80;
        
        if(this.y+this.h > floor_lvl){
            this.y = floor_lvl-this.h; this.vy=0; isG=true;
        } else {
            // Hard coded flat platforms system to save context size. checks collisions from TOP only
            currentMap.platforms.forEach(pl_form => {
               // Only hit if coming from ABOVE the platform previously.
               let pFloorY = canvas.height-pl_form.y_offset;
               if(this.vy>=0 && this.y+this.h >= pFloorY - 10 && this.y+this.h <= pFloorY + 10 && this.x+this.w>pl_form.x && this.x < pl_form.x+pl_form.w){
                   this.y = pFloorY-this.h; this.vy=0; isG=true;
               }
            });
        }
        
        if(isG){this.jCount=0; this.grounded=true;} else{this.grounded=false;}
    }

    sHand(k,t,cost,dmg,size) {
        if(kd(k)){
            if(!this.atkWait[k]){
                if(t==='u' && wave < 10) return; // Ult disabled before wave 10
                if(this.en >= cost) {
                    this.en -= cost;
                    let speed = (t==='1')?18: (t==='u')?10 : 15;
                    p_pr.push({
                         x: this.facing>0? this.x+this.w : this.x, y: this.y+20, 
                         dir: this.facing, s:speed, dmg:dmg, size: size * (this.c.id==='magma'? 2:1), color: this.c.pCol, tgt: this.target
                    });
                    this.vx -= (cost/5)*this.facing; // Pushback physics
                }
                this.atkWait[k] = true;
            }
        }else{this.atkWait[k] = false;}
    }

    swLock() {
        if(this.target) this.target=null; else this.findBestTarget();
    }
    
    findBestTarget() {
        let maxDist = 1200; let trg = null;
        e_arr.forEach(e => {
           let d = Math.abs(e.x - this.x);
           // Must be relatively inside the view port to switch
           if(d < maxDist && e.x > this.x - 300 && e.x < this.x+900) { maxDist=d; trg=e; }
        });
        if(trg) {
            this.target=trg;
            doShake(1);
        }
    }

    draw() {
        ctx.save(); ctx.translate(this.x, this.y);
        ctx.fillStyle = this.c.col; 
        if(this.en > 90) ctx.shadowBlur = 10, ctx.shadowColor = this.c.col;
        ctx.fillRect(0,0,this.w,this.h);
        ctx.shadowBlur = 0;
        
        // Add white "Glow strip" on the edge based on direction (Stylistic visual)
        ctx.fillStyle='rgba(255,255,255,0.7)'; 
        if(this.facing>0) ctx.fillRect(this.w-4, 0, 4, this.h); else ctx.fillRect(0,0,4,this.h);

        // Reticle
        if(this.target){
             let rx = this.target.x + this.target.w/2 - this.x; let ry = this.target.y+this.target.h/2 - this.y;
             ctx.strokeStyle='#ff3838'; ctx.lineWidth=2; 
             ctx.beginPath(); ctx.moveTo(this.w/2, this.h/2); ctx.lineTo(rx,ry); ctx.stroke();
             // Drawing the reticle at end
             ctx.beginPath(); ctx.arc(rx,ry, 30+Math.sin(f/5)*10,0,Math.PI*2); ctx.stroke();
        }
        ctx.restore();
    }
}

class Enemy {
    constructor(x, ty) {
        this.x=x; this.y=0; this.ty = ty; // melee, shooter, jumper
        this.w = 40; this.h=50; this.vx=0; this.vy=0; 
        this.maxHp = 40 + (wave*15);
        if(ty==='boss'){ this.maxHp *= 15; this.w=120; this.h=120;}
        this.hp = this.maxHp; 
        
        // Behaviors & Stats
        this.col = (ty==='shooter')?'#f39c12': (ty==='jumper')?'#8e44ad': (ty==='boss')?'#c0392b' : '#34495e';
        this.s = (ty==='boss')?1 : (ty==='jumper')? 2 : (ty==='shooter')? 1.5 : 2;
        this.shClock = Math.random()*100; // Attack timer
    }
    
    upd() {
        let dx = pl.x - this.x; let flY = canvas.height-80;
        
        // 4 Types of Behavior Systems 
        if(this.ty === 'melee' || this.ty === 'boss'){
            if(Math.abs(dx)>2) this.vx = dx>0? this.s:-this.s;
            if(this.ty==='boss' && Math.random()<0.02 && e_arr.length<3) { e_arr.push(new Enemy(this.x, 'melee')); } // boss spawns minions
        }
        if(this.ty === 'shooter'){
            // Shoots at 400px radius, keeps distance otherwise
            if(Math.abs(dx) > 350) this.vx = dx>0? this.s:-this.s; else this.vx*=0.8;
            this.shClock--;
            if(this.shClock<=0) {
                 this.shClock=90;
                 pr_arr.push({x:this.x+20, y:this.y+20, dx:dx>0?8:-8, dy:0});
            }
        }
        if(this.ty === 'jumper'){
             this.vx = dx>0? this.s+1 : -(this.s+1);
             this.shClock--; if(this.shClock<=0 && this.y+this.h>=flY){ this.vy = -12; this.shClock=50;}
        }

        // Apply physical laws
        this.x+=this.vx; this.vy+=0.6; this.y+=this.vy;
        
        if(this.y+this.h > flY) { this.y=flY-this.h; this.vy=0; }
        
        // Deal Dmg touching player
        if(intersect(this,pl)){
            pl.hp -= this.ty==='boss'?2 : 0.6; 
            pl.vx = dx<0?8:-8;
            doShake(1);
        }
    }
    draw(){
        ctx.fillStyle = this.col; ctx.fillRect(this.x,this.y,this.w,this.h);
        ctx.fillStyle='#111'; ctx.fillRect(this.x, this.y-10, this.w, 5);
        ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.maxHp), 5);
        
        // draw funny pixel art eye 
        ctx.fillStyle='white'; 
        let fw = pl.x > this.x ? this.w-12 : 4; 
        ctx.fillRect(this.x+fw, this.y+8, 8,8);
        ctx.fillStyle='black'; ctx.fillRect(this.x+fw+2, this.y+10,4,4);
    }
}

// Particle Engine FX 
function makeFX(x,y,qty,col,mode) {
    for(let i=0;i<qty;i++){
        fx.push({ x:x, y:y, 
           vx:(Math.random()-0.5)*(mode==='boom'?10:4), vy:(mode==='beam')?-(Math.random()*4): (Math.random()-0.5)*(mode==='boom'?10:4), 
           col:col, l: (mode==='spark')?15:25, s: (mode==='boom')?Math.random()*8+2 : 3 
        });
    }
}

// System flow loops 
function loadWv() {
    let oldWave = wave; // We use JS side increment so we ignore 2nd param but we must define mapped theme!
    currentMap = MAPS[wave > 20 ? 20 : wave]; // Cap 20 max logic.
    
    // Server fetch purely passive (doesnt interrupt client loading!)
    fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'}, body:JSON.stringify({stage:wave, shards:20})});
    
    // Presenting HUD Texts 
    let stI = document.getElementById('stage-info');
    stI.innerText = currentMap.name;
    stI.style.border = `2px solid ${currentMap.bg}`; 
    stI.style.boxShadow = `0 0 10px ${currentMap.bg}`;
    
    let aBox = document.getElementById('stage-alert');
    aBox.innerText = currentMap.is_boss ? "BOSS ENGAGED" : `STAGE ${wave}`;
    aBox.style.color = currentMap.is_boss ? "#e74c3c" : "white";
    aBox.style.opacity = 1; setTimeout(()=>{ aBox.style.opacity = 0}, 2000);

    // Add elements safely
    e_arr =[]; pr_arr=[];
    if(currentMap.is_boss) {
        e_arr.push(new Enemy(pl.x + 1000, 'boss'));
    } else {
        // Build squad! Check maps allowable.
        let mQ = 2+Math.floor(wave/2);
        for(let z=0; z<mQ; z++){
            // Roll between 0 and allowable types length.
            let rTy = currentMap.enemies[Math.floor(Math.random() * currentMap.enemies.length)];
            e_arr.push(new Enemy(pl.x+600+(z*300), rTy));
        }
    }
}

function startMission(charConfig) {
    p_class = charConfig;
    document.getElementById('select-screen').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    pl = new Player(charConfig); wave=1; 
    loadWv(); requestAnimationFrame(sysLoop);
}

// RENDER AND COMPUTE LOOP. Heavy duty part! 
function sysLoop() {
    f++;
    if(pl.hp<=0) {
        document.getElementById('ui-layer').classList.add('hidden');
        let scr = document.getElementById('death-screen'); scr.classList.remove('hidden');
        document.getElementById('final-lvl').innerText=wave; return;
    }
    
    pl.upd();
    
    // Wave Control Trigger System : Automatically progress to next logic
    if(e_arr.length===0){
        wave++; pl.hp = Math.min(pl.hp+(pl.maxHp*0.2), pl.maxHp); 
        loadWv();
    }
    
    // Objects execution phase (Pyschokynetics + Colliders Math Core).
    e_arr.forEach((e,i)=>{ e.upd(); if(e.hp<=0) {makeFX(e.x+20,e.y+20,20,'#8e44ad','boom'); e_arr.splice(i,1);} });
    
    pr_arr.forEach((b,i)=>{ 
         b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 1, 'orange', 'spark'); 
         if(intersect({x:b.x,y:b.y,w:8,h:8}, pl)) { pl.hp-=12; pr_arr.splice(i,1); doShake(3); }
         if(b.y>canvas.height || b.x<camX || b.x>camX+canvas.width*2) pr_arr.splice(i,1);
    });

    p_pr.forEach((b,i)=>{ 
        // Implement Projectile AI curve
        if(b.tgt && b.tgt.hp>0){
            let tgAng = Math.atan2((b.tgt.y+20)-b.y, (b.tgt.x+20)-b.x);
            b.x += Math.cos(tgAng) * b.s; b.y += Math.sin(tgAng) * b.s;
        }else{ b.x += b.dir * b.s;}
        
        makeFX(b.x,b.y,2, b.color, 'spark');

        // Target Strike Checks O(M*N) simplified 
        let dflag = false;
        e_arr.forEach((te)=>{
             if(!dflag && intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, te)) {
                 te.hp-=b.dmg; makeFX(b.x,b.y,6,b.color,'boom'); dflag=true; doShake((b.dmg)/20);
                 te.vx += b.dir*6; // Punch weight on shot
                 
                 // UNIQUE BUFF (Dark mode Vampire / Lifesteal execution here!!!)
                 if(p_class.id === 'dark'){ pl.hp = Math.min(pl.maxHp, pl.hp+(b.dmg*0.02)); } 
             }
        });
        if(dflag || b.y>canvas.height || Math.abs(b.x-pl.x)>1800) {p_pr.splice(i,1);}
    });

    // Particle FX Updater Code Block : Optimizations by index slice!
    for(let i=fx.length-1; i>=0; i--) { 
        fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--;
        if(fx[i].l<=0) fx.splice(i,1); 
    }
    
    // CAMERA / MATRIX MANIPULATION SPACE! --------- ! !
    let cxTar = pl.x - canvas.width/2 + 100; if(cxTar<0) cxTar=0;
    camX += (cxTar-camX)*0.1; 
    let cm_S_X = camX; let cm_S_Y = 0;
    if(shakeV>0) {cm_S_X+=(Math.random()-0.5)*shakeV; cm_S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.9;}
    if(shakeV<0.5) shakeV=0;
    // ---------------------------------------------

    // DRAW SPACE (Paint screen from bottom up layers approach) ! 
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    
    // Big Background stars simulation / abstract art dots to present deep dimension...
    ctx.fillStyle='rgba(255,255,255,0.08)'; 
    for(let ds=0;ds<60;ds++) { let pxX = ((ds*219)-(camX*0.1))%canvas.width; if(pxX<0)pxX+=canvas.width; ctx.beginPath(); ctx.arc(pxX, (ds*1923)%canvas.height, 2+ds%3, 0,7); ctx.fill();}
    
    ctx.save(); ctx.translate(-cm_S_X, cm_S_Y); // TRANSLATE THE VIEW !!! 
    
    // BASE FLOOR Rendering engine segment // 
    ctx.fillStyle = currentMap.floor; 
    ctx.fillRect(cm_S_X - 100, canvas.height-80, canvas.width + 400, 300);
    // Grid Lines on floor using floor darker accent
    ctx.strokeStyle='rgba(0,0,0,0.3)';
    for(let xl=cm_S_X - 100; xl < cm_S_X+canvas.width+400; xl+=120){ ctx.beginPath(); ctx.moveTo(xl,canvas.height-80); ctx.lineTo(xl, canvas.height); ctx.stroke(); }

    // Map Specific Hovering Blocks drawing
    currentMap.platforms.forEach(pf => {
         let pY = canvas.height - pf.y_offset;
         // Draw glow underneath floating base
         ctx.fillStyle=currentMap.bg; ctx.shadowBlur=15; ctx.shadowColor=currentMap.floor; 
         ctx.fillRect(pf.x, pY, pf.w, pf.h);
         ctx.shadowBlur=0; 
         ctx.fillStyle=currentMap.floor; ctx.fillRect(pf.x+3, pY+3, pf.w-6, pf.h-6); 
    });

    pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#f39c12'; pr_arr.forEach(b=>{ctx.fillRect(b.x-4,b.y-4,8,8);}); // draw evil Bullets! 
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.beginPath(); ctx.arc(b.x,b.y,b.size,0,Math.PI*2); ctx.fill();});
    
    // Draw those sexy pixels to wrap up ! 
    fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);});
    ctx.globalAlpha=1;

    ctx.restore();
    // HTML DOM BARS OVERLAY WRAPPERS ! Update Texts without triggering Reflow. Only the essential!
    document.getElementById('hp-bar').style.width = Math.max(0,(pl.hp/pl.maxHp)*100)+'%';
    document.getElementById('hp-t').innerText = Math.floor(pl.hp)+"/"+pl.maxHp;
    document.getElementById('en-bar').style.width = Math.max(0,(pl.en/pl.maxEn)*100)+'%';
    document.getElementById('en-t').innerText = Math.floor(pl.en)+"/"+pl.maxEn;
    
    document.getElementById('lock-hud').style.opacity = pl.target ? 1: 0;
    
    requestAnimationFrame(sysLoop);
}
// Init The roster first so Player clicks one. Game loop waits nicely until clicking StartMision..
createSelectMenu();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("STARTING ENHANCED SYSTEM... Visit port 5009 !")
    app.run(port=5009, debug=True)
