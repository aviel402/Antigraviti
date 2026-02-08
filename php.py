import requests
import re
import random
from flask import Flask, render_template_string, request
from urllib.parse import urljoin

app = Flask(__name__)

# --- הגדרות עיצוב (Themes) ---
THEMES = [

    {"name": "Cyberpunk", "bg": "#0f0524", "primary": "#ff00ff", "secondary": "#00ffff", "text": "#ffffff", "code_theme": "prism-tomorrow"},

    {"name": "Deep Ocean", "bg": "#011627", "primary": "#2081C3", "secondary": "#63D2FF", "text": "#d6e8ee", "code_theme": "prism-okaidia"},

    {"name": "Forest Dark", "bg": "#1a1f16", "primary": "#5e8c31", "secondary": "#a2d240", "text": "#e8f0e2", "code_theme": "prism-twilight"},

    {"name": "Midnight Gold", "bg": "#121212", "primary": "#D4AF37", "secondary": "#FFD700", "text": "#f4f4f4", "code_theme": "prism-funky"},

    {"name": "Mars Rover", "bg": "#2b0f0e", "primary": "#e27d60", "secondary": "#e8a87c", "text": "#ffffff", "code_theme": "prism-coy"},

    {"name": "Soft Purple", "bg": "#2d1b33", "primary": "#c39bd3", "secondary": "#f06292", "text": "#f5f5f5", "code_theme": "prism-dark"},

    {"name": "Matrix", "bg": "#000000", "primary": "#00ff41", "secondary": "#008f11", "text": "#00ff41", "code_theme": "prism-tomorrow"},

    {"name": "Nordic Ice", "bg": "#2e3440", "primary": "#88c0d0", "secondary": "#81a1c1", "text": "#eceff4", "code_theme": "prism-nord"},

]

ADDITIONAL_THEMES = [

    # 1. Sunset / Vaporwave - גווני סגול, ורוד וכתום

    {"name": "Vaporwave Sunset", "bg": "#241744", "primary": "#ff71ce", "secondary": "#01cdfe", "text": "#fff2f1", "code_theme": "prism-tomorrow"},

    

    # 2. Dracula - ערכת הנושא האהובה על מתכנתים (כהה מאוד עם ניאון עדין)

    {"name": "Dracula Night", "bg": "#282a36", "primary": "#bd93f9", "secondary": "#ff79c6", "text": "#f8f8f2", "code_theme": "prism-tomorrow"},

    

    # 3. Emerald City - גווני ירוק בקבוק עמוק וזהב

    {"name": "Emerald City", "bg": "#021c1e", "primary": "#00676b", "secondary": "#2fb98a", "text": "#d8f3dc", "code_theme": "prism-okaidia"},

    

    # 4. Monokai Pro - קלאסיקה של סביבות עבודה (אפור כהה עם צבעוניות פסטלית)

    {"name": "Monokai Classic", "bg": "#2d2a2e", "primary": "#ffd866", "secondary": "#ff6188", "text": "#fcfcfa", "code_theme": "prism-okaidia"},

    

    # 5. Arctic Frost - לבן-כחול נקי (Light Theme)

    {"name": "Arctic Frost", "bg": "#f0f4f8", "primary": "#1b6ca8", "secondary": "#4ba3c3", "text": "#243b53", "code_theme": "prism-coy"},

    

    # 6. Coffee House - גווני חום, בז' ושמנת חמימים

    {"name": "Coffee House", "bg": "#3c2f2f", "primary": "#be9b7b", "secondary": "#854442", "text": "#fff4e6", "code_theme": "prism-twilight"},

    

    # 7. Red Code - למראה "האקרי" דרמטי באדום ושחור

    {"name": "Red Alert", "bg": "#0a0000", "primary": "#ff4d4d", "secondary": "#b30000", "text": "#ffe6e6", "code_theme": "prism-funky"},

    

    # 8. Royal Velvet - כחול צי וחום מוזהב יוקרתי

    {"name": "Royal Velvet", "bg": "#1a1c2c", "primary": "#f4d03f", "secondary": "#d4af37", "text": "#e0e0e0", "code_theme": "prism-tomorrow"}

]

THEMES.extend(ADDITIONAL_THEMES)


def fix_url(url):
    if not url: return ""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def extract_data(html, base_url):
    # חילוץ כל התמונות ללא הגבלה
    img_urls = re.findall(r'<img [^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    full_img_urls = list(set([urljoin(base_url, u) for u in img_urls if u]))
    
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "ללא כותרת"

    desc_match = re.search(r'<meta name=["\']description["\'] content=["\'](.*?)["\']', html, re.IGNORECASE)
    # תיאור מלא ללא חיתוך
    description = desc_match.group(1).strip() if desc_match else "לא נמצא תיאור במטא-דאטה."

    return {
        "images": full_img_urls,
        "total_images": len(full_img_urls),
        "title": title,
        "description": description
    }

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web-Scanner Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/{{ theme.code_theme }}.min.css" rel="stylesheet" />
    <style>
        :root { --bg: {{ theme.bg }}; --primary: {{ theme.primary }}; --secondary: {{ theme.secondary }}; --text: {{ theme.text }}; }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; transition: 0.3s; }
        
        /* מצב טקסט נקי בלבד */
        body.clean-text-mode { background: #1e1e1e; color: #d4d4d4; padding: 0; }
        body.clean-text-mode .main-ui, body.clean-text-mode .nav-btns, body.clean-text-mode .theme-badge { display: none !important; }
        body.clean-text-mode pre { margin: 0; border: none; height: 100vh; overflow: auto; }

        .glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; }
        .btn-gradient { background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; color: #fff; font-weight: bold; }
        
        /* גלריה משופרת */
        .img-container { position: relative; overflow: hidden; border-radius: 8px; border: 1px solid var(--primary); }
        .img-preview { width: 100%; height: 120px; object-fit: cover; }
        .download-overlay { 
            position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.7); 
            display: flex; justify-content: center; padding: 5px; opacity: 0; transition: 0.3s;
        }
        .img-container:hover .download-overlay { opacity: 1; }
        .img-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 15px; max-height: 400px; overflow-y: auto; padding: 10px; }

        pre { border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
        .theme-badge { position: fixed; bottom: 20px; left: 20px; background: var(--primary); color: #000; padding: 5px 15px; border-radius: 20px; font-size: 12px; }
    </style>
</head>
<body class="container py-4">
    
    <div class="main-ui text-center mb-4">
        <h1 style="color: var(--primary); font-weight: 800;">Web-Scanner Pro</h1>
        <div class="d-flex justify-content-center gap-2 mt-2">
            <a href="/php" class="btn btn-sm btn-outline-light">החלף עיצוב 🎲</a>
            {% if html_content %}
            <button class="btn btn-sm btn-dark" onclick="toggleCleanText()">מצב טקסט נקי 📝</button>
            {% endif %}
        </div>
    </div>

    <div class="main-ui row justify-content-center mb-4">
        <div class="col-lg-8">
            <div class="glass-card p-4">
                <form method="GET" class="row g-2">
                    <div class="col-md-9">
                        <input type="text" name="url" class="form-control" style="background:rgba(0,0,0,0.3); color:white; border:1px solid var(--primary);" placeholder="הכנס כתובת אתר..." value="{{ url }}" required>
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-gradient w-100">סרוק</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    {% if html_content %}
    <div class="main-ui row justify-content-center mb-4">
        <div class="col-lg-11">
            <div class="glass-card p-4 mb-4">
                <h5 style="color: var(--secondary)">📄 מידע מלא מהאתר</h5>
                <hr>
                <p><strong>כותרת:</strong> {{ metadata.title }}</p>
                <p><strong>תיאור מלא:</strong> {{ metadata.description }}</p>
                
                <h5 class="mt-4" style="color: var(--secondary)">🖼️ כל התמונות שנמצאו ({{ metadata.total_images }})</h5>
                <div class="img-grid border rounded">
                    {% for img in metadata.images %}
                    <div class="img-container">
                        <img src="{{ img }}" class="img-preview" onerror="this.parentElement.style.display='none'">
                        <div class="download-overlay">
                            <a href="{{ img }}" download target="_blank" class="btn btn-xs btn-info" style="font-size: 10px;">הורדה</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="nav-btns d-flex justify-content-between mb-2">
                <h5>קוד מקור:</h5>
                <button class="btn btn-sm btn-outline-info" onclick="navigator.clipboard.writeText(document.getElementById('main-code').textContent)">העתק קוד 📋</button>
            </div>
            <pre><code id="main-code" class="language-html">{{ html_content | e }}</code></pre>
        </div>
    </div>
    {% endif %}

    <div class="theme-badge">Theme: {{ theme.name }}</div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script>
        function toggleCleanText() {
            document.body.classList.toggle('clean-text-mode');
            if(document.body.classList.contains('clean-text-mode')) {
                alert("לחיצה על ESC או טעינה מחדש תגזיר את הכפתורים");
            }
        }
        // יציאה ממצב טקסט בלחיצה על Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === "Escape") document.body.classList.remove('clean-text-mode');
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def proxy():
    target_url = request.args.get('url', '').strip()
    selected_theme = random.choice(THEMES)
    html_content, error, metadata = None, None, {}

    if target_url:
        target_url = fix_url(target_url)
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(target_url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding 
            html_content = response.text
            metadata = extract_data(html_content, target_url)
        except Exception as e:
            error = str(e)

    return render_template_string(HTML_PAGE, html_content=html_content, error=error, url=target_url, theme=selected_theme, metadata=metadata)

if __name__ == '__main__':
    app.run(debug=True)
