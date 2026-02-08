import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# תבנית דף מעוצבת
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
        body { background: var(--bg); color: #e2e8f0; font-family: 'Inter', sans-serif; min-height: 100vh; }
        
        .glass-card { 
            background: rgba(30, 41, 59, 0.7); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 20px; 
        }

        .search-box {
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid var(--secondary);
            color: white;
            border-radius: 12px;
            padding: 15px;
        }

        .btn-gradient {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none; color: white; font-weight: bold;
            transition: transform 0.2s;
        }

        .btn-gradient:hover { transform: translateY(-2px); color: white; opacity: 0.9; }

        .code-header {
            background: #1e293b;
            padding: 10px 20px;
            border-radius: 15px 15px 0 0;
            border-bottom: 1px solid #334155;
            display: flex; justify-content: space-between; align-items: center;
        }

        pre { margin: 0 !important; border-radius: 0 0 15px 15px !important; max-height: 600px; }

        /* אנימציית כניסה */
        .fade-in { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="container py-5">
    
    <div class="text-center mb-5">
        <h1 style="background: linear-gradient(to right, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 3rem;">
            Web-Scanner Pro
        </h1>
        <p class="text-secondary">חלץ, נתח ולמד מכל אתר ברשת</p>
    </div>

    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="glass-card p-4 mb-5 shadow-lg">
                <form method="GET" class="row g-3">
                    <div class="col-md-9">
                        <input type="url" name="url" class="form-control search-box" 
                               placeholder="הכנס כתובת אתר מלאה..." value="{{ url }}" required>
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-gradient w-100 h-100">סרוק אתר</button>
                    </div>
                </form>
            </div>

            {% if error %}
                <div class="alert alert-danger glass-card border-0 text-white fade-in">{{ error }}</div>
            {% endif %}

            {% if html_content %}
                <div class="fade-in">
                    <div class="code-header">
                        <span class="badge bg-primary">HTML Content</span>
                        <button class="btn btn-sm btn-outline-info" onclick="copyCode()" id="copyBtn">העתק הכל</button>
                    </div>
                    <pre><code id="main-code" class="language-html">{{ html_content | e }}</code></pre>
                </div>
            {% endif %}
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script>
        function copyCode() {
            const code = document.getElementById('main-code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.getElementById('copyBtn');
                btn.innerText = 'הועתק! ✓';
                setTimeout(() => btn.innerText = 'העתק הכל', 2000);
            });
        }
    </script>
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
