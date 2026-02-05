from flask import Flask, render_template_string
import requests

app = Flask(__name__)

TARGET_URL = "https://games.yo-yoo.co.il/games_play.php?game=5502"

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Flask Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Response from {{ url }}</h1>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% else %}
        <pre>{{ content }}</pre>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    try:
        response = requests.get(
            TARGET_URL,
            timeout=5,
            headers={"User-Agent": "Flask-Demo-App"}
        )
        response.raise_for_status()
        content = response.text
        error = None
    except requests.RequestException as e:
        content = ""
        error = f"Failed to fetch URL: {e}"

    return render_template_string(
        TEMPLATE,
        url=TARGET_URL,
        content=content,
        error=error
    )

if __name__ == "__main__":
    app.run()
