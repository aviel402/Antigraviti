from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, render_template_string, send_from_directory
import os

# תיקון פונקציה א' - שימוש ב-f-string כדי להחזיר מחרוזת ולא Tuple
def a(text):
    # שים לב שאני מפצל את זה ל-3 חלקים ומחבר עם +
    part1 = '''
  <style>
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      color: #fff;
      direction: rtl;
    }
    .hero {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 40px 20px;
    }
    .hero h1 {
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1.3;
      margin: 0;
      font-weight: 700;
    }
    .hero .subtitle {
      margin-top: 16px;
      font-size: 1.2rem;
      opacity: 0.85;
    }
  </style>
  <div class="hero">
    <div>
      <h1>'''
      
    part2 = text
    
    part3 = '''</h1>
      <div class="subtitle">🚧 האתר עדיין בפיתוח 🚧</div>
    </div>
  </div>
  '''
    return part1 + part2 + part3 # חיבור עם פלוס, לא פסיק!
# פונקציית עזר ליצירת אפליקציות דמה
def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index():
        return a(text)
    return dummy

# ניסיונות ייבוא (App1-App11)
try: from app1 import app as game1
except ImportError: game1 = create_dummy_app("משחק 1")

try: from app2 import app as game2
except ImportError: game2 = create_dummy_app("משחק 2")

try: from app3 import app as game3
except ImportError: game3 = create_dummy_app("משחק 3")
    
try: from app4 import app as game4
except ImportError: game4 = create_dummy_app("משחק 4")

try: from app5 import app as game5
except ImportError: game5 = create_dummy_app("משחק 5")

try: from app6 import app as game6
except ImportError: game6 = create_dummy_app("משחק 6")
    
try: from app7 import app as game7
except ImportError: game7 = create_dummy_app("משחק 7")

try: from app8 import app as game8
except ImportError: game8 = create_dummy_app("משחק 8")

try: from app9 import app as game9
except ImportError: game9 = create_dummy_app("CLOVER")
    
try: from app10 import app as game10
except ImportError: game10 = create_dummy_app("CLOVER")
    
try: from app11 import app as game11
except ImportError: game11 = create_dummy_app("CLOVER")

try: from php import app as php_app
except ImportError: php_app = create_dummy_app("php app")

# --- האפליקציה הראשית ---
main_app = Flask(__name__)

# פונקציה שמגישה את קובץ האייקון מתיקיית static
@main_app.route('/logo.png')
def favicon():
    return send_from_directory(os.path.join(main_app.root_path, 'static'), 'logo.png', mimetype='image/png')

MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="google-site-verification" content="zOUd6aTS4KigCVQoW-kvBhyHpDRIOOJhoFrDmB6XNCk" />
    <title>Arcade Hub</title>
    
    <!-- קישור לאייקון - הנתיב המלא -->
    <link rel="icon" type="image/png" href="/logo.png">

    <!-- קישור תקין לפונט ללא רווחים -->
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;700;900&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #6c7ce7;
            --accent: #00cec9;
            --bg-dark: #0a0a0c;
            --card-bg: #1e1e24;
            --glow-primary: rgba(108, 124, 231, 0.4);
            --glow-accent: rgba(0, 206, 201, 0.4);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 10% 20%, rgb(30, 30, 30) 0%, rgb(10, 10, 12) 90%);
            color: #dfe6e9;
            font-family: 'Heebo', sans-serif;
            text-align: center;
            padding: 40px 20px;
            min-height: 100vh;
            overflow-x: hidden;
        }

        h1 {
            font-size: clamp(2.5rem, 8vw, 4rem);
            background: linear-gradient(90deg, #a29bfe, #74b9ff, #00cec9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            max-width: 1200px;
            margin: 50px auto;
        }

        .card {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 25px;
            text-decoration: none;
            color: white;
            transition: 0.3s;
            border: 1px solid rgba(255,255,255,0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .card:hover {
            transform: translateY(-8px);
            border-color: var(--accent);
        }

        .emoji-icon { font-size: 55px; margin-bottom: 10px; }

        .loading {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: var(--bg-dark); display: flex; justify-content: center;
            align-items: center; z-index: 9999;
        }
        .loading.hidden { display: none; }
        .spinner { width: 50px; height: 50px; border: 5px solid #222; border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loading" id="loading"><div class="spinner"></div></div>
    
    <h1>Arcade Station</h1>
    <p>בחר משחק להתחלה</p>

    <div class="grid">
        <a href="/game1/" class="card">
            <span class="emoji-icon">🏝️</span>
            <h2>הישרדות</h2>
        </a>
        <a href="/game2/" class="card">
            <span class="emoji-icon">⚔️</span>
            <h2>RPG Legend</h2>
        </a>
        <a href="/game4/" class="card">
            <span class="emoji-icon">💻</span>
            <h2>קוד אדום</h2>
        </a>
        <a href="/game9/" class="card">
            <span class="emoji-icon">🍀</span>
            <h2>CLOVER</h2>
        </a>
    </div>

    <script>
        window.addEventListener('load', () => {
            document.getElementById('loading').classList.add('hidden');
        });
    </script>
</body>
</html>
"""

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

# חיבור כל האפליקציות יחד
app = DispatcherMiddleware(main_app, {
    '/game1': game1,
    '/game2': game2,
    '/game3': game3,
    '/game4': game4,
    '/game5': game5,
    '/game6': game6,
    '/game7': game7,
    '/game8': game8,
    '/game9': game9,
    '/game10': game10,
    '/game11': game11,
    '/php': php_app
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
