class BackupserverException(Exception):
    pass


class DockingError(BackupserverException):
    pass


class UndockingError(BackupserverException):
    pass


class MountingError(BackupserverException):
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
