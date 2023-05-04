from abc import ABC
from dataclasses import dataclass
from typing import Optional, Iterable, Protocol, Any, Set, runtime_checkable, Dict, Union
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


class ComponentState(Protocol):
    def __setattr__(self, key: str, value: Any) -> None:
        ...

    def get(self, attribute: str) -> Any:
        ...


class ComponentStateMixin(BaseModel, ABC):
    observers: Iterable[StateObserver]

    class Config:
        arbitrary_types_allowed = True

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        for observer in self.observers:
            observer.update(self.__class__.__name__, key, value)

    def get(self, attribute: str) -> Any:
        if attribute not in self.__fields__:
            print(f"Warning! Someone tried to retrieve the value for non-existing attribute '{attribute}'!")
            return None
        return getattr(self, attribute)


class DiagnoseData(ComponentStateMixin, BaseModel):
    voltage: Optional[float]
    current: Optional[float]
    temperature: Optional[float]


class BackupDriveState(ComponentStateMixin, BaseModel):
    is_docked: bool
    is_powered: bool
    is_mounted: bool
    usage_percent: Optional[float]


Query = Dict[str, Set[str]]
Response = Dict[str, Dict[str, Any]]


@dataclass
class State:
    diagnose_data: DiagnoseData
    backup_drive_state: BackupDriveState

    def __post_init__(self):
        self._component_states: Dict[str, ComponentState] = {
            cls.__name__: getattr(self, attribute) for attribute, cls in self.__annotations__.items()
        }

    def _get_component_state(self, component_name: str) -> ComponentState:
        if component_name not in self._component_states:
            print(f"Warning! Someone tried to access the non-existing component state '{component_name}'!")
            return {}
        return self._component_states.get(component_name)

    def get(self, query: Query) -> Response:
        return {
            component_name: {key: self._get_component_state(component_name).get(key) for key in keys}
            for component_name, keys in query.items()
        }


if __name__ == "__main__":
    observers = [HardwareUI(SerialInterface(), {"voltage", "current"})]
    dd = DiagnoseData(observers=observers)
    bds = BackupDriveState(observers=observers, is_docked=True, is_powered=True, is_mounted=False)
    state = State(diagnose_data=dd, backup_drive_state=bds)

    dd.voltage = 42
    dd.temperature = 42
    print(state.get({"DiagnoseData": {"voltage", "current"}, "BackupDriveState": {"is_docked"}}))










"""

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
