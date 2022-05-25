from pymongo import MongoClient
from datetime import datetime

# Prints all occurrences of the Soviet Union together with a verb of "breakdown",
# in chronological order, together with the date and speaker's name
# plus two surrounding sentences before and after.

client=MongoClient() #authenticate here
db=client.vode_db
collection=db.ptk

vbs=["pudota",u"itsen\xe4isty\xe4",u"vapautua",u"lopettaa",u"luhistua",u"poistua",u"purkaa",u"julistaa",u"lakkauttaa",u"tuhota",u"paheta",u"heiket\xe4",u"sortua",u"hyl\xe4t\xe4",u"vaarantua",u"erota",u"ep\xe4onnistua",u"kadota",u"murtua",u"romahduttaa",u"tukehtua",u"kuolla",u"k\xe4rjisty\xe4",u"purkautua",u"j\xe4rkky\xe4",u"taipua",u"irrottautua",u"puhjeta",u"heikenty\xe4",u"korvautua",u"kumota",u"murentaa",u"menehty\xe4",u"vaurioitua",u"tuhoutua",u"romuttua",u"mullistaa",u"nujertaa",u"taantua",u"pett\xe4\xe4",u"langeta",u"kariutua",u"t\xf6rm\xe4t\xe4",u"horjua",u"ruostua",u"demokratisoitua",u"vinksahtaa",u"haijoittaa",u"kuivua",u"hajottua",u"tyss\xe4\xe4nty\xe4",u"s\xe4rke\xe4",u"raueta",u"sirpaloitua",u"j\xe4risytt\xe4\xe4",u"huonontua",u"syrj\xe4ytt\xe4\xe4",u"irrottaa",u"mureta",u"valua",u"rampautua",u"rappeutua",u"irtaantua",u"lahota",u"ohimenn\xe4",u"kallistua",u"kutistua",u"katketa",u"kriisiyty\xe4",u"kuukahtaa",u"r\xe4j\xe4ht\xe4\xe4",u"turmeltua",u"laueta",u"eliminoida",u"pilaantua",u"hajottaa",u"pyyhkiyty\xe4",u"vaipua",u"hiipua",u"hajaantua"]

d={}
count=0
for doc in collection.find({"words":{"$elemMatch":{"lemma":"Neuvostoliitto"}}}).sort("_id",1):
	count+=1
	for word in set([w["lemma"] for w in doc["words"] if w["cpos"] in ["VERB","AUX"] or ("Derivation" in w["feat"] and w["feat"]["Derivation"]=="Minen")]): # counting also auxiliary verbs and 4th infinitives
		if word not in d:
			d[word]=1
		else:
			d[word]+=1
		if word in vbs:
			text=""
			for doc2 in collection.find({"_id":{"$gte":doc["_id"]-2,"$lte":doc["_id"]+2}}).sort("_id",1):
				text+=doc2["text"]+" "
			if "sukunimi" in doc["metadata"]:
				print(text.strip()+" ("+doc["metadata"]["sukunimi"]+", "+doc["metadata"]["date"].strftime("%d.%m.%Y")+")")
			else:
				print(text.strip()+" ("+doc["metadata"]["date"].strftime("%d.%m.%Y")+")")
print(d) # all verb counts
print(count) # total count of USSR