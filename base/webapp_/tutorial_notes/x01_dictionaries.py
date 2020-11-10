import configparser

config = configparser.ConfigParser()
config.read('../../config.ini')

config_as_dict = config._sections

for section in config_as_dict:
	print("[%s]" % section)
	for parameter in config_as_dict[section]:
		print("%s = %s" % (parameter, config_as_dict[section][parameter]))
	print("")

# write changes back to the config file
with open('../../config.ini', "w") as config_file:
	config.write(config_file)

# basic stuff
mydict = {'first':'1','second':'2'}
print(mydict)

for key in mydict.keys():
	print("Key %s: %s" % (key, mydict[key]))