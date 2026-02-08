from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, render_template_string
import random

# --- 1. דף "בפיתוח" משודרג (מראה של טרמינל) ---
def under_construction_html(text):
    return f'''
    <style>
        body {{ background: #000; color: #0f0; font-family: 'Courier New', monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; overflow: hidden; }}
        .terminal {{ border: 2px solid #0f0; padding: 40px; box-shadow: 0 0 20px #0f0; }}
        .cursor {{ display: inline-block; width: 10px; height: 20px; background: #0f0; animation: blink 1s infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
    </style>
    <div class="terminal">
        <h1>> ACCESSING: {text}...</h1>
        <p>> STATUS: UNDER_DEVELOPMENT <span class="cursor"></span></p>
        <p>> נתיב המערכת נמצא בבנייה. אנא חזור מאוחר יותר.</p>
    </div>
    '''

def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index(): return under_construction_html(text)
    return dummy

# --- 2. ניהול אפליקציות חכם ---
apps_config = {
    "game1": "הישרדות 🏝️", "game2": "RPG Legend ⚔️", "game3": "Genesis 🚀",
    "game4": "קוד אדום 💻", "game5": "IRON LEGION 🔫", "game6": "מבוך הצללים 🗝️",
    "game7": "PROXIMA 🔥", "game8": "הטפיל 🦠", "game9": "CLOVER 🍀",
    "game10": "CLOVER 2 🍀", "game11": "CLOVER 3 🍀", "php": "Web Scanner 🚀"
}

mounted_apps = {}
for key, name in apps_config.items():
    try:
        # ניסיון ייבוא דינמי
        module = __import__(key)
        mounted_apps[f'/{key}'] = module.app
    except ImportError:
        mounted_apps[f'/{key}'] = create_dummy_app(name)

# --- 3. הלאוצ'ר הראשי ---
main_app = Flask(__name__)

MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Arcade Hub | Future Gaming</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Heebo:wght@300;700&display=swap" rel="stylesheet">
    <style>
        :root { --p: #6c7ce7; --a: #00cec9; --bg: #050507; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: var(--bg);
            color: #fff;
            font-family: 'Heebo', sans-serif;
            overflow-x: hidden;
            background: radial-gradient(circle at center, #111 0%, #000 100%);
        }

        /* אפקט קווי טלוויזיה ישנים */
        body::before {
            content: " "; display: block; position: fixed; top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                        linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2; background-size: 100% 4px, 3px 100%; pointer-events: none;
        }

        header { padding: 60px 20px; text-align: center; position: relative; z-index: 3; }
        h1 { 
            font-family: 'Orbitron', sans-serif; font-size: 4rem; letter-spacing: 5px;
            background: linear-gradient(to bottom, #fff 30%, var(--p));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 15px var(--p));
        }

        .grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px; max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 3;
        }

        .card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px; padding: 30px; text-decoration: none; color: white;
            transition: 0.3s; position: relative; overflow: hidden;
            display: flex; flex-direction: column; align-items: center;
        }

        .card::before {
            content: ""; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
            transition: 0.5s;
        }

        .card:hover::before { left: 100%; }

        .card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.07);
            border-color: var(--a);
            box-shadow: 0 0 30px rgba(0, 206, 201, 0.3);
        }

        .emoji { font-size: 50px; margin-bottom: 15px; transition: 0.3s; }
        .card:hover .emoji { transform: scale(1.2) rotate(5deg); }

        .tag { font-size: 0.7rem; text-transform: uppercase; color: var(--a); letter-spacing: 1px; margin-top: 10px; }

        footer { padding: 40px; text-align: center; color: #444; font-size: 0.8rem; }
    </style>
</head>
<body>
    <header>
        <h1>ARCADE HUB</h1>
        <p style="color: var(--a); opacity: 0.7;">VIRTUAL_STATION_v2.0</p>
    </header>

    <div class="grid">
        <a href="/game1/" class="card"><span class="emoji">🏝️</span><h2>הישרדות</h2><div class="tag">Resources Management</div></a>
        <a href="/game2/" class="card"><span class="emoji">⚔️</span><h2>RPG Legend</h2><div class="tag">Text-Based Action</div></a>
        <a href="/game3/" class="card"><span class="emoji">🚀</span><h2>Genesis</h2><div class="tag">Space Exploration</div></a>
        <a href="/game4/" class="card"><span class="emoji">💻</span><h2>קוד אדום</h2><div class="tag">Hacking Sim</div></a>
        <a href="/game5/" class="card"><span class="emoji">🔫</span><h2>IRON LEGION</h2><div class="tag">Military Strategy</div></a>
        <a href="/game6/" class="card"><span class="emoji">🗝️</span><h2>מבוך הצללים</h2><div class="tag">Dark Adventure</div></a>
        <a href="/game7/" class="card"><span class="emoji">🔥</span><h2>PROXIMA</h2><div class="tag">Deep Space</div></a>
        <a href="/game8/" class="card"><span class="emoji">🦠</span><h2>הטפיל</h2><div class="tag">Body Snatcher</div></a>
        <a href="/php/" class="card"><span class="emoji">🚀</span><h2>Web Scanner</h2><div class="tag">Source Tools</div></a>
    </div>

    <footer>
        &copy; 2026 Developed by Aviel Aluf | System Status: Optimal
    </footer>
</body>
</html>
"""

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

# חיבור כל האפליקציות ל-Launcher
app = DispatcherMiddleware(main_app, mounted_apps)

if __name__ == "__main__":
    print("🚀 Arcade Hub is LIVE at http://localhost:5000")
    run_simple('0.0.0.0', 5000, app, use_reloader=True)
