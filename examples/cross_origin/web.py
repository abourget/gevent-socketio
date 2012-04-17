import os
from bottle import Bottle, static_file, run

HERE = os.path.abspath(os.path.dirname(__file__))
STATIC = os.path.join(HERE, 'static')

app = Bottle()


@app.route('/')
@app.route('/<filename:path>')
def serve(filename='index.html'):
    return static_file(filename, root=STATIC)


if __name__ == '__main__':
    run(app=app, host='localhost', port=8080)
