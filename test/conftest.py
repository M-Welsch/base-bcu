import logging
import sys
from datetime import datetime
from pathlib import Path

import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_logger(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("logs")
    logging.basicConfig(
        filename=Path(tmpdir) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"),
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(name)s: %(message)s",
        datefmt="%m.%d.%Y %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    logger.info(f"I'm here! tmpdir = {tmpdir}")
    yield {"tmpdir": str(tmpdir)}
