import logging

from socketio import socketio_manage
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# for Django 1.3 support
try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include


SOCKETIO_NS = {}


class namespace(object):
    def __init__(self, name=''):
        self.name = name

    def __call__(self, handler):
        SOCKETIO_NS[self.name] = handler
        return handler


@csrf_exempt
def socketio(request):
    try:
        socketio_manage(request.environ, SOCKETIO_NS, request)
    except:
        logging.getLogger("socketio").error("Exception while handling socketio connection", exc_info=True)
    return HttpResponse("")


urls = patterns("", (r'', socketio))
