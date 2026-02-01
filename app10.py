import random
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)
app.secret_key = "neon_rider_secret"

# Game configuration and levels
game_config = {
    "num_levels": 10,
    "base_speed": 5,
    "speed_increase": 0.5,
    "base_obstacle_frequency": 0.05,
}

NEON_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEON SYNTHWAVE RIDER</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --neon-pink: #ff00ff;
            --neon-blue: #00ffff;
            --bg-dark: #050505;
        }

        body {
            margin: 0;
            padding: 0;
            background: var(--bg-dark);
            color: white;
            font-family: 'Orbitron', sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        canvas {
            border: 4px solid var(--neon-blue);
            box-shadow: 0 0 20px var(--neon-blue), inset 0 0 20px var(--neon-blue);
            background: #000;
        }

        .ui-layer {
            position: absolute;
            top: 20px;
            width: 800px;
            display: flex;
            justify-content: space-between;
            font-size: 20px;
            text-shadow: 0 0 10px var(--neon-pink);
            pointer-events: none;
        }

        .level-up {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 60px;
            color: var(--neon-pink);
            text-shadow: 0 0 20px var(--neon-pink);
            display: none;
            animation: fadeInOut 2s forwards;
            pointer-events: none;
        }

        @keyframes fadeInOut {
            0% { opacity: 0; transform: translate(-50%, -40%); }
            20% { opacity: 1; transform: translate(-50%, -50%); }
            80% { opacity: 1; transform: translate(-50%, -50%); }
            100% { opacity: 0; transform: translate(-50%, -60%); }
        }

        .controls-hint {
            position: absolute;
            bottom: 20px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 14px;
        }
        
        .start-screen {
            position: absolute;
            background: rgba(0,0,0,0.8);
            width: 800px;
            height: 600px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
        }

        .btn {
            background: transparent;
            border: 2px solid var(--neon-pink);
            color: var(--neon-pink);
            padding: 15px 40px;
            font-family: inherit;
            font-size: 24px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
        }

        .btn:hover {
            background: var(--neon-pink);
            color: black;
            box-shadow: 0 0 30px var(--neon-pink);
        }
    </style>
</head>
<body>
    <div class="ui-layer">
        <div>SCORE: <span id="score">0</span></div>
        <div>LEVEL: <span id="level">1</span></div>
        <div>BITS: <span id="bits">0</span></div>
    </div>

    <div id="start-screen" class="start-screen">
        <h1 style="color: var(--neon-blue); text-shadow: 0 0 20px var(--neon-blue); font-size: 48px;">NEON RIDER</h1>
        <p style="text-align: center; max-width: 400px; line-height: 1.6;">Dodge the RED triangles, collect the BLUE circles.</p>
        <button class="btn" onclick="startGame()">START</button>
    </div>

    <div id="level-alert" class="level-up">LEVEL UP!</div>

    <canvas id="gameCanvas" width="800" height="600"></canvas>

    <div class="controls-hint">Use LEFT / RIGHT arrows or A / D to move</div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const scoreEl = document.getElementById('score');
        const levelEl = document.getElementById('level');
        const bitsEl = document.getElementById('bits');
        const alertEl = document.getElementById('level-alert');
        const startScreen = document.getElementById('start-screen');

        let gameRunning = false;
        let score = 0;
        let level = 1;
        let bits = 0;
        let speed = 5;
        let player = { x: 400, y: 550, w: 40, h: 20 };
        let obstacles = [];
        let lightBits = [];
        let particles = [];
        let keys = {};

        window.addEventListener('keydown', e => keys[e.key.toLowerCase()] = true);
        window.addEventListener('keyup', e => keys[e.key.toLowerCase()] = false);

        function startGame() {
            startScreen.style.display = 'none';
            gameRunning = true;
            score = 0;
            level = 1;
            bits = 0;
            speed = 5;
            obstacles = [];
            lightBits = [];
            player.x = 400;
            requestAnimationFrame(gameLoop);
        }

        function createExplosion(x, y, color) {
            for(let i=0; i<15; i++) {
                particles.push({
                    x, y,
                    vx: (Math.random() - 0.5) * 10,
                    vy: (Math.random() - 0.5) * 10,
                    life: 1.0,
                    color
                });
            }
        }

        function gameLoop() {
            if(!gameRunning) return;

            // Update
            if(keys['arrowleft'] || keys['a']) player.x -= 8;
            if(keys['arrowright'] || keys['d']) player.x += 8;
            player.x = Math.max(20, Math.min(780 - player.w, player.x));

            // Spawn
            if(Math.random() < 0.05 + (level * 0.01)) {
                obstacles.push({ x: Math.random() * 760 + 20, y: -50, w: 30, h: 30 });
            }
            if(Math.random() < 0.03) {
                lightBits.push({ x: Math.random() * 760 + 20, y: -50, r: 10 });
            }

            // Move & Check collisions
            obstacles.forEach((obs, i) => {
                obs.y += speed;
                if(obs.y > 650) {
                    obstacles.splice(i, 1);
                    score += 10;
                }
                if(collide(player, obs)) {
                    gameRunning = false;
                    createExplosion(player.x + 20, player.y, '#ff0000');
                    setTimeout(() => {
                        startScreen.style.display = 'flex';
                        startScreen.querySelector('h1').innerText = 'GAME OVER';
                        startScreen.querySelector('p').innerText = 'Final Score: ' + score;
                    }, 1000);
                }
            });

            lightBits.forEach((bit, i) => {
                bit.y += speed;
                if(bit.y > 650) lightBits.splice(i, 1);
                if(Math.hypot(player.x + 20 - bit.x, player.y + 10 - bit.y) < 25) {
                    lightBits.splice(i, 1);
                    bits++;
                    score += 50;
                    createExplosion(bit.x, bit.y, '#00ffff');
                }
            });

            particles.forEach((p, i) => {
                p.x += p.vx;
                p.y += p.vy;
                p.life -= 0.02;
                if(p.life <= 0) particles.splice(i, 1);
            });

            // Level Up
            if(score > level * level * 500) {
                level++;
                speed += 0.8;
                alertLevelUp();
            }

            // UI
            scoreEl.innerText = score;
            levelEl.innerText = level;
            bitsEl.innerText = bits;

            draw();
            requestAnimationFrame(gameLoop);
        }

        function alertLevelUp() {
            alertEl.style.display = 'block';
            setTimeout(() => { alertEl.style.display = 'none'; }, 2000);
        }

        function collide(r1, r2) {
            return r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y;
        }

        function draw() {
            ctx.fillStyle = gameRunning ? '#000' : '#100';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Grid lines (Parallax)
            ctx.strokeStyle = '#222';
            ctx.lineWidth = 1;
            for(let i=0; i<canvas.width; i+=40) {
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, canvas.height);
                ctx.stroke();
            }
            for(let i=(score % 40); i<canvas.height; i+=40) {
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }

            // Player
            ctx.fillStyle = '#fff';
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#fff';
            ctx.fillRect(player.x, player.y, player.w, player.h);
            
            // Obstacles
            ctx.fillStyle = '#f00';
            ctx.shadowColor = '#f00';
            obstacles.forEach(obs => {
                ctx.beginPath();
                ctx.moveTo(obs.x, obs.y + obs.h);
                ctx.lineTo(obs.x + obs.w / 2, obs.y);
                ctx.lineTo(obs.x + obs.w, obs.y + obs.h);
                ctx.fill();
            });

            // Light Bits
            ctx.fillStyle = '#0ff';
            ctx.shadowColor = '#0ff';
            lightBits.forEach(bit => {
                ctx.beginPath();
                ctx.arc(bit.x, bit.y, bit.r, 0, Math.PI * 2);
                ctx.fill();
            });

            // Particles
            particles.forEach(p => {
                ctx.globalAlpha = p.life;
                ctx.fillStyle = p.color;
                ctx.fillRect(p.x, p.y, 4, 4);
            });
            ctx.globalAlpha = 1;
            ctx.shadowBlur = 0;
        }

        draw();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(NEON_HTML)

if __name__ == '__main__':
    app.run(port=5010, debug=True)
