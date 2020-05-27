import os
import glob
from base.common.utils import get_sbc_fw_uploads_folder, run_external_command_as_generator_2, run_external_command_string_input

class SBC_Updater():
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
		# sbc_flash_command = ['su','-','max','-c','pyupdi.py -d tiny816 -c /dev/ttyS1 -f {}'.format(sbc_fw_filename)]
		sbc_flash_command = 'sudo su - max -c "pyupdi.py -d tiny816 -c /dev/ttyS1 -f {}"'.format(sbc_fw_filename)
		outcome = run_external_command_string_input(sbc_flash_command)
		print(outcome)
