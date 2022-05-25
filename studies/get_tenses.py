import pymongo

# A method to identify compound (multiword) verb forms based on the dependency parser's annotation.
# It attempts to extract past participle forms, which are common in compound tenses,
# and follow their dependency chains to see if these contain auxiliary or primary verbs.

client=pymongo.MongoClient() #authenticate here
db=client.vode_db

for doc in db.ptk.find().sort("_id",1).limit(1000):
	parts=[w for w in doc["words"] if w["cpos"]=="VERB" and w["feat"]["VerbForm"]=="Part" and w["feat"]["PartForm"]=="Past" and w["feat"]["Case"]=="Nom"]
	if parts:
		for part in parts:
			chain=[]
			ids=[part["id"]]
			new_ids=[w["id"] for w in doc["words"] if w["head"] in ids]
			for id in new_ids:
				if id not in ids:
					ids.append(id)
					chain.append(dict(doc["words"][id-1]))
			sign="+"
			voice=part["feat"]["Voice"]
			if "ei" in [w["lemma"] for w in chain]:
				sign="-"
			tense="Null"
			if "olla" not in [w["lemma"] for w in chain]:
				tense="Impf"
				sign="-"
			elif len([w for w in chain if w["lemma"]=="olla" and "Mood" in w["feat"] and w["feat"]["Mood"]=="Cnd"])>0:
				tense="Kond"
			elif len([w for w in chain if (w["form"].lower().startswith("ole") or (w["lemma"]=="olla" and "Tense" in w["feat"] and w["feat"]["Tense"]=="Pres"))])>0:
				tense="Perf"
			elif len([w for w in chain if (w["form"].lower().startswith("ollut") or (w["lemma"]=="olla" and "Tense" in w["feat"] and w["feat"]["Tense"]=="Past"))])>0:
				tense="Pperf"
			doc["text"]=doc["text"].replace(part["form"],part["form"]+" "+str((part["lemma"],sign,tense,voice)))
		print(str(doc["sentence"])+") "+doc["text"])