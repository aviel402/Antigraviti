import logging
import requests
from flask import Flask, render_template_string

# --- 1. הגדרות וקונפיגורציה (Settings) ---
class Config:
    # כתובת דמה לבדיקה (JSONPlaceholder)
    API_URL = "https://games.yo-yoo.co.il/games_play.php?game=5502"
    TIMEOUT_SECONDS = 5

# --- 2. הגדרת לוגים (Logging) ---
# זה קריטי כדי להבין מה קורה כשהאפליקציה רצה
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# --- 3. לוגיקה עסקית (Service Layer) ---
def fetch_external_data(url):
    """
    ביצוע קריאת API בטוחה עם טיפול בשגיאות.
    """
    if not url or not url.strip():
        return {"error": "לא סופקה כתובת URL תקינה"}

    try:
        logger.info(f"Connecting to {url}...")
        response = requests.get(url, timeout=Config.TIMEOUT_SECONDS)
        response.raise_for_status() # יזרוק שגיאה אם הסטטוס אינו 200 OK
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error("Connection timed out.")
        return {"error": "השרת החיצוני לא הגיב בזמן (Timeout)."}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": "אירעה שגיאה בעת שליפת הנתונים."}

# --- 4. נתיבים (Routes) ---
@app.route('/', methods=['GET'])
def home():
    # הפרדה מלאה: ה-Route רק מנהל את התעבורה, הפונקציה למעלה עושה את העבודה
    data = fetch_external_data(app.config['API_URL'])
    
    # שימוש ב-Template שמוגדר למטה כמשתנה (במקום קובץ נפרד)
    return render_template_string(HTML_TEMPLATE, data=data)

# --- 5. עיצוב האתר (HTML/CSS Template) ---
# ארוז בתוך משתנה כדי להישאר בקובץ אחד
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מערכת בדיקת API</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding-top: 50px; }
        .card { border-radius: 15px; border: none; }
        .json-box { direction: ltr; text-align: left; max-height: 300px; overflow-y: auto; }
        .status-dot { height: 10px; width: 10px; background-color: #28a745; border-radius: 50%; display: inline-block; margin-left: 5px;}
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="text-center mb-4">
                    <h1 class="display-6">🚀 דשבורד ניטור</h1>
                    <p class="text-muted">מציג נתונים בזמן אמת משירות חיצוני</p>
                </div>

                <div class="card shadow-lg">
                    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                        <span class="fw-bold">תוצאות הבקשה</span>
                        <span class="badge bg-light text-primary">Live</span>
                    </div>
                    <div class="card-body">
                        {% if data.error %}
                            <div class="alert alert-danger d-flex align-items-center" role="alert">
                                ⚠️ <strong>שגיאה:</strong> &nbsp; {{ data.error }}
                            </div>
                        {% else %}
                            <div class="alert alert-success" role="alert">
                                <span class="status-dot"></span> התקשורת עברה בהצלחה!
                            </div>
                            <h5 class="card-title">הנתונים שהתקבלו:</h5>
                            <pre class="bg-dark text-white p-3 rounded json-box"><code>{{ data | tojson(indent=4) }}</code></pre>
                        {% endif %}
                    </div>
                    <div class="card-footer text-muted text-center text-small">
                        מערכת מבוססת Flask v3.0
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- 6. הרצה ---
if __name__ == '__main__':
    # הדפסת קישור לחיץ בקונסול לנוחות
    print("✅ Server is running on http://127.0.0.1:5000")
    app.run(debug=True)
