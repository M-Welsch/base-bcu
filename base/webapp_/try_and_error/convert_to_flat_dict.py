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

test_dict = {"Daeomon.dm_listens_to_port":"12345", "Schedule.backup_frequency":"Weekly","Schedule.Weekday":"1"}
print(test_dict)
print(convert_to_nd_dict(test_dict))
