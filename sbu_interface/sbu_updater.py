import os, sys
import glob

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.common.utils import get_sbc_fw_uploads_folder, run_external_command_as_generator_2, run_external_command_string_input

class SbuUpdater():
	def __init__(self):
		pass

	def update_sbc(self):
		sbc_fw_filename = self._get_filename_of_newest_hex_file()
		self._flash_hex_file_to_sbc(sbc_fw_filename)

	def _get_filename_of_newest_hex_file(self):
		list_of_sbc_fw_files = glob.glob("{}/*".format(get_sbc_fw_uploads_folder()))
		latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
		return latest_sbc_fw_file

	def _flash_hex_file_to_sbc(self, sbc_fw_filename):
		print("Updating SBC with {}".format(sbc_fw_filename))
		sbc_flash_command = 'sudo su - max -c "pyupdi.py -d tiny816 -c /dev/ttyS1 -f /home/maxi/test/sbc_fw_flashen/AtTiny816_Blink.hex"'
		sbc_flash_command = 'sudo su - max -c "pyupdi.py -d tiny816 -c /dev/ttyS1 -f {}"'.format(sbc_fw_filename)
		outcome = run_external_command_string_input(sbc_flash_command)
		print(outcome)

if __name__ == '__main__':

	from base.common.config import Config
	from base.common.base_logging import Logger
	from base.hwctrl.hwctrl import *

	_config = Config("/home/maxi/base/config.json")
	_logger = Logger("/home/maxi/base/log")
	_hardware_control = HWCTRL(_config.hwctrl_config, _logger)
	_hardware_control.enable_receiving_messages_from_attiny()
	_hardware_control.set_attiny_serial_path_to_sbc_fw_update()

	SBUU = SbuUpdater()
	SBUU.update_sbc()

	_hardware_control.disable_receiving_messages_from_attiny()
	_hardware_control.set_attiny_serial_path_to_communication()
	_hardware_control.terminate()
	_logger.terminate()

