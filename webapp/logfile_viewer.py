from flask import Blueprint, render_template

logfile_viewer = Blueprint('logfile_viewer', __name__)

@logfile_viewer.route('/logfile_viewer', methods=['GET', 'POST'])
def logfile_viewer():
	available_logs = []
	# pudb.set_trace()
	for file in os.listdir("../log"):
		if file.endswith(".log"):
			# available_logs.append(file.split('.')[0].split('_')[1])
			available_logs.append(file)
	try:
		form_data = request.form
		filename_selected = form_data['filename']
	except:
		filename_selected = available_logs[0]

	logfile = open('../log/%s' % filename_selected, 'r')
	logfile_content = ''
	logfile_content = logfile.readlines()
	# logfile_content.reverse() #to have most current line first
	log = []
	for line in logfile_content:
		if "could not" in line:
			line = '<font color="red">' + line + '</font>'
		if "closed" in line or "opened" in line:
			line = '<font color="blue">' + line + '</font>'
		log.append(line)

	return render_template('logfile_viewer.html',
						   page_name='Logger',
						   user='admin',
						   logfile=log,
						   filenames=available_logs,
						   filename_selected=filename_selected)


