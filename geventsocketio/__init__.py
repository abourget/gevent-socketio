version_info = (0, 1, 0)
__version__ = ".".join(map(str, version_info))

try:
    from geventsocketio.server import SocketIOServer
except ImportError:
    import traceback
    traceback.print_exc()
