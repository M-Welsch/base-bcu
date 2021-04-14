from time import sleep
from typing import List, Optional, Callable

import pyinotify

from base.common.drive_inspector import DriveInspector, PartitionInfo
from base.common.logger import LoggerFactory


LOG = LoggerFactory.get_logger(__name__)


class MyNotifier(pyinotify.Notifier):
    # NOTE: Use this hack because self.stop() does not work
    def cancel(self):
        self._timeout = 0


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, partition_info_setter: Callable, drive_inspector: DriveInspector):
        self._set_partition_info: Callable = partition_info_setter
        self._drive_inspector: DriveInspector = drive_inspector
        self._stop_notifier: Callable

    def set_notifier_callback(self, notifier_callback: Callable) -> None:
        self._stop_notifier = notifier_callback

    def process_IN_CREATE(self, event: pyinotify.Event) -> None:
        assert isinstance(self._stop_notifier, Callable), "Call set_notifier() first."
        LOG.debug(f"File {event.pathname} was created")
        sleep(0.5)  # Todo: wait for model_number and serial_number to be written completely in a more elegant way
                    # (lsof). See notes at bottom of file
        LOG.info("Try to find partition...")
        partition_info = self._drive_inspector.backup_partition_info
        if partition_info is not None:
            self._set_partition_info(partition_info)
            self._stop_notifier()


class FileSystemWatcher:
    dir_events = pyinotify.IN_DELETE | pyinotify.IN_CREATE

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._drive_inspector: DriveInspector = DriveInspector()
        self._watch_manager: pyinotify.WatchManager = pyinotify.WatchManager()
        self._event_handler: EventHandler = EventHandler(self._set_partition_info, self._drive_inspector)
        timeout_milliseconds = timeout_seconds * 1000
        self._notifier: MyNotifier = MyNotifier(
            self._watch_manager, self._event_handler, timeout=timeout_milliseconds
        )
        self._event_handler.set_notifier_callback(self._notifier.cancel)
        self._partition_info: Optional[PartitionInfo] = None

    def _set_partition_info(self, info):
        self._partition_info = info

    def add_watches(self, dirs_to_watch: List[str]) -> None:
        assert all([isinstance(d, str) for d in dirs_to_watch]), "List of strings expected!"
        for directory in dirs_to_watch:
            self._watch_manager.add_watch(directory, FileSystemWatcher.dir_events)

    def backup_partition_info(self) -> PartitionInfo:
        LOG.info("Try to find partition for the first time...")
        partition_info = self._drive_inspector.backup_partition_info
        if partition_info is not None:
            return partition_info
        self._watch_until_timeout()
        if self._partition_info is None:
            LOG.info("Try to find partition for the last time...")
            self._partition_info = self._drive_inspector.backup_partition_info
        return self._partition_info

    def _watch_until_timeout(self):
        assert self._notifier._timeout is not None, 'Notifier must be constructed with a short timeout'
        self._notifier.process_events()
        while self._notifier.check_events():
            self._notifier.read_events()
            self._notifier.process_events()


if __name__ == "__main__":
    watcher = FileSystemWatcher(timeout_seconds=10)
    watcher.add_watches(dirs_to_watch=["/dev", "/home/base"])
    watcher.backup_partition_info()



# # bug 1
# Try to find partition for the first time...
# Backup HDD not found!
# File /dev/sg0 was created
# Try to find partition...
# Backup HDD not found!
# File /dev/bsg was created
# Try to find partition...
# Backup HDD not found!
# File /dev/sda was created
# Try to find partition...
# Backup HDD not found!
# File /dev/sda1 was created
# Try to find partition...
# Backup HDD not found!
# Try to find partition for the last time...
# ['mount', '-t', 'ext4', '/dev/sda1', '/media/BackupHDD']
# Mounted HDD /dev/sda1 at None
#
# ## Analyse:
# * selbes Phänomen bei test_engage
#
# File /dev/sda1 was created
# Try to find partition...
# [DriveInfo(name='sda', path='/dev/sda', model_name='WDC WD3000JD-00K', serial_number=None, bytes_size=300069052416, mount_point=None, rotational=True, drive_type='disk', state='running', partitions=[PartitionInfo(path='/dev/sda1', mount_point=None, bytes_size=300067848192)]), DriveInfo(name='mmcblk0', path='/dev/mmcblk0', model_name=None, serial_number='0x22902883', bytes_size=4012900352, mount_point=None, rotational=False, drive_type='disk', state=None, partitions=[PartitionInfo(path='/dev/mmcblk0p1', mount_point='/', bytes_size=3808051200)]), DriveInfo(name='zram0', path='/dev/zram0', model_name=None, serial_number=None, bytes_size=52428800, mount_point='/var/log', rotational=False, drive_type='disk', state=None, partitions=[]), DriveInfo(name='zram1', path='/dev/zram1', model_name=None, serial_number=None, bytes_size=522620928, mount_point='[SWAP]', rotational=False, drive_type='disk', state=None, partitions=[])]
# Backup HDD not found!
# Try to find partition for the last time...
# [DriveInfo(name='sda', path='/dev/sda', model_name='WDC_WD3000JD-00KLB0', serial_number='WD-WMAMR1169221', bytes_size=300069052416, mount_point=None, rotational=True, drive_type='disk', state='running', partitions=[PartitionInfo(path='/dev/sda1', mount_point=None, bytes_size=300067848192)]), DriveInfo(name='mmcblk0', path='/dev/mmcblk0', model_name=None, serial_number='0x22902883', bytes_size=4012900352, mount_point=None, rotational=False, drive_type='disk', state=None, partitions=[PartitionInfo(path='/dev/mmcblk0p1', mount_point='/', bytes_size=3808051200)]), DriveInfo(name='zram0', path='/dev/zram0', model_name=None, serial_number=None, bytes_size=52428800, mount_point='/var/log', rotational=False, drive_type='disk', state=None, partitions=[]), DriveInfo(name='zram1', path='/dev/zram1', model_name=None, serial_number=None, bytes_size=522620928, mount_point='[SWAP]', rotational=False, drive_type='disk', state=None, partitions=[])]
#
# => warum ist der model_name bei "last time" vollständig und vorher nicht. Vermutlich ist irgendein File nicht zuende geschrieben
