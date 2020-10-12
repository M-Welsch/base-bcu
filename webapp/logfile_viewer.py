import os

class LogfileProcessor():
	def __init__(self, form_data):
		self._form_data = form_data
		self._available_logfiles = []
		self._prepare_logfile_data()

	def _prepare_logfile_data(self):
		self._get_available_logfiles()
		self._logfile_selected = self._get_logfile_name_from_form()
		logfile_content = self._get_logfile_content()
		self._logfile_content = self._beautify_logfile_content(logfile_content)

	@property
	def logfile_content(self):
		return self._logfile_content

	@property
	def available_logfiles(self):
		return self._available_logfiles

	@property
	def logfile_selected(self):
		return self._logfile_selected

	def _get_available_logfiles(self):
		available_logs = []
		for file in os.listdir("../log"):
			if file.endswith(".log"):
				available_logs.append(file)
		self._available_logfiles = available_logs

	def _get_logfile_name_from_form(self):
		try:
			logfile_selected = self._form_data['filename']
		except:
			logfile_selected = self._available_logfiles[0]
		return logfile_selected

	def _get_logfile_content(self):
		logfile = open('../log/%s' % self._logfile_selected, 'r')
		logfile_content = ''
		logfile_content = logfile.readlines()
		logfile.close()
		return logfile_content

	def _beautify_logfile_content(self, logfile_content):
		log = []
		for line in logfile_content:
			if "ERROR" in line:
				line = color_line(line, "red")
			if "WARNING" in line:
				line = color_line(line, "orange")
			if "closed" in line or "opened" in line:
				line = color_line(line, "green")
			log.append(line)
		return log

def color_line(line, color):
	if color in ["red", "blue", "green", "orange", "yellow"]:
		line = '<font color="'+ color + '">' + line + '</font>'
	return line

