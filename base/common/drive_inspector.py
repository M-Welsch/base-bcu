from __future__ import annotations

import json
from dataclasses import dataclass
from subprocess import PIPE, run
from typing import Any, Dict, List, Optional

from base.common.exceptions import ExternalCommandError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


@dataclass
class PartitionInfo:
    path: str
    mount_point: str
    bytes_size: int

    @classmethod
    def from_json(cls, json_info: Dict[str, Any]) -> PartitionInfo:
        return cls(path=json_info["path"], mount_point=json_info["mountpoint"], bytes_size=int(json_info["size"]))


@dataclass
class DriveInfo:
    name: str
    path: str
    model_name: str
    serial_number: str
    bytes_size: int
    mount_point: str
    rotational: bool
    drive_type: str
    state: str
    partitions: List[PartitionInfo]

    @classmethod
    def from_json(cls, json_info: Dict[str, Any]) -> DriveInfo:
        return cls(
            name=json_info["name"],
            path=json_info["path"],
            model_name=json_info["model"],
            serial_number=json_info["serial"],
            bytes_size=int(json_info["size"]),
            mount_point=json_info["mountpoint"],
            rotational=bool(json_info["rota"]),
            drive_type=json_info["type"],
            state=json_info["state"],
            partitions=[PartitionInfo.from_json(partition_info) for partition_info in json_info.get("children", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "serial_number": self.serial_number,
            "bytes_size": self.bytes_size,
        }


@dataclass
class PartitionSignature:
    model_name: str
    serial_number: str
    bytes_size: int
    partition_index: int


class DriveInspector:
    def __init__(self, partition_signature: PartitionSignature) -> None:
        self._partition_signature: PartitionSignature = partition_signature
        self._devices: List[DriveInfo] = []

    @property
    def devices(self) -> List[DriveInfo]:
        self.refresh()
        return self._devices

    def refresh(self) -> None:
        json_info = self._query()
        self._devices = [DriveInfo.from_json(drive_json_info) for drive_json_info in json_info]

    @property
    def backup_partition_info(self) -> Optional[PartitionInfo]:
        candidates = [
            device
            for device in self.devices
            if device.model_name == self._partition_signature.model_name
            and device.serial_number == self._partition_signature.serial_number
            and device.bytes_size == self._partition_signature.bytes_size
        ]
        if not len(candidates) == 1:
            return None
        partitions = [
            p for p in candidates[0].partitions if p.path.endswith(str(self._partition_signature.partition_index))
        ]
        if not len(partitions) == 1:
            LOG.error("Correct partition in Backup HDD not found!")
            return None
        return partitions[0]

    @staticmethod
    def _query() -> List[Dict[str, Any]]:
        command = ["lsblk", "-o", "NAME,PATH,MODEL,SERIAL,SIZE,MOUNTPOINT,ROTA,TYPE,STATE", "-b", "-J"]
        cp = run(command, stdout=PIPE, stderr=PIPE)
        if cp.stderr:
            raise ExternalCommandError(cp.stderr)
        elif not cp.stdout:
            raise ExternalCommandError("Dreck funktioniert ned!")
        devices: List[Dict[str, Any]] = json.loads(cp.stdout.decode())["blockdevices"]
        return devices
