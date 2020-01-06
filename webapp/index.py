from flask import Flask, redirect, url_for, render_template, request
from werkzeug.serving import make_server
import socket
import os
import json
from threading import Thread
from time import sleep

class Webapp(Thread):
	def __init__(self, application):
		super(Webapp, self).__init__() #<- test if this works
		self.srv = make_server('0.0.0.0', 5000, application)
		self.ctx = application.app_context()
		self.ctx.push()

	def run(self):
		# Todo: good point to put a message into the logfile
		self.srv.serve_forever()

	def terminate(self):
		self.srv.shutdown()

application = Flask(__name__)

@application.route('/style.css')
def stylesheet():
	return render_template('style.css')

@application.route('/')
def mainpage():
	print("Bluttber")
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

	# TODO: this function does:
	# - sends signal to daemon to re-read ini-file
	# shows confirmation and ini-file content for review
	return render_template('saveconfig.html', page_name = 'Save Configuration', user = 'admin', config_to_show = nd_dict)

@application.route('/communicator', methods = ['POST', 'GET'])
def communicator():
	try: # if form data was sent
		message_from_page = request.form
		if(message_from_page['signal'] == 'sig_custom'):
			signal_to_send = message_from_page['custom_signal_name']
		else:
			signal_to_send = message_from_page['signal']

	except:
		message_from_page = ''
		signal_to_send = "Hello Daemon"
		answer_string = ''

	# get port
	with open('../config.json', 'r') as jf:
		jobj = json.load(jf)
		port = int(jobj['Daemon']['dm_listens_to_port'])

	print("Port: %r" % port)

	connection_to_daemon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = socket.gethostname()

	try:
		connection_error = connection_to_daemon.connect((host,port)) 
	except Exception as e:
		print("Connection error: %r" % e)
		connection_error = e

	if connection_error == None:
		print("Signal_to_send before overwrite: %r" % signal_to_send)
		connection_to_daemon.send(signal_to_send.encode("utf8"))
		answer_bytes = connection_to_daemon.recv(1024)
		print("Answer Bytes = %r" % answer_bytes)
		answer_string = answer_bytes.decode("utf8")
		print("Answer String = %s" % answer_string)	
		connection_to_daemon.close()
		# FIXME: blocks the webapp

		return render_template('communicator.html', page_name ='Communicator', user='admin', recent_signal = signal_to_send, answer = answer_string)
	else:
		return 'Daemon does not respond: %r<br><a href="..">go back</a>' % connection_error

@application.route('/logger', methods = ['GET', 'POST'])
def logger():
	available_logs = []
	for file in os.listdir("../log"):
		if file.endswith(".log"):
			available_logs.append(file.split('.')[0].split('_')[1])
	
	try:
		form_data = request.form
		year_selected = form_data['year']
	except:
		year_selected = available_logs[0]

	logfile = open('../log/log_%s.log' % year_selected,'r')
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

	return render_template('logger.html', page_name ='Logger', user='admin', logfile = log, years = available_logs, year_selected = year_selected)

if __name__ == '__main__':
   application.run(debug=True)
