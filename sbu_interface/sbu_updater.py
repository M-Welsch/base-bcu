import os, sys
import glob

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.common.utils import get_sbc_fw_uploads_folder, run_external_command_as_generator_2, run_external_command_string_input

class SbuUpdater():
	def __init__(self, hwctrl):
		self._hwctrl = hwctrl

	def update_sbu(self):
		self._hwctrl.enable_receiving_messages_from_attiny()
		self._hwctrl.set_attiny_serial_path_to_sbc_fw_update()

		sbc_fw_filename = self._get_filename_of_newest_hex_file()
		self._flash_hex_file_to_sbc(sbc_fw_filename)

		self._hwctrl.set_attiny_serial_path_to_communication()

	def _get_filename_of_newest_hex_file(self):
		list_of_sbc_fw_files = glob.glob("{}/*".format(get_sbc_fw_uploads_folder()))
		latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
		return latest_sbc_fw_file

	def _flash_hex_file_to_sbc(self, sbc_fw_filename):
		print("Updating SBC with {}".format(sbc_fw_filename))
		sbc_flash_command = 'sudo su - base -c "pyupdi -d tiny816 -c /dev/ttyS1 -f /home/base/test/sbc_fw_flashen/AtTiny816_Blink.hex"'
		# Fixme: use tty-port from config file
		sbc_flash_command = 'sudo su - base -c "pyupdi -d tiny816 -c /dev/ttyS1 -f {}"'.format(sbc_fw_filename)
		outcome = run_external_command_string_input(sbc_flash_command)
		print(outcome)

if __name__ == '__main__':

	from base.common.config import Config
	from base.common.base_logging import Logger
	from base.hwctrl.hwctrl import *

	_config = Config("/home/base/base/config.json")
	_logger = Logger("/home/base/base/log")
	_hardware_control = HWCTRL(_config.hwctrl_config, _logger)

	SBUU = SbuUpdater(_hardware_control)
	SBUU.update_sbu()

	_hardware_control.terminate()
	_logger.terminate()

