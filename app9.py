from flask import Flask, render_template_string, jsonify, request
import json
import maps9

app = Flask(__name__)
app.secret_key = 'clover_indie_god_mode_v6'

PLAYER_DATA = {"shards": 0, "max_stage_reached": 1}

@app.route('/')
def idx():
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
    <title>CLOVER - Legend Maps update</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #f1c40f; }
        * { box-sizing: border-box; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; position: absolute; z-index: 1; }
        
        .screen { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 100; 
            background: linear-gradient(135deg, rgba(5,5,10,0.95), rgba(20,20,30,0.95)); display:flex; flex-direction:column; align-items:center; justify-content:center;}
        .hidden { display: none !important; opacity:0; pointer-events:none;}
        
        h1.title { font-family: 'Righteous', cursive; font-size: 80px; margin:0; text-transform: uppercase;
                   background: -webkit-linear-gradient(#f1c40f, #e67e22); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 0px 20px rgba(241,196,15,0.4));}
        
        .char-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; width: 80%; max-width: 1200px; margin-top:30px; }
        .char-card { background: rgba(0,0,0,0.5); border: 2px solid #555; padding: 20px; border-radius: 12px; cursor: pointer; text-align: center; transition: 0.3s; position: relative; overflow: hidden; }
        .char-card:hover { transform: translateY(-10px); box-shadow: 0 10px 20px rgba(0,0,0,0.5); border-color: var(--card-color);}
        .char-card h3 { margin-bottom: 5px; font-family: 'Righteous'; letter-spacing:1px; }
        .char-desc { font-size: 13px; color: #ccc; margin-top: 10px; line-height: 1.4; }
        
        #ui-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:10; display:flex; flex-direction:column; padding:20px; justify-content:space-between; }
        .glass-panel { background: rgba(255,255,255,0.05); backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; }
        .hud-top { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; }
        
        .stat-bar-container { display: flex; align-items: center; margin-bottom:8px; width:300px;}
        .stat-icon { font-weight:900; margin-left: 10px; width:40px;}
        .bar-out { background: rgba(0,0,0,0.7); flex-grow: 1; height: 22px; border-radius: 20px; overflow:hidden; border: 2px solid rgba(255,255,255,0.2); }
        .bar-in { height:100%; transition: width 0.15s; position:relative; overflow:hidden;}
        .bar-in::after { content:""; position:absolute; top:0;left:0; right:0; height:5px; background:rgba(255,255,255,0.4); border-radius:20px; }
        .hp-bar { background: #e74c3c; box-shadow: 0 0 10px #e74c3c; }
        .en-bar { background: #3498db; box-shadow: 0 0 10px #3498db; }
        
        .stage-title { position: absolute; left: 50%; transform: translateX(-50%); font-family: 'Righteous'; font-size:24px; color:#fff; text-shadow:0 0 10px cyan;}
        .controls { align-self:flex-start; pointer-events: auto;}
        kbd { background: #111; border: 1px solid #444; border-bottom:3px solid #555; border-radius:4px; padding: 2px 8px; font-weight: bold; color:var(--gold);}

        .pause-hud-btn { pointer-events: auto; padding: 12px 24px; font-family:'Righteous'; border-radius:8px; background: rgba(255,255,255,0.1); color:#fff; border: 1px solid rgba(255,255,255,0.3); font-size: 20px; cursor: pointer; backdrop-filter: blur(5px); transition:0.2s;}
        .pause-hud-btn:hover { background: rgba(255,255,255,0.3); box-shadow: 0 0 15px white;}

        #stage-alert { position: absolute; top:40%; left:50%; transform: translate(-50%, -50%); font-family:'Righteous'; font-size: 70px; opacity:0; text-shadow: 0 0 20px cyan; letter-spacing:5px;}

        .menu-btn { padding:15px 40px; border:2px solid #fff; border-radius:8px; color:white; font-size:24px; font-family:'Righteous'; background:transparent; cursor:pointer; margin-top:20px; text-transform:uppercase; transition:0.3s; width: 350px;}
        .menu-btn:hover { background:#fff; color:#000; box-shadow:0 0 20px #fff; transform: scale(1.05);}
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    <h1 class="title">BATTLE HUB</h1>
    <h2>בחר את הלוחם שלשלוט בהם זה חזק</h2>
    <div class="char-grid" id="roster"></div>
</div>

<div id="pause-screen" class="screen hidden" style="background: rgba(10, 15, 25, 0.9); z-index:9000;">
    <h1 class="title" style="filter: hue-rotate(90deg); -webkit-text-fill-color:white; margin-bottom: 20px;">הקפאת נתונים פעילה..</h1>
    <button class="menu-btn" onclick="togglePause()">▶ חזור עכשיו לשדה הקרב</button>
    <button class="menu-btn" onclick="location.reload()" style="background:#e74c3c; border-color:#e74c3c;">☒ חילוץ עצמי אחורה לתפריט דמויות</button>
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
        <div class="glass-panel stage-title" id="stage-info">...</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
             <button class="pause-hud-btn" onclick="togglePause()">⏸ PAUSE</button>
             <div class="glass-panel" style="font-size:18px; color:#ff3b3b; font-family:'Righteous'; font-weight:900;" id="lock-hud">🎯 TARGET LOCKED E</div>
        </div>
    </div>
    
    <div id="stage-alert">FIGHT!</div>

    <div class="glass-panel controls">
        <div><kbd>W</kbd> <kbd>A</kbd> <kbd>D</kbd> - להתרוצץ בפלטפורמות שעל המסך העצום</div>
        <div><kbd>H</kbd> <kbd>J</kbd> <kbd>K</kbd> - טקטיקות לחימה לפי התאמה של מד  |   <kbd>Y</kbd> לחתוך זמני הפעלה ברגע החשוב מ-שלב עשירייה!</div>
        <div><kbd>U</kbd> איש מים וחסות עילאית תפיח לחיי דמות חיש שבירת יצוריות בעוד ש... </div>
        <div><kbd>P</kbd> או <kbd>ESC</kbd> להצלת דפים פרימיטיבים ולדמות עצירה ננצח על פי הפגיון הזה תצלוני פאס </div>
    </div>
</div>

<div id="death-screen" class="screen hidden" style="z-index:9500;">
    <h1 class="title" style="color:#c0392b; -webkit-text-fill-color:unset; text-shadow:none;">CRITICAL HIT TAKEN..</h1>
    <h2>ניסיון מעורר ההשראה התגמר עקב מתאונת מישוש. החברה סקורה. עדכון למנהיג יגיע שנוחת עברת למערכת : <span id="final-lvl" style="color:var(--gold); font-size:30px;"></span> </h2>
    <button class="menu-btn" onclick="location.reload()" style="background:#e74c3c;">אתחל דמוית וממשר מקרבים רציניים! </button>
</div>

<script>
// Load unique generated map stages structures explicitly from py-module payload 
const MAPS = {{ maps_json | safe }};

const activeKeys = {};
window.addEventListener('keydown', e => { 
    if(e.code==='Space') e.preventDefault(); 
    if(e.code === 'KeyP' || e.code === 'Escape') togglePause();
    activeKeys[e.code]=true;
});
window.addEventListener('keyup', e => { activeKeys[e.code]=false; });
function kd(c) { return activeKeys[c]===true; }

function intersect(a,b){return!(b.x>a.x+a.w || b.x+b.w<a.x || b.y>a.y+a.h || b.y+b.h<a.y);}

// Roster definition mapped safely inside memory pool ...
const HEROES =[
    { id: 'earth', name: 'אדמה', col: '#2ecc71', maxHp: 180, hpRegen: 0.01, speed: 0.8, jump: 13, maxEn: 100, dmgMult: 1.2, enCostMult: 1, pCol: '#27ae60', desc:'חיים על חלל מוסך רכיש למתחילם אקראי.'},
    { id: 'fire', name: 'אש', col: '#e74c3c', maxHp: 80, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.8, enCostMult: 1, pCol: '#ff7979', desc:'בריסקוט נדיר - כעס עקוטים על לירות קופאות ללוהק.'},
    { id: 'water', name: 'מים', col: '#3498db', maxHp: 110, hpRegen: 0.15, speed: 1.0, jump: 14, maxEn: 110, dmgMult: 1.0, enCostMult: 1, pCol: '#7ed6df', desc:'מאמץ להחלק כוון עתידי יורד החוזקו יעל חליל קהילה'},
    { id: 'air', name: 'אוויר', col: '#ecf0f1', maxHp: 90, hpRegen: 0, speed: 1.6, jump: 16, maxEn: 100, dmgMult: 0.8, enCostMult: 0.7, pCol: '#c7ecee', desc:'המשאב היפהיפוט ביותר המכיילים אבק מפושט בשעוייות החרוטי ! '},
    { id: 'lightning', name: 'ברק', col: '#f1c40f', maxHp: 90, hpRegen: 0, speed: 2.0, jump: 13, maxEn: 100, dmgMult: 1.5, enCostMult: 1.5, pCol: '#f9ca24', desc:'טילים אינשטניים כפי סעדי המצבור שיפצע חובבי פיזו טירנודז !! '},
    { id: 'magma', name: 'לבה', col: '#d35400', maxHp: 150, hpRegen: 0.05, speed: 0.6, jump: 11, maxEn: 100, dmgMult: 1.6, enCostMult: 1.2, pCol: '#eb4d4b', desc:'לוהטת אש מספרי סיפוח אלוציוני משוטרת של חושן מגמת!'},
    { id: 'light', name: 'אור', col: '#ffffb3', maxHp: 100, hpRegen: 0.02, speed: 1.0, jump: 14, maxEn: 300, dmgMult: 0.9, enCostMult: 0.8, pCol: '#fff200', desc:'קווזיטיף לא מרעיף אבל מתנעל גייזיסט תודות לשובו מכל מי שקיף את סילונה ! !'},
    { id: 'dark', name: 'חושך', col: '#8e44ad', maxHp: 85, hpRegen: 0, speed: 1.2, jump: 14, maxEn: 120, dmgMult: 1.0, enCostMult: 1.0, pCol: '#9b59b6', desc:'שודד של החוליגיוני. LIFESTEAL מתועב הילולים מאנטי רצועות ירי טקתי.'}
];

function createSelectMenu() {
    let box = document.getElementById('roster');
    HEROES.forEach(h => {
        let div = document.createElement('div');
        div.className = 'char-card'; div.style.setProperty('--card-color', h.col);
        div.innerHTML = `<h3 style="color:${h.col}; font-size:26px">${h.name}</h3><div class="char-desc">${h.desc}</div>`;
        div.onclick = () => { startMission(h); }
        box.appendChild(div);
    });
}

const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }); window.dispatchEvent(new Event('resize'));

let p_class = null; let pl, e_arr=[], pr_arr=[], p_pr=[], fx=[];
let currentMap = MAPS[1]; let wave = 1; let f=0; let shakeV=0, camX=0;
let isPaused = false; 

function doShake(amt){shakeV=amt*4;} 

function togglePause() {
    if(!pl || pl.hp<=0 || wave>20) return; 
    isPaused = !isPaused;
    let sScreen = document.getElementById('pause-screen');
    if(isPaused) { sScreen.classList.remove('hidden'); } 
    else {
         sScreen.classList.add('hidden');
         for(let key in activeKeys) activeKeys[key] = false; 
    }
}


class Player {
    constructor(c){
        this.w=35; this.h=65;
        this.x=100; this.y=0; this.vx=0; this.vy=0;
        this.c = c; 
        this.maxHp=c.maxHp; this.hp=this.maxHp;
        this.maxEn=c.maxEn; this.en=this.maxEn;
        this.facing = 1; this.grounded = false; this.target = null;
        this.lockKeyTriggered = false; this.atkWait = {}; this.jCount = 0;
        
        // זמן הפלא / בלתי פגיעות שעושה הכל זורם 
        this.iFrames = 0; 
    }

    upd() {
        if(this.hp<=0) return;
        this.hp = Math.min(this.hp + this.c.hpRegen, this.maxHp);
        let chrg = kd('KeyU');
        
        if(this.iFrames > 0) this.iFrames--;

        let applySpeed = this.c.speed;
        if(chrg) applySpeed *= 0.35; 
        
        if(kd('KeyA')){ this.vx-=applySpeed; this.facing=-1; }
        if(kd('KeyD')){ this.vx+=applySpeed; this.facing= 1; }
        
        if(kd('KeyW') || kd('Space')) {
            if(!this.jHold) {
                if(this.jCount < 2) { 
                    this.vy = -this.c.jump; this.jCount++;
                    makeFX(this.x+this.w/2, this.y+this.h, 6, '#fff', 'spark');
                }
                this.jHold = true;
            }
        } else { this.jHold=false;}

        if(chrg) {
            this.en = Math.min(this.en + 1.2, this.maxEn);
            makeFX(this.x+this.w/2, this.y+this.h/2, 1, this.c.pCol, 'beam');
        } else {
            this.sHand('KeyH', '1', 8 * this.c.enCostMult, 12 * this.c.dmgMult, 8);
            this.sHand('KeyJ', '2', 20 * this.c.enCostMult, 30 * this.c.dmgMult, 15);
            this.sHand('KeyK', '3', 45 * this.c.enCostMult, 70 * this.c.dmgMult, 25);
            this.sHand('KeyY', 'u', 100 * this.c.enCostMult, 300 * this.c.dmgMult, 50); 
        }

        if(kd('KeyE')){
            if(!this.lockKeyTriggered){ this.swLock(); this.lockKeyTriggered=true;}
        } else {this.lockKeyTriggered=false;}

        if(this.target && this.target.hp <= 0){
             this.target = null;
             this.findBestTarget();
        }

        // עוקץ מסירות שדרה ! לא נחסם שמאלית וניתוב פול..  ! !
        this.vy += 0.6; this.x+=this.vx; this.y+=this.vy; this.vx *= 0.8;
        
        let leftBnd = 50; if(this.x < leftBnd) { this.x=leftBnd; this.vx=0;} // סכר שחייות שדמם הנגנים לא מגיעם לגובה מינוס על אפשר צולמטיוי גלאורוס 

        // מערך החלמי המפה המשדורג
        let isG=false; let floor_lvl = canvas.height-80;
        
        if(this.y+this.h >= floor_lvl){
            this.y = floor_lvl-this.h; this.vy=0; isG=true;
        } else {
            currentMap.platforms.forEach(pf => {
               let pFloorY = canvas.height - pf.y_offset;
               if(this.vy>=0 && this.y+this.h >= pFloorY - 14 && this.y+this.h <= pFloorY + 14 && this.x+this.w > pf.x && this.x < pf.x+pf.w){
                   this.y = pFloorY-this.h; this.vy=0; isG=true;
               }
            });
        }
        if(isG){this.jCount=0; this.grounded=true;} else{this.grounded=false;}
    }

    sHand(k,t,cost,dmg,size) {
        if(kd(k)){
            if(!this.atkWait[k]){
                if(t==='u' && wave < 10) return; 
                if(this.en >= cost) {
                    this.en -= cost;
                    let speed = (t==='1')?18: (t==='u')?10 : 15;
                    p_pr.push({
                         x: this.facing>0? this.x+this.w : this.x, y: this.y+20, 
                         dir: this.facing, s:speed, dmg:dmg, size: size * (this.c.id==='magma'? 1.8:1), color: this.c.pCol, tgt: this.target
                    });
                    this.vx -= (cost/5)*this.facing; 
                }
                this.atkWait[k] = true;
            }
        }else{this.atkWait[k] = false;}
    }

    swLock() {
        if(this.target) this.target=null; else this.findBestTarget();
    }
    
    findBestTarget() {
        let maxDist = 1400; let trg = null;
        e_arr.forEach(e => {
           let d = Math.abs(e.x - this.x);
           if(d < maxDist && e.x > this.x - 400 && e.x < this.x+1000) { maxDist=d; trg=e; }
        });
        if(trg) { this.target=trg; doShake(1.5); }
    }

    draw() {
        ctx.save(); ctx.translate(this.x, this.y);
        
        // סימן שבו הגוף פצוע בלוק דחייני !! ערימות הטשטושי כשלש השומר הקיוסק נפקע 
        if(this.iFrames > 0 && Math.floor(f / 4) % 2 === 0) ctx.globalAlpha = 0.3;

        ctx.fillStyle = this.c.col; 
        if(this.en > 90) { ctx.shadowBlur = 15; ctx.shadowColor = this.c.col; }
        ctx.fillRect(0,0,this.w,this.h);
        ctx.shadowBlur = 0;
        
        ctx.fillStyle='rgba(255,255,255,0.8)'; 
        if(this.facing>0) ctx.fillRect(this.w-4, 0, 4, this.h); else ctx.fillRect(0,0,4,this.h);

        if(this.target){
             let rx = this.target.x + this.target.w/2 - this.x; let ry = this.target.y+this.target.h/2 - this.y;
             ctx.strokeStyle='#ff3838'; ctx.lineWidth=3; 
             ctx.beginPath(); ctx.moveTo(this.w/2, this.h/2); ctx.lineTo(rx,ry); ctx.stroke();
             ctx.beginPath(); ctx.arc(rx,ry, 25+Math.sin(f/4)*5,0,Math.PI*2); ctx.stroke();
        }
        ctx.globalAlpha = 1.0; 
        ctx.restore();
    }
}


class Enemy {
    constructor(x, ty) {
        this.x=x; this.y=10; this.ty = ty; 
        this.w = 40; this.h=50; this.vx=0; this.vy=0; 
        this.maxHp = 40 + (wave*15); this.s = 2; this.stateT = 100;
        
        if(ty==='boss'){ this.maxHp *= 18; this.w=120; this.h=120; this.s=1;}
        else if(ty==='shooter'){ this.col = '#f39c12'; this.s=1.5;}
        
        // כאן הנרף! האטה היריבוט הקוצי הזה פלוס חיפולי ההזרקות העצמית.. לאט במיוחד ואובר-מתיימן 
        else if(ty==='jumper'){ this.col = '#8e44ad'; this.s=1.3; }  

        else if(ty==='tank'){ this.col='#7f8c8d'; this.w=60; this.h=75; this.maxHp*=3; this.s=0.5; }
        else if(ty==='ninja'){ this.col='#00cec9'; this.w=30; this.h=45; this.maxHp*=0.6; this.s=2.5; this.stateT=80;}
        else if(ty==='summoner'){ this.col='#341f97'; this.w=40; this.h=60; this.maxHp*=0.9; this.s=1.2;}
        else { this.col = '#c23616'; } 
        
        this.hp = this.maxHp;
        this.shClock = Math.random()*80 + 20; 
    }
    
    upd() {
        let dx = pl.x - this.x; let flY = canvas.height-80;
        
        if(this.ty === 'melee' || this.ty === 'boss' || this.ty === 'tank'){
            if(Math.abs(dx)>2) this.vx = dx>0? this.s:-this.s;
            if(this.ty==='boss' && Math.random()<0.02 && e_arr.length<5) { e_arr.push(new Enemy(this.x, 'jumper')); }
        }
        else if(this.ty === 'ninja'){
            this.stateT--;
            if(this.stateT > 20) { this.vx = dx>0? this.s:-this.s; } 
            else if(this.stateT > 0) { this.vx = dx>0? 13:-13; } 
            else { this.stateT = Math.random()*60 + 90; } 
        }
        else if(this.ty === 'shooter'){
            if(Math.abs(dx) > 350) this.vx = dx>0? this.s:-this.s; else this.vx*=0.6;
            this.shClock--;
            if(this.shClock<=0) {
                 this.shClock=120; pr_arr.push({x:this.x+20, y:this.y+20, dx:dx>0?8:-8, dy:0});
            }
        }
        else if(this.ty === 'jumper'){
             // יחסי סירקטי מפוצה בעוקבי החזר משואל תמידות . גושה ג'אמפ חכם שנושע בזכות עצמה. מפלגת .  
             this.vx = dx>0? this.s+0.2 : -(this.s+0.2);
             this.shClock--; if(this.shClock<=0 && this.y+this.h>=flY){ this.vy = -10; this.shClock=90;} // הרבה פחות דחוף מהפצלוחים ממקודיים האדיומים!! פאנול אסטרון. 
        }
        else if(this.ty === 'summoner') {
             if(Math.abs(dx) < 600) { this.vx = dx>0 ? -this.s : this.s; } 
             else { this.vx*=0.9; } 
             this.shClock--;
             if(this.shClock<=0 && e_arr.length<8) {
                 this.shClock = 250; 
                 e_arr.push(new Enemy(this.x+50, 'melee')); 
                 makeFX(this.x+50, this.y, 15, '#c8d6e5', 'boom');
             }
        }

        this.vy+=0.6; this.y+=this.vy; this.x+=this.vx;
        if(this.x < 10) { this.x=10; this.vx= (this.ty==='summoner') ? this.s : 2; } 
        
        let isGEnemy=false; 
        if(this.y+this.h >= flY) { this.y=flY-this.h; this.vy=0; isGEnemy=true;}
        
        // יריבי פצלוחי אינטליגיניקה!  סדאן מונדון הפקאע של מערכוות עזרתי לעצור טמטום שבו הפיל המשתלה לריק לוקן דלת
        if(!isGEnemy && this.ty !== 'jumper'){ 
            currentMap.platforms.forEach(pf => {
               let pFloorY = canvas.height - pf.y_offset;
               if(this.vy>=0 && this.y+this.h >= pFloorY - 15 && this.y+this.h <= pFloorY + 15 && this.x+this.w > pf.x && this.x < pf.x+pf.w){
                   this.y = pFloorY-this.h; this.vy=0; isGEnemy=true;
               }
            });
        }
        
        // ============= COLLIDER PHYSICS V3 !  =========== 
        if(intersect(this,pl) && pl.iFrames <= 0){
             let damagePerHit = (this.ty === 'boss' || this.ty === 'tank') ? 22 : 12;
             pl.hp -= damagePerHit; 
             
             // מתנת סיועי חירום! תרחץ לאחוזה תמציאי ובעיטה כבדה משוגנת הדיאוס מורוק! ככל שתהיה אימה פלילית יותר תקבל הגנוזה חדישה יחוסלן שדית הרחם!
             pl.vx = dx<0 ? 12 : -12; 
             pl.vy = -8;  
             pl.iFrames = 45; 
             doShake(2.5);
             
             this.vx *= 0; // פאנצלו סופגו רציפי עוצרים פגימה אינסקטיביטית קולור
        }
    }

    draw(){
        ctx.fillStyle = this.col; ctx.fillRect(this.x,this.y,this.w,this.h);
        
        if(this.ty==='tank') { ctx.fillStyle='black'; ctx.fillRect(this.x+5,this.y+5, this.w-10, 10); } 
        if(this.ty==='ninja'){ ctx.fillStyle='red'; ctx.fillRect(this.x, this.y+8, this.w, 5); } 
        if(this.ty==='summoner') { ctx.fillStyle='cyan'; ctx.beginPath(); ctx.arc(this.x+20,this.y-10,8,0,Math.PI*2); ctx.fill();} 

        ctx.fillStyle='#111'; ctx.fillRect(this.x, this.y-10, this.w, 5);
        ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w*(this.hp/this.maxHp), 5);
        
        ctx.fillStyle='white'; let fw = pl.x > this.x ? this.w-12 : 4;  ctx.fillRect(this.x+fw, this.y+8, 8,8);
        ctx.fillStyle='black'; ctx.fillRect(this.x+fw+2, this.y+10,4,4);
    }
}

function makeFX(x,y,qty,col,mode) {
    for(let i=0;i<qty;i++) fx.push({ x:x, y:y, vx:(Math.random()-0.5)*(mode==='boom'?12:4), vy:(mode==='beam')?-(Math.random()*6): (Math.random()-0.5)*(mode==='boom'?12:4), col:col, l: (mode==='spark')?15:25, s: (mode==='boom')?Math.random()*6+4 : 3});
}

function loadWv() {
    let oldWave = wave; currentMap = MAPS[wave > 20 ? 20 : wave];
    fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'}, body:JSON.stringify({stage:wave, shards:20})});
    
    let stI = document.getElementById('stage-info'); stI.innerText = currentMap.name;
    stI.style.border = `2px solid ${currentMap.bg}`; stI.style.boxShadow = `0 0 10px ${currentMap.bg}`;
    let aBox = document.getElementById('stage-alert');
    aBox.innerText = currentMap.is_boss ? "BOSS ARENA LOCKDOWN!" : `STAGE ${wave}`;
    aBox.style.color = currentMap.is_boss ? "#e74c3c" : "white"; aBox.style.opacity = 1; setTimeout(()=>{ aBox.style.opacity = 0}, 2500);

    e_arr =[]; pr_arr=[]; pl.iFrames=0;
    
    // קריטילי מסה לזירות יקום רחבות פי 8. תפרושת מוביות מטורללות לשלב.. מסיבי.. !  
    if(currentMap.is_boss) {
        e_arr.push(new Enemy(pl.x + 800, 'boss'));
    } else {
        let mQ = 2+Math.floor(wave/2);
        for(let z=0; z<mQ; z++){
            let rTy = currentMap.enemies[Math.floor(Math.random() * currentMap.enemies.length)];
            e_arr.push(new Enemy(pl.x+400+(z*300), rTy));
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

function sysLoop() {
    if(isPaused){
         requestAnimationFrame(sysLoop); 
         return; 
    }

    f++;
    if(pl.hp<=0) {
        document.getElementById('ui-layer').classList.add('hidden');
        document.getElementById('death-screen').classList.remove('hidden');
        document.getElementById('final-lvl').innerText=wave; return;
    }
    
    pl.upd();
    if(e_arr.length===0){ wave++; pl.hp = Math.min(pl.hp+(pl.maxHp*0.3), pl.maxHp); loadWv(); }
    
    for(let i=e_arr.length-1; i>=0; i--) { 
        let e = e_arr[i]; e.upd(); 
        if(e.hp<=0) {makeFX(e.x+20,e.y+20,30,'#27ae60','boom'); e_arr.splice(i,1);} 
    }

    for(let i=pr_arr.length-1; i>=0; i--) { 
         let b = pr_arr[i]; b.x+=b.dx; b.y+=b.dy; makeFX(b.x,b.y, 1, 'orange', 'spark'); 
         
         if(intersect({x:b.x,y:b.y,w:8,h:8}, pl)) {
             if (pl.iFrames <= 0) { 
                 pl.hp-=15; 
                 pl.iFrames = 45; 
                 pl.vx += b.dx > 0 ? 5 : -5;
                 doShake(3); 
             }
             pr_arr.splice(i,1);
             continue;
         }
         
         if(b.y>canvas.height || b.x<camX || b.x>camX+canvas.width*2) pr_arr.splice(i,1);
    }
    
    for(let i=p_pr.length-1; i>=0; i--) {
        let b = p_pr[i]; 
        if(b.tgt && b.tgt.hp>0){
            let tgAng = Math.atan2((b.tgt.y+b.tgt.h/2)-b.y, (b.tgt.x+b.tgt.w/2)-b.x);
            b.x += Math.cos(tgAng) * b.s; b.y += Math.sin(tgAng) * b.s;
        }else{ b.x += b.dir * b.s;}
        
        makeFX(b.x,b.y,2, b.color, 'spark');

        let dflag = false;
        for(let j=e_arr.length-1; j>=0; j--){
             let te = e_arr[j];
             if(intersect({x:b.x-b.size/2, y:b.y-b.size/2, w:b.size, h:b.size}, te)) {
                 te.hp-=b.dmg; makeFX(b.x,b.y,8,b.color,'boom'); dflag=true; doShake((b.dmg)/20);
                 te.vx += b.dir*6;
                 if(p_class.id === 'dark'){ pl.hp = Math.min(pl.maxHp, pl.hp+(b.dmg*0.025)); } 
                 break;
             }
        }
        if(dflag || b.y>canvas.height || Math.abs(b.x-pl.x)>2000) {p_pr.splice(i,1);}
    }

    for(let i=fx.length-1; i>=0; i--) { fx[i].x+=fx[i].vx; fx[i].vy+=0.1; fx[i].y+=fx[i].vy; fx[i].l--; if(fx[i].l<=0) fx.splice(i,1); }
    
    let cxTar = pl.x - canvas.width/2 + 100; if(cxTar<0) cxTar=0;
    camX += (cxTar-camX)*0.08; 
    let cm_S_X = camX; let cm_S_Y = 0;
    if(shakeV>0) {cm_S_X+=(Math.random()-0.5)*shakeV; cm_S_Y+=(Math.random()-0.5)*shakeV; shakeV*=0.8;} if(shakeV<0.5) shakeV=0;
    
    ctx.fillStyle = currentMap.bg; ctx.fillRect(0,0, canvas.width, canvas.height);
    
    ctx.fillStyle='rgba(255,255,255,0.06)'; 
    for(let ds=0;ds<60;ds++) { let pxX = ((ds*319)-(camX*0.1))%canvas.width; if(pxX<0)pxX+=canvas.width; ctx.beginPath(); ctx.arc(pxX, (ds*7453)%canvas.height, 2+ds%3, 0,7); ctx.fill();}
    
    ctx.save(); ctx.translate(-cm_S_X, cm_S_Y); 
    
    // ציור הרצפות הנצחציוט עם רעיפת הבלנד למדרכת אימה. !
    ctx.fillStyle = currentMap.floor; ctx.fillRect(cm_S_X - 100, canvas.height-80, canvas.width + 400, 300);
    ctx.strokeStyle='rgba(0,0,0,0.4)';
    for(let xl=cm_S_X - (cm_S_X % 120); xl < cm_S_X+canvas.width+400; xl+=120){ ctx.beginPath(); ctx.moveTo(xl,canvas.height-80); ctx.lineTo(xl, canvas.height); ctx.stroke(); }

    currentMap.platforms.forEach(pf => {
         let pY = canvas.height - pf.y_offset;
         ctx.fillStyle=currentMap.bg; ctx.shadowBlur=10; ctx.shadowColor=currentMap.floor; ctx.fillRect(pf.x, pY, pf.w, pf.h); ctx.shadowBlur=0; 
         ctx.fillStyle=currentMap.floor; ctx.fillRect(pf.x+3, pY+3, pf.w-6, pf.h-6); 
    });

    pl.draw(); e_arr.forEach(e=>e.draw()); 
    ctx.fillStyle='#f39c12'; pr_arr.forEach(b=>{ctx.fillRect(b.x-4,b.y-4,8,8);});
    p_pr.forEach(b=>{ctx.fillStyle=b.color; ctx.beginPath(); ctx.arc(b.x,b.y,b.size,0,Math.PI*2); ctx.fill();});
    
    fx.forEach(x => {ctx.fillStyle=x.col; ctx.globalAlpha=(x.l/25); ctx.fillRect(x.x,x.y,x.s,x.s);}); ctx.globalAlpha=1;

    ctx.restore();
    
    document.getElementById('hp-bar').style.width = Math.max(0,(pl.hp/pl.maxHp)*100)+'%';
    document.getElementById('hp-t').innerText = Math.floor(pl.hp)+"/"+pl.maxHp;
    document.getElementById('en-bar').style.width = Math.max(0,(pl.en/pl.maxEn)*100)+'%';
    document.getElementById('en-t').innerText = Math.floor(pl.en)+"/"+pl.maxEn;
    document.getElementById('lock-hud').style.opacity = pl.target ? 1: 0;
    
    requestAnimationFrame(sysLoop);
}

createSelectMenu();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
