from socket import socket, AF_INET, SOCK_DGRAM
from sys import exc_info

from base.common.logger import LoggerFactory


# TODO: Remove everything logging related after proper exception is being catched in get_ip_address
LOG = LoggerFactory.get_logger(__name__)


def get_ip_address() -> str:
    sock = socket(AF_INET, SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        sock.connect(("10.255.255.255", 1))
        ip_address, _ = sock.getsockname()
    except Exception:
        exc_type, _, _ = exc_info()  # TODO: Remove this after proper exception is being catched in get_ip_address
        LOG.warning(f"TODO: Which exception is this: '{exc_type}'? Put it in common/network_utils.py:get_ip_address()!")
        ip_address = "127.0.0.1"
    finally:
        sock.close()
    return ip_address
