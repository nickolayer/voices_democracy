from json import dumps, loads
import codecs
from datetime import datetime
from collections import OrderedDict
from urllib import unquote

# This script either appends the current query to the system's history file
# or returns all of the current user's previously made queries.

sort_d={"dataset1":5000,"dataset2":5000,"dataset3":5000,"dataset4":5000,"dataset5":5000,"dataset6":5000,"dataset7":5000,"dataset8":5000,"dataset9":5000,"dataset10":5000,"lemma":4000,"minyear":3800,"maxyear":3600,"party":3400,"stype":3100,"sttype":2500,"lang":2400,"speaker":2300,"radius":300,"window":200,"agent":-1,"time":-1}
#this dictionary forces an artificial sort ordering for the history fields, showing the "most important" ones first - 
#the history file itself stores them in arbitrary order, but they are sorted appropriately whenever fetched

def application(environ, start_response):
	name=environ["REMOTE_USER"]
	response_headers=[('Pragma','no-cache'),('Cache-Control','no-cache'),'Content-type','application/json']
	s=unquote(environ["QUERY_STRING"])
	ob=loads(s[5:])
	baseURL="./users/"
	results=[]
	if "save" in ob and ob["save"]:
		number=0
		del ob["save"]
		file=codecs.open(baseURL+"requests.txt","a+",encoding="utf-8")
		for line in file:
			if line=="\n" or line=="":
				continue
			number=line.split("\t")[0]
		number=int(number)+1
		ob["time"]=datetime.now().strftime("%Y-%m-%d/%H:%M:%S")
		file.write("\t".join([str(number),"name~"+name]+[key+"~"+ob[key].replace("\t"," ").replace("\n"," ").strip() for key in ob])+"\n")
		file.close()
		results={"number":number}
	else:
		file=codecs.open(baseURL+"requests.txt","r",encoding="utf-8")
		for line in file:
			line=line.replace("\n","").split("\t")
			if line[1]=="name~"+name:
				out={}
				for pair in line[2:]:
					pair=pair.split("~")
					out[pair[0]]=pair[1]
				results.append(OrderedDict(sorted(out.items(),key=lambda k: -sort_d[k[0]] if k[0] in sort_d else -2)))
		file.close()
		results.reverse()
	s=dumps(results)
	response_headers.append(('Content-Length',str(len(s))))
	start_response("200 OK", response_headers)
	return [s]