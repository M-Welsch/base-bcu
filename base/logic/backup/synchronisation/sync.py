from __future__ import annotations

import os
import re
import signal
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from types import TracebackType
from typing import Generator, List, Optional, Type

from base.common.config import get_config
from base.common.logger import LoggerFactory
from base.logic.backup.synchronisation.rsync_command import RsyncCommand
from base.logic.backup.synchronisation.rsync_patterns import Patterns
from base.logic.backup.synchronisation.sync_status import SyncStatus

LOG = LoggerFactory.get_logger(__name__)


class Sync:
    def __init__(self, local_target_location: Path, source_location: Path) -> None:
        self._sync_config = get_config("sync.json")
        self._nas_config = get_config("nas.json")
        self._process: Optional[Popen] = None
        self._status: SyncStatus = SyncStatus()
        self._source = source_location
        self._target = local_target_location

    def update_target(self, new_target: Path) -> None:
        self._target = new_target

    def __enter__(self) -> Generator[SyncStatus, None, None]:
        rsync_command: str = RsyncCommand().compose(self._target, self._source)
        LOG.debug(f"syncing with command: {rsync_command}")
        # Fixme: we're having an outdated version of "target" here ...
        self._process = Popen(
            rsync_command,
            bufsize=0,
            universal_newlines=True,
            stdout=PIPE,
            stderr=STDOUT,
            shell=True,
            preexec_fn=os.setsid,
        )
        return self._output_generator()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        if isinstance(self._process, Popen):
            self._process.wait()  # Fixme: put timeout of "1" back in?
        try:
            self.terminate()
        except ProcessLookupError:
            pass

    def _output_generator(self) -> Generator[SyncStatus, None, None]:
        assert isinstance(self._process, Popen)
        while self._process.stdout is not None:
            line = self._process.stdout.readline()
            # LOG.debug(f"line: {line}")
            code = self._process.poll()

            if not line:
                if code is None:
                    continue
                else:
                    break

            self._status = parse_line_to_status(line.rstrip(), self._status)
            yield self._status

    def terminate(self) -> None:
        assert isinstance(self._process, Popen)
        LOG.debug(f"terminating process ID {self._process.pid}")
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    @property
    def pid(self) -> int:
        assert isinstance(self._process, Popen)
        return self._process.pid


def parse_line_to_status(line: str, status: SyncStatus) -> SyncStatus:
    if not line:
        pass
    elif line == "receiving incremental file list":
        pass
    elif re.fullmatch(Patterns.file_stats, line):
        match = re.search(Patterns.percentage, line)
        assert isinstance(match, re.Match)
        status.progress = float(match[0][:-1]) / 100
    elif re.fullmatch(Patterns.end_stats_a, line):
        status.path = Path()
    elif re.fullmatch(Patterns.end_stats_b, line):
        status.finished = True
    elif re.fullmatch(Patterns.path, line):
        status.path = Path(line)
    elif re.fullmatch(Patterns.dir_not_found, line):
        status.finished = True
        status.error = True
    else:
        pass
    return status
