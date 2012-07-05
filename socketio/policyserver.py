from gevent.server import StreamServer

__all__ = ['FlashPolicyServer']


class FlashPolicyServer(StreamServer):
    policy = """<?xml version="1.0"?><!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy><allow-access-from domain="*" to-ports="*"/></cross-domain-policy>"""

    def __init__(self, listener=None, backlog=None):
        if listener is None:
            listener = ('0.0.0.0', 10843)
        StreamServer.__init__(self, listener=listener, backlog=backlog)

    def handle(self, sock, address):
        # send and read functions should not wait longer than three seconds
        sock.settimeout(3)
        try:
            # try to receive at most 128 bytes (`POLICYREQUEST` is shorter)
            # Interestingly if we dont do this and we write to the spcket directly
            # I am getting strange errors.
            input = sock.recv(128)
            if input.startswith(FlashPolicyServer.policyrequest):
                sock.sendall(FlashPolicyServer.policy)
        except socket.timeout:
            pass
        sock.close()
