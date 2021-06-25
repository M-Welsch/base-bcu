from pathlib import Path
from typing import List

from base.common.logger import LoggerFactory
from base.common.config import Config

LOG = LoggerFactory.get_logger(__name__)


def list_logfiles(newest_first: bool) -> List[str]:
    cfg_path = Path("/home/base/python.base/base/config/")
    logs_dir = LoggerFactory.get_logs_directory(cfg_path)
    logfiles = [file.stem for file in logs_dir.glob("**/*") if file.is_file() and not file.stem == "warnings"]
    if newest_first:
        logfiles.sort(reverse=True)
    else:
        logfiles.sort(reverse=False)
    return logfiles


def logfile_content(logfile_name: str, recent_line_first: bool) -> List[str]:
    cfg_path = Path("/home/base/python.base/base/config/")
    logs_dir = LoggerFactory.get_logs_directory(cfg_path)
    logfile = logs_dir / f"{logfile_name}.log"
    with open(logfile, "r") as f:
        content = f.readlines()
    if recent_line_first:
        content.sort(reverse=True)
    return content
