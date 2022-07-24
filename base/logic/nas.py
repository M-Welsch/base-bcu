from configparser import ConfigParser, ParsingError
from pathlib import Path

from base.common.config import get_config
from base.common.exceptions import NasSmbConfError, RemoteCommandError
from base.common.ssh_interface import SSHInterface


class Nas:
    def __init__(self) -> None:
        self._config = get_config("nas.json")

    def reachable(self) -> bool:
        reachable = True
        try:
            with SSHInterface() as sshi:
                sshi.connect(self._config.ssh_host, self._config.ssh_user)
        except RemoteCommandError:
            reachable = False
        return reachable

    def root_of_share(self, share_name: str = "Backup") -> Path:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            smb_conf = self._get_smb_conf(sshi)
            return self._extract_root_of_share(smb_conf, share_name)

    def _get_smb_conf(self, sshi: SSHInterface) -> ConfigParser:
        try:
            smb_conf_str = sshi.run_and_raise(f"cat /etc/samba/smb.conf")
        except RuntimeError as e:
            raise NasSmbConfError from e

        return self._get_parser_from_smb_conf(smb_conf_str)

    @staticmethod
    def _get_parser_from_smb_conf(smb_conf_str: str) -> ConfigParser:
        parser = ConfigParser()
        try:
            parser.read_string(smb_conf_str)
        except ParsingError as e:
            raise NasSmbConfError("your Nas's /etc/samba/smb.conf is invalid") from e
        return parser

    @staticmethod
    def _extract_root_of_share(smb_conf: ConfigParser, share_name: str) -> Path:
        try:
            return Path(smb_conf[share_name]["path"])
        except KeyError as e:
            raise NasSmbConfError("/etc/samba/smb.conf on NAS does not seem to exist. Is samba installed?") from e
