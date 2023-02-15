from enum import Enum


class WakeupReason(Enum):
    BACKUP_NOW = "BACKUP"
    SCHEDULED_BACKUP = "SCHEDULED"
    CONFIGURATION = "CONFIG"
    HEARTBEAT_TIMEOUT = "HEARTBEAT"
    NO_REASON = ""
