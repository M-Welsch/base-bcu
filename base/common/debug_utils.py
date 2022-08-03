from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, SubprocessError, TimeoutExpired, check_output
from typing import IO, List

from base.common.config import get_config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


@dataclass
class RepositoryInfo:
    hash: str
    branch: str
    last_commit_date: str
    status: str


class BcuRevision:
    def log_repository_info(self) -> None:
        repo = self.get_repository_info()
        LOG.info("Repository Info:")
        LOG.info(f"  Commit: {repo.hash}")
        LOG.info(f"  Branch: {repo.branch}")
        LOG.info(f"  Date:   {repo.last_commit_date}")
        LOG.info(f"  Status: {repo.status}")

    def get_repository_info(self) -> RepositoryInfo:
        return RepositoryInfo(
            hash=self._parse_information(["git", "rev-parse", "HEAD"]),
            branch=self._parse_information(["git", "branch", "--show-current"]),
            last_commit_date=self._parse_information(["git", "log", "-n", "1", "--pretty=format:%ad"]),
            status=self._repo_status(),
        )

    @staticmethod
    def _parse_information(command: List[str]) -> str:
        try:
            return_value = check_output(command).decode().strip()
        except Exception:
            LOG.warning(f"cannot determine repo info with {' '.join(command)}")
            return_value = "not available"
        return return_value

    @staticmethod
    def _repo_status() -> str:
        command = ["git", "status", "-s", "--untracked-files=no"]
        try:
            dirty = bool(check_output(command).decode())
            status = "dirty" if dirty else "clean"
        except Exception:
            LOG.warning(f"cannot determine repo status with {' '.join(command)}")
            status = "unknown"
        return status


def dump_ifconfig() -> None:
    logs_directory = get_config("base.json").logs_directory
    filename = Path(logs_directory) / datetime.now().strftime("ifconfig_%Y-%m-%d_%H-%M-%S.log")
    command = f"ifconfig > {filename}"
    for line in _run_external_command_as_generator_shell(command):
        print(line)
    LOG.debug(f"Dumped ifconfig into {filename}")


def copy_logfiles_to_nas() -> None:
    try:
        config_debug = get_config("debug.json")
        local_log_directory = Path("/home/base") / Path(get_config("base.json").logs_directory)
        command = (
            f'rsync -avH -e "ssh -i /home/base/.ssh/id_rsa" {local_log_directory}/* '
            f"{config_debug.ssh_user}@{config_debug.ssh_host}:{config_debug.logfile_target_path}"
        )
        LOG.info(f"Copying logfiles to Nas with command {command}")
        _run_external_command_as_generator_shell(command, timeout=10)
        LOG.info(f"Copied Logfiles to NAS into: {config_debug.logfile_target_path}")
    except TimeoutExpired as e:
        LOG.warning(f"Copying logfiles timed out! {e}")
    except SubprocessError as e:
        LOG.warning(f"Copying Logfile wasn't successful (not due to timeout): {e}")
    except Exception as e:
        LOG.warning(f"some unexpected error happened during copying the logfiles to nas: {e}")


def _run_external_command_as_generator_shell(command: str, timeout: int = None) -> IO[str]:
    p = Popen(command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=STDOUT)
    if timeout:
        p.communicate(timeout=timeout)
    assert p.stdout is not None
    return p.stdout
