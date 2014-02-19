import json
from pprint import pprint
import re

json_data = open('dictionary.json')
dictionary = json.load(json_data)
json_data = open('sentences.json')
sentences = json.load(json_data)

engSent = []
for line in sentences["dev"]:
	for p in dictionary["phrases"]:
		p = re.sub('[,.]+', '', p)
		line.replace(" "+p+" ", " "+dictionary["phrases"][p]+" ")
	words = line.split(" ")
	output = []
	for w in words:
		if w in dictionary["words"]:
			output.append(dictionary["words"][w][0])
		elif w.lower() in dictionary["words"]:
			output.append(dictionary["words"][w.lower()][0])
		else:
			output.append(w)
	engSent.append(output)


print engSent