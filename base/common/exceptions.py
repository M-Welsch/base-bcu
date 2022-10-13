from __future__ import annotations

from typing import Any


class BackupserverException(Exception):
    pass


class UndockingError(BackupserverException):
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


class NasSmbConfError(BackupserverException):
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


class SbuNotAvailableError(Exception):
    """Raise if UART interface is not found."""


class SerialInterfaceError(Exception):
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


class RemoteDirectoryException(Exception):
    pass


class LocalDirectoryException(Exception):
    pass


class SbuNoResponseError(SbuCommunicationTimeout):
    pass


class ConfigValidationError(Exception):
    """Invalid config value exception."""


class ConfigSaveError(Exception):
    pass


class BackupSizeRetrievalError(Exception):
    pass


class CriticalException(Exception):
    pass


class InvalidBackupSource(CriticalException):
    pass


class DockingError(CriticalException):
    pass


class BackupDeletionError(Exception):
    pass


class BackupHddNotAvailable(CriticalException):
    pass


class MountError(CriticalException):
    pass


class TimeSynchronisationError(Exception):
    pass
