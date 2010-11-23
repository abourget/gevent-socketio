#!/usr/bin/python
# Note, that geventsocketio.SocketIOServer starts flash policy server by default
# so running this script is not strictly necessary

import sys
from geventsocketio.policyserver import FlashPolicyServer
server = FlashPolicyServer()
server.start()
print >> sys.stderr, 'Listening on %s:%s' % (server.server_host, server.server_port)
server.serve_forever()
