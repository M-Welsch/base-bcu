year_selected = 2016
logfile = open('../../log/log_%s.log' % year_selected,'r')
logfile_content = ''
logfile_content = logfile.readlines()
logfile_content.reverse() # to have most current line first
log = ''
for line in logfile_content:
	if "could not" in line:
		line = '<style="warning">'+line+'</style>'
		print(line)
	log = log + line+'\n'

logfile_edited = open('logfile_edited.log','w')

logfile_edited.write(log)