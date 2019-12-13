import json

with open('../../config.json', 'r') as jf:
	jobj = json.load(jf)
	port = jobj['Daemon']['dm_listens_to_port']

print(port)