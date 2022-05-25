from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from glob import glob
import codecs
import datetime
from argparse import ArgumentParser
from collections import OrderedDict
from re import sub

# This script handles the insertion of "pack" files into MongoDB.
# Files from any dataset that were split and parsed, one line of metadata + one line of paragraph text,
# can be inserted by this script and will have the same DB document structure.

client=MongoClient() #authenticate here
db=client.vode_db

def is_oppos(party,dt):
# Looks up whether party was in the government or the opposition on date dt
# (for those documents that do not have this field).
	ds=dt.strftime("%Y-%m-%d")
	govs=[{"from":"1979-05-26","to":"1982-02-18","parties":["sd","kesk","r","skdl"]}, # Koiviston II hallitus
{"from":"1982-02-19","to":"1982-12-31","parties":["sd","kesk","r","skdl"]}, # Sorsan III
{"from":"1983-01-01","to":"1983-05-05","parties":["sd","kesk","r","lkp"]}, # Sorsan IIIb (SKDL left)
{"from":"1983-05-06","to":"1987-04-29","parties":["sd","kesk","r","smp"]}, # Sorsan IV
{"from":"1987-04-30","to":"1990-08-28","parties":["sd","kok","r","smp"]}, # Holkerin
{"from":"1990-08-29","to":"1991-04-25","parties":["sd","kok","r"]}, # SMP left
{"from":"1991-04-26","to":"1994-06-28","parties":["kesk","kok","r","skl"]}, # Ahon
{"from":"1994-06-29","to":"1995-04-12","parties":["kesk","kok","r"]}, # SKL left
{"from":"1995-04-13","to":"1999-04-14","parties":["sd","kok","vihr","vas","r"]}, # Lipposen I
{"from":"1999-04-15","to":"2002-05-31","parties":["sd","kok","vihr","vas","r"]}, # Lipposen II
{"from":"2002-06-01","to":"2003-04-16","parties":["sd","kok","vas","r"]}, # Vihreat left
{"from":"2003-04-17","to":"2003-06-23","parties":["sd","kesk","r"]}, # Jaatteenmaen
{"from":"2003-06-24","to":"2007-04-18","parties":["sd","kesk","r"]}, # Vanhasen I
{"from":"2007-04-19","to":"2010-06-21","parties":["kesk","vihr","kok","r"]}, # Vanhasen II
{"from":"2010-06-22","to":"2011-06-21","parties":["kesk","vihr","kok","r"]}, # Kiviniemen
{"from":"2011-06-22","to":"2014-04-03","parties":["sd","kok","vihr","vas","kd","r"]}, # Kataisen
{"from":"2014-04-04","to":"2014-06-23","parties":["sd","kok","vihr","kd","r"]}, # Vasemmistoliitto left
{"from":"2014-06-24","to":"2014-08-18","parties":["sd","kok","vihr","kd","r"]}, # Stubbin
{"from":"2014-09-18","to":"2015-05-28","parties":["sd","kok","kd","r"]}, # Vihreat left
{"from":"2015-05-29","to":"2017-06-12","parties":["kok","kesk","ps"]}, # Sipilan
{"from":"2017-06-13","to":"2019-06-05","parties":["kok","kesk","si","sin"]}, # PS split
{"from":"2019-06-06","to":"2019-12-09","parties":["sd","kesk","vihr","vas","r"]}, # Rinteen
{"from":"2019-12-10","to":"2021-09-17","parties":["sd","kesk","vihr","vas","r"]}] # Marinin
	for gov in govs:
		if ds>=gov["from"] and ds<=gov["to"]:
			return (party in gov["parties"])
	return None

def insr(name):
# Reads a "final" text file in CoNLL-U.
# Yields individual sentences as dictionaries to be inserted in MongoDB.
	attribs={}
	words=[]
	text=""
	paragraph=0
	count=0
	wordkeys=["id","form","lemma","cpos","pos","feat","head","deprel","deps","misc"]
	file=codecs.open(name,"r",encoding="utf-8")
	start=0
	end=0
	old_docid=-1
	new_docid=-1
	old_tunniste=""
	type=file.readline().split("|")[0].split(":")[1].upper()
	file.seek(0)
	parflag=False
	for line in file:
		if line.startswith("###C:PAGE"):
			if "page" in attribs:
				attribs["page"]=int(line.replace("\n","").split("=")[1])
			continue
		if line.startswith("###C:"+type):
			attribs={}
			parflag=True
			keys=line.replace("\n","").split("|")[1:]
			for key in keys:
				key=key.split("=")
				if key[1].isdigit():
					attribs[key[0]]=int(key[1])
				else:
					attribs[key[0]]=key[1]
			paragraph+=1
			attribs["paragraph"]=paragraph
			if "date" in attribs: #and isinstance(attribs["date"],basestring):
				attribs["date"]=attribs["date"].replace(u"\u2014","")
				if "." in attribs["date"]:
					attribs["date"]=datetime.datetime.strptime(attribs["date"],"%Y-%m-%d %H.%M")
				else:
					attribs["date"]=datetime.datetime.combine(datetime.datetime.strptime(attribs["date"],"%Y-%m-%d").date(),datetime.time.min)
#Adjust paragraph-level attributes here
			if type=="PTK":
				if "ekryhma" in attribs:
					attribs["ekryhma"]=attribs["ekryhma"].replace(" ","").replace(":","")
				if "ipvm" in attribs:
					if "kaika" in attribs:
						tm=attribs["kaika"]
						if isinstance(tm,(int,long)):
							tm="0"*(2-len(str(tm)))+str(tm)+".00"
						else:
							tm=tm.replace(u"\u2014","")
							if "(" in tm:
								tm=tm[tm.index("(")+1:tm.index(")")]
							tm="0"*(2-len(str(tm)))+tm
						attribs["date"]=datetime.datetime.strptime(attribs["ipvm"]+" "+tm,"%Y-%m-%d %H.%M")
						del attribs["kaika"]
					else:
						attribs["date"]=datetime.datetime.strptime(attribs["ipvm"],"%Y-%m-%d")
					del attribs["ipvm"]
				old_tunniste=attribs["tunniste"]
				if isinstance(attribs["tunniste"],basestring):
					attribs["tunniste"]=int(attribs["tunniste"].split(" ")[1].split("/")[1])
					if "sukunimi" in attribs and "ekryhma" in attribs and attribs["ekryhma"]!="":
						attribs["gov"]=is_oppos(attribs["ekryhma"],attribs["date"])
				else:
					if "gov" in attribs:
						attribs["gov"]=(attribs["gov"]=="True")
			continue
		if line=="" or line=="\n": #end of sentence
			if parflag:
				continue
#this guards against empty paragraphs, when the attribute line is followed by nothing at all -
#there's an empty line, which should not be treated as end of sentence
			count+=1
			if type=="PTK":
				tunniste=attribs["vp"]
				id=tunniste*10000*1000+attribs["inro"]*10000+count
			new_docid=id//10000
			if new_docid!=old_docid:
				count=1
				paragraph=1
				attribs["paragraph"]=1
				id=new_docid*10000+1
			old_docid=new_docid
			text=text.rstrip()
			output={"_id":id,"words":words,"text":text,"sentence":count,"metadata":dict(attribs)}
#Adjust sentence-level attributes here
			#if type=="PTK":
			#	...
			yield output
			words=[]
			text=""
			continue
		parflag=False
		word={}
		line=line.replace("\n","").split("\t")
		for i in range(0,len(wordkeys)):
			word[wordkeys[i]]=line[i]
		word["head"]=int(word["head"])
		word["id"]=int(word["id"])
		word["rlemma"]=word["lemma"][::-1] #optional, to be used in a DB index
		feat=word["feat"]
		word["feat"]={}
		if feat!="_":
			for t in feat.split("|"):
				word["feat"][t.split("=")[0]]=t.split("=")[1]
				if t.startswith("Clitic=") and "," in t:
					word["feat"]["Clitic"]=word["feat"]["Clitic"].split(",")
		text+=word["form"]
		if "|SpaceAfter=No" in word["misc"]:
			word["misc"]=word["misc"][0:word["misc"].index("|")]
		else:
			text+=" "
		if word["misc"]!="_":
			word["misc"]=word["misc"][word["misc"].index(".")+1:]
		del word["pos"]
		del word["deps"]
		words.append(word)
	file.close()

def get_metadata(coll):
# Returns the total number of sentences in every document of collection coll.
# This is displayed by the search system together with sentence numbers.
	global db
	stage1={"doc":{"$floor":{"$divide":["$_id",10000]}}} # convert sentence IDs to document IDs
	stage2={"_id":"$doc","count":{"$sum":1}} # group by document ID, count the documents with the same ID
	stage3={"_id":1} # sort by document ID
	cur=db[coll].aggregate([{"$project":stage1},{"$group":stage2},{"$sort":stage3}])
	out=OrderedDict()
	for doc in cur:
		out[doc["_id"]]=doc["count"]
	return out

def main():
	parser=ArgumentParser()
	parser.add_argument("-i","--insert",help="insert parsed files into collection; pass empty collection name to test without inserting",nargs=2,metavar=("<path>","[collection]"))
	parser.add_argument("-m","--metadata",help="print metadata from a collection",nargs=1,metavar=("<collection>"))
	args=vars(parser.parse_args())

	global db
	count=0
	if args["insert"]:
		coll=args["insert"][1]
		if coll and (coll not in db.list_collection_names()):
			print("Collection "+coll+" does not exist.")
		else:
			count=0
			scount=0
			for fname in sorted(glob(args["insert"][0]+"/*.txt")):
				if "final" not in fname:
					continue
				count+=1
				print("Inserting from "+fname)
				if coll:
					docs=[]
					for s in insr(fname):
						docs.append(s)
						scount+=1
						if len(docs)==4000:
							try:
								db[coll].insert_many(docs)
							except BulkWriteError as e:
								print (e.details)
							docs=[]
							break
					if docs:
						db[coll].insert_many(docs)
				else:
					for s in insr(fname):
						scount+=1
			print(str(scount)+" sentences in "+str(count)+" files")
	if args["metadata"]:
		coll=args["metadata"][0]
		if coll and coll in db.list_collection_names():
			s="{"
			res=get_metadata(coll)
			if res:
				for k,v in res.items():
					s+=str(int(k))+": "+str(v)+", "
				print(s[:-2]+"}")
			else:
				print("Collection "+coll+" is likely empty.")
		else:
			print("Collection "+coll+" does not exist.")

main()