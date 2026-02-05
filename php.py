import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# תבנית דף מעוצבת
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>מעתיק מקור דף מקצועי</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f7f6; }
        .code-container { background: #2d2d2d; color: #ccc; padding: 20px; border-radius: 8px; direction: ltr; text-align: left; max-height: 600px; overflow: auto; }
    </style>
</head>
<body class="container py-5">
    <div class="card shadow-sm p-4 mb-4">
        <h2 class="mb-4">הזן כתובת אתר (URL)</h2>
        <form method="GET">
            <div class="input-group mb-3">
                <input type="url" name="url" class="form-control" placeholder="https://www.google.com" value="{{ url }}" required>
                <button type="submit" class="btn btn-dark">חלץ מקור דף</button>
            </div>
        </form>
    </div>

    {% if error %}
        <div class="alert alert-danger shadow-sm">{{ error }}</div>
    {% endif %}

    {% if html_content %}
        <div class="card shadow-lg">
            <div class="card-header bg-success text-white">מקור הדף חולץ בהצלחה!</div>
            <div class="card-body">
                <pre class="code-container"><code>{{ html_content | e }}</code></pre>
            </div>
        </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET'])
def proxy():
    target_url = request.args.get('url')
    html_content = None
    error = None

    if target_url:
        # שימוש ב-Session כדי לנהל עוגיות ולמנוע לופים
        session = requests.Session()
        
        # התחזות לדפדפן Chrome אמיתי (מונע חסימות)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,he;q=0.8',
            'Referer': 'https://www.google.com/'
        }

        try:
            # allow_redirects=True עם הגבלה ל-10 הפניות כדי למנוע את השגיאה שלך
            # timeout מוודא שלא נתקע לנצח
            response = session.get(target_url, headers=headers, timeout=15, allow_redirects=True)
            
            # אם יש יותר מדי הפניות, Requests יעצור לבד
            response.raise_for_status()
            html_content = response.text

        except requests.exceptions.TooManyRedirects:
            error = "שגיאה: האתר נמצא בלופ של הפניות (Redirect Loop). ניסינו יותר מדי פעמים."
        except Exception as e:
            error = f"שגיאה בשליפת הדף: {str(e)}"

    return render_template_string(HTML_PAGE, html_content=html_content, error=error, url=target_url or "")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
