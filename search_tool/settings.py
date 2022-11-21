from json import dumps, loads
import io
from urllib import unquote

# This script either saves the user's updated settings after a change
# or returns them as a JSON object to the frontend.

def application(environ, start_response):
	name=environ["REMOTE_USER"]
	response_headers=[('Pragma','no-cache'),('Cache-Control','no-cache'),('Content-type','application/json')]
	s=unquote(environ["QUERY_STRING"])
	ob=loads(s[5:])
	baseURL="./users/"
	results={}
	if "save" in ob:
		del ob["save"]
		file=io.open(baseURL+"settings_"+name+".txt","w",encoding="utf-8")
		for key in ob:
			if isinstance(ob[key],list):
				val="["+",".join(ob[key])+"]"
			else:
				val=ob[key]
			file.write(key+"="+str(val)+"\n")
		results["state"]=True
	else:
		file=io.open(baseURL+"settings_"+name+".txt","r",encoding="utf-8")
		for line in file:
			line=line.replace("\n","").split("=")
			if "[" in line[1] and "]" in line[1]:
				if line[1]=="[]":
					results[line[0]]=[]
				else:
					results[line[0]]=line[1][line[1].index("[")+1:line[1].index("]")].split(",")
			else:
				if line[1].isdecimal():
					results[line[0]]=int(line[1])
				else:
					results[line[0]]=line[1]
	file.close()
	s=dumps(results)
	response_headers.append(('Content-type','application/json'))
	response_headers.append(('Content-Length',str(len(s))))
	start_response("200 OK", response_headers)
	return [s]