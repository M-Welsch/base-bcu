import logging


def setup_logger(debug: bool = False):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s"))
    base_logger = logging.getLogger("BaSe")
    base_logger.handlers = [handler]
    base_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    base_logger.propagate = False


def get_logger(name):
    return logging.getLogger(".".join(("BaSe", name)))
