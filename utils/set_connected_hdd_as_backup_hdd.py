import json
import os
import sys
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)


from base.common.config import Config
from base.common.drive_inspector import DriveInfo, DriveInspector


class BuHddSetter:
    def __init__(self) -> None:
        Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
        self._drive_inspector = DriveInspector()

    def set_conneted_hdd_as_backup_hdd(self) -> None:
        drive = self.current_hdd_driveinfo()
        drive_dict = drive.to_dict()
        drive_dict["partition_index"] = 1
        print(drive_dict)
        with open("/home/base/python.base/base/config/drive.json", "r") as jf:
            obj = json.load(jf)
        with open("/home/base/python.base/base/config/drive.json", "w") as jf:
            obj.update({"backup_hdd_device_signature": drive_dict})
            json.dump(obj, jf)

    def current_hdd_driveinfo(self) -> DriveInfo:
        relevant_devices = []
        for device in self._drive_inspector.devices:
            if device.path.startswith("/dev/sd"):
                relevant_devices.append(device)
        if len(relevant_devices) == 1:
            return relevant_devices[0]
        else:
            print(f"found ambigous or no devices. Aborting: relevant devices: {relevant_devices}")
            exit(0)


if __name__ == "__main__":
    bhs = BuHddSetter()
    bhs.set_conneted_hdd_as_backup_hdd()
