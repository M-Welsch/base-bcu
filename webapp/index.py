from flask import Flask, redirect, url_for, render_template, request
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename
import socket
import os
import sys
import json
from threading import Thread
from time import sleep
#import pudb

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)
from base.common.tcp import TCPClientInterface

application = Flask(__name__)
application.config['SBC_FW_FOLDER'] = "{}/sbc_interface/sbc_fw_uploads".format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@application.route('/style.css')
def stylesheet():
	return render_template('style.css')

@application.route('/')
def mainpage():
	return render_template('mainpage.html', page_name = 'Welcome', user = 'admin')

@application.route('/shutdown')
def shutdown_webapp():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()

@application.route('/shutdown', methods=['POST'])
def shutdown():
	shutdown_webapp()
	return 'Server shutting down...'

@application.route('/editconfig')
def editconfig():
	# load and parse config file
	with open('../config.json', 'r') as jf:
		config = json.load(jf)
		return render_template('editconfig.html', page_name = 'Edit Configuration', user = 'admin', data=config)

def convert_to_nd_dict(d):
	# TODO: implement:
	# split keys at dots and convert flat dict to multi-dimensional dict
	# Example:
	# {"asdf.jklö.qwertz": 1234} to {"asdf":{"jklö":{"qwertz":1234}}}
	nd_dict = {}
	for key, value in d.items():
		print(key)
		# implemented for 2 dimensions. n-Dimensional tbd
		section, element_sp = key.split('.')

		# create key for section if nonexistent
		if not section in nd_dict:
			nd_dict[section] = {}

		nd_dict[section][element_sp] = value

	return nd_dict

@application.route('/saveconfig', methods = ['POST'])
def saveconfig():
	nd_dict = convert_to_nd_dict(request.form)
	print(nd_dict)
	with open('../config.json', 'w') as jf:
		json.dump(nd_dict, jf)

	return render_template('saveconfig.html', page_name = 'Save Configuration', user = 'admin', config_to_show = nd_dict)

def get_port():
	with open('../config.json', 'r') as jf:
		jobj = json.load(jf)
		port = jobj['Daemon']['dm_listens_to_port']
	return port	

def get_signal_to_send(request):
	if request.method == "POST":
		data_from_form = request.form
		if(data_from_form['signal'] == 'sig_custom'):
			signal_to_send = data_from_form['custom_signal_name']
		else:
			signal_to_send = data_from_form['signal']
	else:
		signal_to_send = "Hello Daemon"

	return signal_to_send

def get_codebook():
	with open('../config.json', 'r') as jf:
		jobj = json.load(jf)
		codebook = jobj['Webapp']['TCP_Codebook']
		jf.close()
	return codebook

@application.route('/communicator', methods = ['POST', 'GET'])
def communicator_old():
	answer_string = ''
	signal_to_send = get_signal_to_send(request)
	connection_to_daemon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	codebook = get_codebook()

	host = socket.gethostname()
	port = get_port()
	connection_trials = 0
	while connection_trials < 2:
		try:
			connection_error = connection_to_daemon.connect((host,port)) 
			break
		except Exception as e:
			print("Connection error: %r" % e)
			connection_error = e
			port += 1
			connection_trials += 1

	if connection_error == None:
		print("Signal_to_send before overwrite: %r" % signal_to_send)
		connection_to_daemon.send(signal_to_send.encode("utf8"))
		answer_bytes = connection_to_daemon.recv(1024)
		print("Answer Bytes = %r" % answer_bytes)
		answer_string = answer_bytes.decode("utf8")
		print("Answer String = %s" % answer_string)	
		connection_to_daemon.close()
		# FIXME: blocks the webapp

		return render_template('communicator.html', 
								page_name ='Communicator', 
								user='admin', 
								recent_signal = signal_to_send, 
								answer = answer_string, 
								codebook = codebook)
	else:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_error

@application.route('/communicator_rev2', methods = ['POST', 'GET'])

def communicator():
	signal_to_send = get_signal_to_send(request)
	answer_string = ''
	codebook = get_codebook()
	connection_success = send_tcp_message_to_daemon_or_return_error(signal_to_send)
	if connection_success:
		return render_template('communicator.html', 
								page_name ='Communicator', 
								user='admin', 
								recent_signal = signal_to_send, 
								answer = answer_string, 
								codebook = codebook)
	else:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_error 


@application.route('/logger', methods = ['GET', 'POST'])
def logger():
	available_logs = []
	# pudb.set_trace()
	for file in os.listdir("../log"):
		if file.endswith(".log"):
			#available_logs.append(file.split('.')[0].split('_')[1])
			available_logs.append(file)
	try:
		form_data = request.form
		filename_selected = form_data['filename']
	except:
		filename_selected = available_logs[0]

	logfile = open('../log/%s' % filename_selected,'r')
	logfile_content = ''
	logfile_content = logfile.readlines()
	#logfile_content.reverse() #to have most current line first
	log = []
	for line in logfile_content:
		if "could not" in line:
			line = '<font color="red">'+line+'</font>'
		if "closed" in line or "opened" in line:
			line = '<font color="blue">'+line+'</font>'
		log.append(line)

	return render_template('logger.html', 
							page_name ='Logger', 
							user='admin', 
							logfile = log, 
							filenames = available_logs, 
							filename_selected = filename_selected)

@application.route('/update_sbc_fw')
def update_sbc_fw():
	return render_template('update_sbc_fw.html',
						    page_name = 'Update SBC Firmware',
						    user='admin')

@application.route('/upload_and_flash_fw_to_sbc', methods=['POST'])
def upload_and_flash_fw_to_sbc():
	try:
		sbc_fw_file = get_sbc_fw_file_from_request(request)
		check_sbc_fw_filename(sbc_fw_file.filename)
	except ValueError as e:
		return e
	sbc_fw_filename = secure_filename(sbc_fw_file.filename)
	sbc_fw_file.save(os.path.join(application.config['SBC_FW_FOLDER'], sbc_fw_filename))
	tell_daemon_about_new_sbc_fw(sbc_fw_filename)
	# now the daemon must change the owner according to whoever needs the file
	# todo: the daemon needs the information where the file is located
	# todo: the daemon needs to flash the hex-file to the attiny816

	return "File sucessfully uploaded"

def tell_daemon_about_new_sbc_fw(sbc_fw_filename):
	port = get_port()
	send_tcp_message_to_daemon_or_return_error("update_sbc")

def send_tcp_message_to_daemon_or_return_error(message):
	port = get_port()
	connection_trials = 0
	while connection_trials < 2:
		try:
			TCP_Client = TCPClientInterface(port = port)
			answer_string = TCP_Client.send(message)
			connection_success = True
			break
		except ConnectionRefusedError as e:
			port += 1
			connection_success = e
		connection_trials += 1
	return connection_success

def get_sbc_fw_file_from_request(request):
	if request.method == 'POST':
		if 'sbc_fw_file' not in request.files:
			raise ValueError('no sbc fw file uploaded') 
		return request.files['sbc_fw_file']

def check_sbc_fw_filename(sbc_fw_filename):
	if sbc_fw_filename.rsplit('.')[1] == 'hex':
		return True
	else:
		raise ValueError('uploaded file is no hex-file')

if __name__ == '__main__':
   application.run('0.0.0.0', debug=True)
