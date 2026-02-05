from flask import Flask, render_template_string
import requests

app = Flask(__name__)

GAME_URL = "https://games.yo-yoo.co.il/games_play.php?game=5502"

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Flask Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        pre { background: #f4f4f4; padding: 15px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Response from {{ url }}</h1>

    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% else %}
        <pre>{{ content }}</pre>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    try:
        response = requests.get(GAME_URL, timeout=5)
        response.raise_for_status()
        content = response.text
        error = None
    except requests.exceptions.RequestException as e:
        content = ""
        error = f"Failed to fetch URL: {e}"

    return render_template_string(
        HTML_TEMPLATE,
        url=GAME_URL,
        content=content,
        error=error
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
