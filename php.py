import requests
import re
from flask import Flask, render_template_string, request
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

def extract_images(html, base_url):
    """מוציא את כל כתובות התמונות מהקוד ומתקן נתיבים יחסיים"""
    # חיפוש תגיות img ושליפת ה-src
    img_urls = re.findall(r'<img [^>]*src="([^"]+)"', html)
    full_urls = []
    for img_url in img_urls:
        # הפיכת נתיב יחסי לנתיב מלא (למשל /img.jpg ל- https://site.com/img.jpg)
        full_urls.append(urljoin(base_url, img_url))
    return list(set(full_urls)) # הסרת כפילויות

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web-Scanner Pro | Extract & Analyze</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <style>
        :root { --primary: #00f2fe; --secondary: #4facfe; --bg: #0f172a; }
        body { background: var(--bg); color: #e2e8f0; font-family: 'Segoe UI', sans-serif; min-height: 100vh; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
        .search-box { background: rgba(15, 23, 42, 0.8); border: 2px solid var(--secondary); color: white; border-radius: 12px; padding: 15px; }
        .btn-gradient { background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; color: white; font-weight: bold; }
        .nav-tabs .nav-link { color: #ccc; border: none; }
        .nav-tabs .nav-link.active { background: var(--secondary); color: white; border-radius: 10px; }
        .img-card { height: 150px; object-fit: cover; border-radius: 10px; border: 1px solid #334155; background: #1e293b; }
        pre { max-height: 500px; border-radius: 0 0 15px 15px !important; }
        .code-header { background: #1e293b; padding: 10px 20px; border-radius: 15px 15px 0 0; border-bottom: 1px solid #334155; }
    </style>
</head>
<body class="container py-5">
    
    <div class="text-center mb-5">
        <h1 style="background: linear-gradient(to right, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 3rem;">
            Web-Scanner Pro
        </h1>
        <p class="text-secondary">חלץ קוד, תמונות ונכסים מכל אתר</p>
    </div>

    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="glass-card p-4 mb-4 shadow-lg">
                <form method="GET" class="row g-3">
                    <div class="col-md-9">
                        <input type="url" name="url" class="form-control search-box" placeholder="https://example.com" value="{{ url }}" required>
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-gradient w-100 h-100">סרוק עכשיו</button>
                    </div>
                </form>
            </div>

            {% if error %}
                <div class="alert alert-danger glass-card border-0 text-white">{{ error }}</div>
            {% endif %}

            {% if html_content %}
            <ul class="nav nav-tabs mb-3 border-0" id="myTab" role="tablist">
                <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#code-tab">קוד מקור</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#img-tab">תמונות ({{ images|length }})</button></li>
            </ul>

            <div class="tab-content">
                <div class="tab-pane fade show active" id="code-tab">
                    <div class="code-header d-flex justify-content-between align-items-center">
                        <span class="text-info small">HTML SOURCE</span>
                        <button class="btn btn-sm btn-outline-info" onclick="copyCode()">העתק קוד</button>
                    </div>
                    <pre><code id="main-code" class="language-html">{{ html_content | e }}</code></pre>
                </div>

                <div class="tab-pane fade" id="img-tab">
                    <div class="row g-3 p-3 glass-card">
                        {% for img in images %}
                        <div class="col-md-3 col-6">
                            <a href="{{ img }}" target="_blank">
                                <img src="{{ img }}" class="img-fluid img-card w-100" onerror="this.src='https://via.placeholder.com/150?text=Error'">
                            </a>
                        </div>
                        {% endfor %}
                        {% if not images %}
                        <p class="text-center py-5">לא נמצאו תמונות גלויות בדף.</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script>
        function copyCode() {
            const code = document.getElementById('main-code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                alert('הקוד הועתק לקליפבורד!');
            });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def proxy():
    target_url = request.args.get('url', '').strip()
    html_content = None
    images = []
    error = None

    if target_url:
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            html_content = response.text
            images = extract_images(html_content, target_url)

        except Exception as e:
            error = f"שגיאה: {str(e)}"

    return render_template_string(HTML_PAGE, html_content=html_content, images=images, error=error, url=target_url)

if __name__ == '__main__':
    app.run(debug=True)
