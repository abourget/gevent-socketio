import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.importlib import import_module

from django.conf.urls import patterns


LOADING_SOCKETIO = False


def autodiscover():
    """
    Auto-discover INSTALLED_APPS sockets.py modules and fail silently when
    not present. NOTE: socketio_autodiscover was inspired/copied from
    django.contrib.admin autodiscover
    """
    global LOADING_SOCKETIO
    if LOADING_SOCKETIO:
        return
    LOADING_SOCKETIO = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:

        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('sockets', app_path)
        except ImportError:
            continue

        import_module("%s.sockets" % app)

    LOADING_SOCKETIO = False


@csrf_exempt
def socketio(request):
    try:
        socket = request.environ.get('engine_socket', None)
        if socket is not None:
            socket.context['request'] = request
    except:
        logging.getLogger("socketio").error("Exception while handling socketio connection", exc_info=True)
    return HttpResponse("")

autodiscover()

urls = patterns("", (r'', socketio))
