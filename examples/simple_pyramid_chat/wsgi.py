from pyramid.paster import get_app

app = get_app('development.ini')

# Can run with gunicorn using:
#gunicorn -b 0.0.0.0:8080 --workers=4 --worker-class socketio.sgunicorn.GeventSocketIOWorker wsgi:app

