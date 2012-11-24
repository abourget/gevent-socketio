import os
import gevent
import time

from gevent.pool import Pool

from gunicorn.workers.ggevent import GeventPyWSGIWorker
from gunicorn.workers.ggevent import PyWSGIHandler
from gunicorn.workers.ggevent import GeventResponse
from socketio.server import SocketIOServer
from socketio.handler import SocketIOHandler

from geventwebsocket.handler import WebSocketHandler

from datetime import datetime

class GunicornWSGIHandler(PyWSGIHandler, SocketIOHandler):
    pass

class GunicornWebSocketWSGIHandler(WebSocketHandler):
    def log_request(self):
            start = datetime.fromtimestamp(self.time_start)
            finish = datetime.fromtimestamp(self.time_finish)
            response_time = finish - start
            resp = GeventResponse(self.status, [],
                    self.response_length)
            req_headers = [h.split(":", 1) for h in self.headers.headers]
            self.server.log.access(resp, req_headers, self.environ, response_time)

class GeventSocketIOBaseWorker(GeventPyWSGIWorker):
    """ The base gunicorn worker class """
    def __init__(self, age, ppid, socket, app, timeout, cfg, log):
        if os.environ.get('POLICY_SERVER', None) is None:
            if self.policy_server:
                os.environ['POLICY_SERVER'] = 'true'
        else:
            self.policy_server = False

        super(GeventSocketIOBaseWorker, self).__init__(age, ppid, socket, app, timeout, cfg, log)

    def run(self):
        self.socket.setblocking(1)
        pool = Pool(self.worker_connections)
        self.server_class.base_env['wsgi.multiprocess'] = \
            self.cfg.workers > 1

        server = self.server_class(
            self.socket
            , application=self.wsgi
            , spawn=pool
            , resource=self.resource
            , log=self.log
            , policy_server=self.policy_server
            , handler_class=self.wsgi_handler
            , ws_handler_class=self.ws_wsgi_handler
        )

        server.start()
        pid = os.getpid()

        try:
            while self.alive:
                self.notify()

                if  pid == os.getpid() and self.ppid != os.getppid():
                    self.log.info("Parent changed, shutting down: %s", self)
                    break

                gevent.sleep(1.0)

        except KeyboardInterrupt:
            pass

        try:
            # Stop accepting requests
            server.kill()

            # Handle current requests until graceful_timeout
            ts = time.time()
            while time.time() - ts <= self.cfg.graceful_timeout:
                if server.pool.free_count() == server.pool.size:
                    return # all requests was handled

                self.notify()
                gevent.sleep(1.0)

            # Force kill all active the handlers
            self.log.warning("Worker graceful timeout (pid:%s)" % self.pid)
            server.stop(timeout=1)
        except:
            pass


class GeventSocketIOWorker(GeventSocketIOBaseWorker):
    """
    Default gunicorn worker utilizing gevent

    Uses the namespace 'socket.io' and defaults to the flash policy server
    being disabled.
    """
    server_class = SocketIOServer
    wsgi_handler = GunicornWSGIHandler
    ws_wsgi_handler = GunicornWebSocketWSGIHandler
    # We need to define a namespace for the server, it would be nice if this
    # was a configuration option, will probably end up how this implemented,
    # for now this is just a proof of concept to make sure this will work
    resource = 'socket.io'
    policy_server = True
