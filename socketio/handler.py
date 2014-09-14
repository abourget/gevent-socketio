import copy
import sys
import urlparse
import Cookie

import gevent
from gevent.pywsgi import WSGIHandler

from socketio.engine import transports
from socketio.engine.handler import EngineHandler


class SocketIOHandler(EngineHandler):
    pass