from typing import Any


class BackupserverException(Exception):
    pass


class DockingError(BackupserverException):
    pass


class UndockingError(BackupserverException):
    pass


class MountError(BackupserverException):
    pass


class ExternalCommandError(BackupserverException):
    pass


class UnmountError(BackupserverException):
    pass


class SbuCommunicationTimeout(BackupserverException):
    pass


class ScheduleError(BackupserverException):
    pass


class NewBuDirCreationError(BackupserverException):
    pass


class NasNotAvailableError(BackupserverException):
    pass


class NetworkError(BackupserverException):
    pass


class BackupHddAccessError(BackupserverException):
    pass


class NasNotCorrectError(Exception):
    pass


class NasNotMountedError(Exception):
    pass


class BackupRequestError(Exception):
    pass


class RemoteCommandError(BackupserverException):
    pass


if __name__ == "__main__":
    try:
        raise DockingError("Timout exceeded!")
    except DockingError:
        print(f"Cannot Do Backup due to DockingError: {DockingError}")


class SbuNotAvailableError(Exception):
    """Raise if UART interface is not found."""


class SerialWrapperError(Exception):
    pass


class ComponentOffError(Exception):
    def __init__(
        self, message: str, component: str, avoids_backup: bool = False, avoids_shutdown: bool = False, *args: Any
    ) -> None:
        super().__init__(message, *args)
        self.component: str = component
        self.avoids_backup: bool = avoids_backup
        self.avoids_shutdown: bool = avoids_shutdown


class BackupPartitionError(Exception):
    pass
