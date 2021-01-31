import logging
from pathlib import Path
from subprocess import Popen, PIPE
from datetime import datetime
import os

from signalslot import Signal
from typing import List

from base.logic.sync import RsyncWrapperThread
from base.logic.network_share import NetworkShare
from base.logic.nas import Nas
from base.common.config import Config
from base.common.exceptions import NetworkError, DockingError, NewBuDirCreationError, BackupHddAccessError
from base.logic.ssh_interface import SSHInterface


LOG = logging.getLogger(Path(__file__).name)

class WeatherFrog:
    def allright(self):
        LOG.debug("WeatherFrog agrees")
        return True


class Backup:
    postpone_request = Signal(args=['seconds'])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()
    reschedule_request = Signal()
    shutdown_request = Signal()

    def __init__(self, is_maintenance_mode_on):
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._sync = None
        self._config = Config("backup.json")
        self._postpone_count = 0
        self._nas = Nas()

    @property
    def backup_conditions_met(self):
        return (
                not self._is_maintenance_mode_on() and
                (self._sync is None or not self._sync.running) and
                WeatherFrog().allright()
        )

    def on_backup_request(self, **kwargs):
        LOG.debug("Received backup request...")
        try:
            if self.backup_conditions_met:
                LOG.debug("...and backup conditions are met!")
                self._run_backup_sequence()
            else:
                LOG.debug("...but backup conditions are not met.")
        except NetworkError as e:
            LOG.error(e)
        except DockingError as e:
            LOG.error(e)

    def on_backup_finished(self, **kwargs):
        LOG.info("Backup terminated")
        try:
            self._return_to_default_state()
        except DockingError as e:
            LOG.error(e)
        except NetworkError as e:
            LOG.error(e)
        finally:
            self.reschedule_request.emit()
            if self._config.shutdown_between_backups:
                self.shutdown_request.emit()

    def _run_backup_sequence(self):
        LOG.debug("Running backup sequence")
        if Config("sync.json").protocol == "smb":
            LOG.debug("Mounting data source via smb")
            self._nas.smb_backup_mode()
            NetworkShare().mount_datasource_via_smb()
        else:
            LOG.debug("Don't do backup via smb")
        self._nas.stop_services()
        self.hardware_engage_request.emit()
        new_backup_directory = IncrementalBackupPreparator().prepare()
        LOG.info(f"Backing up into: {new_backup_directory}")
        self._sync = RsyncWrapperThread(new_backup_directory)
        self._sync.start()

    def _return_to_default_state(self):
        self.hardware_disengage_request.emit()
        self._nas.resume_services()
        if Config("sync.json").protocol == "smb":
            NetworkShare().unmount_datasource_via_smb()
            self._nas.smb_normal_mode()


class IncrementalBackupPreparator:
    def __init__(self):
        self._config_nas = Config("nas.json")
        self._config_sync = Config("sync.json")
        self._new_backup_folder = None

    def prepare(self) -> Path:
        self._free_space_on_backup_hdd_if_necessary()
        return self._create_folder_for_backup()

    def _free_space_on_backup_hdd_if_necessary(self):
        while not self.enough_space_for_full_backup():
            self.delete_oldest_backup()

    def enough_space_for_full_backup(self) -> bool:
        free_space_on_bu_hdd = self._obtain_free_space_on_backup_hdd()
        space_needed_for_full_bu = self.space_occupied_on_nas_hdd()
        LOG.info("Space free on BU HDD: {}, Space needed: {}".format(free_space_on_bu_hdd, space_needed_for_full_bu))
        return free_space_on_bu_hdd < space_needed_for_full_bu

    def _obtain_free_space_on_backup_hdd(self) -> int:
        command = (["df", "--output=avail", self._config_sync.local_backup_target_location])
        out = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        free_space_on_bu_hdd = self._remove_heading_from_df_output(out.stdout)
        return free_space_on_bu_hdd

    def _remove_heading_from_df_output(self, df_output) -> int:
        df_output_cleaned = ""
        for line in df_output:
            if not line.strip() == "Avail":
                df_output_cleaned = int(line.strip())
        return int(df_output_cleaned)

    def space_occupied_on_nas_hdd(self) -> int:
        with SSHInterface() as ssh:
            ssh.connect(self._config_nas.ssh_host, self._config_nas.ssh_user)
            space_occupied = int(ssh.run_and_raise('df --output="used" /mnt/HDD | tail -n 1'))
        return space_occupied

    def delete_oldest_backup(self):
        with BackupBrowser() as bb:
            oldest_backup = bb.get_oldest_backup()
        LOG.info("deleting {} to free space for new backup".format(oldest_backup))

    def _newest_backup_dir_path(self) -> Path:
        with BackupBrowser() as bb:
            return bb.get_newest_backup_abolutepath()

    def _create_folder_for_backup(self) -> Path:
        path = self._get_path_for_new_bu_directory()
        print(f"create new folder: {path}")
        self._create_that_very_directory(path)
        self._check_whether_directory_was_created(path)
        return path

    def _get_path_for_new_bu_directory(self) -> Path:
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        path = Path(Path(self._config_sync.local_backup_target_location)/f"backup_{timestamp}")
        return path

    def _create_that_very_directory(self, path):
        try:
            os.mkdir(path)
        except OSError:
            LOG.error(
                f'Could not create directory for new backup in {self._config_sync.local_backup_target_location}')

    def _check_whether_directory_was_created(self, path):
        if os.path.isdir(path):
            LOG.info(f'Created directory for new backup: {path}')
            self._new_backup_folder = path
        else:
            LOG.error(f"Directory {path} wasn't created!")
            raise NewBuDirCreationError

    def _copy_newest_backup_with_hardlinks(self, recent_backup, new_backup):
        recent_backup = self.check_path_end_slash_and_asterisk(recent_backup)
        copy_command = f"cp -al {recent_backup} {new_backup}"
        print(f"copy command: {copy_command}")
        p = Popen(copy_command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        # p.communicate(timeout=10)
        for line in p.stdout:
            print(f"copying with hl: {line}")
        for line in p.stderr:
            print(line)

    def _rename_bu_directory_to_new_timestamp(self):
        newest_existing_bu_dir = self._newest_backup_dir_path()
        new_backup_folder = self._get_path_for_new_bu_directory()
        os.rename(newest_existing_bu_dir, new_backup_folder)
        self._new_backup_folder = new_backup_folder

    @staticmethod
    def check_path_end_slash_and_asterisk(path_to_check):
        # Todo: check if this function is still necessary
        path_to_check = str(path_to_check)
        if path_to_check.endswith('/*'):
            pass
        elif path_to_check.endswith('/'):
            path_to_check += '*'
        else:
            path_to_check += '/*'
        return path_to_check


class BackupBrowser:
    def __init__(self):
        self._config_sync = Config("sync.json")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def list_backups_by_age(self) -> List[Path]:
        # lowest index is the oldest
        list_of_backups = []
        try:
            for file in os.listdir(self._config_sync.local_backup_target_location):
                if file.startswith("backup"):
                    list_of_backups.append(file)
        except OSError as e:
            LOG.error(f"BackupHDD cannot be accessed! {e}")
            raise BackupHddAccessError
        list_of_backups.sort()
        backup_paths = []
        for bu in list_of_backups:
            backup_paths.append(Path(bu))
        return backup_paths

    def get_oldest_backup(self) -> Path:
        backups = self.list_backups_by_age()
        if backups:
            return backups[0]

    def get_newest_backup_abolutepath(self) -> Path:
        backups = self.list_backups_by_age()
        if backups:
            return Path(Path(self._config_sync.local_backup_target_location)/backups[-1])

    @staticmethod
    def get_backup_size(path) -> int:
        p = Popen(f"du -s {path}".split(), stdout=PIPE, stderr=PIPE)
        try:
            size = p.stdout.readlines()[0].decode().split()[0]
        except ValueError as e:
            LOG.error(f"cannot check size of directory: {path}. Python says: {e}")
            size = 0
        return int(size)
