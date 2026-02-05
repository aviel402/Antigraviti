import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# תבנית HTML פשוטה שמאפשרת לך גם להזין כתובת וגם לראות את המקור
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>מעתיק מקור דף</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container py-5">
    <h2 class="mb-4">הזן כתובת אתר להעתקת מקור:</h2>
    <form method="GET" class="mb-4">
        <div class="input-group">
            <input type="text" name="url" class="form-control" placeholder="https://example.com" value="{{ url }}">
            <button type="submit" class="btn btn-primary">העתק מקור</button>
        </div>
    </form>

    {% if html_content %}
        <div class="card">
            <div class="card-header d-flex justify-content-between">
                <span>מקור הדף עבור: {{ url }}</span>
                <button class="btn btn-sm btn-outline-secondary" onclick="navigator.clipboard.writeText(document.getElementById('source').innerText)">העתק הכל</button>
            </div>
            <div class="card-body">
                <pre id="source" style="background: #f4f4f4; padding: 15px; max-height: 500px; overflow: auto; direction: ltr; text-align: left;"><code>{{ html_content | e }}</code></pre>
            </div>
        </div>
    {% endif %}

    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET'])
def proxy():
    # שליפת הכתובת מה-URL (למשל: /?url=http://google.com)
    target_url = request.args.get('url')
    html_content = None
    error = None

    if target_url:
        try:
            # הוספת User-Agent כדי שהאתר לא יחסום אותנו (מתנהג כמו דפדפן רגיל)
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # כאן אנחנו לוקחים את ה-HTML הגולמי
            html_content = response.text
            
        except Exception as e:
            error = f"שגיאה בשליפת הדף: {str(e)}"

    return render_template_string(HTML_PAGE, html_content=html_content, error=error, url=target_url or "")

if __name__ == '__main__':
    app.run(debug=True)
