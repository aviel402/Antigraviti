from flask import Flask, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

def a(text):
    sss = f'''
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      color: #fff;
    }}
  
    .hero {{
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 40px 20px;
    }}

    .hero h1 {{
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1.3;
      margin: 0;
      font-weight: 700;
    }}

    .hero .subtitle {{
      margin-top: 16px;
      font-size: 1.2rem;
      opacity: 0.85;
    }}
  </style>

  <div class="hero">
    <div>
      <h1>{text}</h1>
      <div class="subtitle">🚧 האתר עדיין בפיתוח 🚧</div>
    </div>
  </div>

  '''
    return sss

# נסה לייבא. אם חסר קובץ, נשתמש באפליקציית דמה (Dummy App) כדי שהקוד ירוץ
def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index():
        return a(text)
    return dummy

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
except ImportError: game6 = create_dummy_app("משחק 6 - ההרפתקה (לא נמצא הקובץ)")
    
try: from app7 import app as game7
except ImportError: game7 = create_dummy_app("משחק 7")

try: from app8 import app as game8
except ImportError: game8 = create_dummy_app("משחק 8")

try: from app9 import app as game9
except ImportError: game9 = create_dummy_app("CLOVER")


# --- הלאוצ'ר הראשי ---
main_app = Flask(__name__)

MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<!-- (שאר התוכן ללא שינוי כדי שלא להאריך כאן) -->
</html>
"""

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

# בניית הניתוב הראשי
app = DispatcherMiddleware(main_app, {
    '/game1': game1,
    '/game2': game2,
    '/game3': game3,
    '/game4': game4,
    '/game5': game5,
    '/game6': game6,
    '/game7': game7,
    '/game8': game8,
    '/game9': game9
})

if __name__ == "__main__":
    print("🎮 Arcade Station Running at http://localhost:5000")
    print("✨ Press CTRL+C to stop the server")
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
