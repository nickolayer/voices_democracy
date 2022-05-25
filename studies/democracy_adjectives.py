import pymongo
import codecs
import datetime

# Attempts to identify and count adjectives defining democracy:
# those having a direct UD relation to it and sharing the same case form.

client=pymongo.MongoClient() #authenticate here
db=client.vode_db

adj={}
count=0
d={}
coll="ptk"
term="demokratia"

ob={"words":{"$elemMatch":{"lemma":term}}}
# Alternatively, to exclude everything except actual speeches:
#ob={"$and":[{"metadata.tyyppi":{"$exists":True}},{"metadata.tyyppi":{"$nin":["johdanto","pmpuhe","prespuhe","puhemiehenpuhe","ilmasia",u"p\xe4\xe4t\xf6s","saarna","puhemies",u"p\xe4\xe4tt\xe4minen"]}}]}
#ob["$and"].append({"words":{"$elemMatch":{"lemma":term}}})

for doc in db[coll].find(ob):
	count+=1
	targets=[w["id"] for w in doc["words"] if w["lemma"]==term] # originally 1-based
	ad=[]
	for w in doc["words"]:
		if w["cpos"]=="ADJ" and w["head"] in targets:
			for t in targets:
				if ("Case" not in w ["feat"]) or w["feat"]["Case"]==doc["words"][t-1]["feat"]["Case"]:
					if w["lemma"] in adj:
						adj[w["lemma"]]+=1
					else:
						adj[w["lemma"]]=1
					ad.append(w["lemma"])
					break #one adjective per occurrence?
	#print(ad)

print(d)
print(adj)
print(count)