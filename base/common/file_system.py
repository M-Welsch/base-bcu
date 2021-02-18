import logging
from pathlib import Path
from typing import List, Optional

import pyinotify

from base.common.drive_inspector import DriveInspector, PartitionInfo


LOG = logging.getLogger(Path(__file__).name)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, drive_inspector: DriveInspector):
        self._drive_inspector: DriveInspector = drive_inspector
        self._notifier: pyinotify.Notifier

    def set_notifier(self, notifier: pyinotify.Notifier) -> None:
        self._notifier = notifier

    def process_IN_CREATE(self, event: pyinotify.Event) -> None:
        assert isinstance(self._notifier, pyinotify.Notifier), "Call set_notifier() first."
        LOG.debug(f"File {event.pathname} was created")
        LOG.info("Try to find partition...")
        self._notifier.partition_info = self._drive_inspector.backup_partition_info
        if self._notifier.partition_info is not None:
            # self._notifier.stop()  # Use dirty hack instead
            self._notifier._timeout = 0


class FileSystemWatcher:
    dir_events = pyinotify.IN_DELETE | pyinotify.IN_CREATE

    def __init__(self, timeout_in_secs: int = 10) -> None:
        self._drive_inspector: DriveInspector = DriveInspector()
        self._watch_manager: pyinotify.WatchManager = pyinotify.WatchManager()
        self._event_handler: EventHandler = EventHandler(self._drive_inspector)
        timeout_in_millisecs = timeout_in_secs * 1000
        self._notifier: pyinotify.Notifier = pyinotify.Notifier(
            self._watch_manager, self._event_handler, timeout=timeout_in_millisecs
        )
        self._event_handler.set_notifier(self._notifier)
        self.partition_info: Optional[PartitionInfo] = None

    def add_watches(self, dirs_to_watch: List[str]) -> None:
        for directory in dirs_to_watch:
            self._watch_manager.add_watch(directory, FileSystemWatcher.dir_events)

    def backup_partition_info(self) -> PartitionInfo:
        LOG.info("Try to find partition for the first time...")
        partition_info = self._drive_inspector.backup_partition_info
        if partition_info is not None:
            return partition_info
        self._watch_until_timeout()
        if self.partition_info is None:
            LOG.info("Try to find partition for the last time...")
            self.partition_info = self._drive_inspector.backup_partition_info
        return self.partition_info

    def _watch_until_timeout(self):
        assert self._notifier._timeout is not None, 'Notifier must be constructed with a short timeout'
        self._notifier.process_events()
        while self._notifier.check_events():
            self._notifier.read_events()
            self._notifier.process_events()


if __name__ == "__main__":
    watcher = FileSystemWatcher(timeout=10000)
    watcher.add_watches(dirs_to_watch=["/dev", "/home/base"])
    watcher.backup_partition_info()
