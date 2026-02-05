import flask as fl
import requests as re
app = fl.Flask(__name__)
@app.route('/',methods=['GET'])
def a():return re.get("https://games.yo-yoo.co.il/games_play.php?game=5502")
if __name__ == '__main__':
    app.run(debug=True)
