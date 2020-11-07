from os import path
from time import sleep
import logging

from base.common.utils import wait_for_device_file, run_external_command
from base.common.exceptions import *


class MountManager:
    def __init__(self, config):
        self.b_hdd_device = config["backup_hdd_device_file_path"]
        self.b_hdd_fsys = config["backup_hdd_file_system"]  # Fixme: this file has to be identified
        self.b_hdd_mount = config["backup_hdd_mount_point"]
        self.b_timeout = config["backup_device_file_timeout"]

    def mount_hdd(self):
        print("mount_hdd:", self._backup_hdd_mounted(), self._backup_hdd_available())
        if not self._backup_hdd_mounted() and self._backup_hdd_available():
            self._mount_backup_hdd()

    def unmount_hdd(self):
        if self._backup_hdd_mounted():  # TODO: Don't ask for permission!
            try:
                self._unmount_backup_hdd()
            except UnmountError:
                logging.error(f"Unmounting didnt work: {UnmountError}")
            except RuntimeError:
                logging.error(f"Unmounting didnt work: {RuntimeError}")

    def _backup_hdd_mounted(self):
        return path.ismount(self.b_hdd_mount)

    def _backup_hdd_available(self):
        try:
            wait_for_device_file(self.b_hdd_device, self.b_timeout)
            # TODO: Ensure that the right HDD is found. (identifier-file?)
            return True
        except RuntimeError as e:
            logging.error(e)
            return False

    def _mount_backup_hdd(self):
        print("_mount_backup_hdd: Trying to mount backup HDD...")
        command = ["mount", "-t", self.b_hdd_fsys,
                   self.b_hdd_device, self.b_hdd_mount]
        success_msg = "Mounting backup HDD probably successful."
        error_msg = "Failed mounting backup HDD. Traceback:"
        try:
            run_external_command(command, success_msg, error_msg)
        except ExternalCommandError:
            raise MountingError(f"Backup HDD could not be mounted")

    def _unmount_backup_hdd(self):
        print("Trying to unmount backup HDD...")
        command = ["sudo", "umount", self.b_hdd_mount]
        success_msg = "Unmounting backup HDD probably successful."
        error_msg = "Failed unmounting backup HDD. Traceback:"
        unmount_trials = 0
        unmount_success = False
        while unmount_trials < 5 and not unmount_success:
            try:
                run_external_command(command, success_msg, error_msg)
                unmount_success = True
            except ExternalCommandError as e:
                if "not mounted" in str(e):
                    print("BackupHDD already unmounted")
                    logging.warning(f"BackupHDD already unmounted. stderr: {e}")
                    unmount_success = True
                # Todo: find out who accesses the drive right now and write into logfile (with lsof?)
                sleep(1)
                unmount_trials += 1
                if unmount_trials == 5:
                    logging.warning(f"Couldn't unmount BackupHDD within 5 trials. Error: {e}")
                    if "target is busy" in str(e):
                        raise UnmountError(e)
                    else:
                        raise RuntimeError
