from datetime import datetime
import logging
import os
from pathlib import Path
from subprocess import Popen, PIPE

from base.common.config import Config
from base.common.exceptions import NewBuDirCreationError
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.ssh_interface import SSHInterface


LOG = logging.getLogger(Path(__file__).name)


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
        LOG.info(f"Space free on BU HDD: {free_space_on_bu_hdd}, Space needed: {space_needed_for_full_bu}")
        return free_space_on_bu_hdd > space_needed_for_full_bu

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
        copy_command = f"cp -al {recent_backup}/* {new_backup}"
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
