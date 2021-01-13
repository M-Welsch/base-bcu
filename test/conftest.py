import logging
import sys

import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_logger():
    # Path(self._config.logs_directory).mkdir(exist_ok=True)
    logging.basicConfig(
        # filename=Path(self._config.logs_directory)/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log'),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
        datefmt='%m.%d.%Y %H:%M:%S'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
