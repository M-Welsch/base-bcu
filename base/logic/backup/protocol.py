from __future__ import annotations

from enum import Enum

from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class Protocol(Enum):
    SSH = "ssh"
    NFS = "nfs"

    @classmethod
    def _missing_(cls, value: object) -> Protocol:
        LOG.error(f"{value} is not a valid protocol! Defaulting to SSH.")
        return Protocol.SSH
