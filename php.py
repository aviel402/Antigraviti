import requests
import re
import random
from flask import Flask, render_template_string, request
from urllib.parse import urljoin

app = Flask(__name__)

# 1. הגדרת 10 עיצובים שונים (Themes)
THEMES = [
    {"name": "Cyberpunk", "bg": "#0f0524", "primary": "#ff00ff", "secondary": "#00ffff", "text": "#ffffff"},
    {"name": "Deep Ocean", "bg": "#011627", "primary": "#2081C3", "secondary": "#63D2FF", "text": "#d6e8ee"},
    {"name": "Forest Dark", "bg": "#1a1f16", "primary": "#5e8c31", "secondary": "#a2d240", "text": "#e8f0e2"},
    {"name": "Midnight Gold", "bg": "#121212", "primary": "#D4AF37", "secondary": "#FFD700", "text": "#f4f4f4"},
    {"name": "Mars Rover", "bg": "#2b0f0e", "primary": "#e27d60", "secondary": "#e8a87c", "text": "#ffffff"},
    {"name": "Soft Purple", "bg": "#2d1b33", "primary": "#c39bd3", "secondary": "#f06292", "text": "#f5f5f5"},
    {"name": "Matrix", "bg": "#000000", "primary": "#00ff41", "secondary": "#008f11", "text": "#00ff41"},
    {"name": "Nordic Ice", "bg": "#2e3440", "primary": "#88c0d0", "secondary": "#81a1c1", "text": "#eceff4"},
    {"name": "Vampire", "bg": "#1a0606", "primary": "#e63946", "secondary": "#a8dadc", "text": "#f1faee"},
    {"name": "Space Gray", "bg": "#23272a", "primary": "#7289da", "secondary": "#ffffff", "text": "#ffffff"}
]

def extract_images(html, base_url):
    img_urls = re.findall(r'<img [^>]*src="([^"]+)"', html)
    return list(set([urljoin(base_url, u) for u in img_urls]))

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web-Scanner Pro | {{ theme.name }} Mode</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <style>
        :root { 
            --bg: {{ theme.bg }}; 
            --primary: {{ theme.primary }}; 
            --secondary: {{ theme.secondary }}; 
            --text: {{ theme.text }}; 
        }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; transition: 0.5s; }
        .glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }
        .btn-gradient { background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; color: white; font-weight: bold; }
        .search-box { background: rgba(0,0,0,0.3); border: 1px solid var(--primary); color: white; border-radius: 10px; }
        
        /* מצב קוד בלבד */
        body.code-only-mode .main-ui { display: none; }
        body.code-only-mode .code-section { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; }
        body.code-only-mode pre { height: 100vh !important; max-height: 100vh !important; border-radius: 0 !important; }

        .img-card { height: 150px; object-fit: cover; border-radius: 10px; border: 1px solid var(--primary); }
        .theme-badge { position: fixed; bottom: 20px; left: 20px; background: var(--primary); color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 12px; }
    </style>
</head>
<body class="container py-5">
    
    <div class="main-ui text-center mb-5">
        <h1 style="color: var(--primary); font-weight: 800; text-shadow: 0 0 10px var(--primary);">Web-Scanner Pro</h1>
        <p>עיצוב נוכחי: <strong>{{ theme.name }}</strong></p>
        
        <div class="d-flex justify-content-center gap-2 mt-3">
            <button class="btn btn-sm btn-outline-light" onclick="location.reload()">החלף עיצוב רנדומלי 🎲</button>
            {% if html_content %}
            <button class="btn btn-sm btn-info" onclick="toggleCodeOnly()">מצב קוד בלבד 🖥️</button>
            {% endif %}
        </div>
    </div>

    <div class="main-ui row justify-content-center">
        <div class="col-lg-10">
            <div class="glass-card p-4 mb-4">
                <form method="GET" class="row g-3">
                    <div class="col-md-9">
                        <input type="url" name="url" class="form-control search-box" placeholder="https://..." value="{{ url }}" required>
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-gradient w-100">סרוק אתר</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    {% if html_content %}
    <div class="code-section row justify-content-center">
        <div class="col-lg-10">
            <div class="d-flex justify-content-between mb-2">
                <button class="btn btn-sm btn-light" onclick="copyCode()">העתק קוד</button>
                <button class="btn btn-sm btn-danger exit-code-btn d-none" onclick="toggleCodeOnly()">יציאה ממצב קוד</button>
            </div>
            <pre><code id="main-code" class="language-html">{{ html_content | e }}</code></pre>
        </div>
    </div>
    {% endif %}

    <div class="theme-badge">Theme: {{ theme.name }}</div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script>
        function toggleCodeOnly() {
            document.body.classList.toggle('code-only-mode');
            document.querySelector('.exit-code-btn').classList.toggle('d-none');
        }

        function copyCode() {
            const code = document.getElementById('main-code').textContent;
            navigator.clipboard.writeText(code).then(() => alert('הועתק!'));
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def proxy():
    target_url = request.args.get('url', '').strip()
    html_content = None
    error = None
    
    # בחירת עיצוב רנדומלי בכל כניסה
    selected_theme = random.choice(THEMES)

    if target_url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(target_url, headers=headers, timeout=10)
            html_content = response.text
        except Exception as e:
            error = str(e)

    return render_template_string(HTML_PAGE, 
                                 html_content=html_content, 
                                 error=error, 
                                 url=target_url, 
                                 theme=selected_theme)

if __name__ == '__main__':
    app.run(debug=True)
