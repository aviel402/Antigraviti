import random
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "maze_runner_secret"

MAZE_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAZE APPLE RUNNER</title>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #2c3e50;
            color: white;
            font-family: 'Fredoka One', cursive;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }
        #game-container {
            position: relative;
            border: 10px solid #34495e;
            border-radius: 10px;
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }
        canvas {
            background-color: #ecf0f1;
            display: block;
        }
        .ui {
            margin-bottom: 20px;
            display: flex;
            gap: 40px;
            font-size: 24px;
        }
        .alert {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            padding: 20px 40px;
            border-radius: 20px;
            text-align: center;
            display: none;
            z-index: 100;
        }
        .btn {
            background: #e74c3c;
            border: none;
            color: white;
            padding: 10px 20px;
            font-family: inherit;
            font-size: 20px;
            cursor: pointer;
            border-radius: 10px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="ui">
        <div>LEVEL: <span id="level">1</span></div>
        <div>APPLES: <span id="apples">0</span></div>
        <div>TIME: <span id="time">60</span>s</div>
    </div>

    <div id="game-container">
        <canvas id="gameCanvas" width="600" height="600"></canvas>
        <div id="msg" class="alert">
            <h1 id="msg-title">LEVEL COMPLETE!</h1>
            <p id="msg-body">Heading to the next maze...</p>
            <button class="btn" onclick="nextLevel()">CONTINUE</button>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const levelEl = document.getElementById('level');
        const applesEl = document.getElementById('apples');
        const timeEl = document.getElementById('time');
        const msgEl = document.getElementById('msg');

        let level = 1;
        let apples = 0;
        let timeLeft = 60;
        let gridSize = 20;
        let maze = [];
        let player = { x: 1, y: 1 };
        let exit = { x: 0, y: 0 };
        let appleList = [];
        let ghosts = [];
        let cellSize = 0;
        let gameRunning = true;

        function initLevel() {
            gridSize = 15 + (level * 2);
            cellSize = canvas.width / gridSize;
            generateMaze(gridSize, gridSize);
            player = { x: 1, y: 1 };
            exit = { x: Math.floor(gridSize/2), y: Math.floor(gridSize/2) };
            maze[exit.y][exit.x] = 2; // Exit type
            
            // Add apples
            appleList = [];
            for(let i=0; i<level + 5; i++) {
                let ax, ay;
                do {
                    ax = Math.floor(Math.random() * gridSize);
                    ay = Math.floor(Math.random() * gridSize);
                } while(maze[ay][ax] !== 0);
                appleList.push({x: ax, y: ay});
            }

            // Add ghosts for higher levels
            ghosts = [];
            if(level > 2) {
                for(let i=0; i < Math.floor(level/2); i++) {
                    ghosts.push({x: gridSize-2, y: gridSize-2, lastMove: 0});
                }
            }

            timeLeft = 60 + (level * 5);
            gameRunning = true;
            msgEl.style.display = 'none';
            updateUI();
        }

        function generateMaze(width, height) {
            maze = Array(height).fill().map(() => Array(width).fill(1));
            function carve(x, y) {
                const dirs = [[0, -1], [0, 1], [-1, 0], [1, 0]].sort(() => Math.random() - 0.5);
                maze[y][x] = 0;
                for (let [dx, dy] of dirs) {
                    let nx = x + dx * 2, ny = y + dy * 2;
                    if (nx >= 0 && nx < width && ny >= 0 && ny < height && maze[ny][nx] === 1) {
                        maze[y + dy][x + dx] = 0;
                        carve(nx, ny);
                    }
                }
            }
            carve(1, 1);
        }

        function updateUI() {
            levelEl.innerText = level;
            applesEl.innerText = apples;
            timeEl.innerText = Math.ceil(timeLeft);
        }

        function nextLevel() {
            level++;
            initLevel();
        }

        window.addEventListener('keydown', e => {
            if(!gameRunning) return;
            let nx = player.x, ny = player.y;
            if(e.key === 'ArrowUp') ny--;
            if(e.key === 'ArrowDown') ny++;
            if(e.key === 'ArrowLeft') nx--;
            if(e.key === 'ArrowRight') nx++;

            if(nx >= 0 && nx < gridSize && ny >= 0 && ny < gridSize && maze[ny][nx] !== 1) {
                player.x = nx;
                player.y = ny;
                checkCollisions();
            }
        });

        function checkCollisions() {
            // Check Apple
            appleList.forEach((a, i) => {
                if(a.x === player.x && a.y === player.y) {
                    appleList.splice(i, 1);
                    apples++;
                    timeLeft += 5;
                    updateUI();
                }
            });

            // Check Exit
            if(player.x === exit.x && player.y === exit.y) {
                gameRunning = false;
                msgEl.style.display = 'block';
                document.getElementById('msg-title').innerText = 'LEVEL COMPLETE!';
                document.getElementById('msg-body').innerText = 'You reached the center!';
            }
        }

        function moveGhosts() {
            ghosts.forEach(g => {
                // Simple AI: Move towards player if possible
                let dx = 0, dy = 0;
                if(Math.random() < 0.3) {
                    if(g.x < player.x) dx = 1; else if(g.x > player.x) dx = -1;
                    if(g.y < player.y) dy = 1; else if(g.y > player.y) dy = -1;
                } else {
                    const d = [[0,1],[0,-1],[1,0],[-1,0]][Math.floor(Math.random()*4)];
                    dx = d[0]; dy = d[1];
                }

                if(maze[g.y + dy] && maze[g.y + dy][g.x + dx] === 0) {
                    g.x += dx; g.y += dy;
                }

                if(g.x === player.x && g.y === player.y) {
                    gameRunning = false;
                    msgEl.style.display = 'block';
                    document.getElementById('msg-title').innerText = 'CAUGHT!';
                    document.getElementById('msg-body').innerText = 'The ghost got you!';
                    document.querySelector('.btn').innerText = 'RETRY';
                    document.querySelector('.btn').onclick = () => location.reload();
                }
            });
        }

        function gameLoop() {
            if(gameRunning) {
                timeLeft -= 1/60;
                if(timeLeft <= 0) {
                    gameRunning = false;
                    msgEl.style.display = 'block';
                    document.getElementById('msg-title').innerText = 'TIME OUT!';
                    document.getElementById('msg-body').innerText = 'You ran out of time!';
                    document.querySelector('.btn').innerText = 'RETRY';
                    document.querySelector('.btn').onclick = () => location.reload();
                }
                if(Math.floor(timeLeft * 60) % 15 === 0) moveGhosts();
                updateUI();
            }

            // Draw
            ctx.clearRect(0,0, canvas.width, canvas.height);
            for(let y=0; y<gridSize; y++) {
                for(let x=0; x<gridSize; x++) {
                    if(maze[y][x] === 1) {
                        ctx.fillStyle = '#34495e';
                        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
                    } else if(maze[y][x] === 2) {
                        ctx.fillStyle = '#f1c40f';
                        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
                        ctx.font = cellSize + 'px Arial';
                        ctx.fillText('⭐', x*cellSize, (y+1)*cellSize);
                    }
                }
            }

            // Apples
            ctx.fillStyle = '#e74c3c';
            appleList.forEach(a => {
                ctx.beginPath();
                ctx.arc((a.x + 0.5) * cellSize, (a.y + 0.5) * cellSize, cellSize/3, 0, Math.PI*2);
                ctx.fill();
            });

            // Ghosts
            ctx.fillStyle = '#9b59b6';
            ghosts.forEach(g => {
                ctx.beginPath();
                ctx.arc((g.x + 0.5) * cellSize, (g.y + 0.5) * cellSize, cellSize/2.5, 0, Math.PI*2);
                ctx.fill();
            });

            // Player
            ctx.fillStyle = '#2ecc71';
            ctx.beginPath();
            ctx.arc((player.x + 0.5) * cellSize, (player.y + 0.5) * cellSize, cellSize/2.2, 0, Math.PI*2);
            ctx.fill();

            requestAnimationFrame(gameLoop);
        }

        initLevel();
        gameLoop();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MAZE_HTML)

if __name__ == '__main__':
    app.run(port=5011, debug=True)
