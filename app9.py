from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)
# מפתח סודי לסשן (לא קריטי במשחק הזה אבל טוב שיהיה)
app.secret_key = 'clover_fixed_key_v2'

# שמירת נתונים בזיכרון השרת (זמני עד לריסטארט)
PLAYER_DATA = {
    "shards": 0,
    "max_stage_reached": 1
}

@app.route('/')
def idx():
    return render_template_string(GAME_HTML)

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    try:
        data = request.json
        if not data: return jsonify({"status": "no data"}), 400
        
        # עדכון כסף
        added_shards = data.get("shards", 0)
        PLAYER_DATA["shards"] += added_shards
        
        # עדכון שלב מקסימלי
        current_stage = data.get("stage", 1)
        if current_stage > PLAYER_DATA["max_stage_reached"]:
            PLAYER_DATA["max_stage_reached"] = current_stage
            
        print(f"Game Saved: {PLAYER_DATA}")
        return jsonify(PLAYER_DATA)
    except Exception as e:
        print(f"Error saving: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/data')
def get_data():
    return jsonify(PLAYER_DATA)


GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Legend of Elements</title>
    <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --hp-col: #e74c3c;
            --en-col: #3498db;
            --gold: #f1c40f;
        }
        body { margin: 0; overflow: hidden; background: #050505; font-family: 'Rubik', sans-serif; color: white; user-select: none; }
        canvas { display: block; width: 100%; height: 100vh; image-rendering: pixelated; }
        
        /* ממשק משתמש עליון */
        #ui-layer {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; padding: 20px; box-sizing: border-box;
            display: flex; flex-direction: column; justify-content: space-between; z-index: 10;
        }

        .hud-top { 
            display: flex; flex-direction: column; width: 100%; align-items: center; 
            text-shadow: 2px 2px 0px #000;
        }
        
        .stage-container {
            width: 60%; height: 25px; background: #222; border: 2px solid #555;
            border-radius: 10px; margin-bottom: 10px; position: relative; overflow: hidden;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        .stage-fill { height: 100%; background: linear-gradient(90deg, #6c5ce7, #a29bfe); width: 0%; transition: width 0.5s; }
        .stage-text { position: absolute; width: 100%; text-align: center; top: 1px; font-size: 16px; font-weight: bold; z-index: 2;}

        .bars-wrapper { display: flex; width: 100%; justify-content: space-between; align-items: flex-end; padding: 0 50px; }
        .stat-box { display: flex; flex-direction: column; gap: 5px; width: 300px; }
        
        .bar-outline { width: 100%; height: 20px; background: #111; border: 2px solid #fff; border-radius: 4px; overflow: hidden; position: relative; }
        .bar-inner { height: 100%; transition: width 0.1s linear; }
        .hp-inner { background: var(--hp-col); }
        .en-inner { background: var(--en-col); }
        
        .hud-label { font-size: 18px; font-weight: bold; display: flex; justify-content: space-between; }

        /* הודעות משחק */
        #game-message {
            position: absolute; top: 25%; left: 50%; transform: translate(-50%, -50%);
            font-size: 60px; color: #fff; text-shadow: 0 0 20px var(--gold);
            font-weight: 900; text-align: center; opacity: 0; transition: opacity 0.3s;
            pointer-events: none;
        }

        /* רמז מקשים */
        .controls {
            direction: ltr; text-align: left;
            font-size: 14px; color: rgba(255,255,255,0.8); background: rgba(0,0,0,0.6);
            padding: 15px; border-radius: 12px; align-self: flex-start;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .key { color: var(--gold); font-weight: bold; border: 1px solid #777; padding: 0 4px; border-radius: 4px; background: #333; }

        /* מסכים (תפריט, סיום) */
        .screen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(10, 10, 15, 0.95); display: flex; flex-direction: column;
            align-items: center; justify-content: center; z-index: 100;
            opacity: 1; transition: opacity 0.5s;
        }
        .hidden { display: none !important; opacity: 0; pointer-events: none; }
        
        h1 { font-size: 60px; margin: 0; color: #fff; text-shadow: 4px 4px 0 #6c5ce7; letter-spacing: 2px; }
        h2 { color: var(--gold); margin-top: 10px; margin-bottom: 40px; font-weight: normal; }
        
        .btn {
            padding: 15px 50px; font-size: 24px; cursor: pointer;
            background: transparent; color: #fff; border: 3px solid #fff; 
            font-family: inherit; font-weight: bold;
            transition: 0.2s; text-transform: uppercase;
        }
        .btn:hover { background: #fff; color: #000; box-shadow: 0 0 20px #fff; transform: scale(1.05); }

        #error-log {
            position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(200, 0, 0, 0.8);
            color: white; font-size: 12px; padding: 5px; z-index: 9999; display: none; direction: ltr;
        }

        #unlock-notify {
            position: absolute; bottom: 30%; left: 50%; transform: translateX(-50%);
            background: rgba(108, 92, 231, 0.9); border: 2px solid white;
            padding: 20px 40px; text-align: center; display: none; border-radius: 20px;
            animation: floatUp 4s forwards;
            z-index: 20;
        }
        @keyframes floatUp {
            0% { opacity: 0; transform: translate(-50%, 20px); }
            15% { opacity: 1; transform: translate(-50%, 0); }
            85% { opacity: 1; transform: translate(-50%, 0); }
            100% { opacity: 0; transform: translate(-50%, -50px); }
        }
    </style>
</head>
<body>

<!-- UI Layers -->
<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="stage-container">
            <div class="stage-fill" id="prog-bar"></div>
            <div class="stage-text">LEVEL <span id="lvl-display">1</span> / 20</div>
        </div>
        
        <div class="bars-wrapper">
            <!-- HP -->
            <div class="stat-box" style="direction: ltr;">
                <div class="hud-label"><span style="color:var(--hp-col)">HP</span> <span id="hp-txt">100</span></div>
                <div class="bar-outline"><div class="hp-inner bar-inner" id="hp-bar" style="width: 100%"></div></div>
            </div>
            
            <!-- Lock On Indicator -->
            <div id="lock-icon" style="opacity:0; color: #ff5555; font-size: 30px;">[🎯 LOCKED]</div>

            <!-- Energy -->
            <div class="stat-box" style="direction: ltr; text-align: right;">
                <div class="hud-label"><span id="en-txt">100</span> <span style="color:var(--en-col)">ENERGY</span></div>
                <div class="bar-outline"><div class="en-inner bar-inner" id="en-bar" style="width: 100%"></div></div>
            </div>
        </div>
    </div>
    
    <div id="game-message">STAGE 1</div>

    <div class="controls">
        <div>Move/Jump: <span class="key">W</span> <span class="key">A</span> <span class="key">D</span></div>
        <div>Shots: <span class="key">H</span> (Low) <span class="key">J</span> (Med) <span class="key">K</span> (High)</div>
        <div>Skills: <span class="key">U</span> Charge | <span class="key">E</span> Lock-On | <span class="key">Y</span> Ult</div>
        <div style="margin-top:5px; font-size: 11px; opacity: 0.7;">(Keys work in any language)</div>
    </div>
</div>

<div id="unlock-notify">
    <h2 style="margin:0; font-size: 30px;">UNLOCKED!</h2>
    <p id="unlock-text" style="font-size:20px; margin-top: 10px;">Double Jump</p>
</div>

<!-- Start Screen -->
<div id="menu-screen" class="screen">
    <a href="/" style="position: absolute; top:20px; left:20px; color:#aaa; text-decoration:none;">⬅ יציאה לארקייד</a>
    <h1>CLOVER</h1>
    <h2>THE ELEMENTAL GUARDIAN</h2>
    <button class="btn" onclick="startGame()">START GAME</button>
</div>

<!-- Game Over -->
<div id="game-over-screen" class="screen hidden">
    <h1 style="color: #c0392b">YOU DIED</h1>
    <p style="font-size: 20px;">הגעת עד לשלב <span id="death-stage" style="color: var(--gold); font-weight:bold;"></span></p>
    <button class="btn" onclick="location.reload()" style="margin-top: 30px;">נסה שוב</button>
    <a href="/" class="btn" style="margin-top: 20px; font-size: 16px; border: 1px solid #777;">יציאה</a>
</div>

<!-- Victory -->
<div id="victory-screen" class="screen hidden">
    <h1 style="color: #f1c40f">VICTORY!</h1>
    <p>סיימת את כל 20 השלבים!</p>
    <a href="/" class="btn" style="margin-top: 30px;">חזור לתפריט הראשי</a>
</div>

<!-- Debug Log -->
<div id="error-log"></div>

<script>
/** 
 * ERROR HANDLING FOR DEBUGGING
 */
window.onerror = function(msg, url, line, col, error) {
   let log = document.getElementById('error-log');
   log.style.display = 'block';
   log.innerHTML += `<div>Error: ${msg} (Line ${line})</div>`;
   return false;
};

// --- KEY INPUT HANDLING (FIXED FOR HEBREW/ENGLISH) ---
// אנו משתמשים ב- code במקום key. זה בודק מיקום פיזי של המקש ולא את השפה.
const activeKeys = {};

window.addEventListener('keydown', (e) => {
    // מניעת גלילה עם רווח
    if(e.code === 'Space') e.preventDefault();
    activeKeys[e.code] = true; 
});

window.addEventListener('keyup', (e) => {
    activeKeys[e.code] = false;
});

// פונקציית עזר לבדיקת מקשים
function isKeyDown(code) {
    return activeKeys[code] === true;
}

// מיפוי מקשים נוח
const KEYS = {
    UP: 'KeyW', LEFT: 'KeyA', DOWN: 'KeyS', RIGHT: 'KeyD',
    JUMP: 'Space',
    CHARGE: 'KeyU', LOCK: 'KeyE',
    SHOOT_1: 'KeyH', SHOOT_2: 'KeyJ', SHOOT_3: 'KeyK', ULT: 'KeyY'
};

// --- GAME SETUP ---
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);

// התאמת גודל מסך
function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
}
window.addEventListener('resize', resize);
resize();

// משתני מערכת
let gameState = 'MENU'; 
let frames = 0;
const GRAVITY = 0.6;
const FLOOR_Y = canvas.height - 100;

// נתוני משחק
let gameData = { stage: 1, maxStage: 20, shards: 0 };
let unlocks = { doubleJump: false, superAttack: false, autoCharge: false };

// ישויות
let player;
let enemies = [];
let projectiles = [];
let particles = [];
let camX = 0;
let shakeIntensity = 0;

// --- מחלקת שחקן ---
class Player {
    constructor() {
        this.w = 32; this.h = 64;
        this.x = 100; this.y = FLOOR_Y - this.h;
        this.vx = 0; this.vy = 0;
        this.speed = 0.8; // תאוצה
        this.friction = 0.85;
        this.hp = 100; this.maxHp = 100;
        this.energy = 100; this.maxEnergy = 100;
        
        this.facing = 1; // 1 ימין, -1 שמאל
        this.onGround = false;
        this.jumps = 0;
        
        // מנגנון נעילה
        this.target = null;
        this.lockToggleWait = false;
        
        // טעינת מקש
        this.shootWait = {};
    }
    
    update() {
        if (this.hp <= 0) return;

        // -- תנועה --
        // אם מטעין - זז לאט
        let isCharging = isKeyDown(KEYS.CHARGE);
        
        if (!isCharging) {
            if (isKeyDown(KEYS.LEFT)) { this.vx -= this.speed; this.facing = -1; }
            if (isKeyDown(KEYS.RIGHT)) { this.vx += this.speed; this.facing = 1; }
            
            // קפיצה (תומך W או רווח)
            if (isKeyDown(KEYS.UP) || isKeyDown(KEYS.JUMP)) {
                if (!this.jumpKeyHeld) {
                    this.tryJump();
                    this.jumpKeyHeld = true;
                }
            } else {
                this.jumpKeyHeld = false;
            }
        } else {
            // פעולת טעינה
            this.vx *= 0.5; // האטה משמעותית
            if (this.energy < this.maxEnergy) {
                this.energy += 0.8;
                spawnSpark(this.x + this.w/2, this.y, '#3498db');
            }
        }

        // טעינה אוטומטית (אנלוק)
        if (unlocks.autoCharge && !isCharging && frames % 10 === 0 && this.energy < this.maxEnergy) {
            this.energy += 0.2;
        }

        // -- יריות --
        if (!isCharging) {
            this.handleShoot(KEYS.SHOOT_1, 'weak', 10);
            this.handleShoot(KEYS.SHOOT_2, 'med', 25);
            this.handleShoot(KEYS.SHOOT_3, 'high', 50);
            this.handleShoot(KEYS.ULT, 'super', 100);
        }

        // -- נעילה (LOCK ON) --
        if (isKeyDown(KEYS.LOCK)) {
            if (!this.lockToggleWait) {
                this.toggleLock();
                this.lockToggleWait = true;
            }
        } else {
            this.lockToggleWait = false;
        }

        // אם המטרה מתה - בטל נעילה
        if (this.target && this.target.hp <= 0) this.target = null;

        // פיזיקה
        this.vy += GRAVITY;
        this.x += this.vx;
        this.y += this.vy;
        
        this.vx *= this.friction; // חיכוך
        
        // רצפה
        let groundLevel = FLOOR_Y;
        if (this.y + this.h > groundLevel) {
            this.y = groundLevel - this.h;
            this.vy = 0;
            this.onGround = true;
            this.jumps = 0;
        } else {
            this.onGround = false;
        }

        // קירות מסך שמאל
        if (this.x < 0) { this.x = 0; this.vx = 0; }
    }
    
    tryJump() {
        let allowed = unlocks.doubleJump ? 2 : 1;
        if (this.jumps < allowed) {
            this.vy = -14;
            this.jumps++;
            // אפקט קפיצה
            spawnExplosion(this.x + this.w/2, this.y + this.h, '#fff', 5);
        }
    }
    
    handleShoot(key, type, cost) {
        if (isKeyDown(key)) {
            if (!this.shootWait[key]) {
                if (type === 'super' && !unlocks.superAttack) return; // הגנה
                
                if (this.energy >= cost) {
                    this.energy -= cost;
                    this.shoot(type);
                    // הדף לאחור
                    let recoil = (cost / 10);
                    this.vx -= (this.facing * recoil);
                } else {
                    // אין אנרגיה
                }
                this.shootWait[key] = true;
            }
        } else {
            this.shootWait[key] = false;
        }
    }

    shoot(type) {
        let stats = { dmg: 10, spd: 15, size: 8, color: '#f1c40f' };
        
        if (type === 'med') stats = { dmg: 25, spd: 18, size: 14, color: '#e67e22' };
        if (type === 'high') stats = { dmg: 60, spd: 22, size: 20, color: '#e74c3c' };
        if (type === 'super') stats = { dmg: 150, spd: 12, size: 40, color: '#8e44ad' };

        projectiles.push(new Projectile(
            this.x + (this.facing===1 ? this.w : 0),
            this.y + this.h/2 - 10,
            this.facing,
            stats,
            this.target
        ));
    }
    
    toggleLock() {
        if (this.target) {
            this.target = null;
        } else {
            // מצא את הקרוב ביותר
            let closest = null;
            let dist = 1200; // מרחק מקסימלי לנעילה
            enemies.forEach(e => {
                let d = Math.abs(e.x - this.x);
                if (d < dist && e.x > this.x - 400 && e.x < this.x + 900) {
                    dist = d;
                    closest = e;
                }
            });
            if(closest) this.target = closest;
        }
        
        let icon = document.getElementById('lock-icon');
        icon.style.opacity = (this.target ? 1 : 0);
    }
    
    draw() {
        ctx.fillStyle = '#3498db';
        // הבהוב אם טעון מלא
        if (this.energy > 95) ctx.shadowBlur = 10; 
        ctx.shadowColor = '#fff';
        
        ctx.fillRect(this.x, this.y, this.w, this.h);
        
        ctx.shadowBlur = 0; // Reset
        
        // עיניים (מציין כיוון)
        ctx.fillStyle = '#fff';
        let eyeX = (this.facing === 1) ? this.x + 22 : this.x + 2;
        ctx.fillRect(eyeX, this.y + 12, 8, 8);
        
        // ציור נעילה
        if (this.target) {
            let t = this.target;
            ctx.strokeStyle = 'rgba(255, 50, 50, 0.7)';
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(t.x + t.w/2, t.y + t.h/2, 50, 0, Math.PI*2);
            ctx.stroke();
            ctx.lineWidth = 1;
            // קו מחבר
            ctx.beginPath(); ctx.moveTo(this.x + this.w/2, this.y); ctx.lineTo(t.x + t.w/2, t.y + t.h/2); 
            ctx.strokeStyle = "rgba(255,0,0,0.2)"; ctx.stroke();
        }
    }
}

class Projectile {
    constructor(x, y, dir, stats, target) {
        this.x = x; this.y = y;
        this.dir = dir;
        this.stats = stats;
        this.target = target;
        
        this.vx = dir * stats.spd;
        this.vy = 0;
        this.w = stats.size; this.h = stats.size;
        this.dead = false;
        
        this.isHoming = (!!target);
    }
    
    update() {
        // מנגנון ביות (Homing)
        if (this.isHoming && this.target && this.target.hp > 0) {
            let tx = this.target.x + this.target.w/2;
            let ty = this.target.y + this.target.h/2;
            
            // חישוב וקטור למטרה
            let dx = tx - this.x;
            let dy = ty - this.y;
            let angle = Math.atan2(dy, dx);
            
            // המרה חזרה למהירות
            // ירייה חלשה מתבייתת מהר יותר
            let agility = 0.2; 
            if (this.stats.size > 30) agility = 0.05; // אולט כבד ופחות גמיש
            
            this.vx += (Math.cos(angle) * this.stats.spd - this.vx) * agility;
            this.vy += (Math.sin(angle) * this.stats.spd - this.vy) * agility;
        }
        
        this.x += this.vx;
        this.y += this.vy;
        
        // בדיקת פגיעה
        for (let e of enemies) {
            if (rectIntersect(this, e)) {
                e.hp -= this.stats.dmg;
                this.dead = true;
                
                // אפקט פגיעה
                spawnExplosion(this.x, this.y, this.stats.color, 5);
                
                // הזזת האויב
                e.vx += (this.vx > 0) ? 5 : -5;
                e.flash = 5;
                
                shake(2);
                break;
            }
        }
        
        // יציאה מהמסך (מוות)
        if (Math.abs(this.x - player.x) > 1500 || this.y > canvas.height + 200) this.dead = true;
    }
    
    draw() {
        ctx.fillStyle = this.stats.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.w/2, 0, Math.PI*2);
        ctx.fill();
    }
}

class Enemy {
    constructor(x, type, stage) {
        this.isBoss = (type === 'boss');
        this.x = x; 
        this.y = FLOOR_Y - (this.isBoss ? 150 : 40);
        this.w = this.isBoss ? 100 : 40; 
        this.h = this.isBoss ? 150 : 40;
        
        // חיזוק עם שלבים
        let multiplier = stage * 0.5;
        this.maxHp = this.isBoss ? 500 + (stage * 50) : 30 + (stage * 5);
        this.hp = this.maxHp;
        
        this.color = this.isBoss ? '#8e44ad' : '#c0392b';
        this.vx = 0;
        this.speed = this.isBoss ? 2 + (stage*0.1) : 1.5 + (stage*0.1);
        
        this.flash = 0;
    }
    
    update() {
        // AI פשוט - רוץ לשחקן
        let dx = player.x - this.x;
        
        // אם לא קרוב מדי (שמירה על מרחק נגיעה) או אם רחוק מאוד (רדום)
        if (Math.abs(dx) < 1000) {
            if (Math.abs(dx) > 2) {
                this.vx = (dx > 0) ? this.speed : -this.speed;
            }
        }
        
        this.x += this.vx;
        
        // פגיעה בשחקן (Melee)
        if (rectIntersect(this, player)) {
             player.hp -= (this.isBoss ? 1 : 0.5);
             shake(2);
             // דחייה הדדית
             if (this.x < player.x) { this.x -= 2; player.vx += 3; } 
             else { this.x += 2; player.vx -= 3; }
        }
        
        if (this.flash > 0) this.flash--;
    }
    
    draw() {
        ctx.fillStyle = (this.flash > 0) ? '#fff' : this.color;
        ctx.fillRect(this.x, this.y, this.w, this.h);
        
        // פס חיים
        ctx.fillStyle = '#000';
        ctx.fillRect(this.x, this.y - 10, this.w, 5);
        ctx.fillStyle = '#e74c3c';
        ctx.fillRect(this.x, this.y - 10, this.w * (this.hp / this.maxHp), 5);
        
        if (this.isBoss) {
            ctx.fillStyle = "#fff";
            ctx.fillText("BOSS", this.x + 30, this.y - 15);
        }
    }
}

// מערכת חלקיקים
function spawnSpark(x, y, c) { particles.push({x,y,vx:0,vy:-2,c,life:20,s:2}); }
function spawnExplosion(x, y, c, n) {
    for(let i=0;i<n;i++) particles.push({
        x, y, c, life: 30, s: Math.random()*5+2,
        vx: (Math.random()-0.5)*10, vy: (Math.random()-0.5)*10
    });
}

function updateParticles() {
    for (let i=particles.length-1; i>=0; i--) {
        let p = particles[i];
        p.x+=p.vx; p.y+=p.vy; p.life--; p.vy+=0.2; // gravity
        if(p.life<=0) particles.splice(i,1);
    }
}
function drawParticles() {
    particles.forEach(p => {
        ctx.fillStyle = p.c;
        ctx.fillRect(p.x, p.y, p.s, p.s);
    });
}

// --- ניהול שלבים ---
let waveTimer = 0;
function spawnLevel() {
    let s = gameData.stage;
    let title = "STAGE " + s;
    let isBoss = (s % 5 === 0);
    
    if (isBoss) title = "☠ BOSS FIGHT ☠";
    showMessage(title);

    enemies = [];
    if (isBoss) {
        enemies.push(new Enemy(player.x + 800, 'boss', s));
    } else {
        let count = 2 + Math.floor(s/2);
        for(let i=0; i<count; i++) {
            enemies.push(new Enemy(player.x + 500 + (i*200), 'minion', s));
        }
    }
    
    // Save
    fetch('save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ stage: s, shards: 0 })
    }).catch(console.error);
}

function checkWinCondition() {
    if (enemies.length === 0) {
        if (waveTimer === 0) waveTimer = 100; // Delay
        else {
            waveTimer--;
            if (waveTimer === 1) {
                // בדיקת UNLOCKS
                if (gameData.stage === 5) doUnlock('Double Jump (Space x2)', 'doubleJump');
                if (gameData.stage === 10) doUnlock('Super Blast (Press Y)', 'superAttack');
                if (gameData.stage === 15) doUnlock('Auto Recharge', 'autoCharge');

                if (gameData.stage >= 20) {
                    gameState = 'VICTORY';
                    document.getElementById('ui-layer').classList.add('hidden');
                    document.getElementById('victory-screen').classList.remove('hidden');
                } else {
                    gameData.stage++;
                    player.hp = Math.min(player.hp + 20, player.maxHp); // ריפוי קטן
                    spawnLevel();
                }
            }
        }
    }
}

function doUnlock(txt, key) {
    unlocks[key] = true;
    document.getElementById('unlock-text').innerText = txt;
    let n = document.getElementById('unlock-notify');
    n.style.display = 'block';
    setTimeout(() => n.style.display = 'none', 5000);
}


// --- LULU & RENDER ---
function startGame() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    player = new Player();
    gameData.stage = 1;
    spawnLevel();
    gameState = 'PLAY';
    requestAnimationFrame(loop);
}

function loop() {
    if (gameState !== 'PLAY') return;
    
    frames++;
    
    // לוגיקה
    player.update();
    enemies.forEach((e, i) => {
        e.update();
        if (e.hp <= 0) {
             spawnExplosion(e.x+e.w/2, e.y+e.h/2, '#8e44ad', 10);
             enemies.splice(i, 1);
        }
    });
    projectiles.forEach((p, i) => {
        p.update();
        if(p.dead) projectiles.splice(i,1);
    });
    updateParticles();
    
    checkWinCondition();
    
    if (player.hp <= 0) {
        gameState = 'GAMEOVER';
        document.getElementById('ui-layer').classList.add('hidden');
        document.getElementById('game-over-screen').classList.remove('hidden');
        document.getElementById('death-stage').innerText = gameData.stage;
        return;
    }
    
    // מצלמה
    let targetX = player.x - 200;
    if (targetX < 0) targetX = 0;
    // החלקת מצלמה
    camX += (targetX - camX) * 0.1;
    
    if (shakeIntensity > 0) {
        camX += (Math.random()-0.5) * shakeIntensity;
        shakeIntensity *= 0.9;
        if(shakeIntensity < 0.5) shakeIntensity = 0;
    }

    // ציור
    // רקע
    ctx.fillStyle = '#0a0a10';
    ctx.fillRect(0,0, canvas.width, canvas.height);
    
    ctx.save();
    ctx.translate(-camX, 0); // הזזת עולם
    
    // רצפה
    ctx.fillStyle = '#222';
    ctx.fillRect(0, FLOOR_Y, 50000, canvas.height - FLOOR_Y);
    ctx.strokeStyle = '#555'; ctx.beginPath(); ctx.moveTo(0, FLOOR_Y); ctx.lineTo(50000, FLOOR_Y); ctx.stroke();
    
    player.draw();
    enemies.forEach(e => e.draw());
    projectiles.forEach(p => p.draw());
    drawParticles();
    
    ctx.restore();
    
    // UI Update
    document.getElementById('hp-bar').style.width = (player.hp/player.maxHp*100) + "%";
    document.getElementById('hp-txt').innerText = Math.floor(player.hp);
    document.getElementById('en-bar').style.width = (player.energy/player.maxEnergy*100) + "%";
    document.getElementById('en-txt').innerText = Math.floor(player.energy);
    document.getElementById('prog-bar').style.width = (gameData.stage / 20 * 100) + "%";
    document.getElementById('lvl-display').innerText = gameData.stage;

    requestAnimationFrame(loop);
}

function showMessage(txt) {
    let el = document.getElementById('game-message');
    el.innerText = txt;
    el.style.opacity = 1;
    setTimeout(() => el.style.opacity = 0, 2000);
}
function rectIntersect(r1, r2) {
    return !(r2.x > r1.x + r1.w || r2.x + r2.w < r1.x || r2.y > r1.y + r1.h || r2.y + r2.h < r1.y);
}
function shake(val) { shakeIntensity = val * 5; }

</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
