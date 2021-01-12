from datetime import datetime
from pathlib import Path
from subprocess import SubprocessError, TimeoutExpired
import logging
import json
from base.common.config import Config
from base.common.utils import run_external_command_as_generator_shell


LOG = logging.getLogger(Path(__file__).name)


def dump_ifconfig():
    logs_directory = Config("base.json").logs_directory
    filename = Path(logs_directory)/datetime.now().strftime('ifconfig_%Y-%m-%d_%H-%M-%S.log')
    command = f"ifconfig > {filename}"
    for line in run_external_command_as_generator_shell(command):
        print(line)
    LOG.debug(f'Dumped ifconfig into {filename}')


def copy_logfiles_to_nas():
    try:
        remote_user = "root"
        remote_host = "192.168.0.100"
        remote_directory = "/mnt/HDD/share/Max/BaSe_Logs/"
        command = f"scp -i /home/base/.ssh/id_rsa -o LogLevel=DEBUG3 {logs_directory}* " \
                  f"{remote_user}@{remote_host}:{remote_directory}"
        print(command)
        run_external_command_as_generator_shell(command, timeout=10)
        LOG.info(f"Copied Logfiles to NAS into: {remote_directory}")
    except TimeoutExpired:
        LOG.warning(f"Copying logfiles timed out! {TimeoutExpired}")
    except SubprocessError as e:
        LOG.warning(f"Copying Logfile wasn't sucessful (not due to timeout): {e}")
