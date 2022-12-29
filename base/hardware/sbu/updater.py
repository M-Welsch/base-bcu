import asyncio
import os
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Optional

from base.common.logger import LoggerFactory
from base.hardware.drivers.pin_interface import pin_interface
from base.hardware.sbu.uart_finder import get_sbu_uart_interface

LOG = LoggerFactory.get_logger(__name__)


class SbuUpdater:
    _serial_connection_delay_seconds: float = 4e-8
    # Todo: cleanup

    async def update(self, sbu_fw_filename: Optional[Path] = None) -> None:
        await pin_interface.connect_serial_update_path()
        sbu_uart_channel = await self._get_sbu_uart_channel()
        if sbu_uart_channel is None:
            LOG.warning("SBU didn't respond on any UART Interface. Defaulting to /dev/ttyS1")
            sbu_uart_channel = Path("/dev/ttyS1")
        pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        if sbu_fw_filename is None:
            sbu_fw_filename = self._get_filename_of_newest_hex_file()
            LOG.info(f"updating sbu with file: {sbu_fw_filename}")
        self._execute_sbu_update(sbu_fw_filename, sbu_uart_channel)

    @staticmethod
    def _execute_sbu_update(sbu_fw_filename: Path, sbu_uart_channel: Path) -> None:
        sbu_update_command = f"pyupdi -d tiny816 -c {sbu_uart_channel} -f {sbu_fw_filename}"
        try:
            process = Popen(
                sbu_update_command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE
            )
            if process.stdout is not None:
                for line in process.stdout:
                    LOG.info(str(line))
            if process.stderr is not None:
                if process.stderr:
                    LOG.error(str(process.stderr.readlines()))
        finally:
            pin_interface.set_sbu_serial_path_to_communication()

    @staticmethod
    async def _get_sbu_uart_channel() -> Path:
        sbu_uart_channel = await get_sbu_uart_interface()
        if not sbu_uart_channel:
            sbu_uart_channel = Path("/dev/ttyS1")
        return sbu_uart_channel

    @staticmethod
    def _get_filename_of_newest_hex_file() -> Path:
        list_of_sbc_fw_files = Path("/home/base/base-bcu/sbu_fw_files/").glob("*")
        latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
        return latest_sbc_fw_file

    async def connect_serial_update_path(self) -> None:
        pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        pin_interface.enable_receiving_messages_from_sbu()
        # t_on / t_off max of ADG734 (ensures signal switchover)
        await asyncio.sleep(self._serial_connection_delay_seconds)
