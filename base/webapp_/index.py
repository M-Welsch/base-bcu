from flask import Flask, redirect, url_for, render_template, request
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename
import socket
import os
import sys
import json
from threading import Thread
from time import sleep

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)
from base.common.tcp import TCPClientInterface, TCPClientThread
from base.common.utils import wait_for_new_device_file
from base.webapp_.logfile_viewer import *

application = Flask(__name__)
application.config['SBC_FW_FOLDER'] = "{}/sbu_interface/sbu_fw_uploads".format(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@application.route('/style.css')
def stylesheet():
	return render_template('style.css')


@application.route('/')
def mainpage():
	return render_template('mainpage.html', page_name='Welcome', user='admin')


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
		return render_template('editconfig.html', page_name='Edit Configuration', user='admin', data=config)


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


@application.route('/saveconfig', methods=['POST'])
def saveconfig():
	nd_dict = convert_to_nd_dict(request.form)
	print(nd_dict)
	with open('../config.json', 'w') as jf:
		json.dump(nd_dict, jf)

	return render_template('saveconfig.html', page_name='Save Configuration', user='admin', config_to_show=nd_dict)


def get_port():
	with open('../config.json', 'r') as jf:
		jobj = json.load(jf)
		port = jobj['Daemon']['dm_listens_to_port']
	return port


def get_signal_to_send(request):
	if request.method == "POST":
		data_from_form = request.form
		if (data_from_form['signal'] == 'sig_custom'):
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


@application.route('/communicator', methods=['POST', 'GET'])
def communicator():
	signal_to_send = get_signal_to_send(request)
	answer_string = ''
	codebook = get_codebook()
	[connection_success, answer_string] = send_tcp_message_to_daemon_and_return_answer_or_error(signal_to_send)
	if connection_success == True:
		return render_template('communicator.html',
							   page_name='Communicator',
							   user='admin',
							   recent_signal=signal_to_send,
							   answer=answer_string,
							   codebook=codebook)
	else:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_error


@application.route('/logfile_viewer', methods=['GET', 'POST'])
def logfile_viewer():
	CP = LogfileProcessor(request.form)
	available_logfiles = CP.available_logfiles
	logfile_content = CP.logfile_content
	logfile_selected = CP.logfile_selected

	# logfile_content.reverse() #to have most current line first

	return render_template('logfile_viewer.html',
						   page_name='Logger',
						   user='admin',
						   logfile=logfile_content,
						   filenames=available_logfiles,
						   logfile_selected=logfile_selected)

@application.route('/update_sbc_fw')
def update_sbc_fw():
	return render_template('update_sbc_fw.html',
						   page_name='Update SBC Firmware',
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

	return render_template('sbc_fw_uploaded_success_message_and_next_steps.html',
						   page_name='SBC Firmware Update Success Message',
						   user='admin')


def tell_daemon_about_new_sbc_fw(sbc_fw_filename):
	port = get_port()
	send_tcp_message_to_daemon_and_return_answer_or_error("update_sbc")


def send_tcp_message_to_daemon_and_return_answer_or_error(message):
	port = get_port()
	connection_trials = 0
	while connection_trials < 2:
		try:
			TCP_Client = TCPClientInterface(port=port)
			answer_string = TCP_Client.send(message)
			connection_success = True
			break
		except ConnectionRefusedError as e:
			port += 1
			answer_string = ''
			connection_success = e
		connection_trials += 1
	return [connection_success, answer_string]


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


@application.route('/setup_backup_hdd')
def setup_backup_hdd_step_1():
	return render_template("setup_backup_hdd_step_1.html",
						   page_name='Setup Backup HDD',
						   user='admin')


@application.route('/setup_backup_hdd_step_2')
def setup_backup_hdd_step_2():
	[connection_success, answer_string] = send_tcp_message_to_daemon_and_return_answer_or_error("test_docking")
	if not connection_success:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_success
	else:
		try:
			wait_for_new_device_file(2)
		except RuntimeError as e:
			# return str(e)
			pass
		hdd_parameters = request_hdd_parameters()
		save_hdd_params_to_temp_file(hdd_parameters,"/tmp/hdd_parameters_tmp")
		#return hdd_parameters
		return render_template("setup_backup_hdd_step_2.html",
							   page_name='Setup Backup HDD',
							   user='admin',
							   hdd_parameters = hdd_parameters)

def save_hdd_params_to_temp_file(hdd_parameters, filename):
	hdd_params_str = str(hdd_parameters).replace("'",'"')
	save_to_temporary_file(hdd_params_str, filename)


def save_to_temporary_file(content, filename):
	f = open(filename, "w")
	f.write(content)
	f.close()

def read_and_remove_temporary_file(filename):
	f = open(filename, "r")
	content = f.read()
	f.close()
	os.remove(filename)
	return content


@application.route('/setup_backup_hdd_step_3', methods=['POST'])
def setup_backup_hdd_step_3():
	if request.method == 'POST':
		data = request.form

	hdd_parameters_of_buhdd_to_use = get_mn_sn_from_sd_file(data["device_for_BUHDD"])
	save_hdd_params_to_temp_file(hdd_parameters_of_buhdd_to_use, "/tmp/hdd_parameters_of_buhdd_to_use") #fixme:file is not being created for some reason
	tell_daemon_to_use_new_buhdd()
	return render_template("setup_backup_hdd_step_3.html",
						   page_name='Setup Backup HDD',
						   user='admin',
						   hdd_parameters = hdd_parameters_of_buhdd_to_use)	

def tell_daemon_to_use_new_buhdd():
	[connection_success, answer_string] = send_tcp_message_to_daemon_and_return_answer_or_error("new_buhdd")
	if not connection_success:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_success


def get_mn_sn_from_sd_file(sd_file):
	try:
		hdd_params_str = read_and_remove_temporary_file("/tmp/hdd_parameters_tmp")
	except FileNotFoundError as e:
		return 'Temporary file "/tmp/hdd_parameters_tmp" could not be accessed: ' + str(e)
	hdd_params_dict = json.loads(hdd_params_str)
	return hdd_params_dict[sd_file]


@application.route('/test_hdd_parameter_display')
def test_hdd_parameter_display():
	mockup_answer_string = '{"sda": {"Model Number": "WDC WD20EFRX-68AX9N0", "Serial Number": "WD-WMC300945476", "device size with M = 1000*1000": "2000398 MBytes (2000 GB)"}, "sdb": {"Model Number": "something", "Serial Number": "something else", "device size with M = 1000*1000": "11520507389987 MBytes (11520507389 GB)"}}'
	hdd_parameters = json.loads(mockup_answer_string)
	return render_template("setup_backup_hdd_step_2.html",
					   page_name='Setup Backup HDD',
					   user='admin',
					   hdd_parameters = hdd_parameters)

def request_hdd_parameters() -> dict:
	[connection_success, hdd_parameters_raw] = send_tcp_message_to_daemon_and_return_answer_or_error("readout_hdd_parameters")
	hdd_parameters = json.loads(hdd_parameters_raw)
	return hdd_parameters

if __name__ == '__main__':
	application.run('0.0.0.0', debug=True)
