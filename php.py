import flask as fl
import requests as re

app = fl.Flask(__name__)

@app.route('/')
def home():
    url = "https://games.yo-yoo.co.il/games_play.php?game=5502"  # החלף לכתובת שתרצה
    response = re.get(url)

    template = """
    <!doctype html>
    <html>
        <head>
            <title>Flask Demo</title>
        </head>
        <body>
            <h1>Response from {{ url }}</h1>
            <pre>{{ content }}</pre>
        </body>
    </html>
    """

    return fl.render_template_string(
        template,
        url=url,
        content=response.text
    )

if __name__ == '__main__':
    app.run(debug=True)
