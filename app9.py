from flask import Flask, render_template_string, jsonify, request
import json
import maps9
from txt9 import GAME_TEXT # ייבוא הטקסטים מהקובץ החדש

app = Flask(__name__)
app.secret_key = 'clover_continuous_world'

PLAYER_DATA = {"shards": 0, "max_stage_reached": 1}

@app.route('/')
def idx():
    full_world = maps9.generate_maps()
    # הזרקת המפות והטקסטים
    return render_template_string(GAME_HTML, 
                                 maps_json=json.dumps(full_world), 
                                 txt=json.dumps(GAME_TEXT))

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    data = request.json
    PLAYER_DATA["shards"] += data.get("shards", 0)
    return jsonify(PLAYER_DATA)

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Seamless World</title>
    <link href="https://fonts.googleapis.com/css2?family=Righteous&family=Rubik:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        body { margin:0; overflow:hidden; background:#000; font-family:'Rubik', sans-serif; color:white; }
        canvas { display:block; width:100%; height:100vh; image-rendering:pixelated; }
        .screen { position:absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:100; background:rgba(0,0,0,0.9); }
        .hidden { display:none !important; }
        .btn { padding:15px 40px; border:2px solid #fff; color:#fff; background:none; cursor:pointer; font-size:24px; font-family:'Righteous'; transition:0.3s; margin:10px; }
        .btn:hover { background:#fff; color:#000; }
        #ui { position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; padding:20px; z-index:10; }
        .bar { width:250px; height:15px; border:2px solid #fff; border-radius:10px; overflow:hidden; background:#222; margin-top:5px; }
        .fill { height:100%; transition:width 0.2s; }
        .stage-msg { position:absolute; left:50%; transform:translateX(-50%); top:20px; font-size:24px; font-family:'Righteous'; color:gold; }
        #charge-indicator { position:absolute; bottom:150px; left:50%; transform:translateX(-50%); font-size:30px; color:#00ffff; display:none; text-shadow:0 0 10px blue;}
        .char-grid { display:grid; grid-template-columns: repeat(4,1fr); gap:15px; width:80%; }
        .card { padding:15px; border:1px solid #555; border-radius:10px; cursor:pointer; text-align:center; transition:0.2s; }
        .card:hover { transform:scale(1.05); border-color: gold; }
    </style>
</head>
<body>

<div id="select-screen" class="screen">
    <h1 style="font-size:80px; font-family:'Righteous'; color:gold;">CLOVER</h1>
    <h3 id="txt-subtitle"></h3>
    <div class="char-grid" id="roster"></div>
</div>

<div id="ui" class="hidden">
    <div style="direction:ltr;">
        HP <div class="bar"><div id="hp-bar" class="fill" style="background:#ff3e3e; width:100%;"></div></div>
        ENERGY <div class="bar"><div id="en-bar" class="fill" style="background:#3e3eff; width:100%;"></div></div>
    </div>
    <div id="lock-label" style="color:red; opacity:0; font-weight:bold; margin-top:10px;">🎯 TARGET LOCKED</div>
    <div id="charge-indicator">POWERING SUPER...</div>
    <div class="stage-msg" id="stage-msg">STAGE 1</div>
</div>

<div id="pause-screen" class="screen hidden">
    <h1 id="txt-pause">PAUSED</h1>
    <button class="btn" onclick="togglePause()" id="txt-resume">Resume</button>
</div>

<div id="victory-screen" class="screen hidden">
    <h1 style="color:gold;">SUCCESS</h1>
    <h2 id="txt-victory">מצאת את הקלובר!</h2>
    <button class="btn" onclick="location.reload()">MAIN MENU</button>
</div>

<script>
const WORLD_MAPS = {{ maps_json | safe }};
const TXT = {{ txt | safe }};

const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);
function res() { canvas.width=window.innerWidth; canvas.height=window.innerHeight; ctx.imageSmoothingEnabled=false; }
window.onresize=res; res();

const activeKeys = {};
window.onkeydown = e => activeKeys[e.code]=true;
window.onkeyup = e => {
    if(e.code === 'KeyI' && pl) pl.releaseSuper();
    if(e.code === 'KeyP' || e.code === 'Escape') togglePause();
    activeKeys[e.code]=false;
};

// -- Game Stats --
let pl, enemies=[], pickups=[], bullets=[], barriers=[], clover_chest=null, fx=[];
let camX=0, shake=0, frames=0, paused=false;

function intersect(a,b){return!(b.x>a.x+a.w||b.x+b.w<a.x||b.y>a.y+a.h||b.y+b.h<a.y);}

// -- Entities --
class Player {
    constructor(c){
        this.w=35; this.h=65; this.x=100; this.y=0; this.vx=0; this.vy=0;
        this.maxHp=c.maxHp; this.hp=this.maxHp;
        this.maxEn=c.maxEn; this.en=this.maxEn;
        this.stats=c; this.facing=1; this.grounded=false; this.iFrames=0;
        this.jumps=0; this.chargeTime=0; this.target=null;
    }
    upd(){
        if(this.iFrames>0) this.iFrames--;
        
        // Super Charge I
        if(activeKeys['KeyI']){
            this.chargeTime++;
            this.vx *= 0.5; // לא יכול לזוז
            document.getElementById('charge-indicator').style.display='block';
            return;
        } else {
            document.getElementById('charge-indicator').style.display='none';
        }

        // Move
        if(activeKeys['KeyA']){ this.vx -= this.stats.speed; this.facing=-1; }
        if(activeKeys['KeyD']){ this.vx += this.stats.speed; this.facing=1; }
        
        // Jump (Space/W)
        if((activeKeys['Space']||activeKeys['KeyW']) && !this.jumpHold){
            if(this.jumps < 2){ this.vy = -this.stats.jump; this.jumps++; }
            this.jumpHold=true;
        } else if(!activeKeys['Space'] && !activeKeys['KeyW']) { this.jumpHold=false; }

        // Normal Attacks
        if(activeKeys['KeyH']) this.shoot(10, 15, 10);
        if(activeKeys['KeyJ']) this.shoot(25, 40, 15);
        if(activeKeys['KeyK']) this.shoot(50, 90, 20);
        
        // Auto Lock Toggle
        if(activeKeys['KeyE'] && !this.lockHold) {
            this.findTarget(); this.lockHold=true;
        } else if(!activeKeys['KeyE']) this.lockHold=false;

        // Physics
        this.vy+=0.6; this.x+=this.vx; this.y+=this.vy; this.vx*=0.85;
        this.collision();
    }
    
    shoot(cost, dmg, size){
        if(this.en >= cost && frames % 10 === 0){
            this.en -= cost;
            bullets.push(new Bullet(this.x+20, this.y+30, this.facing, dmg, size, this.target, this.stats.pCol));
            this.vx -= this.facing * 5;
        }
    }
    
    releaseSuper(){
        if(this.chargeTime > 30){
            let pwr = Math.min(this.chargeTime * 2.5, 800);
            let size = 20 + (this.chargeTime / 5);
            bullets.push(new Bullet(this.x+20, this.y+30, this.facing, pwr, size, this.target, "gold", true));
            shake=10;
        }
        this.chargeTime=0;
    }
    
    collision(){
        let floorY = canvas.height-80;
        if(this.y+this.h > floorY){ this.y=floorY-this.h; this.vy=0; this.grounded=true; this.jumps=0; }
        else this.grounded=false;
        
        // Wall & Barriers
        if(this.x < 20) {this.x=20; this.vx=0;}
        barriers.forEach(b => {
            if(!b.open && intersect(this, b)){
                this.x = b.x - this.w - 5; this.vx=0;
                document.getElementById('stage-msg').innerText = TXT.barrier_msg;
            }
        });
    }

    findTarget(){
        if(this.target) { this.target=null; return; }
        let nearest=null, minDist=600;
        enemies.forEach(e => {
            let d = Math.abs(e.x - this.x);
            if(d < minDist) { minDist=d; nearest=e; }
        });
        this.target = nearest;
    }
    
    draw(){
        ctx.fillStyle = this.iFrames % 2 === 0 ? this.stats.col : "transparent";
        ctx.fillRect(this.x, this.y, this.w, this.h);
        if(this.target){
            ctx.strokeStyle='red'; ctx.strokeRect(this.target.x-5, this.target.y-5, this.target.w+10, this.target.h+10);
        }
    }
}

class Enemy {
    constructor(x, sData, type){
        this.x=x; this.y=canvas.height-130; this.w=40; this.h=50; this.ty=type;
        this.hp = 30 + (sData.stage * 20); this.maxHp = this.hp;
        this.sData = sData; this.aggro = false; this.vx=0;
        this.col = type==='jumper'?'#8e44ad': (type==='tank'?'#555':'#c0392b');
    }
    upd(){
        let d = Math.abs(this.x - pl.x);
        if(d < 500) this.aggro = true; // Aggro zone

        if(this.aggro){
            let dir = pl.x > this.x ? 1 : -1;
            this.vx = dir * 2.5;
            this.x += this.vx;
            // Attack on collision
            if(intersect(this, pl) && pl.iFrames<=0){
                pl.hp -= 15; pl.iFrames=40; shake=5;
                pl.vx = dir * 15;
            }
        }
    }
    draw(){
        ctx.fillStyle = this.col;
        ctx.fillRect(this.x, this.y, this.w, this.h);
        // Hp bar
        ctx.fillStyle='red'; ctx.fillRect(this.x, this.y-10, this.w * (this.hp/this.maxHp), 5);
    }
}

class Barrier {
    constructor(x, stageIdx){
        this.x=x; this.y=0; this.w=30; this.h=canvas.height;
        this.stage = stageIdx; this.open = false;
    }
    upd(){
        // Check if all enemies in the section [X-3500, X] are dead
        let enemiesInRange = enemies.filter(e => e.sData.stage === this.stage && e.hp > 0);
        if(enemiesInRange.length === 0) {
            if(!this.open) console.log("Barrier stage " + this.stage + " open!");
            this.open = true;
        }
    }
    draw(){
        if(this.open) return;
        ctx.fillStyle = "rgba(255,0,0,0.5)";
        ctx.fillRect(this.x, this.y, this.w, this.h);
    }
}

class Bullet {
    constructor(x, y, dir, dmg, sz, tgt, col, isSuper=false){
        this.x=x; this.y=y; this.dir=dir; this.dmg=dmg; this.sz=sz;
        this.tgt=tgt; this.col=col; this.super=isSuper;
        this.life=200; this.vx = dir * 15; this.vy=0;
    }
    upd(){
        if(this.tgt && this.tgt.hp>0){
            let dx=this.tgt.x - this.x, dy=this.tgt.y - this.y;
            let a=Math.atan2(dy, dx);
            this.vx = Math.cos(a)*15; this.vy = Math.sin(a)*15;
        }
        this.x+=this.vx; this.y+=this.vy;
        enemies.forEach(e => {
            if(intersect({x:this.x, y:this.y, w:this.sz, h:this.sz}, e)){
                e.hp -= this.dmg; e.aggro=true; this.life=0;
                if(pl.stats.id==='dark') pl.hp = Math.min(pl.hp+2, pl.maxHp);
                if(e.hp<=0) spawnPickup(e);
            }
        });
        if(clover_chest && intersect({x:this.x,y:this.y,w:this.sz,h:this.sz}, clover_chest)){
            clover_chest.hp--; this.life=0;
            if(clover_chest.hp<=0) document.getElementById('victory-screen').classList.remove('hidden');
        }
        this.life--;
    }
    draw(){
        ctx.fillStyle=this.col;
        ctx.beginPath(); ctx.arc(this.x,this.y,this.sz,0,Math.PI*2); ctx.fill();
    }
}

class Pickup {
    constructor(x, y, type){this.x=x; this.y=y; this.ty=type; this.w=20; this.h=20;}
    upd(){
        if(intersect(this, pl)){
            if(this.ty==='hp') pl.hp = Math.min(pl.hp+25, pl.maxHp);
            if(this.ty==='boss'){ pl.maxHp+=20; pl.maxEn+=20; pl.hp=pl.maxHp; pl.en=pl.maxEn; }
            this.life=0;
        }
    }
    draw(){ ctx.fillStyle=this.ty==='hp'?'#00ff00':'gold'; ctx.fillRect(this.x,this.y,this.w,this.h); }
}

function spawnPickup(e){
    pickups.push(new Pickup(e.x, e.y, e.ty==='boss'?'boss':'hp'));
}

// -- Core Systems --
function startMission(char){
    document.getElementById('select-screen').classList.add('hidden');
    document.getElementById('ui').classList.remove('hidden');
    pl = new Player(char);
    
    // Generate entire continuous world
    WORLD_MAPS.forEach(s => {
        barriers.push(new Barrier(s.x_end, s.stage));
        let numEn = s.is_boss ? 1 : 5;
        for(let i=0; i<numEn; i++){
            let ety = s.is_boss ? 'boss' : s.enemies[Math.floor(Math.random()*s.enemies.length)];
            enemies.push(new Enemy(s.x_start + 400 + (i*600), s, ety));
        }
    });
    // Add the Clover Chest at the very end
    clover_chest = {x: 20 * 3500 + 500, y: canvas.height-180, w:100, h:100, hp:10, draw: function(){
        ctx.fillStyle='gold'; ctx.fillRect(this.x,this.y,this.w,this.h);
        ctx.fillStyle='#fff'; ctx.fillText("THE CLOVER", this.x+10, this.y-20);
    }};
    
    requestAnimationFrame(gameLoop);
}

function togglePause(){ paused=!paused; document.getElementById('pause-screen').classList.toggle('hidden'); }

function gameLoop(){
    if(paused) return requestAnimationFrame(gameLoop);
    frames++;
    ctx.clearRect(0,0,canvas.width,canvas.height);

    // Dynamic Level background & stage msg
    let activeStage = WORLD_MAPS.find(m => pl.x >= m.x_start && pl.x < m.x_end);
    if(activeStage){
        ctx.fillStyle=activeStage.bg; ctx.fillRect(0,0,canvas.width,canvas.height);
        document.getElementById('stage-msg').innerText = TXT.stage_prefix + activeStage.stage + " - " + activeStage.name;
    }

    // Cam logic
    camX += (pl.x - canvas.width/2 - camX) * 0.1;
    let sX=0, sY=0; if(shake>0){sX=(Math.random()-0.5)*shake; sY=(Math.random()-0.5)*shake; shake*=0.9;}
    ctx.save(); ctx.translate(-camX+sX, sY);

    // Render logic
    ctx.fillStyle="#111"; ctx.fillRect(0, canvas.height-80, 80000, 80); // Massive Floor
    
    pl.upd(); pl.draw();
    enemies.forEach((e,i) => { e.upd(); e.draw(); if(e.hp<=0) enemies.splice(i,1); });
    bullets.forEach((b,i) => { b.upd(); b.draw(); if(b.life<=0) bullets.splice(i,1); });
    pickups.forEach((p,i) => { p.upd(); p.draw(); if(p.life===0) pickups.splice(i,1); });
    barriers.forEach(b => { b.upd(); b.draw(); });
    if(clover_chest) clover_chest.draw();

    ctx.restore();
    
    // UI Update
    document.getElementById('hp-bar').style.width = (pl.hp/pl.maxHp*100)+'%';
    document.getElementById('en-bar').style.width = (pl.en/pl.maxEn*100)+'%';
    document.getElementById('lock-label').style.opacity = pl.target?1:0;
    if(pl.hp<=0) location.reload();

    requestAnimationFrame(gameLoop);
}

// Initial Select UI
(function initUI(){
    document.getElementById('txt-subtitle').innerText = TXT.subtitle;
    document.getElementById('txt-pause').innerText = TXT.pause_title;
    document.getElementById('txt-resume').innerText = TXT.resume_btn;
    const grid = document.getElementById('roster');
    const hero_ids = ['earth','fire','water','air','lightning','magma','light','dark'];
    const hero_colors = ['#2ecc71','#e74c3c','#3498db','#ecf0f1','#f1c40f','#d35400','#ffffb3','#8e44ad'];
    hero_ids.forEach((id, i) => {
        let stats = {
            id, col: hero_colors[i], maxHp: (id==='earth'?200:100), maxEn: (id==='light'?300:100),
            speed: (id==='air'?1.6:1.0), jump: (id==='air'?18:14), pCol: hero_colors[i]
        };
        let c = document.createElement('div'); c.className='card';
        c.innerHTML = `<h3 style="color:${hero_colors[i]}">${id.toUpperCase()}</h3><p style="font-size:10px">${TXT['char_'+id]}</p>`;
        c.onclick = () => startMission(stats);
        grid.appendChild(c);
    });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5009, debug=True)
