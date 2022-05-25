# Helper file.
# Converts the search system's common history file into a CSV representation.

f=open("requests.txt","r",encoding="utf-8")
g=open("requests.csv","w",encoding="utf-8")
g.write("num,name,time,ds1,ds2,ds3,ds4,lemma,window,radius,minyear,maxyear,misc\n")
order=["name","time","dataset1","dataset2","dataset3","dataset4","lemma","window","radius","minyear","maxyear"]

for line in f:
	temp=line.replace("\n","").split("\t")
	pairs=[(x.split("~")[0],x.split("~")[1]) for x in temp[1:]]
	out=[temp[0]]
	for heading in order:
		for pair in pairs:
			if pair[0]==heading:
				out.append(pair[1])
				break
		else:
			out.append("-")
	last=""
	for pair in pairs:
		if pair[0] not in order:
			last+=pair[0]+"="+pair[1]+" "
	out.append(last)
	g.write(",".join(out)+"\n")
	
f.close()
g.close()