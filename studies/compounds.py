from pymongo import MongoClient
import re

# Gets the counts of all compound nouns starting with "valta"
# (counting only one occurrence of each per sentence).

client=MongoClient() #authenticate here
db=client.vode_db

out={}
for doc in db.ptk.find({"words":{"$elemMatch":{"lemma":re.compile("^valta"),"cpos":"NOUN"}}},{"words":1}):
	words=[]
	for w in doc["words"]:
		if w["lemma"].startswith("valta") and w not in words:
			words.append(w["lemma"])
	for w in words:
		if w not in out:
			out[w]=1
		else:
			out[w]+=1

print(out)