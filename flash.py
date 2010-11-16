# If you want to handler FlashSockets, please start the following server:

from gevent.server import StreamServer

policy = """<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
<allow-access-from domain="*" to-ports="*"/>
</cross-domain-policy>
"""

def policy_file(socket, address):
    sock = socket.makefile()
    print "write"
    sock.write(policy + "\x00")
    sock.flush()


policy_server = StreamServer(('0.0.0.0', 843), policy_file)
policy_server.serve_forever()
