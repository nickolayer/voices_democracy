import json
import codecs
import pymongo

# This script handles the creation of user-specific custom collections,
# which store all the results of the latest search for later use.

def index(req,reqs):
	ob=json.loads(reqs)
	req.get_basic_auth_pw()
	name=req.user
	req.headers_out["Pragma"]="no-cache"
	req.headers_out["Cache-Control"]="no-cache"
	client=pymongo.MongoClient() # authenticate here
	db=client.vode_db
	trs={"minute":"ptk"} # DB collection name as the value
	muls={"minute":1}
	if "save" in ob:
		target=""
		radius=ob["radius"]
		for i in range(1,11):
			if name+str(i) not in db.list_collection_names():
				target=name+str(i)
				db.create_collection(target)
				break
		if not target:
			return json.dumps({"name":""}) # save failed, too many collections for this user
		count=0
		file=codecs.open("./users/cache_"+name+".txt","r",encoding="utf-8")
		for line in file:
			if "|" not in line:
				break
			line=line.replace("\n","").split("|")
			olddocument=0
			document=0
			sentences={}
			inserted=[]
			for i in range(1,len(line),2):
				cname=line[i]
				if line[i] in trs:
					cname=trs[line[i]]
				if cname not in sentences:
					sentences[cname]={}
				data=line[i+1].split(";")
				for id in data:
					doc=db[cname].find_one({"_id":int(id)})
					if radius>0 and not line[i].startswith(name):
# If you copy from a custom collection, it might not have the context around the documents you've queried
						document=doc["_id"]-doc["sentence"]
						if document not in sentences[cname]:
							sentences[cname][document]=[]
						csource=cname
						if line[i] not in trs:
							csource=trs[doc["type"]]
						for j in range(doc["_id"]-radius,doc["_id"]+radius+1):
							if j%10000 not in sentences[cname][document]:
								#try:
									dt=db[csource].find_one({"_id":j})
									if dt is not None:
										if not line[i].startswith(name):
											dt["type"]=line[i]
											dt["_id"]=(dt["_id"]-dt["sentence"])*muls[dt["type"]]+dt["sentence"]
										try:
											db[target].insert_one(dt)
										except pymongo.errors.DuplicateKeyError:
											continue
										inserted.append(dt["_id"])
										sentences[cname][document].append(j%10000)
										count+=1
								#except Exception as e:
									#return str(e)+str(inserted)
					else:
						if not line[i].startswith(name):
							doc["type"]=line[i]
							doc["_id"]=(doc["_id"]-doc["sentence"])*muls[doc["type"]]+doc["sentence"]
						try:
							db[target].insert_one(doc)
						except pymongo.errors.DuplicateKeyError: # possible if copying the same document from an original dataset and a custom collection
							continue
						count+=1
		file.close()
		return json.dumps({"name":target,"count":count})
	if "delete" in ob:
		if ob["name"].startswith(name) and ob["name"][len(name):].isdigit():
			db[ob["name"]].drop()
		return json.dumps({"name":ob["name"]})
	return json.dumps({"1":2})