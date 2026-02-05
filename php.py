import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- עיצוב האתר (HTML) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>מעתיק קוד מקור</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; padding: 20px; }
        pre { background: #2d2d2d; color: #ccc; padding: 15px; border-radius: 8px; direction: ltr; text-align: left; max-height: 600px; }
        .url-form { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
</head>
<body>
<div class="container">
    <div class="url-form text-center">
        <h2>העתקת קוד מקור של אתר</h2>
        <form method="GET" class="row g-3 mt-3">
            <div class="col-md-9">
                <input type="text" name="url" class="form-control" placeholder="הכנס כתובת אתר (למשל: https://google.com)" value="{{ current_url }}">
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-primary w-100">הצג קוד מקור</button>
            </div>
        </form>
    </div>

    {% if source %}
        <div class="card shadow">
            <div class="card-header bg-dark text-white">קוד המקור של: {{ current_url }}</div>
            <div class="card-body">
                <pre><code>{{ source | e }}</code></pre> 
            </div>
        </div>
    {% elif error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
</div>
</body>
</html>
"""

@app.route('/')
def get_source():
    url = request.args.get('url')
    source = None
    error = None

    if url:
        try:
            # הגדרת User-Agent כדי שהאתר יחשוב שאנחנו דפדפן רגיל
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            source = response.text # זהו קוד המקור (HTML)
        except Exception as e:
            error = f"שגיאה בשליפת הדף: {str(e)}"

    return render_template_string(HTML_TEMPLATE, source=source, error=error, current_url=url or "")

if __name__ == '__main__':
    app.run(debug=True)
