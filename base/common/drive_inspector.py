from subprocess import run, PIPE
from dataclasses import dataclass
import json
from typing import List

from base.common.exceptions import ExternalCommandError


@dataclass
class PartitionInfo:
    path: str
    bytes_size: int

    @classmethod
    def from_json(cls, json_info):
        return cls(
            path=json_info["path"],
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
    partitions: list

    @classmethod
    def from_json(cls, json_info):
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
    def __init__(self):
        command = ["lsblk", "-o", "NAME,PATH,MODEL,SERIAL,SIZE,MOUNTPOINT,ROTA,TYPE,STATE", "-b", "-J"]
        self._json_info = self._query(command)

    @property
    def devices(self) -> List[DriveInfo]:
        return [DriveInfo.from_json(drive_json_info) for drive_json_info in self._json_info]

    def device_file(self, model_name, serial_number, bytes_size, partition_index):
        candidates = [
            device for device in self.devices if device.model_name == model_name and
                                                 device.serial_number == serial_number and
                                                 device.bytes_size == bytes_size
        ]
        assert len(candidates) == 1
        partitions = [p for p in candidates[0].partitions if p.path.endswith(str(partition_index))]
        assert len(partitions) == 1
        return partitions[0].path

    @staticmethod
    def _query(command):
        cp = run(command, stdout=PIPE, stderr=PIPE)
        if cp.stderr:
            raise ExternalCommandError(cp.stderr)
        elif not cp.stdout:
            raise ExternalCommandError("Dreck funktioniert ned!")
        return json.loads(cp.stdout.decode())["blockdevices"]
