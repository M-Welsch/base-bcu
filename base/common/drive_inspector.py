from __future__ import annotations
from dataclasses import dataclass
import json
from subprocess import run, PIPE
from typing import Any, Dict, List
import logging
from pathlib import Path

from base.common.exceptions import ExternalCommandError


LOG = logging.getLogger(Path(__file__).name)


@dataclass
class PartitionInfo:
    path: str
    mount_point: str
    bytes_size: int

    @classmethod
    def from_json(cls, json_info: Dict[str, Any]) -> PartitionInfo:
        return cls(
            path=json_info["path"],
            mount_point=json_info["mountpoint"],
            bytes_size=int(json_info["size"])
        )


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
            partitions=[PartitionInfo.from_json(partition_info) for partition_info in json_info.get("children", [])]
        )


class DriveInspector:
    def __init__(self) -> None:
        command = ["lsblk", "-o", "NAME,PATH,MODEL,SERIAL,SIZE,MOUNTPOINT,ROTA,TYPE,STATE", "-b", "-J"]
        json_info = self._query(command)
        self._devices = [DriveInfo.from_json(drive_json_info) for drive_json_info in json_info]

    @property
    def devices(self) -> List[DriveInfo]:
        return self._devices

    def device_info(self, model_name: str, serial_number: str, bytes_size: int, partition_index: int) -> PartitionInfo:
        candidates = [
            device for device in self.devices if device.model_name == model_name and
                                                 device.serial_number == serial_number and
                                                 device.bytes_size == bytes_size
        ]
        try:
            assert len(candidates) == 1
        except AssertionError as e:
            LOG.error("Backup HDD not found! Python says " + e)
            return None
        partitions = [p for p in candidates[0].partitions if p.path.endswith(str(partition_index))]
        try:
            assert len(partitions) == 1
        except AssertionError as e:
            LOG.error("Correct Partition in Backup HDD not found! Python says " + e)
            return None
        return partitions[0]

    @staticmethod
    def _query(command: List[str]) -> List[Dict[str, Any]]:
        cp = run(command, stdout=PIPE, stderr=PIPE)
        if cp.stderr:
            raise ExternalCommandError(cp.stderr)
        elif not cp.stdout:
            raise ExternalCommandError("Dreck funktioniert ned!")
        return json.loads(cp.stdout.decode())["blockdevices"]
