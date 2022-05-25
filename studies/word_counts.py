import pymongo
import codecs

# Prints out all the words and their counts in the dataset,
# in alphabetical order.

client=pymongo.MongoClient() #authenticate here
db=client.vode_db

tokens={}
for doc in db["ptk"].find():
	for w in doc["words"]:
		if w["lemma"] not in tokens:
			tokens[w["lemma"]]=1
		else:
			tokens[w["lemma"]]+=1

out=codecs.open("counts.txt","w",encoding="utf-8")
for k in sorted(tokens.keys()):
	out.write(k+"\t"+str(tokens[k])+"\n")
out.close()