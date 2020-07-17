class SystemdManager:
	def __init__(self):
		pass
		
	def is_active(self, service):
		print("Systemd Mockup: pretending to check activeness of {}".format(service))
		
	def start_unit(self, service):
		print("Systemd Mockup: pretending to start {}".format(service))	
	
	def stop_unit(self, service):
		print("Systemd Mockup: pretending to stop {}".format(service))

