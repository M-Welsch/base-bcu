class TCP_Codebook():
	commands_awaiting_response = ["readout_hdd_parameters"]

#class WebApp_Daemon_Codebook():

class SBC_Codebook():
	command_prefixes = {"Display Write String":"DS:",
						"Display Dim":"DD:",
						"LED Dim":"LD",
						"Current Consumption":"CC"
						}
	commands = {"Shutdown Request":"SR"}