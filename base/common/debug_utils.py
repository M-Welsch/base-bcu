from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, SubprocessError, TimeoutExpired
from typing import IO

from base.common.config import get_config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


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
