from collections import namedtuple
from dataclasses import dataclass, fields
from typing import List

BAUD_RATE: int = 9600


backup_process_step = namedtuple("backup_process_step", "suffix description may_be_continued")


@dataclass
class BackupDirectorySuffix:
    while_copying: backup_process_step = backup_process_step(".in_preparation", "copying ", False)
    while_backing_up: backup_process_step = backup_process_step(".unfinished", "synchronisation in progress", True)
    finished: backup_process_step = backup_process_step("", "completed backup", True)

    @classmethod
    def not_valid_for_continuation(cls) -> List[str]:
        return [field.default.suffix for field in fields(cls) if not field.default.may_be_continued]
