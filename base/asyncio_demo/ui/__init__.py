from abc import ABC, abstractmethod
from dataclasses import dataclass

from base.asyncio_demo.state import State
from base.common.observer import Signal


@dataclass
class Signals:
    shutdown_countdown_paused = Signal()
    shutdown_countdown_reset = Signal()
    backup_now_pressed = Signal()


class UI(ABC):
    def __init__(self):  # , state: State):
        # self._state = state
        self.signals = Signals()

    @abstractmethod
    async def on_shutdown_seconds_changed(self, remaining_seconds: float):
        ...

    @abstractmethod
    def on_diagnose_data(self, diagnose_data) -> None:
        ...

    @abstractmethod
    def on_backup_started(self) -> None:
        ...

    @abstractmethod
    def on_backup_finished(self) -> None:
        ...

    @abstractmethod
    def on_backup_progress_changed(self, percentage: float, current_file_name: str):
        ...


"""
@dataclass(frozen=True)
class ShutdownCountdownState:
    is_running: bool
    time_remaining: timedelta


@dataclass(frozen=True)
class BackupDriveState:
    is_docked: bool
    is_powered: bool
    is_mounted: bool
    usage_percent: Optional[float]


@dataclass(frozen=True)
class BackupState:
    next_due_time: Optional[datetime]
    is_running: bool
    current_backup_percent: Optional[float]
    current_file_name: Optional[str]


@dataclass(frozen=True)
class DiagnoseData:
    voltage: float
    current: float
    temperature: float


@dataclass(frozen=True)
class Schedule:
    backup_interval: BackupInterval
    day_of_month: int
    day_of_week: int
    time_of_day: Time


@dataclass(frozen=True)
class Behaviour:
    is_shutdown_between_backups_active: bool
    shutdown_between_backups_delay_minutes: int
    is_pre_backup_hook_active: bool
    pre_backup_hook_content: str
    is_post_backup_hook_active: bool
    post_backup_hook_content: str


class BackupProtocol(Enum):
    SSH = 0
    NFS = 1


@dataclass(frozen=True)
class DataSource:
    protocol: BackupProtocol
    ip_address: str


ShutdownManager -> shutdown_countdown_updated(ShutdownCountdownState)
DockableDrive   -> backup_drive_state_updated(BackupDriveState)
BackupConductor -> backup_state_updated(BackupState)
BackupConductor -> backup_list_changed(list[Path])
Logger          -> log_tail_updated(list[str])
Logger          -> log_list_changed(list[Path])
Logger          -> log_file_content_updated(str)
HardwareDriver  -> diagnose_data_updated(DiagnoseData)


BaseApplication <- shutdown_triggered()
BaseApplication <- settings_changed(Schedule, Behaviour, DataSource)
BackupConductor <- backup_manually_triggered()
BackupConductor <- backup_manually_aborted()
Logger          <- log_requested(Path)
HardwareDriver  <- display_brightness_percent_changed(float)
"""
