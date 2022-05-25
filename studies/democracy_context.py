from pymongo import MongoClient
import codecs

# Counts the most frequent nouns and proper nouns around each appearance of democracy
# (same sentence or at most 3 sentences away).

client=MongoClient() #authenticate here
db=client.vode_db

out={}
counts=[0]*42
for doc in db.ptk.find({"words":{"$elemMatch":{"lemma":"demokratia"}}},{"words.$":1,"metadata.date":1}):
	id=doc["_id"]
	words=[]
	wnum=doc["words"][0]["id"]
	for dc in db.ptk8021.find({"_id":{"$in":[id-1,id-2,id-3,id,id+1,id+2,id+3]}},{"words":1}):
		if dc["_id"]==id: # skipping the found word itself
			del dc["words"][wnum-1]
		add=[w["lemma"] for w in dc["words"] if w["cpos"] in ["NOUN","PROPN"]]
		for word in add:
			if word not in words:
				words.append(word)
	idx=doc["metadata"]["date"].year-1980
	for word in words:
		if word in out:
			out[word][idx]+=1
		else:
			out[word]=[0]*42
			out[word][idx]+=1
	counts[idx]+=1
print(counts)

#Write out a tab-separated table of each common word's counts by year
outf=codecs.open("dems.txt","w",encoding="utf-8-sig")
for word in out:
	if sum(out[word])>=60:
		tmp=[str(x) for x in out[word]]
		temp=[word]+tmp+[str(sum(out[word]))]
		outf.write("\t".join(temp)+"\n")

#Alternatively:
#divide each word's yearly count by the respective count of democracy,
#showing how often this word was found next to it,
#track the change of this fraction from year to year,
#and print the sum of the squared differences
#as a measure of the word's "volatility" in context.
#for word in out:
#	if sum(out[word])>=60:
#		diff=0
#		for i in range(0,len(out[word])):
#			out[word][i]=out[word][i]*1.0/counts[i]
#		for i in range(1,len(out[word])):
#			diff+=(out[word][i]-out[word][i-1])*(out[word][i]-out[word][i-1])
#		tmp=[str(x) for x in out[word]]
#		temp=[word]+tmp+[str(diff)]
#		outf.write("\t".join(temp)+"\n")