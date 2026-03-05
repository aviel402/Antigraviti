from flask import Flask, render_template_string, jsonify, request

# חשוב: אפליקציה זו מיובאת כ- game9 בקובץ הראשי
app = Flask(__name__)
app.secret_key = 'clover_master_key_v100_final'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 3 # שומר למשתמש התחברות קפואה ל2 ימים אליו אישית בלבד (משאר קופות ארקייד.. ) 

# אחסון נתונים בזיכרון (מתאפס בריסטארט של הסרבר)
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
    data = request.json
    # עדכון שארדים (כסף) ושלב מקסימלי
    PLAYER_DATA["shards"] += data.get("shards", 0)
    
    current_stage = data.get("stage", 1)
    if current_stage > PLAYER_DATA["max_stage_reached"]:
        PLAYER_DATA["max_stage_reached"] = current_stage
        
    print(f"Server Saved: {PLAYER_DATA}")
    return jsonify(PLAYER_DATA)

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
            --ui-bg: rgba(20, 20, 30, 0.95);
            --text-color: #eee;
            --hp-col: #e74c3c;
            --en-col: #3498db;
            --gold: #f1c40f;
        }
        body { margin: 0; overflow: hidden; background: #050505; font-family: 'Rubik', sans-serif; color: var(--text-color); user-select: none; }
        canvas { display: block; image-rendering: pixelated; width: 100%; height: 100vh; }
        
        /* UI Container */
        #ui-layer {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; padding: 20px; box-sizing: border-box;
            display: flex; flex-direction: column; justify-content: space-between;
        }

        /* Top Bar */
        .hud-top { 
            display: flex; flex-direction: column; width: 100%; align-items: center; 
            text-shadow: 1px 1px 4px black;
        }
        
        /* Progress Bar */
        .stage-container {
            width: 50%; height: 20px; background: #222; border: 2px solid #555;
            border-radius: 10px; margin-bottom: 10px; position: relative; overflow: hidden;
        }
        .stage-fill { height: 100%; background: linear-gradient(90deg, #6c5ce7, #a29bfe); width: 0%; transition: width 0.5s; }
        .stage-text { position: absolute; width: 100%; text-align: center; top: 0; line-height: 20px; font-size: 14px; font-weight: bold; }

        /* HP & Energy */
        .bars-wrapper { display: flex; gap: 20px; width: 100%; justify-content: space-between; align-items: flex-start; }
        .stat-box { display: flex; flex-direction: column; gap: 5px; width: 250px; }
        
        .bar-outline { width: 100%; height: 18px; background: #111; border: 2px solid #fff; border-radius: 4px; overflow: hidden; position: relative; }
        .bar-inner { height: 100%; transition: width 0.1s linear; }
        .hp-inner { background: var(--hp-col); }
        .en-inner { background: var(--en-col); }
        
        .hud-label { font-size: 14px; font-weight: bold; display: flex; justify-content: space-between; }

        /* Message Log / Boss Title */
        #game-message {
            position: absolute; top: 20%; left: 50%; transform: translate(-50%, -50%);
            font-size: 40px; color: #fff; text-shadow: 0 0 20px rgba(255,255,255,0.5);
            font-weight: bold; text-align: center; opacity: 0; transition: opacity 0.5s;
        }

        /* Controls Hint */
        .controls {
            direction: ltr;
            font-size: 12px; color: rgba(255,255,255,0.7); background: rgba(0,0,0,0.5);
            padding: 10px; border-radius: 8px; align-self: flex-start;
        }
        .key { color: var(--gold); font-weight: bold; }

        /* Screens */
        .screen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9); display: flex; flex-direction: column;
            align-items: center; justify-content: center; z-index: 100;
            pointer-events: auto; opacity: 1; transition: opacity 0.5s;
        }
        .hidden { display: none !important; opacity: 0; pointer-events: none; }
        
        h1 { font-size: 50px; margin: 0; background: -webkit-linear-gradient(#eee, #333); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        h2 { color: var(--gold); margin-top: 5px; }
        
        .btn {
            margin-top: 30px; padding: 15px 40px; font-size: 20px; cursor: pointer;
            background: transparent; color: #fff; border: 2px solid #fff; font-family: inherit;
            transition: 0.2s; text-transform: uppercase; font-weight: bold;
        }
        .btn:hover { background: #fff; color: #000; box-shadow: 0 0 15px #fff; }

        /* Floating unlock notification */
        #unlock-notify {
            position: absolute; bottom: 20%; left: 50%; transform: translateX(-50%);
            background: linear-gradient(90deg, transparent, rgba(108, 92, 231, 0.8), transparent);
            padding: 20px 50px; text-align: center; border-radius: 0;
            display: none; animation: floatUp 3s forwards;
        }
        @keyframes floatUp {
            0% { opacity: 0; transform: translate(-50%, 20px); }
            20% { opacity: 1; transform: translate(-50%, 0); }
            80% { opacity: 1; transform: translate(-50%, 0); }
            100% { opacity: 0; transform: translate(-50%, -20px); }
        }

        .back-link {
            position: absolute; top: 20px; left: 20px; color: #777; text-decoration: none; font-size: 14px;
        }
    </style>
</head>
<body>

<!-- UI Game Layout -->
<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="stage-container">
            <div class="stage-fill" id="prog-bar"></div>
            <div class="stage-text">שלב <span id="lvl-display">1</span> / 20</div>
        </div>
        
        <div class="bars-wrapper">
            <!-- HP -->
            <div class="stat-box" style="direction: ltr;">
                <div class="hud-label"><span style="color:var(--hp-col)">HP</span> <span id="hp-txt">100/100</span></div>
                <div class="bar-outline"><div class="hp-inner bar-inner" id="hp-bar" style="width: 100%"></div></div>
            </div>

            <!-- Enemy/Lock Icon placeholder in middle if needed -->
            <div id="lock-indicator" style="opacity: 0; color: #e74c3c; font-weight: bold; font-size: 20px;">TARGET LOCKED [E]</div>

            <!-- Energy -->
            <div class="stat-box" style="direction: ltr; text-align: right;">
                <div class="hud-label"><span id="en-txt">100/100</span> <span style="color:var(--en-col)">ENERGY</span></div>
                <div class="bar-outline"><div class="en-inner bar-inner" id="en-bar" style="width: 100%"></div></div>
            </div>
        </div>
    </div>
    
    <div id="game-message">BOSS WAVE</div>

    <div class="controls">
        <div>תזוזה: <span class="key">W A D</span></div>
        <div>יריות: <span class="key">H</span> (10%) <span class="key">J</span> (25%) <span class="key">K</span> (50%)</div>
        <div>סופר: <span class="key">Y</span> (100% - שלב 10)</div>
        <div>טעינה: <span class="key">U</span> (החזק)</div>
        <div>נעילה: <span class="key">E</span> (הפעל/בטל)</div>
    </div>
</div>

<!-- Notification -->
<div id="unlock-notify">
    <h2 style="margin:0">קיבלת יכולת חדשה!</h2>
    <p id="unlock-text" style="font-size:18px">Double Jump Unlocked</p>
</div>

<!-- Menus -->
<div id="menu-screen" class="screen">
    <a href="/" class="back-link">ESC : יציאה לתפריט ראשי</a>
    <h1 style="font-size: 80px;">CLOVER</h1>
    <h2>Elemental Chronicles</h2>
    <button class="btn" onclick="startGame()">התחל משחק</button>
</div>

<div id="game-over-screen" class="screen hidden">
    <h1 style="color: #c0392b">GAME OVER</h1>
    <p>הגעת לשלב <span id="death-stage" style="color:white; font-weight:bold;">1</span></p>
    <button class="btn" onclick="location.reload()">נסה שוב</button>
</div>

<div id="victory-screen" class="screen hidden">
    <h1 style="color: #f1c40f">ניצחון!</h1>
    <p>סיימת את כל 20 השלבים</p>
    <p>אתה אדון האלמנטים</p>
    <a href="/" class="btn">חזור לארקייד</a>
</div>


<script>
/**
 * LETS BUILD THE GAME ENGINE
 */
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);

// Resizing
function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
}
window.onresize = resize;
resize();

// --- Configuration & Stats ---
const CONFIG = {
    gravity: 0.6,
    friction: 0.85,
    groundY: canvas.height - 100
};

// State
let gameState = "MENU"; // MENU, PLAY, GAMEOVER, VICTORY
let keys = {};
let frame = 0;

let gameData = {
    stage: 1,
    maxStage: 20,
    shards: 0
};

let unlocks = {
    doubleJump: false, // After Stage 5 (Boss 1)
    superAttack: false, // After Stage 10 (Boss 2)
    autoCharge: false  // After Stage 15 (Boss 3)
};

// Entities
let player;
let enemies = [];
let projectiles = [];
let particles = [];
let camX = 0;
let shake = 0;

// Input Listeners
window.addEventListener('keydown', e => keys[e.key.toUpperCase()] = true);
window.addEventListener('keyup', e => keys[e.key.toUpperCase()] = false);
// Also prevent space scrolling
window.addEventListener('keydown', e => { if(e.keyCode == 32) e.preventDefault(); });


class Player {
    constructor() {
        this.w = 30; this.h = 60;
        this.x = 200; this.y = CONFIG.groundY - this.h;
        this.vx = 0; this.vy = 0;
        this.hp = 100; this.maxHp = 100;
        this.energy = 100; this.maxEnergy = 100;
        this.facing = 1; // 1 right, -1 left
        
        this.grounded = false;
        this.jumpCount = 0;
        this.isCharging = false;
        
        this.lockedTarget = null; // Target object for E lock
        this.lockCooldown = 0;
        this.lockEnabled = false;

        this.color = "#3498db";
    }

    update() {
        if(this.hp <= 0) return;

        // --- Controls ---
        this.isCharging = keys['U'];

        if (this.isCharging) {
            // Charging Mechanic
            this.vx *= 0.5; // Slow down drasticly
            if (this.energy < this.maxEnergy) {
                this.energy += 1;
                spawnParticle(this.x + this.w/2, this.y + this.h, this.color, 1);
            }
        } else {
            // Movement
            if (keys['A']) { this.vx -= 1; this.facing = -1; }
            if (keys['D']) { this.vx += 1; this.facing = 1; }
            
            // Jump (Space or W)
            if ((keys[' '] || keys['W'])) {
                if (!keys.jumpHeld) {
                    this.jump();
                    keys.jumpHeld = true;
                }
            } else {
                keys.jumpHeld = false;
            }
        }

        // --- Abilities & Shooting ---
        // Lock On Toggle
        if (keys['E'] && !keys.eHeld) {
            this.toggleLock();
            keys.eHeld = true;
        } else if (!keys['E']) keys.eHeld = false;

        // Shoot Keys
        if (!this.isCharging) {
            if (keys['H'] && !keys.hHeld) { this.shoot('weak'); keys.hHeld = true; }
            else if (!keys['H']) keys.hHeld = false;

            if (keys['J'] && !keys.jHeld) { this.shoot('medium'); keys.jHeld = true; }
            else if (!keys['J']) keys.jHeld = false;

            if (keys['K'] && !keys.kHeld) { this.shoot('strong'); keys.kHeld = true; }
            else if (!keys['K']) keys.kHeld = false;
            
            if (keys['Y'] && !keys.yHeld) { this.shoot('super'); keys.yHeld = true; }
            else if (!keys['Y']) keys.yHeld = false;
        }

        // Auto Charge Unlock
        if (unlocks.autoCharge && frame % 10 === 0 && this.energy < this.maxEnergy) {
            this.energy += 0.5;
        }

        // --- Physics ---
        this.vy += CONFIG.gravity;
        this.x += this.vx;
        this.y += this.vy;
        
        // Ground
        if (this.y + this.h > CONFIG.groundY) {
            this.y = CONFIG.groundY - this.h;
            this.vy = 0;
            this.grounded = true;
            this.jumpCount = 0;
        } else {
            this.grounded = false;
        }
        
        // Walls
        if (this.x < 0) { this.x = 0; this.vx = 0; }
        
        // Friction
        this.vx *= CONFIG.friction;

        // Cleanup Target if dead
        if (this.lockedTarget && this.lockedTarget.hp <= 0) {
            this.lockedTarget = null;
        }
    }

    jump() {
        let maxJumps = unlocks.doubleJump ? 2 : 1;
        if (this.jumpCount < maxJumps) {
            this.vy = -14;
            this.jumpCount++;
            spawnParticle(this.x + this.w/2, this.y + this.h, '#fff', 10);
        }
    }

    toggleLock() {
        if (this.lockEnabled) {
            this.lockEnabled = false;
            this.lockedTarget = null;
            showMessage("נעילה בוטלה");
        } else {
            // Find closest enemy
            let closest = null;
            let minDist = 10000;
            for(let e of enemies) {
                let d = Math.abs(e.x - this.x);
                if (d < minDist && e.x > this.x - 500 && e.x < this.x + 800) { // On screen ish
                    minDist = d;
                    closest = e;
                }
            }
            if (closest) {
                this.lockEnabled = true;
                this.lockedTarget = closest;
                showMessage("מטרה ננעלה!");
            } else {
                showMessage("אין אויבים");
            }
        }
        
        let el = document.getElementById('lock-indicator');
        el.style.opacity = this.lockEnabled ? 1 : 0;
    }

    shoot(type) {
        let cost = 0;
        let power = 0;
        let color = '#fff';
        let size = 5;
        
        switch(type) {
            case 'weak':
                cost = 10; power = 10; color = '#f1c40f'; size = 6;
                break;
            case 'medium':
                cost = 25; power = 25; color = '#e67e22'; size = 10;
                break;
            case 'strong':
                cost = 50; power = 60; color = '#e74c3c'; size = 15;
                break;
            case 'super':
                if (!unlocks.superAttack) return;
                cost = 100; power = 200; color = '#9b59b6'; size = 30;
                break;
        }

        if (this.energy >= cost) {
            this.energy -= cost;
            // Kickback
            this.vx -= (this.facing * power * 0.1); 
            
            projectiles.push(new Projectile(
                this.x + (this.facing===1 ? this.w : 0), 
                this.y + this.h/2, 
                this.facing, 
                type,
                this.lockedTarget
            ));
        } else {
            // Not enough energy visual
            showMessage("אין מספיק אנרגיה!");
        }
    }

    draw() {
        ctx.save();
        ctx.fillStyle = this.color;
        // Simple glow if full energy
        if (this.energy >= 95) {
            ctx.shadowBlur = 10; ctx.shadowColor = '#3498db';
        }
        ctx.fillRect(this.x, this.y, this.w, this.h);
        
        // Eyes
        ctx.fillStyle = '#fff';
        let ex = this.facing === 1 ? this.x + 20 : this.x + 5;
        ctx.fillRect(ex, this.y + 10, 5, 5);

        // Lock on Reticle
        if (this.lockEnabled && this.lockedTarget) {
            let t = this.lockedTarget;
            ctx.strokeStyle = '#e74c3c';
            ctx.lineWidth = 3;
            let pad = 10;
            ctx.strokeRect(t.x - pad, t.y - pad, t.w + pad*2, t.h + pad*2);
            ctx.beginPath(); ctx.moveTo(t.x + t.w/2, t.y - 20); ctx.lineTo(t.x + t.w/2, t.y); ctx.stroke();
        }

        ctx.restore();
    }
}

class Enemy {
    constructor(x, stage, isBoss = false) {
        this.x = x;
        this.y = CONFIG.groundY - 40;
        this.w = 40; this.h = 40;
        this.isBoss = isBoss;
        
        // Stats Scaling
        let scalar = isBoss ? 5 : 1;
        this.maxHp = (30 * stage) * scalar;
        if(isBoss) {
            this.w = 80; this.h = 100; this.y = CONFIG.groundY - 100;
            this.maxHp = 400 * (stage/5); // Boss stages are 5,10,15,20
        }
        this.hp = this.maxHp;
        
        this.vx = 0;
        this.color = isBoss ? "#8e44ad" : "#c0392b";
        this.speed = isBoss ? 2 + (stage*0.1) : 1 + (stage*0.1);
        this.damage = isBoss ? 15 : 5;
    }

    update() {
        // Simple AI: Move to player
        let dist = player.x - this.x;
        
        if (Math.abs(dist) < 800) {
            if (dist > 0) this.vx = this.speed;
            else this.vx = -this.speed;
        } else {
            this.vx = 0;
        }

        this.x += this.vx;

        // Collision with Player
        if (rectIntersect(this, player)) {
             player.hp -= 0.5; // DoT when touching
             // Knockback
             if(player.x > this.x) player.vx += 1; else player.vx -= 1;
             shakeScreen(1);
        }
    }

    draw() {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.w, this.h);
        
        // HP Bar
        ctx.fillStyle = "black";
        ctx.fillRect(this.x, this.y - 15, this.w, 6);
        ctx.fillStyle = "red";
        ctx.fillRect(this.x, this.y - 15, this.w * (this.hp / this.maxHp), 6);
        
        if (this.isBoss) {
            ctx.fillStyle = "#fff";
            ctx.font = "14px Rubik";
            ctx.fillText("BOSS", this.x + 20, this.y - 25);
        }
    }
}

class Projectile {
    constructor(x, y, dir, type, target) {
        this.x = x; this.y = y;
        this.target = target;
        this.type = type;
        
        // Base Stats
        this.speed = 15;
        this.vx = dir * this.speed;
        this.vy = 0;
        this.life = 100;
        this.w = 10; this.h = 10;
        
        // Adjust by type
        switch(type) {
            case 'weak': this.dmg = 15; this.color = '#f1c40f'; break;
            case 'medium': this.dmg = 40; this.color = '#e67e22'; this.w=15; this.h=15; break;
            case 'strong': this.dmg = 100; this.color = '#e74c3c'; this.w=20; this.h=20; break;
            case 'super': this.dmg = 300; this.color = '#9b59b6'; this.w=40; this.h=40; this.speed=8; break;
        }
    }
    
    update() {
        // Homing Logic
        if (this.target && this.target.hp > 0) {
            let tx = this.target.x + this.target.w/2;
            let ty = this.target.y + this.target.h/2;
            
            // Standard homing formula
            let dx = tx - this.x;
            let dy = ty - this.y;
            let angle = Math.atan2(dy, dx);
            
            // For 'Super' it's less maneuverable, for Weak it's very accurate
            let turnSpeed = (this.type === 'super') ? 0.05 : 0.2;
            
            // Apply Velocity directly for simpler arcade feel
            this.vx = Math.cos(angle) * this.speed;
            this.vy = Math.sin(angle) * this.speed;
        }

        this.x += this.vx;
        this.y += this.vy;
        this.life--;
        
        // Particle trail
        if (frame % 2 === 0) {
            spawnParticle(this.x, this.y, this.color, 1);
        }

        // Collision Check
        for (let i = enemies.length - 1; i >= 0; i--) {
            let e = enemies[i];
            if (rectIntersect(this, e)) {
                e.hp -= this.dmg;
                this.life = 0;
                shakeScreen(this.dmg / 10);
                spawnParticle(e.x+e.w/2, e.y+e.h/2, "#fff", 5);
                
                // Knockback enemy
                e.x += (this.vx > 0 ? 10 : -10);
                break;
            }
        }
    }
    
    draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.w/2, 0, Math.PI*2);
        ctx.fill();
    }
}

// Particle System
class Particle {
    constructor(x, y, c, spd) {
        this.x = x; this.y = y; this.color = c;
        this.vx = (Math.random()-0.5) * spd * 3;
        this.vy = (Math.random()-0.5) * spd * 3;
        this.life = 30;
    }
    update() { this.x+=this.vx; this.y+=this.vy; this.life--; }
    draw() { ctx.fillStyle = this.color; ctx.globalAlpha = this.life/30; ctx.fillRect(this.x,this.y, 4,4); ctx.globalAlpha=1; }
}

function spawnParticle(x, y, c, count) {
    for(let i=0; i<count; i++) particles.push(new Particle(x, y, c, 3));
}

// --- Wave System ---
let waveDelay = 0;
let bossFightActive = false;

function spawnWave() {
    let stage = gameData.stage;
    let isBoss = (stage % 5 === 0);
    
    showMessage(isBoss ? "!! BOSS BATTLE !!" : "Stage " + stage);
    
    enemies = [];
    
    if (isBoss) {
        // Spawn one BIG Boss
        let boss = new Enemy(player.x + 600, stage, true);
        enemies.push(boss);
        bossFightActive = true;
    } else {
        // Regular Waves
        let count = 2 + Math.floor(stage / 2);
        for (let i = 0; i < count; i++) {
            // Spawn dispersed
            enemies.push(new Enemy(player.x + 400 + (i*200), stage));
        }
        bossFightActive = false;
    }
    
    // Save Game progress on wave start
    fetch('save', {
        method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({stage: stage, shards: 0})
    }).catch(e=>{});
}

function handleWaveLogic() {
    // If all enemies dead
    if (enemies.length === 0 && waveDelay <= 0) {
        waveDelay = 150; // 2.5 seconds delay between waves
    }
    
    if (enemies.length === 0 && waveDelay > 0) {
        waveDelay--;
        if (waveDelay === 0) {
            handleLevelComplete();
        }
    }
}

function handleLevelComplete() {
    // Unlock Checks logic BEFORE increasing stage count for display
    let s = gameData.stage;
    
    if (s === 5) showUnlock("קפיצה כפולה! (מקש רווח x2)", "doubleJump");
    if (s === 10) showUnlock("סופר ירייה! (מקש Y)", "superAttack");
    if (s === 15) showUnlock("טעינה אוטומטית!", "autoCharge");
    
    if (s >= 20) {
        winGame();
        return;
    }
    
    gameData.stage++;
    spawnWave();
}

function showUnlock(text, prop) {
    unlocks[prop] = true;
    document.getElementById('unlock-text').innerText = text;
    let notif = document.getElementById('unlock-notify');
    notif.style.display = 'block';
    setTimeout(() => { notif.style.display = 'none'; }, 4000);
}


// --- Main Loops ---

function init() {
    player = new Player();
    gameData.stage = 1;
    gameData.shards = 0;
    particles = [];
    projectiles = [];
    shake = 0;
    spawnWave();
}

function startGame() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    gameState = "PLAY";
    init();
    loop();
}

function loop() {
    if (gameState !== "PLAY") return;
    frame++;

    // Logic
    player.update();
    projectiles.forEach(p => p.update());
    enemies.forEach(e => e.update());
    particles.forEach(p => p.update());

    // Clean Arrays
    projectiles = projectiles.filter(p => p.life > 0);
    particles = particles.filter(p => p.life > 0);
    // Remove dead enemies
    for(let i=enemies.length-1; i>=0; i--) {
        if(enemies[i].hp <= 0) {
            spawnParticle(enemies[i].x, enemies[i].y, 'purple', 10);
            gameData.shards += (enemies[i].isBoss ? 50 : 5);
            enemies.splice(i, 1);
        }
    }

    handleWaveLogic();

    // Death check
    if (player.hp <= 0) {
        endGame();
        return;
    }

    // Camera follow player
    let targetCamX = player.x - 200;
    if (targetCamX < 0) targetCamX = 0;
    camX += (targetCamX - camX) * 0.1;
    if(shake>0) {
        camX += (Math.random()-0.5)*shake;
        shake *= 0.9;
        if(shake<0.5) shake=0;
    }

    // Rendering
    draw();
    updateUI();
    
    requestAnimationFrame(loop);
}

function draw() {
    // Background
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0,0, canvas.width, canvas.height);
    
    // Moon
    ctx.fillStyle = "#dfe6e9";
    ctx.beginPath(); ctx.arc(canvas.width-100, 100, 40, 0, Math.PI*2); ctx.fill();
    
    ctx.save();
    ctx.translate(-camX, 0);

    // Floor
    ctx.fillStyle = "#2c3e50";
    ctx.fillRect(0, CONFIG.groundY, 20000, 500); // Infinite-ish floor
    ctx.fillStyle = "#8e44ad"; // Accent line
    ctx.fillRect(0, CONFIG.groundY, 20000, 5);

    // Grid details on floor
    ctx.strokeStyle = "#34495e";
    for(let i=0; i<20000; i+=100) {
        ctx.strokeRect(i, CONFIG.groundY, 100, 50);
    }
    
    // Entities
    player.draw();
    enemies.forEach(e => e.draw());
    projectiles.forEach(p => p.draw());
    particles.forEach(p => p.draw());

    ctx.restore();
}

// --- Utils ---

function updateUI() {
    let pHP = Math.max(0, (player.hp / player.maxHp) * 100);
    let pEN = Math.max(0, (player.energy / player.maxEnergy) * 100);
    
    document.getElementById('hp-bar').style.width = pHP + "%";
    document.getElementById('hp-txt').innerText = Math.ceil(player.hp);
    
    document.getElementById('en-bar').style.width = pEN + "%";
    document.getElementById('en-txt').innerText = Math.floor(player.energy);
    
    document.getElementById('lvl-display').innerText = gameData.stage;
    
    // Progress bar fill based on Stage/20
    document.getElementById('prog-bar').style.width = (gameData.stage / 20 * 100) + "%";
}

function showMessage(text) {
    let el = document.getElementById('game-message');
    el.innerText = text;
    el.style.opacity = 1;
    // Animation reset trick
    el.style.animation = 'none';
    el.offsetHeight; /* trigger reflow */
    setTimeout(()=> el.style.opacity = 0, 2000);
}

function rectIntersect(r1, r2) {
    return !(r2.x > r1.x + r1.w || 
             r2.x + r2.w < r1.x || 
             r2.y > r1.y + r1.h || 
             r2.y + r2.h < r1.y);
}

function shakeScreen(amount) { shake = amount; }

function endGame() {
    gameState = "GAMEOVER";
    document.getElementById('death-stage').innerText = gameData.stage;
    document.getElementById('ui-layer').classList.add('hidden');
    document.getElementById('game-over-screen').classList.remove('hidden');
}

function winGame() {
    gameState = "VICTORY";
    document.getElementById('ui-layer').classList.add('hidden');
    document.getElementById('victory-screen').classList.remove('hidden');
}

</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)


