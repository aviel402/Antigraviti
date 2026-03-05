from flask import Flask, render_template_string, jsonify, request

# חשוב: זו האפליקציה שמיובאת בקובץ הראשי שלך בתור game9
app = Flask(__name__)
app.secret_key = 'clover_master_key_v99'

# Placeholder for persistent improvement storage (in a real app, use a DB)
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
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Elemental Chronicles</title>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        :root {
            --ui-bg: rgba(20, 20, 30, 0.9);
            --text-color: #eee;
        }
        body { margin: 0; overflow: hidden; background: #111; font-family: 'Press Start 2P', cursive; color: var(--text-color); }
        canvas { display: block; image-rendering: pixelated; }
        
        #ui-layer {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; display: flex; flex-direction: column;
            justify-content: space-between; padding: 20px; box-sizing: border-box;
        }

        .hud-top { display: flex; flex-direction: column; gap: 10px; }
        .hud-bar { display: flex; gap: 10px; align-items: center; text-shadow: 2px 2px #000;}
        .bar-container { position: relative; width: 200px; height: 15px; background: #222; border: 2px solid #fff; border-radius: 4px; overflow: hidden; }
        .bar-fill { height: 100%; transition: width 0.1s ease-out; }
        .hp-fill { background: #ff3333; }
        .en-fill { background: #33ccff; }
        
        #shards-display {
            font-size: 20px; color: gold; text-shadow: 2px 2px #000; pointer-events: auto;
        }
        
        .controls-hint {
            position: absolute; bottom: 20px; right: 20px; text-align: right;
            font-size: 10px; opacity: 0.8; line-height: 1.8; text-shadow: 1px 1px #000;
        }
        .controls-hint span { color: gold; }

        #menu-screen, #char-select {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85); display: flex; flex-direction: column;
            align-items: center; justify-content: center; pointer-events: auto; z-index: 100;
        }
        
        .hidden { display: none !important; }
        h1 { font-size: 40px; color: #fff; text-shadow: 4px 4px 0 #33ccff; margin-bottom: 40px; text-align: center;}
        h2 { color: gold; margin-bottom: 20px; text-align: center;}
        
        .btn {
            background: #222; border: 4px solid #fff; color: #fff; padding: 15px 30px;
            font-family: inherit; font-size: 16px; cursor: pointer; margin: 10px;
            text-transform: uppercase; transition: transform 0.1s, border-color 0.2s;
        }
        .btn:hover { background: #444; border-color: gold; transform: scale(1.05); }
        .btn:active { transform: scale(0.95); }
        
        .char-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 800px; }
        .char-card { background: #111; border: 2px solid #555; padding: 15px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .char-card:hover { border-color: #33ccff; background: #222; transform: translateY(-5px);}
        .char-icon { width: 48px; height: 48px; margin: 0 auto 10px; border-radius: 8px;}
        
        .scanlines {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(to bottom, rgba(255,255,255,0) 50%, rgba(0,0,0,0.1) 50%);
            background-size: 100% 4px; pointer-events: none; z-index: 999;
        }
        #gameover-screen {
             position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(100,0,0,0.8);
             display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 150;
             pointer-events: auto;
        }

        .back-hub { position: absolute; top: 20px; left: 20px; font-size: 10px; padding: 10px; }
    </style>
</head>
<body>

<div class="scanlines"></div>

<canvas id="gameCanvas"></canvas>

<!-- UI Layer -->
<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="hud-bar">
            <span>HP</span><div class="bar-container"><div class="bar-fill hp-fill" id="hp-bar" style="width: 100%"></div></div>
        </div>
        <div class="hud-bar">
            <span>EN</span><div class="bar-container"><div class="bar-fill en-fill" id="en-bar" style="width: 100%"></div></div>
        </div>
        <div id="shards-display" style="margin-top: 10px;">💎 0</div>
    </div>
    
    <div class="controls-hint">
        <div><span>[W A D]</span> Move/Jump</div>
        <div><span>[ U ]</span> Charge Energy</div>
        <div><span>[ J ]</span> Attack</div>
    </div>
</div>

<!-- Main Menu -->
<div id="menu-screen">
    <!-- Back to Main Arcade Launcher Button -->
    <a href="/" class="btn back-hub">🔙 EXIT TO HUB</a>
    
    <h1>🍀 CLOVER</h1>
    <p style="margin-bottom: 20px;">Elemental Chronicles</p>
    <button class="btn" onclick="openCharSelect()">START ADVENTURE</button>
</div>

<!-- Character Select -->
<div id="char-select" class="hidden">
    <h2>CHOOSE YOUR HERO</h2>
    <div class="char-grid" id="char-grid"></div>
    <button class="btn" onclick="backToMenu()" style="margin-top: 30px;">BACK TO TITLE</button>
</div>

<!-- Game Over -->
<div id="gameover-screen" class="hidden">
    <h1 style="color: #ff3333;">YOU DIED</h1>
    <p>Total Shards Collected: <span id="final-shards" style="color:gold;">0</span></p>
    <button class="btn" onclick="location.reload()">TRY AGAIN</button>
    <br>
    <a href="/" class="btn back-hub" style="position: relative; display: inline-block; margin-top: 20px; top:0; left:0;">🔙 EXIT TO HUB</a>
</div>


<script>
// --- Canvas Setup ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const GRAVITY = 0.5; const FRICTION = 0.8;
let gameState = 'MENU';
let camera = { x: 0, y: 0 };
let currentShards = 0;

// Dynamic Resize
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
});
window.dispatchEvent(new Event('resize'));

// --- Input System ---
const keys = { w:false, a:false, s:false, d:false, j:false, k:false, u:false };
window.addEventListener('keydown', e => { if(keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = true; });
window.addEventListener('keyup', e => { if(keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = false; });

// --- Game Data ---
const CLASSES = {
    fire: { name: "Pyromancer", color: "#ff4422", skill: "Fireball" },
    water: { name: "Hydromancer", color: "#2244ff", skill: "Wave" },
    earth: { name: "Geomancer", color: "#88aa44", skill: "Rock" },
    air: { name: "Aeromancer", color: "#ccddff", skill: "Windblade" },
    warrior: { name: "Warrior", color: "#aaaaaa", skill: "Slash" },
    light: { name: "Lightbringer", color: "#ffffaa", skill: "Beam" },
    dark: { name: "Voidwalker", color: "#6600cc", skill: "Void" }
};

let player, enemies = [], particles = [], projectiles = [];

// --- Server API Connectors ---
// ** FIXED ROUTING: uses 'save' instead of '/save' so DispatcherMiddleware knows it belongs to game9
async function collectShard(amount) {
    currentShards += amount;
    document.getElementById('shards-display').innerText = `💎 ${currentShards}`;
    
    // Post to relative endpoint for this game 
    fetch('save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shards: amount })
    }).catch(e => console.error("Could not save to server", e));
}

// --- Physics Engine ---
class Entity {
    constructor(x, y, w, h, color) {
        this.x = x; this.y = y; this.w = w; this.h = h;
        this.vx = 0; this.vy = 0;
        this.color = color; this.grounded = false; this.facing = 1;
        this.hp = 100; this.maxHp = 100;
    }
    update() {
        this.vy += GRAVITY; this.x += this.vx; this.y += this.vy;
        
        // Ground Collision
        let groundY = 400;
        if (this.y + this.h > groundY) {
            this.y = groundY - this.h; this.vy = 0; this.grounded = true;
        } else { this.grounded = false; }
        
        this.vx *= FRICTION;
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.w, this.h);
        
        // Healthbar for enemies
        if(this.maxHp !== 100 || this instanceof Enemy) {
            ctx.fillStyle = "red";
            ctx.fillRect(this.x, this.y - 10, this.w * (this.hp/this.maxHp), 4);
        }
    }
}

class Player extends Entity {
    constructor(clsKey) {
        super(100, 300, 24, 48, CLASSES[clsKey].color);
        this.cls = CLASSES[clsKey];
        this.energy = 100; this.maxEnergy = 100;
        this.charging = false; this.attackCooldown = 0;
    }
    update() {
        if (this.hp <= 0) return;
        
        if (!this.charging) {
            if (keys.a) { this.vx -= 1.5; this.facing = -1; }
            if (keys.d) { this.vx += 1.5; this.facing = 1; }
            if (keys.w && this.grounded) { this.vy = -12; this.grounded = false; spawnParticles(this.x, this.y+this.h, "#fff", 5); }
        }
        
        // Bound player so he can't go backwards infinitely past 0
        if(this.x < 0) { this.x = 0; this.vx = 0; }

        // Energy Mechanics
        this.charging = keys.u;
        if (this.charging) {
            this.energy = Math.min(this.energy + 2, this.maxEnergy);
            this.vx *= 0.8;
            spawnParticles(this.x + this.w/2, this.y + this.h, this.color, 1, 0.5);
        }
        
        // Attack
        if (this.attackCooldown > 0) this.attackCooldown--;
        if (keys.j && this.attackCooldown <= 0 && this.energy >= 15) {
            this.attack();
        }
        
        super.update();
        
        // HUD Update
        document.getElementById('hp-bar').style.width = Math.max((this.hp / this.maxHp * 100), 0) + "%";
        document.getElementById('en-bar').style.width = (this.energy / this.maxEnergy * 100) + "%";
    }
    
    attack() {
        this.attackCooldown = 15;
        this.energy -= 15;
        let pvx = this.facing * 12; // Shoots direction we look
        projectiles.push(new Projectile(this.x + (this.facing===1?this.w:0), this.y + this.h/3, pvx, 0, this.color));
        player.vx -= this.facing * 3; // Kickback recoil
        shakeScreen(2);
    }
    
    draw() {
        super.draw();
        // Character Eye
        ctx.fillStyle = 'white';
        let eyeX = this.facing === 1 ? this.x + 14 : this.x + 4;
        ctx.fillRect(eyeX, this.y + 10, 6, 6);
        
        // Charging shield visual
        if (this.charging) {
            ctx.strokeStyle = this.color; ctx.lineWidth = 2; ctx.beginPath();
            ctx.arc(this.x + this.w/2, this.y + this.h/2, 35 + Math.random()*5, 0, Math.PI * 2); ctx.stroke();
        }
    }
}

class Enemy extends Entity {
    constructor(x) {
        super(x, 300, 32, 32, '#a02b4d');
        this.timer = 0;
        this.maxHp = 40;
        this.hp = 40;
    }
    update() {
        super.update();
        // Aggressive AI: moves towards player
        let distance = Math.abs(player.x - this.x);
        if(distance < 600 && distance > 20) {
            if (this.x > player.x) { this.vx -= 0.2; this.facing = -1; } 
            else { this.vx += 0.2; this.facing = 1; }
        }
        
        // Melee Damage
        if (checkRectCollide(this, player)) {
            player.hp -= 2; // Damage per tick
            player.vx = (player.x > this.x) ? 6 : -6; // Knockback player
            player.vy = -4;
            shakeScreen(5);
        }
    }
    draw() {
        super.draw();
        // Angry eyes
        ctx.fillStyle = '#ffaa00';
        let ex = this.facing === 1 ? this.x + 20 : this.x + 4;
        ctx.fillRect(ex, this.y + 8, 8, 4);
    }
}

class Projectile {
    constructor(x, y, vx, vy, color) {
        this.x = x; this.y = y; this.vx = vx; this.vy = vy;
        this.color = color; this.w = 12; this.h = 12; this.life = 60;
    }
    update() {
        this.x += this.vx; this.y += this.vy; this.life--;
        spawnParticles(this.x + this.w/2, this.y + this.h/2, this.color, 2, 0.2);
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath(); ctx.arc(this.x, this.y, 6, 0, Math.PI * 2); ctx.fill();
    }
}

class Particle {
    constructor(x, y, color, speed) {
        this.x = x; this.y = y;
        this.vx = (Math.random() - 0.5) * speed * 8;
        this.vy = (Math.random() - 1) * speed * 8; // Tends to fly up
        this.color = color;
        this.life = 20 + Math.random() * 20;
        this.size = Math.random() * 6 + 2;
    }
    update() {
        this.vy += 0.2; // little gravity
        this.x += this.vx; this.y += this.vy; this.life--;
        this.size *= 0.9; // shrink
    }
    draw() {
        ctx.fillStyle = this.color; ctx.globalAlpha = Math.max(0, this.life / 40);
        ctx.fillRect(this.x, this.y, this.size, this.size); ctx.globalAlpha = 1;
    }
}

// --- Utils ---
function checkRectCollide(r1, r2) {
    return (r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y);
}
function spawnParticles(x, y, color, count, speed=1) {
    for(let i=0; i<count; i++) particles.push(new Particle(x, y, color, speed));
}
let shake = 0; function shakeScreen(amount) { shake = amount; }

// --- Game Logic ---
function initGame(clsKey) {
    player = new Player(clsKey);
    enemies = [new Enemy(800), new Enemy(1200), new Enemy(1600)];
    particles = []; projectiles = []; currentShards = 0;
    
    // Fetch start shards from server relative endpoint
    fetch('data').then(res=>res.json()).then(data=>{ 
        currentShards = data.shards;
        document.getElementById('shards-display').innerText = `💎 ${currentShards}`;
    }).catch(e => console.log('Playing without server sync'));

    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    
    gameState = 'PLAY';
    requestAnimationFrame(loop);
}

function update() {
    player.update();
    
    // Smooth Camera logic
    let targetCamX = player.x - canvas.width / 2 + 100;
    // Don't let camera go before start of map
    if (targetCamX < 0) targetCamX = 0;
    camera.x += (targetCamX - camera.x) * 0.1;
    
    // Endless Enemy Generation
    if(enemies.length < 5) {
        enemies.push(new Enemy(player.x + 800 + Math.random()*500));
    }
    
    // Process Enemies
    for (let i = enemies.length - 1; i >= 0; i--) {
        let e = enemies[i];
        e.update();
        if(e.hp <= 0) {
            spawnParticles(e.x + e.w/2, e.y + e.h/2, 'gold', 20, 1);
            collectShard(5); // Gives 5 shards per kill
            enemies.splice(i, 1); 
            shakeScreen(4);
        }
    }
    
    // Process Projectiles (Hits)
    for (let i = projectiles.length - 1; i >= 0; i--) {
        let p = projectiles[i];
        p.update();
        for (let e of enemies) {
            if (checkRectCollide(p, e)) {
                e.hp -= 25; // Hit Damage
                p.life = 0; // kill bullet
                e.vx += player.facing * 8; // pushback
                spawnParticles(e.x, e.y, player.color, 10);
                shakeScreen(2);
                break;
            }
        }
        if(p.life <= 0) projectiles.splice(i, 1);
    }
    
    particles = particles.filter(p => p.life > 0);
    particles.forEach(p => p.update());
    
    // Check death
    if (player.hp <= 0 && gameState !== 'GAMEOVER') {
        gameState = 'GAMEOVER';
        document.getElementById('final-shards').innerText = currentShards;
        document.getElementById('ui-layer').classList.add('hidden');
        document.getElementById('gameover-screen').classList.remove('hidden');
    }
}

function draw() {
    // Parallax background clear
    let bgGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bgGrad.addColorStop(0, '#0a0a2a'); bgGrad.addColorStop(1, '#1b1b44');
    ctx.fillStyle = bgGrad; ctx.fillRect(0,0, canvas.width, canvas.height);
    
    // Simple stars in background moving slowly
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    for(let i=0; i<150; i++) {
        let starX = ((i * 77) - camera.x * 0.2) % canvas.width;
        if(starX < 0) starX += canvas.width;
        ctx.fillRect(starX, (i * 91) % 400, 2, 2);
    }

    ctx.save();
    // Screen Shake Implementation
    if (shake > 0) {
        ctx.translate((Math.random() - 0.5) * shake, (Math.random() - 0.5) * shake);
        shake *= 0.8; if(shake < 0.5) shake = 0;
    }
    
    // Transform View Camera
    ctx.translate(-camera.x, 0);
    
    // Draw Floor 
    ctx.fillStyle = '#1c1f2e'; 
    ctx.fillRect(camera.x - 200, 400, canvas.width + 400, canvas.height); 
    ctx.fillStyle = '#3ee989'; 
    ctx.fillRect(camera.x - 200, 400, canvas.width + 400, 4); 

    // Draw Starting boundary (Wall at x=0)
    ctx.fillStyle = '#445';
    ctx.fillRect(-100, 0, 100, canvas.height);

    // Draw entities (NO internal translations inside draw!)
    enemies.forEach(e => e.draw());
    player.draw();
    projectiles.forEach(p => p.draw());
    particles.forEach(p => p.draw());
    
    ctx.restore();
}

function loop() {
    if (gameState === 'PLAY') {
         update();
         draw();
         requestAnimationFrame(loop);
    }
}

// --- Menu Controls ---
function openCharSelect() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.remove('hidden');
    
    const grid = document.getElementById('char-grid');
    grid.innerHTML = '';
    
    // Inject Character options
    for (let k in CLASSES) {
        let cls = CLASSES[k];
        let el = document.createElement('div');
        el.className = 'char-card';
        el.innerHTML = `
            <div class="char-icon" style="background:${cls.color}; box-shadow: 0 0 10px ${cls.color}"></div>
            <h3 style="font-size:12px">${cls.name}</h3>
            <p style="font-size:8px; color:#aaa; margin-top:5px;">Magic: ${cls.skill}</p>
        `;
        el.onclick = () => initGame(k);
        grid.appendChild(el);
    }
}

function backToMenu() {
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('menu-screen').classList.remove('hidden');
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
