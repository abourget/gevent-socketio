#!/usr/bin/env python
from sqlalchemy import engine_from_config

from pyramid.config import Configurator

from chatter4.models import DBSession
from chatter4.views import socketio_service
from chatter4.views import index
from chatter4.views import get_log


def simple_route(config, name, url, fn, renderer=None):
    if not renderer:
        renderer = "chatter4:templates/%s.mako" % name

    config.add_route(name, url)
    config.add_view(fn, route_name=name, renderer=renderer)


def main(global_config, **settings):
    config = Configurator()

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    simple_route(config, 'index', '/', index)
    simple_route(config, 'get_log', '/get_log', get_log, renderer='json')
    simple_route(config, 'socket_io', 'socket.io/*remaining', socketio_service)

    config.add_static_view('static', 'static', cache_max_age=3600)

    app = config.make_wsgi_app()

    return app
