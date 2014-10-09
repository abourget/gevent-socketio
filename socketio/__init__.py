import logging

log = logging.getLogger(__name__)


def has_bin(*args):
    """
    Helper function checks whether args contains bytearray
    :param args:
    :return: (bool)
    """
    for arg in args:
        if type(arg) is bytearray:
            return True

    return False
