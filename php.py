import requests
import re
import io
import zipfile
import os
import mimetypes
from flask import Flask, render_template_string, request, Response, send_file
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup  # pip install beautifulsoup4

app = Flask(__name__)

# --- קונפיגורציה לזיוף דפדפן ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.5'
}

def clean_filename(url):
    path = urlparse(url).path
    filename = os.path.basename(unquote(path))
    if not filename: return "file"
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)

def fix_url(url):
    url = unquote(url)
    if url and not url.startswith('http'):
        url = 'https://' + url
    return url

def generate_fixed_zip(url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(url, timeout=15)
        response.encoding = response.apparent_encoding
        
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = url
        zip_buffer = io.BytesIO()
        downloaded_files = {} 
        file_counter = 0

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            tags_to_process = [
                ('img', ['src', 'data-src'], 'assets_img'),
                ('script', ['src'], 'assets_js'),
                ('link', ['href'], 'assets_css')
            ]

            for tag_name, attrs, folder in tags_to_process:
                for tag in soup.find_all(tag_name):
                    
                    if tag.has_attr('srcset'): del tag['srcset'] 
                    if tag.has_attr('crossorigin'): del tag['crossorigin']
                    if tag.has_attr('integrity'): del tag['integrity']

                    target_attr = None
                    original_val = None
                    for attr in attrs:
                        if tag.has_attr(attr) and tag[attr]:
                            target_attr = attr
                            original_val = tag[attr]
                            break
                    
                    if not target_attr: continue
                    if original_val.startswith('data:') or original_val.startswith('#'): continue

                    abs_url = urljoin(base_url, original_val)
                    
                    if abs_url in downloaded_files:
                        tag[target_attr] = downloaded_files[abs_url] 
                        continue

                    try:
                        file_res = session.get(abs_url, timeout=5)
                        if file_res.status_code == 200:
                            file_counter += 1
                            ext = os.path.splitext(clean_filename(abs_url))[1]
                            if not ext:
                                content_type = file_res.headers.get('Content-Type', '')
                                ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.bin'

                            local_filename = f"{folder}/res_{file_counter}{ext}"
                            zf.writestr(local_filename, file_res.content)
                            tag[target_attr] = local_filename
                            
                            if target_attr == 'data-src':
                                tag['src'] = local_filename
                                del tag['data-src']

                            downloaded_files[abs_url] = local_filename
                    except Exception as e:
                        pass

            extra_css = soup.new_tag("style")
            extra_css.string = "body { margin: 0; padding: 0; overflow-x: hidden; } img { max-width: 100%; }"
            if soup.head: soup.head.append(extra_css)

            zf.writestr('index.html', soup.prettify())
        
        zip_buffer.seek(0)
        return zip_buffer

    except Exception as e:
        print(f"Error generating ZIP: {e}")
        return None

# --- HTML תבנית ה ---
HTML_UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web Ripper V3 - Direct Action</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #121212;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', sans-serif;
            padding: 20px;
        }
        .container-center {
            text-align: center;
            background: #1e1e1e;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 550px;
            border: 1px solid #333;
        }
        .title-gradient {
            background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.2rem;
            margin-bottom: 25px;
        }
        .form-control {
            background: #2d2d2d;
            border: 1px solid #444;
            color: white;
            padding: 18px;
            text-align: center;
            border-radius: 12px;
            margin-bottom: 25px;
            font-size: 1.1rem;
        }
        .form-control:focus {
            background: #333;
            color: white;
            box-shadow: none;
            border-color: #00C9FF;
        }
        .action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            font-size: 1.15rem;
            font-weight: bold;
            color: white;
            border: none;
            border-radius: 12px;
            margin-bottom: 12px;
            transition: 0.3s;
            cursor: pointer;
            width: 100%;
        }
        .action-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }
        .btn-copy { background: #6c5ce7; }
        .btn-html { background: #00cec9; color: #111; }
        .btn-zip { background: linear-gradient(45deg, #fd79a8, #e84393); }
        .action-btn:hover:not(:disabled) { transform: scale(1.02); opacity: 0.9; }
        
        /* Message Area */
        #msg-box {
            min-height: 24px;
            font-weight: bold;
            margin-top: 15px;
            color: #ff7675;
        }
    </style>
</head>
<body>

    <div class="container-center">
        <div class="title-gradient">Web Scanner V4</div>
        <p class="text-secondary mb-4">הדבק קישור ובחר ישירות את הפעולה המבוקשת:</p>
        
        <input type="text" id="urlInput" class="form-control" placeholder="https://example.com" required>

        <!-- הכפתורים מתפקדים כטריגר הישיר! אין יותר כפתור סרוק מוקדם -->
        <button id="btnCopy" onclick="handleDirectAction('copy')" class="action-btn btn-copy">
            העתק קוד מקור (HTML) 📋
        </button>
        
        <button id="btnHtml" onclick="handleDirectAction('html')" class="action-btn btn-html">
            הורד כקובץ HTML 📄
        </button>
        
        <button id="btnZip" onclick="handleDirectAction('zip')" class="action-btn btn-zip">
            הורד כחבילה (כולל קבצים - ZIP) 📦
        </button>

        <div id="msg-box"></div>
    </div>

    <script>
        function getUrl() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) {
                document.getElementById('msg-box').innerText = "❌ שגיאה: יש להכניס קישור תחילה!";
                setTimeout(() => document.getElementById('msg-box').innerText = "", 2500);
                return null;
            }
            return url;
        }

        async function handleDirectAction(type) {
            const url = getUrl();
            if(!url) return;

            document.getElementById('msg-box').innerText = ""; // מנקה שגיאות

            if(type === 'copy') {
                const btn = document.getElementById('btnCopy');
                const origText = btn.innerHTML;
                
                // הפיכת הכפתור לכפתור טעינה
                btn.innerHTML = 'מייבא נתונים... אנא המתן ⏳';
                btn.disabled = true;

                try {
                    // מושך רק את ה-HTML לתוך הטקסט של הקליפבורד
                    const res = await fetch('/api/get_html?target=' + encodeURIComponent(url));
                    if(!res.ok) throw new Error("Server error");
                    const text = await res.text();
                    
                    await navigator.clipboard.writeText(text);
                    btn.innerHTML = 'הקוד הועתק ללוח בהצלחה! 👌';
                } catch(e) {
                    btn.innerHTML = 'שגיאה בשליפת הקוד ❌';
                }

                // החזרת הכפתור למצבו הרגיל אחרי שניה וחצי
                setTimeout(() => {
                    btn.innerHTML = origText;
                    btn.disabled = false;
                }, 2000);

            } 
            else if (type === 'html' || type === 'zip') {
                const btn = type === 'html' ? document.getElementById('btnHtml') : document.getElementById('btnZip');
                const origText = btn.innerHTML;
                
                btn.innerHTML = 'מכין קובץ ומפעיל הורדה... ⏳';
                btn.disabled = true;
                
                // הפעלת נתיב הורדה מאחורי הקלעים באמצעות הדפדפן (זה מוריד ישירות כקובץ בלי לשנות עמוד)
                window.location.href = `/download/${type}?target=` + encodeURIComponent(url);

                setTimeout(() => {
                    btn.innerHTML = origText;
                    btn.disabled = false;
                }, 3000);
            }
        }
    </script>
</body>
</html>
"""

# --- Routes (ניתובים חכמים שקופים למשתמש) ---

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/api/get_html')
def api_get_html():
    """נקודת קצה שמיועדת ספציפית לכפתור העתק: מקבלת בקשה מהרשת ומחזירה מיד רק HTML מקור"""
    url = fix_url(request.args.get('target', ''))
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        return res.text
    except Exception as e:
        return "Error loading page.", 400

@app.route('/download/html')
def download_html():
    url = fix_url(request.args.get('target', ''))
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(url, timeout=15)
        res.encoding = res.apparent_encoding
        return Response(res.text, mimetype="text/html", headers={"Content-Disposition": "attachment; filename=scanned_page.html"})
    except:
        return "Error fetching file.", 400

@app.route('/download/zip')
def download_zip_route():
    url = fix_url(request.args.get('target', ''))
    zip_buffer = generate_fixed_zip(url)
    
    if zip_buffer:
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='website_complete.zip'
        )
    else:
        return "Error building zip. Possible blocking by target site.", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
