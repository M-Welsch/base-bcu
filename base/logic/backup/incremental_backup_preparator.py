import os
from datetime import datetime
from pathlib import Path
from re import findall
from subprocess import PIPE, Popen
from typing import Tuple

from base.common.config import Config
from base.common.exceptions import NewBuDirCreationError
from base.common.logger import LoggerFactory
from base.common.ssh_interface import SSHInterface
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.nas import Nas

LOG = LoggerFactory.get_logger(__name__)


class IncrementalBackupPreparator:
    def __init__(self, backup_browser):
        self._backup_browser = backup_browser
        self._config_nas = Config("nas.json")
        self._config_sync = Config("sync.json")
        self._new_backup_folder = None

    def prepare(self) -> Tuple[Path]:
        self._free_space_on_backup_hdd_if_necessary()
        backup_source = self._backup_source_directory()
        most_recent_backup = self._newest_backup_dir_path()
        backup_target = self._create_folder_for_backup()
        self._copy_newest_backup_with_hardlinks(most_recent_backup, backup_target)
        return backup_source, backup_target

    def _free_space_on_backup_hdd_if_necessary(self):
        while not self.enough_space_for_full_backup():
            self.delete_oldest_backup()

    def enough_space_for_full_backup(self) -> bool:
        free_space_on_bu_hdd = self._obtain_free_space_on_backup_hdd()
        space_needed_for_full_bu = self.space_occupied_by_backup_source_data()
        LOG.info(f"Space free on BU HDD: {free_space_on_bu_hdd}, Space needed: {space_needed_for_full_bu}")
        return free_space_on_bu_hdd > space_needed_for_full_bu

    def _obtain_free_space_on_backup_hdd(self) -> int:
        command = ["df", "--output=avail", self._config_sync.local_backup_target_location]
        LOG.info(f"obtaining free space on bu hdd with command: {command}")
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
            command = 'df --output="used" /mnt/HDD | tail -n 1'
            LOG.info(f"obtaining space occupied nas hdd with command: {command}")
            space_occupied = int(ssh.run_and_raise(command))
        return space_occupied

    def space_occupied_by_backup_source_data(self) -> int:
        path_on_nas = self._config_sync.remote_backup_source_location
        try:
            with SSHInterface() as ssh:
                ssh.connect(self._config_nas.ssh_host, self._config_nas.ssh_user)
                command = f"du {path_on_nas} -s"
                response = ssh.run_and_raise(command)
                LOG.info(f"obtaining space occupied nas hdd with command: {command}. Received {response}")
            space_occupied = int(findall("\d+", response)[0])
        except RuntimeError as e:
            if "No such file or directory" in str(e):
                LOG.warning("couldn't assess space needed for backup. Assuming it's 0 so the backup can go on!")
                space_occupied = 0
        except IndexError as e:
            LOG.warning("couldn't assess space needed for backup. Assuming it's 0 so the backup can go on!")
            space_occupied = 0
        return space_occupied

    def delete_oldest_backup(self):
        with self._backup_browser as bb:
            oldest_backup = bb.get_oldest_backup()
        LOG.info("deleting {} to free space for new backup".format(oldest_backup))

    def _newest_backup_dir_path(self) -> Path:
        with self._backup_browser as bb:
            return bb.get_newest_backup_abolutepath()

    def _create_folder_for_backup(self) -> Path:
        path = self._get_path_for_new_bu_directory()
        print(f"create new folder: {path}")
        self._create_that_very_directory(path)
        self._check_whether_directory_was_created(path)
        return path

    def _get_path_for_new_bu_directory(self) -> Path:
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        path = Path(Path(self._config_sync.local_backup_target_location) / f"backup_{timestamp}")
        return path

    def _create_that_very_directory(self, path):
        try:
            os.mkdir(path)
        except OSError:
            LOG.error(f"Could not create directory for new backup in {self._config_sync.local_backup_target_location}")

    def _check_whether_directory_was_created(self, path):
        if os.path.isdir(path):
            LOG.info(f"Created directory for new backup: {path}")
            self._new_backup_folder = path
        else:
            LOG.error(f"Directory {path} wasn't created!")
            raise NewBuDirCreationError

    def _copy_newest_backup_with_hardlinks(self, recent_backup, new_backup):
        copy_command = f"cp -al {recent_backup}/* {new_backup}"
        LOG.info(f"copy command: {copy_command}")
        p = Popen(copy_command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        # p.communicate(timeout=10)
        for line in p.stdout:
            LOG.debug(f"copying with hl: {line}")
        for line in p.stderr:
            LOG.warning(line)

    def _rename_bu_directory_to_new_timestamp(self):
        newest_existing_bu_dir = self._newest_backup_dir_path()
        new_backup_folder = self._get_path_for_new_bu_directory()
        os.rename(newest_existing_bu_dir, new_backup_folder)
        self._new_backup_folder = new_backup_folder

    def _backup_source_directory(self) -> Path:
        protocol = self._config_sync.protocol
        remote_backup_source_location = Path(self._config_sync.remote_backup_source_location)
        local_nas_hdd_mount_path = Path(self._config_sync.local_nas_hdd_mount_point)
        if protocol == "smb":
            source_directory = self._derive_backup_source_directory_smb(
                local_nas_hdd_mount_path, remote_backup_source_location
            )
        elif protocol == "ssh":
            source_directory = remote_backup_source_location
        else:
            LOG.error(f"{protocol} is not a valid protocoll! Defaulting to smb")
            source_directory = self._derive_backup_source_directory_smb(
                local_nas_hdd_mount_path, remote_backup_source_location
            )
        return Path(source_directory)

    @staticmethod
    def _derive_backup_source_directory_smb(local_nas_hdd_mount_path, remote_backup_source_location):
        source_mountpoint = Nas().mount_point(remote_backup_source_location)
        subfolder_on_mountpoint = remote_backup_source_location.relative_to(source_mountpoint)
        source_directory = local_nas_hdd_mount_path / subfolder_on_mountpoint
        return source_directory
