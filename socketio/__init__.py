version_info = (0, 1, 0)
__version__ = ".".join(map(str, version_info))

__all__ = ['SocketIOServer']


from socketio.server import SocketIOServer
