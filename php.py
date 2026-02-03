import flask as fl
import requests as re
app = fl.Flask(__name__)
@app.route('/',methods=['GET'])
def a():return re.get('view-source:' + fl.request.args['x'] if fl.request.args['x'] else 'https://aviel1.vercel.app')
if __name__ == '__main__':
    app.run(debug=True)
