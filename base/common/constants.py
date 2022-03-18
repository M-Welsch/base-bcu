from collections import namedtuple
from dataclasses import dataclass, fields
from typing import List

BAUD_RATE: int = 9600


current_backup_timestring_format_for_directory = "%Y_%m_%d-%H_%M_%S"


next_backup_timestring_format_for_sbu = "%d.%m.%Y %H:%M"


BackupProcessStep = namedtuple("BackupProcessStep", "suffix description may_be_continued")


@dataclass
class BackupDirectorySuffix:
    while_copying: BackupProcessStep = BackupProcessStep(".in_preparation", "copying ", False)
    while_backing_up: BackupProcessStep = BackupProcessStep(".unfinished", "synchronisation in progress", True)
    finished: BackupProcessStep = BackupProcessStep("", "completed backup", True)

    @classmethod
    def not_valid_for_continuation(cls) -> List[str]:
        return [field.default.suffix for field in fields(cls) if not field.default.may_be_continued]
