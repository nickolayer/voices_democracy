import json
import codecs

# This script either saves the user's updated settings after a change
# or returns them as a JSON object to the frontend.

def index(req,reqs):
	ob=json.loads(reqs)
	req.get_basic_auth_pw()
	name=req.user
	req.headers_out["Pragma"]="no-cache"
	req.headers_out["Cache-Control"]="no-cache"
	baseURL="./users/"
	results={}
	if "save" in ob:
		del ob["save"]
		file=codecs.open(baseURL+"settings_"+name+".txt","w",encoding="utf-8")
		for key in ob:
			if isinstance(ob[key],list):
				val="["+",".join(ob[key])+"]"
			else:
				val=ob[key]
			file.write(key+"="+str(val)+"\n")
		results["state"]=True
	else:
		file=codecs.open(baseURL+"settings_"+name+".txt","r",encoding="utf-8")
		for line in file:
			line=line.replace("\n","").split("=")
			if "[" in line[1] and "]" in line[1]:
				results[line[0]]=line[1][line[1].index("[")+1:line[1].index("]")].split(",")
				if results[line[0]]==[""]:
					results[line[0]]=[]
			else:
				if line[1].isdecimal():
					results[line[0]]=int(line[1])
				else:
					results[line[0]]=line[1]
	file.close()
	return json.dumps(results)
