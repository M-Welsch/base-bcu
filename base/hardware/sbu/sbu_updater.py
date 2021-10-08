import os
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Optional

from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface
from base.hardware.sbu.sbu_uart_finder import SbuUartFinder

LOG = LoggerFactory.get_logger(__name__)


class SbuUpdater:
    # Todo: cleanup
    def __init__(self) -> None:
        self._pin_interface: PinInterface = PinInterface.global_instance()

    def prepare_update(self) -> None:
        self._pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        self._pin_interface.enable_receiving_messages_from_sbu()

    def update(self, sbu_fw_filename: Optional[Path] = None) -> None:
        self.prepare_update()
        sbu_uart_channel = self._get_sbu_uart_channel()
        if sbu_uart_channel is None:
            LOG.warning("SBU didn't respond on any UART Interface. Defaulting to /dev/ttyS1")
            sbu_uart_channel = Path("/dev/ttyS1")
        self._pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        if sbu_fw_filename is None:
            sbu_fw_filename = self._get_filename_of_newest_hex_file()
            LOG.info(f"updating sbu with file: {sbu_fw_filename}")
        self._execute_sbu_update(sbu_fw_filename, sbu_uart_channel)

    def _execute_sbu_update(self, sbu_fw_filename: Path, sbu_uart_channel: Path) -> None:
        sbu_update_command = f'sudo su - base -c "pyupdi -d tiny816 -c {sbu_uart_channel} -f {sbu_fw_filename}"'
        try:
            process = Popen(
                sbu_update_command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE
            )
            if process.stdout is not None:
                for line in process.stdout:
                    LOG.info(str(line))
            if process.stderr is not None:
                if process.stderr:
                    LOG.error(str(process.stderr))
        finally:
            self._pin_interface.set_sbu_serial_path_to_communication()

    @staticmethod
    def _get_sbu_uart_channel() -> Path:
        sbu_uart_channel = SbuUartFinder().get_sbu_uart_interface()
        if not sbu_uart_channel:
            sbu_uart_channel = Path("/dev/ttyS1")
        return sbu_uart_channel

    @staticmethod
    def _get_filename_of_newest_hex_file() -> Path:
        list_of_sbc_fw_files = Path("/home/base/python.base/sbu_fw_files/").glob("*")
        latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
        return latest_sbc_fw_file
