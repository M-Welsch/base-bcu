class BackupserverException(Exception):
    # for future use
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

def break_it():
    raise DockingError("Timout exceeded!")

if __name__ == "__main__":
    try:
        break_it()
    except DockingError:
        print(f"Cannot Do Backup due to DockingError: {DockingError}")
