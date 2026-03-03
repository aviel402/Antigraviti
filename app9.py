from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)
app.secret_key = 'clover_master_key_v99'

# Placeholder for persistent improvement storage
PLAYER_DATA = {
    "shards": 0,
    "unlocks": ["fire", "warrior"],
    "upgrades": {
        "hp": 0,
        "energy_charge": 0,
        "potion": 0
    }
}

@app.route('/')
def idx():
    return render_template_string(GAME_HTML)

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    data = request.json
    PLAYER_DATA["shards"] += data.get("shards", 0)
    print(f"Server Saved (CLOVER /game9/): User now has {PLAYER_DATA['shards']} Shards!")
    return jsonify(PLAYER_DATA)

@app.route('/data')
def get_data():
    return jsonify(PLAYER_DATA)

@app.route('/unlock', methods=['POST'])
def unlock_class():
    return jsonify({"status": "ok"})

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Elemental Chronicles</title>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        :root { --ui-bg: rgba(20,20,30,0.9); --text-color: #eee; }
        body { margin:0; overflow:hidden; background:#111; font-family:'Press Start 2P', cursive; color:var(--text-color); }
        canvas { display:block; image-rendering:pixelated; }
        #ui-layer {
            position:absolute; top:0; left:0; width:100%; height:100%;
            pointer-events:none; display:flex; flex-direction:column;
            justify-content:space-between; padding:20px; box-sizing:border-box;
        }
        .hud-top { display:flex; flex-direction:column; gap:8px; }
        .hud-bar { display:flex; gap:10px; align-items:center; text-shadow:2px 2px #000; font-size:14px; }
        .bar-container { position:relative; width:220px; height:18px; background:#222; border:3px solid #fff; border-radius:4px; overflow:hidden; }
        .bar-fill { height:100%; transition:width 0.1s ease-out; }
        .hp-fill { background:#ff3333; }
        .en-fill { background:#33ccff; }
        #shards-display { font-size:22px; color:gold; text-shadow:2px 2px #000; pointer-events:auto; }
        #stage-display { position:absolute; top:20px; right:20px; font-size:18px; color:#ffcc00; text-shadow:2px 2px #000; }
        .controls-hint {
            position:absolute; bottom:20px; right:20px; text-align:right;
            font-size:10px; opacity:0.85; line-height:1.7; text-shadow:1px 1px #000;
        }
        .controls-hint span { color:gold; }
        #menu-screen, #char-select, #gameover-screen {
            position:absolute; top:0; left:0; width:100%; height:100%;
            background:rgba(0,0,0,0.9); display:flex; flex-direction:column;
            align-items:center; justify-content:center; pointer-events:auto; z-index:100;
        }
        .hidden { display:none !important; }
        h1 { font-size:48px; color:#fff; text-shadow:4px 4px 0 #33ccff; margin-bottom:30px; }
        .btn {
            background:#222; border:4px solid #fff; color:#fff; padding:14px 32px;
            font-family:inherit; font-size:15px; cursor:pointer; margin:10px;
            text-transform:uppercase; transition:all 0.1s;
        }
        .btn:hover { background:#444; border-color:gold; transform:scale(1.08); }
        .char-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:18px; max-width:860px; }
        .char-card {
            background:#111; border:3px solid #555; padding:12px; text-align:center;
            cursor:pointer; transition:all 0.2s; border-radius:8px;
        }
        .char-card:hover { border-color:#33ccff; background:#222; transform:translateY(-8px); }
        .char-emoji { font-size:52px; margin-bottom:8px; }
        .scanlines {
            position:fixed; top:0; left:0; width:100%; height:100%;
            background:linear-gradient(to bottom, rgba(255,255,255,0) 50%, rgba(0,0,0,0.12) 50%);
            background-size:100% 4px; pointer-events:none; z-index:999;
        }
    </style>
</head>
<body>
<div class="scanlines"></div>
<canvas id="gameCanvas"></canvas>

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="hud-bar"><span>HP</span><div class="bar-container"><div class="bar-fill hp-fill" id="hp-bar" style="width:100%"></div></div></div>
        <div class="hud-bar"><span>EN</span><div class="bar-container"><div class="bar-fill en-fill" id="en-bar" style="width:100%"></div></div></div>
        <div id="shards-display">💎 0</div>
    </div>
    <div id="stage-display">STAGE 1</div>
    
    <div class="controls-hint">
        <div><span>W / SPACE</span> קפיצה (כפולה אחרי בוס)</div>
        <div><span>A D</span> תנועה</div>
        <div><span>H</span> התקפה חלשה <span>J</span> התקפה רגילה <span>K</span> התקפה חזקה</div>
        <div><span>S</span> התכופפות <span>R</span> נעילה על אויב</div>
    </div>
</div>

<!-- MENU -->
<div id="menu-screen">
    <a href="/" class="btn" style="position:absolute;top:20px;left:20px;">🔙 חזרה להאב</a>
    <h1>🍀 CLOVER</h1>
    <p style="margin-bottom:30px;font-size:18px;">Elemental Chronicles</p>
    <button class="btn" onclick="openCharSelect()">התחל הרפתקה</button>
</div>

<!-- CHAR SELECT -->
<div id="char-select" class="hidden">
    <h2 style="color:gold;">בחר גיבור</h2>
    <div class="char-grid" id="char-grid"></div>
    <button class="btn" onclick="backToMenu()" style="margin-top:40px;">חזרה לתפריט</button>
</div>

<!-- GAME OVER -->
<div id="gameover-screen" class="hidden">
    <h1 style="color:#ff3333;">נפלת!</h1>
    <p>שברים שנאספו: <span id="final-shards" style="color:gold;">0</span></p>
    <button class="btn" onclick="location.reload()">נסה שוב</button>
    <br><a href="/" class="btn" style="margin-top:20px;">🔙 חזרה להאב</a>
</div>

<script>
// ====================== SETUP ======================
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const GRAVITY = 0.55;
const FRICTION = 0.82;

let gameState = 'MENU';
let camera = { x: 0 };
let stage = 1;
let stageProgress = 0;
let currentShards = 0;
let lockedEnemy = null;
let hasDoubleJump = false;
let superPower = false;          // כוח סופר (פעיל אחרי בוס)
let superTimer = 0;

// ====================== INPUT ======================
const keys = { w:false, a:false, s:false, d:false, h:false, j:false, k:false, r:false };
let rPressedLast = false;

window.addEventListener('keydown', e => {
    const k = e.key.toLowerCase();
    if (keys.hasOwnProperty(k)) keys[k] = true;
});
window.addEventListener('keyup', e => {
    const k = e.key.toLowerCase();
    if (keys.hasOwnProperty(k)) keys[k] = false;
});

// ====================== CLASSES WITH EMOJI ======================
const CLASSES = {
    fire:   { name: "Pyromancer", color: "#ff4422", emoji: "🔥", skill: "Fireball" },
    water:  { name: "Hydromancer", color: "#2244ff", emoji: "💧", skill: "Wave" },
    earth:  { name: "Geomancer", color: "#88aa44", emoji: "🌍", skill: "Rock" },
    air:    { name: "Aeromancer", color: "#ccddff", emoji: "🌬️", skill: "Windblade" },
    warrior:{ name: "Warrior", color: "#aaaaaa", emoji: "⚔️", skill: "Slash" },
    light:  { name: "Lightbringer", color: "#ffffaa", emoji: "✨", skill: "Beam" },
    dark:   { name: "Voidwalker", color: "#6600cc", emoji: "🌑", skill: "Void" }
};

let player, enemies = [], projectiles = [], enemyProjectiles = [], particles = [];

// ====================== ENTITIES ======================
class Entity {
    constructor(x, y, w, h, color, emoji) {
        this.x = x; this.y = y; this.w = w; this.h = h;
        this.vx = 0; this.vy = 0;
        this.color = color; this.emoji = emoji || "👹";
        this.grounded = false;
        this.hp = 100; this.maxHp = 100;
    }
    update() { /* will be overridden */ }
    draw() {
        // emoji body
        ctx.save();
        ctx.font = `${this.h}px Arial`;
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";
        ctx.fillStyle = this.color;
        ctx.fillText(this.emoji, this.x + this.w/2, this.y + this.h + 4);
        ctx.restore();

        // health bar
        if (this.hp < this.maxHp) {
            const barW = this.w * (this.hp / this.maxHp);
            ctx.fillStyle = "red";
            ctx.fillRect(this.x, this.y - 12, barW, 5);
            ctx.strokeStyle = "#fff";
            ctx.lineWidth = 1;
            ctx.strokeRect(this.x, this.y - 12, this.w, 5);
        }
    }
}

class Player extends Entity {
    constructor(clsKey) {
        const c = CLASSES[clsKey];
        super(120, 320, 32, 52, c.color, c.emoji);
        this.cls = c;
        this.energy = 100;
        this.maxEnergy = 100;
        this.attackCooldown = 0;
        this.jumpCount = 0;
        this.standHeight = 52;
        this.crouchHeight = 26;
    }
update() {
    if (this.hp <= 0) return;

    // crouch – רק אם על הקרקע
    const isCrouching = keys.s && this.grounded;
    const targetH = isCrouching ? this.crouchHeight : this.standHeight;
    if (this.h !== targetH) {
        const diff = this.h - targetH;
        this.y += diff;  // שומר על רגליים על הקרקע
        this.h = targetH;
    }

    // תנועה – חסומה רק אם crouch מלא (אפשר להוסיף תנועה איטית אם רוצים)
    let moveSpeed = isCrouching ? 0.8 : 1.8;  // איטי יותר כשמתכופף
    if (keys.a) { this.vx -= moveSpeed; }
    if (keys.d) { this.vx += moveSpeed; }

    // קפיצה + כפולה
    if (keys.w && this.grounded) {
        this.vy = -13.5;
        this.grounded = false;
        this.jumpCount = 1;
        spawnParticles(this.x + 16, this.y + this.h, "#fff", 8);
    } else if (keys.w && this.jumpCount < (hasDoubleJump ? 2 : 1) && !this.grounded && this.vy > -5) {
        // אפשר רק אם לא ממש באוויר גבוה
        this.vy = -13;
        this.jumpCount++;
        spawnParticles(this.x + 16, this.y + this.h, "#fff", 12);
    }

    // טעינה ידנית חזרה עם U (אם אתה רוצה – אפשר להסיר אם לא)
    if (keys.u) {
        this.energy = Math.min(this.maxEnergy, this.energy + 3.5);  // טעינה מהירה
        this.vx *= 0.6;  // מאט אותך קצת בזמן טעינה
        spawnParticles(this.x + this.w/2, this.y + this.h/2, this.color, 2);
    } else {
        // טעינה אוטומטית איטית יותר כשלא לוחץ U
        this.energy = Math.min(this.maxEnergy, this.energy + 0.45);
    }

    // התקפות – ניקוי תנאים + debug
    if (this.attackCooldown > 0) this.attackCooldown--;

    if (keys.h && this.attackCooldown <= 0 && this.energy >= 9) {
        this.attack(15, 7, "#ffff00", 8, 9);   // חלשה
    }
    if (keys.j && this.attackCooldown <= 0 && this.energy >= 16) {
        this.attack(26, 11, this.color, 14, 16); // רגילה
    }
    if (keys.k && this.attackCooldown <= 0 && this.energy >= 28) {
        this.attack(48, 9, "#ff8800", 24, 28);   // חזקה
    }

    // פיזיקה בסיסית
    this.vy += GRAVITY;
    this.x += this.vx;
    this.y += this.vy;
    this.vx *= FRICTION;

    // קרקע
    const groundY = 400;
    if (this.y + this.h > groundY) {
        this.y = groundY - this.h;
        this.vy = 0;
        this.grounded = true;
        this.jumpCount = 0;
    } else {
        this.grounded = false;
    }

    if (this.x < 0) { this.x = 0; this.vx = 0; }

    // HUD update
    document.getElementById('hp-bar').style.width = Math.max(0, this.hp / this.maxHp * 100) + "%";
    document.getElementById('en-bar').style.width = (this.energy / this.maxEnergy * 100) + "%";
}
    attack(dmg, speed, color, cd, energyCost) {
        this.attackCooldown = cd;
        this.energy -= energyCost;
        const dir = 1;
        const px = this.x + (dir > 0 ? this.w : 0);
        const py = this.y + this.h * 0.35;
        const p = new Projectile(px, py, speed * dir, 0, color, dmg);
        if (lockedEnemy && lockedEnemy.hp > 0) p.locked = lockedEnemy;
        projectiles.push(p);
        this.vx -= dir * 4.5; // recoil
        shakeScreen(3);
    }

    draw() {
        super.draw();
        // super power glow
        if (superPower) {
            ctx.save();
            ctx.strokeStyle = "#ffff00";
            ctx.lineWidth = 4;
            ctx.globalAlpha = 0.4 + Math.sin(Date.now()/80)*0.2;
            ctx.beginPath();
            ctx.arc(this.x + this.w/2, this.y + this.h/2, this.h*0.7, 0, Math.PI*2);
            ctx.stroke();
            ctx.restore();
        }
    }
}

class Projectile {
    constructor(x, y, vx, vy, color, dmg) {
        this.x = x; this.y = y; this.vx = vx; this.vy = vy;
        this.color = color; this.dmg = dmg || 25;
        this.life = 55;
        this.locked = null;
    }
    update() {
        if (this.locked && this.locked.hp > 0) {
            const dx = this.locked.x + this.locked.w/2 - this.x;
            const dy = this.locked.y + this.locked.h/2 - this.y;
            const dist = Math.hypot(dx, dy) || 1;
            this.vx = (dx / dist) * 11;
            this.vy = (dy / dist) * 11;
        }
        this.x += this.vx;
        this.y += this.vy;
        this.life--;
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, 7, 0, Math.PI*2);
        ctx.fill();
    }
}

class Enemy extends Entity {
    constructor(x, isBoss = false) {
        super(x, 320, isBoss ? 52 : 34, isBoss ? 52 : 34, isBoss ? "#aa0000" : "#a02b4d", isBoss ? "🐉" : "👹");
        this.maxHp = isBoss ? 240 : 42;
        this.hp = this.maxHp;
        this.isBoss = isBoss;
        this.shootTimer = 0;
    }
    update() {
        this.vx *= 0.88;
        const dist = player.x - this.x;
        if (Math.abs(dist) < 620 && Math.abs(dist) > 30) {
            this.vx += (dist > 0 ? 0.35 : -0.35);
        }
        this.vy += GRAVITY;
        this.x += this.vx;
        this.y += this.vy;

        if (this.y + this.h > 400) {
            this.y = 400 - this.h;
            this.vy = 0;
        }

        // shoot
        this.shootTimer++;
        if (this.shootTimer > (this.isBoss ? 35 : 68) && Math.random() < 0.65) {
            this.shootTimer = 0;
            const dir = player.x > this.x ? 1 : -1;
            const p = new Projectile(this.x + this.w/2, this.y + 18, dir * 6.5, 0, "#ff00aa", this.isBoss ? 18 : 11);
            enemyProjectiles.push(p);
        }

        // melee
        if (checkRectCollide(this, player)) {
            player.hp -= this.isBoss ? 3.5 : 2;
            player.vx = (player.x > this.x ? 9 : -9);
            shakeScreen(6);
        }
    }
}

// ====================== UTILS ======================
function checkRectCollide(a, b) {
    return !(a.x > b.x + b.w || a.x + a.w < b.x || a.y > b.y + b.h || a.y + a.h < b.y);
}

function spawnParticles(x, y, color, count) {
    for (let i = 0; i < count; i++) {
        particles.push({
            x, y,
            vx: (Math.random()-0.5)*7,
            vy: (Math.random()-1)*7 - 2,
            life: 18 + Math.random()*14,
            color,
            size: 5 + Math.random()*4
        });
    }
}

let shake = 0;
function shakeScreen(n) { shake = Math.max(shake, n); }

function getClosestEnemy() {
    let best = null;
    let bestDist = 999999;
    for (let e of enemies) {
        const d = Math.abs(e.x - player.x);
        if (d < bestDist) {
            bestDist = d;
            best = e;
        }
    }
    return best;
}

// ====================== GAME INIT ======================
function initGame(clsKey) {
    player = new Player(clsKey);
    enemies = [];
    projectiles = [];
    enemyProjectiles = [];
    particles = [];
    stage = 1;
    stageProgress = 0;
    currentShards = 0;
    lockedEnemy = null;
    hasDoubleJump = false;
    superPower = false;
    superTimer = 0;

    // initial enemies
    for (let i = 0; i < 4; i++) enemies.push(new Enemy(700 + i * 280));

    fetch('data').then(r => r.json()).then(d => {
        currentShards = d.shards;
        document.getElementById('shards-display').innerText = `💎 ${currentShards}`;
    });

    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    document.getElementById('stage-display').innerText = `STAGE ${stage}`;

    gameState = 'PLAY';
    requestAnimationFrame(loop);
}

function unlockBonus() {
    const r = Math.random();
    if (!hasDoubleJump) {
        hasDoubleJump = true;
        showTempMessage("קפיצה כפולה נפתחה! 🦘");
    } else if (!superPower) {
        superPower = true;
        superTimer = 720; // ~12 שניות
        showTempMessage("כוח סופר! ⚡");
    } else {
        player.maxEnergy += 35;
        showTempMessage("אנרגיה מקסימלית +35! 🔋");
    }
}

function showTempMessage(txt) {
    const msg = document.createElement('div');
    msg.style.position = "fixed";
    msg.style.top = "35%";
    msg.style.left = "50%";
    msg.style.transform = "translate(-50%,-50%)";
    msg.style.fontSize = "28px";
    msg.style.color = "#ff0";
    msg.style.textShadow = "0 0 15px #ff0";
    msg.style.zIndex = "9999";
    msg.style.pointerEvents = "none";
    msg.innerText = txt;
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 2200);
}

// ====================== MAIN LOOP ======================
function update() {
    if (gameState !== 'PLAY') return;

    player.update();

    // camera
    let targetCam = player.x - canvas.width * 0.35;
    if (targetCam < 0) targetCam = 0;
    camera.x += (targetCam - camera.x) * 0.12;

    // stage progress
    stageProgress++;
    if (stageProgress > 380 + stage * 45) {
        stage++;
        stageProgress = 0;
        document.getElementById('stage-display').innerText = `STAGE ${stage} 🔥`;
        for (let i = 0; i < 3; i++) {
            enemies.push(new Enemy(player.x + 750 + i * 190));
        }
        if (stage % 5 === 0) {
            const boss = new Enemy(player.x + 920, true);
            enemies.push(boss);
        }
    }

    // enemies
    for (let i = enemies.length - 1; i >= 0; i--) {
        const e = enemies[i];
        e.update();

        if (e.hp <= 0) {
            spawnParticles(e.x + e.w/2, e.y + e.h/2, "gold", 28);
            collectShard(e.isBoss ? 35 : 6);
            if (e.isBoss) unlockBonus();
            enemies.splice(i, 1);
            shakeScreen(7);
        }
    }

    // player projectiles
    for (let i = projectiles.length - 1; i >= 0; i--) {
        const p = projectiles[i];
        p.update();

        for (let j = enemies.length - 1; j >= 0; j--) {
            if (checkRectCollide(p, enemies[j])) {
                const realDmg = superPower ? Math.floor(p.dmg * 1.65) : p.dmg;
                enemies[j].hp -= realDmg;
                p.life = 0;
                spawnParticles(p.x, p.y, "#ff0", 9);
                break;
            }
        }
        if (p.life <= 0) projectiles.splice(i, 1);
    }

    // enemy projectiles
    for (let i = enemyProjectiles.length - 1; i >= 0; i--) {
        const p = enemyProjectiles[i];
        p.x += p.vx;
        p.life--;
        if (checkRectCollide(p, player)) {
            player.hp -= p.dmg;
            shakeScreen(8);
            enemyProjectiles.splice(i, 1);
            continue;
        }
        if (p.life <= 0) enemyProjectiles.splice(i, 1);
    }

    // particles
    particles = particles.filter(p => {
        p.x += p.vx; p.y += p.vy; p.vy += 0.35; p.life--; p.size *= 0.92;
        return p.life > 0;
    });

    // death
    if (player.hp <= 0) {
        gameState = 'GAMEOVER';
        document.getElementById('final-shards').innerText = currentShards;
        document.getElementById('ui-layer').classList.add('hidden');
        document.getElementById('gameover-screen').classList.remove('hidden');
    }
}

function draw() {
    // background
    const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, "#0a0a2a");
    grad.addColorStop(1, "#1b1b44");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    if (shake > 0) {
        ctx.translate((Math.random()-0.5)*shake, (Math.random()-0.5)*shake);
        shake *= 0.82;
    }
    ctx.translate(-camera.x, 0);

    // floor
    ctx.fillStyle = "#1c1f2e";
    ctx.fillRect(camera.x - 300, 400, canvas.width + 800, canvas.height - 400);
    ctx.fillStyle = "#3ee989";
    ctx.fillRect(camera.x - 300, 400, canvas.width + 800, 6);

    // entities
    enemies.forEach(e => e.draw());
    player.draw();
    projectiles.forEach(p => p.draw());
    enemyProjectiles.forEach(p => {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 6, 0, Math.PI*2);
        ctx.fill();
    });
    particles.forEach(p => {
        ctx.globalAlpha = p.life / 30;
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, p.size, p.size);
    });
    ctx.globalAlpha = 1;

    ctx.restore();
}

function loop() {
    if (gameState === 'PLAY') {
        update();
        draw();
    }
    requestAnimationFrame(loop);
}

// ====================== SHARDS ======================
async function collectShard(amount) {
    currentShards += amount;
    document.getElementById('shards-display').innerText = `💎 ${currentShards}`;
    fetch('save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({shards: amount})
    }).catch(() => {});
}

// ====================== MENU ======================
function openCharSelect() {
    document.getElementById('menu-screen').classList.add('hidden');
    const grid = document.getElementById('char-grid');
    grid.innerHTML = '';
    for (let k in CLASSES) {
        const c = CLASSES[k];
        const card = document.createElement('div');
        card.className = 'char-card';
        card.innerHTML = `
            <div class="char-emoji">${c.emoji}</div>
            <h3 style="margin:4px 0 6px">${c.name}</h3>
            <small style="color:#aaa">${c.skill}</small>
        `;
        card.onclick = () => initGame(k);
        grid.appendChild(card);
    }
    document.getElementById('char-select').classList.remove('hidden');
}

function backToMenu() {
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('menu-screen').classList.remove('hidden');
}

// Lock-on R
window.addEventListener('keydown', e => {
    if (e.key.toLowerCase() === 'r' && gameState === 'PLAY') {
        if (lockedEnemy) {
            lockedEnemy = null;
        } else {
            lockedEnemy = getClosestEnemy();
        }
    }
});

window.onload = () => {
    document.getElementById('menu-screen').classList.remove('hidden');
};
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)

