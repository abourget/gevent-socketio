import sys
if 'threading' in sys.modules:
    del sys.modules['threading']
import gevent
import gevent.socket
import gevent.monkey
gevent.monkey.patch_all()

import chat
chat.init_db()
