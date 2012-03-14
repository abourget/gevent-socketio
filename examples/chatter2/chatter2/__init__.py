#!/usr/bin/env python
from sqlalchemy import engine_from_config
from pyramid.config import Configurator
from chatter2.views import socketio_service
from chatter2.views import index
from chatter2.models import DBSession

def simple_route(config, name, url, fn):
    """ Function to simplify creating routes in pyramid 
        Takes the pyramid configuration, name of the route, url, and view
        function 
    """
    config.add_route(name, url)
    config.add_view(fn, route_name=name,
            renderer="chatter2:templates/%s.mako" % name)

def main(global_config, **settings):
    config = Configurator()

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    simple_route(config, 'index', '/', index)

    # The socketio view configuration
    simple_route(config, 'socket_io', 'socket.io/*remaining', socketio_service)

    config.add_static_view('static', 'static', cache_max_age=3600)

    app = config.make_wsgi_app()

    return app
