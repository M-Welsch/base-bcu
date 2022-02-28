from pathlib import Path


def pytest_configure() -> None:
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    from base.common.logger import LoggerFactory

    LoggerFactory(Path.cwd() / "base/config", "BaSe_test", development_mode=True)
