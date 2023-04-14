from abc import ABC
from datetime import datetime, time
from enum import Enum
from typing import Optional, Iterable, Protocol, Any, Set, runtime_checkable
from pydantic import BaseModel


class SerialInterface:
    @staticmethod
    def send(component_name, key, value):
        print(f"{key} of {component_name} was changed to {value}")


@runtime_checkable
class StateObserver(Protocol):
    def update(self, component_name: str, key: str, value: Any) -> None:
        ...


class HardwareUI:
    def __init__(self, serial_interface, keys_of_interest: Set[str]) -> None:
        self._serial_interface = serial_interface
        self._keys_of_interest: Set[str] = keys_of_interest

    def update(self, component_name: str, key: str, value: Any) -> None:
        if key in self._keys_of_interest:
            self._serial_interface.send(component_name, key, value)


class ComponentStateMixin(BaseModel, ABC):
    observers: Iterable[StateObserver]

    class Config:
        arbitrary_types_allowed = True

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        for observer in self.observers:
            observer.update(self.__class__.__name__, key, value)


class DiagnoseData(ComponentStateMixin, BaseModel):
    voltage: Optional[float]
    current: Optional[float]
    temperature: Optional[float]


class BackupDriveState(ComponentStateMixin, BaseModel):
    is_docked: bool
    is_powered: bool
    is_mounted: bool
    usage_percent: Optional[float]


class State:
    def __init__(self):
        self._diagnose_data = DiagnoseData(
            name="diagnose_data", notify=lambda name, val: print(f"{name} has new value {val}")
        )
        self._backup_drive_state = BackupDriveState(
            name="backup_drive_state", notify=lambda name, val: print(f"{name} has new value {val}"),
            is_docked=False, is_powered=False, is_mounted=False
        )















class BackupInterval(Enum):
    MONTHLY = 0
    WEEKLY = 1
    DAILY = 2


class BackupProtocol(Enum):
    SSH = 0
    NFS = 1


class DataSource(BaseModel):
    protocol: BackupProtocol
    ip_address: str


class Schedule(BaseModel):
    backup_interval: BackupInterval
    day_of_month: int
    day_of_week: int
    time_of_day: time


class Behaviour(BaseModel):
    is_shutdown_between_backups_active: bool
    shutdown_between_backups_delay_minutes: int
    is_pre_backup_hook_active: bool
    pre_backup_hook_content: str
    is_post_backup_hook_active: bool
    post_backup_hook_content: str


# class DiagnoseData(BaseModel):
#     voltage: float
#     current: float
#     temperature: float


# class BackupDriveState(BaseModel):
#     is_docked: bool
#     is_powered: bool
#     is_mounted: bool
#     usage_percent: float


class RunningBackupStatistics(BaseModel):
    current_backup_percent: float
    max_absolute_bytes: int
    current_absolute_bytes: int
    elapsed_seconds: int
    remaining_seconds: int


class BackupInfo(BaseModel):
    next_due_time: Optional[datetime] = None
    is_running: bool = False
    running_backup_statistics: Optional[RunningBackupStatistics] = None


class Persistent(BaseModel):
    schedule: Schedule
    behaviour: Behaviour
    data_source: DataSource


class Volatile(BaseModel):
    backup_drive_state: BackupDriveState
    current_backup: BackupInfo
    diagnose_data: DiagnoseData


# class State(BaseModel):
#     persistent: Persistent
#     volatile: Optional[Volatile] = None


"""
State
    Persistent
        Schedule
        Behaviour
        DataSource
    Volatile
        BackupDriveState
        BackupInfo
            RunningBackupStatistics
        DiagnoseData
"""
