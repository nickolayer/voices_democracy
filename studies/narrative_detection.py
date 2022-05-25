import pymongo
import codecs
import glob

# This script is an experiment in detecting narratives within the data.
# It tries to find chains of sentences exhibiting certain grammatical properties,
# mostly verbs in particular tenses or of a particular semantic type,
# with the assumption that such chains are commonly found in narratives.
# The output is then compared to human-annotated files, where the same text
# is marked by various codes in a specific format.

client=pymongo.MongoClient() #authenticate here
db=client.vode_db

def show(code,model,answer):
# Pretty-prints the original annotated file, showing the annotations,
# the properties and the narratives suggested by the algorithm for each sentence
# in a tabular form.
	f=codecs.open(name,"r",encoding="utf-8-sig")
	out=codecs.open(name.replace(".txt","_kone.txt"),"w",encoding="utf-8-sig")
	lastnum=0
	for line in f:
		line=line.replace("\n","").replace("  "," ").strip()
		if not line:
			continue
		line=line.split(" ")
		for i in range(0,len(line)):
			if line[i].isdigit():
				break
			i+=1
		num=int(line[i])
		who=line[i+2]
		text=" ".join(line[i+3:])
		annot=""
		if i==1:
			annot=line[0]
		if i==2:
			if line[0]=="KK":
				annot=line[1]
			elif line[1]=="KK":
				annot=line[0]
			else:
				annot=line[0]+" "+line[1]
		comment=""
		# Construct the "comment" showing the sentence-level properties
		# relevant to the algorithm, depending on what it found in the sentence
		if num in model["ks"]:
			comment+="L"
		if num in model["ps"]:
			comment+="p"
		if num in model["rs"]:
			comment+="r"
		if num in model["pks"]:
			comment+="K"
		if num in model["pps"]:
			comment+="P"
		if num in model["imps"]:
			comment+="i"
		if num in model["m_imps"]:
			comment=comment.replace("i","I")
		if num in model["konds"]:
			comment+="k"
		if num in model["bridges"]:
			comment+="S"
		if num in model["empty"]:
			comment+="-"
		for i in range(0,len(model["narratives"])):
			if num==model["narratives"][i][0]:
				comment="["+comment
				break
			if num==model["narratives"][i][1]:
				comment+="]"
				break
		cutoff=140
		if len(text)>cutoff and text[cutoff-1]!=" ":
			cutoff=text[0:cutoff].rindex(" ")
		out.write(" ".join([str(num).rjust(4," "),annot.ljust(2," "),comment.ljust(5," "),who[0:10].ljust(10," "),text[0:cutoff]])+"\n")
		text=text[cutoff:]
		while text:
			cutoff=140
			if text[0]==" ":
				text=text[1:]
			if len(text)>cutoff and text[cutoff-1]!=" ":
				cutoff=text[0:cutoff].rindex(" ")
			out.write(" "*25+text[0:cutoff]+"\n")
			text=text[cutoff:]
	f.close()

	# Counting statistics about the algorithm's performance
	true_narratives=answer
	model_narratives=model["narratives"]
	overlaps=[]
	total_overlap=(0,0)
	for nr in true_narratives:
		cnt=0
		for i in range(nr[0],nr[1]+1):
			for mnr in model_narratives:
				if i>=mnr[0] and i<=mnr[1]:
					cnt+=1
					break
		overlaps.append((cnt,nr[1]-nr[0]+1))
		total_overlap=(total_overlap[0]+cnt,total_overlap[1]+nr[1]-nr[0]+1)

	empty_frags=0
	half_frags=0
	model_overlaps=[]
	total_model_overlap=(0,0)
	for mnr in model_narratives:
		cnt=0
		for i in range(mnr[0],mnr[1]+1):
			for nr in true_narratives:
				if i>=nr[0] and i<=nr[1]:
					cnt+=1
					break
		if cnt==0:
			empty_frags+=1
		elif cnt>int((mnr[1]-mnr[0]+1)/2):
			half_frags+=1
		model_overlaps.append((cnt,mnr[1]-mnr[0]+1))
		total_model_overlap=(total_model_overlap[0]+cnt,total_model_overlap[1]+mnr[1]-mnr[0]+1)

	out.write(u"\nActual narratives: "+str(len(true_narratives))+"\n")
	out.write(u"Model fragments: "+str(len(model_narratives))+"\n")
	out.write(u"Model fragments without narrative sentences: "+str(empty_frags)+"\n")
	out.write(u"Model fragments with over half narrative sentences: "+str(half_frags)+"\n")
	out.write(u"Actual narrative sentences in the output (per narrative): "+str(overlaps)+"\n")
	code=code.split("/")[-1].replace(".txt","")
	if total_overlap[1]>0:
		out.write(u"total "+str(total_overlap[0])+"/"+str(total_overlap[1])+", "+str(round(100*total_overlap[0]/(total_overlap[1]*1.0),1))+" %\n")
	out.write(u"Actual narrative sentences in the output (per fragment): "+str(model_overlaps)+"\n")
	if total_model_overlap[1]>0:
		out.write(u"total "+str(total_model_overlap[0])+"/"+str(total_model_overlap[1])+", "+str(round(100*total_model_overlap[0]/(total_model_overlap[1]*1.0),1))+" %\n")
	out.write(str(model["stats"]))
	if total_overlap[1]==0:
		data=[code,len(true_narratives),len(model_narratives),empty_frags,half_frags,total_overlap[0],total_overlap[1],-1,total_model_overlap[1],round(100*total_model_overlap[0]/(total_model_overlap[1]*1.0),1)]
	elif total_model_overlap[1]==0:
		data=[code,len(true_narratives),len(model_narratives),empty_frags,half_frags,total_overlap[0],total_overlap[1],round(100*total_overlap[0]/(total_overlap[1]*1.0),1),total_model_overlap[1],-1]
	else:
		data=[code,len(true_narratives),len(model_narratives),empty_frags,half_frags,total_overlap[0],total_overlap[1],round(100*total_overlap[0]/(total_overlap[1]*1.0),1),total_model_overlap[1],round(100*total_model_overlap[0]/(total_model_overlap[1]*1.0),1)]
	out.close()
	return data

def get_narratives(numb):
# Tentatively identifies narratives in a single document encoded by numb (e.g. 2015ptk138).
	refer=[u"anella",u"argumentoida",u"artikuloida",u"arvostella",u"debatoida",u"depatoida",u"diskuteerata",u"ehdotella",u"ehdottaa",u"esitell\xe4",u"esitt\xe4\xe4",u"haastella",u"halventaa",u"harmitella",u"haukkua",u"hehkuttaa",u"herjata",u"hokea",u"hoputtaa",u"horista",u"huhuta",u"huikata",u"huomautella",u"huomauttaa",u"hurskastella",u"huudahdella",u"huudahtaa",u"huudella",u"huutaa",u"h\xe4list\xe4",u"h\xf6list\xe4",u"h\xf6lp\xf6tt\xe4\xe4",u"h\xf6l\xe4ytell\xe4",u"h\xf6l\xf6tt\xe4\xe4",u"h\xf6pist\xe4",u"h\xf6psi\xe4",u"h\xf6p\xf6tell\xe4",u"h\xf6p\xf6tt\xe4\xe4",u"ilkkua",u"ilmaista",u"ilmoitella",u"ilmoittaa",u"imarrella",u"informeerata",u"informoida",u"intt\xe4\xe4",u"irvailla",u"irvistell\xe4",u"irvi\xe4",u"isotella",u"ivailla",u"ivata",u"jaanata",u"jaaritella",u"jaarittaa",u"jankata",u"jankuttaa",u"jeesustella",u"jorista",u"jossitella",u"juksata",u"julistaa",u"julistella",u"julkikuuluttaa",u"julkilausua",u"juoruilla",u"juoruta",u"jupista",u"juputtaa",u"jurputtaa",u"jutella",u"jutustaa",u"jutustella",u"jututella",u"jututtaa",u"j\xe4k\xe4tt\xe4\xe4",u"kaakattaa",u"kailottaa",u"kakistaa",u"kakistella",u"kalkattaa",u"kannella",u"karjaista",u"kaunistella",u"kehaista",u"kehotella",u"kehottaa",u"kehua",u"kehuskella",u"keljuilla",u"kerskailla",u"kerskata",u"kerskua",u"kertoa",u"kertoilla",u"keskustella",u"kiekaista",u"kielt\xe4yty\xe4",u"kielt\xe4\xe4",u"kiistell\xe4",u"kiist\xe4\xe4",u"kiitell\xe4",u"kiitt\xe4\xe4",u"kiivailla",u"kimitt\xe4\xe4",u"kinastella",u"kinata",u"kinuta",u"kiritt\xe4\xe4",u"kiroilla",u"kirota",u"kiusoitella",u"kivahdella",u"komennella",u"komentaa",u"kommentoida",u"kommunikoida",u"korostaa",u"kritikoida",u"kritiseerata",u"kritisoida",u"kuiskata",u"kuittailla",u"kummastella",u"kummeksua",u"kuuluttaa",u"kuvailla",u"kysell\xe4",u"kysy\xe4",u"kys\xe4ist\xe4",u"k\xe4l\xe4tt\xe4\xe4",u"k\xe4rjistell\xe4",u"k\xe4rjist\xe4\xe4",u"k\xe4rtt\xe4\xe4",u"k\xe4ske\xe4",u"k\xe4skytt\xe4\xe4",u"ladella",u"lausahdella",u"lausahtaa",u"lausua",u"laususkella",u"laverrella",u"leperrell\xe4",u"lepert\xe4\xe4",u"letkautella",u"letkauttaa",u"leuhkia",u"leukailla",u"levennell\xe4",u"liioitella",u"lipsautella",u"lipsauttaa",u"lirkutella",u"luennoida",u"luonnehtia",u"lupailla",u"luvata",u"l\xe4nkytt\xe4\xe4",u"l\xe4rp\xe4tt\xe4\xe4",u"l\xe4ssytell\xe4",u"l\xe4ssytt\xe4\xe4",u"l\xe4tist\xe4",u"l\xf6pist\xe4",u"l\xf6rp\xf6tell\xe4",u"maanitella",u"mahtailla",u"mainita",u"makeilla",u"manailla",u"manata",u"mankua",u"marmattaa",u"mekastaa",u"mekkaloida",u"melskata",u"meluta",u"mesoa",u"mesota",u"messuta",u"mielistell\xe4",u"moitiskella",u"moittia",u"mollaillla",u"mollata",u"molottaa",u"mongertaa",u"moralisoida",u"morkata",u"motkottaa",u"muistutella",u"mukista",u"mumista",u"murahdella",u"murahtaa",u"murjaista",u"mussuttaa",u"mustamaalata",u"mutista",u"my\xf6nnell\xe4",u"my\xf6nt\xe4\xe4",u"m\xe4\xe4ritell\xe4",u"m\xe4\xe4r\xe4ill\xe4",u"m\xe4\xe4r\xe4t\xe4",u"m\xf6l\xe4ytell\xe4",u"m\xf6l\xe4ytt\xe4\xe4",u"m\xf6l\xf6tt\xe4\xe4",u"nahistella",u"naljailla",u"naljaista",u"naljauttella",u"nalkuttaa",u"napista",u"neuvoa",u"nimitell\xe4",u"nipottaa",u"noitua",u"nokitella",u"nuhdella",u"nurista",u"n\xe4lvi\xe4",u"n\xe4s\xe4viisastella",u"ohjeistaa",u"oikaista",u"onnitella",u"opastaa",u"paasata",u"pahoitella",u"paisutella",u"parjata",u"patistaa",u"perustella",u"per\xe4\xe4nkuuluttaa",u"pilkata",u"puhella",u"puhutella",u"puolustaa",u"puolustella",u"purnata",u"pyydell\xe4",u"pyyt\xe4\xe4",u"referoida",u"riidell\xe4",u"ripitt\xe4\xe4",u"rukoilla",u"ruotia",u"rupatella",u"r\xe4hist\xe4",u"r\xe4hj\xe4t\xe4",u"saarnata",u"sanella",u"selitell\xe4",u"selitt\xe4\xe4",u"selostaa",u"selvent\xe4\xe4",u"seurustella",u"siteerata",u"spekuloida",u"suositella",u"suostutella",u"syytt\xe4\xe4",u"taivutella",u"tentata",u"tiedustella",u"tilitt\xe4\xe4",u"tivata",u"todeta",u"todistella",u"toistaa",u"toitottaa",u"toivottaa",u"tokaista",u"tunnustaa",u"t\xe4hdent\xe4\xe4",u"t\xe4sment\xe4\xe4",u"uhkailla",u"uhota",u"uskotella",u"vaatia",u"vakuuttaa",u"valehdella",u"valistaa",u"valitella",u"vannoa",u"varoitella",u"varoittaa",u"vastailla",u"vastata",u"vedota",u"vihjata",u"vinkata",u"vinoilla",u"vitsailla",u"v\xe4h\xe4tell\xe4",u"v\xe4itell\xe4",u"v\xe4itt\xe4\xe4",u"ylipuhua",u"ylist\xe4\xe4",u"yllytt\xe4\xe4"]
	emotion=["aliarvostaa",u"arveluttaa",u"samaistua",u"v\xe4heksy\xe4",u"ahdistaa",u"ahdistua",u"arastella",u"aristella",u"arkailla",u"arvostaa",u"digata",u"diggailla",u"empi\xe4",u"haikailla",u"haitata",u"haltioitua",u"halveksia",u"harmistua",u"harmittaa",u"hatuttaa",u"helty\xe4",u"hermostua",u"hermostuttaa",u"hirvitt\xe4\xe4",u"huolestua",u"huolestuttaa",u"huolettaa",u"huvittaa",u"hymyilytt\xe4\xe4",u"h\xe4kelty\xe4",u"h\xe4mmenty\xe4",u"h\xe4mment\xe4\xe4",u"h\xe4mm\xe4stell\xe4",u"h\xe4mm\xe4stytt\xe4\xe4",u"h\xe4mm\xe4sty\xe4",u"h\xe4m\xe4\xe4nty\xe4",u"h\xe4peill\xe4",u"h\xe4tk\xe4ht\xe4\xe4",u"h\xe4t\xe4\xe4nty\xe4",u"h\xe4vett\xe4\xe4",u"h\xe4vet\xe4",u"h\xf6lmisty\xe4",u"ihailla",u"ihannoida",u"ihastua",u"ihmetytt\xe4\xe4",u"ik\xe4v\xf6id\xe4",u"ilahduttaa",u"ilahtua",u"iloita",u"inhota",u"inhottaa",u"innostua",u"jurppia",u"j\xe4nnitt\xe4\xe4",u"j\xe4rkytty\xe4",u"kadehtia",u"kaduttaa",u"kaivata",u"kalvaa",u"kammoksua",u"kammota",u"kammottaa",u"karsastaa",u"katua",u"kauhistella",u"kauhistua",u"kauhistuttaa",u"kehdata",u"keljuttaa",u"kiehtoa",u"kiinty\xe4",u"kiivastua",u"kimmastua",u"kimpaantua",u"kiroiluttaa",u"kismitt\xe4\xe4",u"kiukustua",u"kiukuttaa",u"kiusaantua",u"kokea",u"korveta",u"kummastua",u"kummastuttaa",u"kummeksuttaa",u"kunnioittaa",u"kuohahtaa",u"kyll\xe4stytt\xe4\xe4",u"kyll\xe4sty\xe4",u"leipiinty\xe4",u"leip\xe4\xe4nty\xe4",u"liikuttua",u"loukkaantua",u"lumoutua",u"luottaa",u"mielty\xe4",u"murehduttaa",u"murehtia",u"murjottaa",u"mykisty\xe4",u"myrty\xe4",u"my\xf6t\xe4el\xe4\xe4",u"m\xf6k\xf6tell\xe4",u"m\xf6k\xf6tt\xe4\xe4",u"nauttia",u"nolostella",u"nolostua",u"nolostuttaa",u"nolottaa",u"n\xe4rk\xe4stytt\xe4\xe4",u"n\xe4rk\xe4sty\xe4",u"oudoksua",u"oudoksuttaa",u"pahastua",u"paheksua",u"pakahtua",u"pelj\xe4t\xe4",u"pelottaa",u"pel\xe4sty\xe4",u"pel\xe4t\xe4",u"petty\xe4",u"piitata",u"raivostua",u"raivostuttaa",u"rakastaa",u"rakastua",u"rassata",u"reagoida",u"riitaantua",u"rohjeta",u"surettaa",u"surra",u"suuttua",u"suututtaa",u"s\xe4ik\xe4ht\xe4\xe4",u"tahtoa",u"tohtia",u"tulistua",u"tuntea",u"tuohtua",u"turhauttaa",u"turhautua",u"tuskastua",u"tyk\xe4t\xe4",u"tymp\xe4ist\xe4",u"vaiva#utua",u"vaivata",u"vakuuttua",u"vieh\xe4tt\xe4\xe4",u"vihata",u"v\xe4litt\xe4\xe4",u"yll\xe4tty\xe4",u"\xe4rsytt\xe4\xe4",u"\xe4rsyynty\xe4",u"\xe4rty\xe4"]
	cogn=[u"aatella",u"aavistaa",u"aavistella",u"ajatella",u"ammentaa",u"analyseerata",u"analysoida",u"aprikoida",u"arvailla",u"arvata",u"arvella",u"arvottaa",u"arvuutella",u"asennoitua",u"askarruttaa",u"assosioida",u"ennakoida",u"ennustaa",u"ep\xe4ill\xe4",u"ep\xe4r\xf6id\xe4",u"eritell\xe4",u"fundeerailla",u"fundeerata",u"funteerata",u"funtsailla",u"funtsata",u"funtsia",u"haaveilla",u"hahmottaa",u"harkita",u"hokata",u"hoksata",u"huomata",u"huomioida",u"ideoida",u"ihmetell\xe4",u"jahkailla",u"jaotella",u"junailla",u"j\xe4rkeill\xe4",u"j\xe4sennell\xe4",u"j\xe4sent\xe4\xe4",u"kaavailla",u"kehitell\xe4",u"kekata",u"keksi\xe4",u"kelata",u"keskitty\xe4",u"kiinnostua",u"kiteytt\xe4\xe4",u"kiukutella",u"klaarata",u"kohdistaa",u"konstruoida",u"kuvitella",u"kypsytell\xe4",u"k\xe4sitt\xe4\xe4",u"laskelmoida",u"luokitella",u"luulla",u"mielikuvitella",u"mieli\xe4",u"mielt\xe4\xe4",u"mietiskell\xe4",u"mietitytt\xe4\xe4",u"mietti\xe4",u"muistaa",u"muistella",u"muistua",u"noteerata",u"oivaltaa",u"olettaa",u"omaksua",u"orientoitua",u"otaksua",u"ounastella",u"paneutua",u"panostaa",u"peilata",u"perehty\xe4",u"pohdiskella",u"pohjustaa",u"pohtia",u"priorisoida",u"punnita",u"puntaroida",u"p\xe4\xe4tell\xe4",u"rinnastaa",u"samaistaa",u"sis\xe4ist\xe4\xe4",u"summata",u"suunnitella",u"syventy\xe4",u"tajuta",u"tarkoittaa",u"tiedostaa",u"tiet\xe4\xe4",u"tulkita",u"tuumata",u"tuumia",u"unohtaa",u"uppoutua",u"vatvoa",u"veikata",u"ymm\xe4rt\xe4\xe4",u"\xe4lyt\xe4"]
	y=int(numb[0:4])
	n=int(numb[7:10])
	cur=db["ptk"].find({"_id":{"$gt":y*10000*1000+n*10000,"$lt":y*10000*1000+(n+1)*10000}}).sort("_id",1)
	source=[]
	for doc in cur:
		if doc["metadata"]["tyyppi"] in ["ilmasia","johdanto",u"p\xe4\xe4t\xf6s",u"p\xe4\xe4tt\xe4minen","loppu","foreword"]:
			# Skip text not related to anyone's speech, but keep it in the output for numbering consistency
			source.append({"id":doc["_id"],"text":doc["text"],"comment":"","tenses":[]})
			continue
		comment=""
		tenses=[]
		icount=0
		if not [w for w in doc["words"] if w["cpos"] in ["VERB","AUX"]]:
			comment+="-"
		for w in doc["words"]:
			if w["lemma"]=="kun":
				comment+="k"
				break
		for w in doc["words"]:
			if w["cpos"]=="VERB" and w["lemma"] in refer and "Person2" in w["feat"] and w["feat"]["Person2"]=="3" and "Voice2" in w["feat"] and w["feat"]["Voice2"]=="Act":
				comment+="r"
				break
		marked=[w for w in doc["words"] if "Tense2" in w["feat"]]
		active_flag=False
		for word in marked:
			if word["feat"]["Tense2"]=="Perf" and word["feat"]["Voice2"]=="Act":
				tenses.append("p")
			if word["feat"]["Tense2"]=="Kperf" and word["feat"]["Voice2"]=="Act":
				tenses.append("pk")
			if word["feat"]["Tense2"]=="Pperf":
				tenses.append("pp")
			if word["feat"]["Tense2"]!="Inf" and word["feat"]["Voice2"]=="Act":
				active_flag=True
			if word["feat"]["Tense2"]=="Impf":
				tenses.append("i")
				icount+=1
			if word["feat"]["Tense2"]=="Kond":
				tenses.append("k")
			if word["feat"]["Tense2"]!="Inf" and word["feat"]["Voice2"]=="Act":
				active_flag=True
		if "p" in tenses or "pk" in tenses:
			comment+="p"
		if ("i" in tenses or "pp" in tenses): #and active_flag:
			comment+="i"
		if icount>=3:
			comment+="I"
		source.append({"id":doc["_id"],"text":doc["text"],"comment":comment,"tenses":list(set(tenses))})

	stats={"k":0,"p":0,"r":0}
	triplets=[]
	nums=[i for i in range(0,len(source)) if "k" in source[i]["comment"] or "p" in source[i]["comment"] or "r" in source[i]["comment"]]
	imps=[i for i in range(0,len(source)) if "i" in source[i]["comment"]]
	blanks=[i for i in range(0,len(source)) if "-" in source[i]["comment"]]
	chains=[]
	# Look for narratives: any sentence with 'k' or 'p' or 'r',
	# followed by at least two sentences with 'i' or one with 'I',
	# adding any more sentences with 'i' directly before and after these
	for n in nums:
		mce=-1
		mcs=-1
		k=n+1
		cblank=0
		while k in imps+blanks: #extend right
			if k in blanks:
				cblank+=1
			k=k+1
		if k>n+2+cblank:
			mce=k-1
			mcs=n
		if mcs>0: #extend left
			k=mcs
			while k-1 in imps+blanks and k>0:
				k=k-1
			mcs=k
		while mcs in blanks:
			mcs+=1
		while mce in blanks:
			mce-=1
		if mcs>=0 and mce>=0: #valid narrative
			if [mcs,mce] not in chains:
				chains.append([mcs,mce])
			if "k" in source[n]["comment"]:
				stats["k"]+=1
			if "p" in source[n]["comment"]:
				stats["p"]+=1
			if "r" in source[n]["comment"]:
				stats["r"]+=1
			triplets.append((n+1,mcs+1,mce+1))
	i=0
	# Remove overlapping ranges
	while i<len(triplets)-1:
		curr=triplets[i]
		next=triplets[i+1]
		if next[1]>curr[1]:
			if next[2]>curr[2]:
				i+=1
				continue
			else:
				del triplets[i+1]
				continue
		if next[1]==curr[1]:
			if next[2]>=curr[2]:
				del triplets[i]
				continue
			else:
				i+=1
				continue
	tmp=[]
	if len(chains)>1:
		frames=chains[0][0]
		framee=chains[0][1]
		for i in range(1,len(chains)):
			if chains[i][1]>framee and chains[i][0]<=framee+1:
				framee=chains[i][1]
			if chains[i][0]>framee+1 or chains[i][1]<frames-1:
				tmp.append([frames,framee])
				frames=chains[i][0]
				framee=chains[i][1]
				continue
		tmp.append([frames,framee])
	# Include 1-sentence gaps between two ranges
	bridges=[]
	for b in range(0,len(tmp)-1):
		if tmp[b][1]+2==tmp[b+1][0]:
			bridges.append(tmp[b][1]+1)
	if len(chains)==1:
		tmp=[list(chains[0])]
	chains=list(tmp)

	numbers=[]
	keynumbers=[]
	brnumbers=[]
	imnumbers=[]
	for p in nums:
		keynumbers.append((source[0]["id"]%10000)+p)
	for p in imps:
		imnumbers.append((source[0]["id"]%10000)+p)
	if chains: #and not (len(questions[k][0]["chains"])==1 and questions[k][0]["chains"][0][1]-questions[k][0]["chains"][0][0]<4):
		for p in chains:
			numbers.append(((source[0]["id"]%10000)+p[0],(source[0]["id"]%10000+p[1])))
		for i in range(0,len(source)):
			if i in bridges:
				brnumbers.append((source[0]["id"]%10000)+i)

	ks=[i+1 for i in range(0,len(source)) if "k" in source[i]["comment"]]
	rs=[i+1 for i in range(0,len(source)) if "r" in source[i]["comment"]]
	perfs=[i+1 for i in range(0,len(source)) if "p" in source[i]["comment"]]
	pps=[i+1 for i in range(0,len(source)) if "pp" in source[i]["tenses"]]
	pks=[i+1 for i in range(0,len(source)) if "pk" in source[i]["tenses"]]
	ps=[i+1 for i in range(0,len(source)) if "p" in source[i]["tenses"]]
	#perfs includes conditional perfect in addition to "plain" present perfect, ps doesn't

	i=0
	while i<len(numbers)-1:
		for br in brnumbers:
			if numbers[i][1]+1==br:
				numbers[i]=(numbers[i][0],numbers[i+1][1])
				del numbers[i+1]
				i-=1
				break
		i+=1

	imnumbers=[i for i in imnumbers if "i" in source[i-1]["tenses"]]
	knumbers=[i+1 for i in range(0,len(source)) if "k" in source[i]["tenses"]]
	temp={}
	#print(triplets)
	for i in triplets:
		temp[i[0]]=source[i[0]-1]["comment"]
	#temp={(i+1):source[i[0]-1]["comment"] for i in triplets}
	print(temp)
	print(numbers)
	return {"analysis":temp, "narratives":numbers, "m_imps": [i+1 for i in range(0,len(source)) if "I" in source[i]["comment"]], "empty": [i+1 for i in range(0,len(source)) if "-" in source[i]["comment"]], "konds":[int(p) for p in knumbers], "bridges":[int(p) for p in brnumbers], "imps":[int(p) for p in imnumbers], "ks":ks, "rs":rs, "perfs":perfs, "pps":pps, "pks":pks, "ps":ps,"stats":stats}

# Correct narrative ranges from annotated files
answers={"1999ptk087": [(70,83),(205,209)],
"1999ptk123": [(858,865),(1070,1081)],
"1999ptk129": [(766,775),(871,880),(1435,1446),(2419,2426),(2883,2890),(4289,4307)],
"2000ptk008": [(192,198),(1176,1186),(1223,1240),(1904,1909)],
"2000ptk061": [],
"2000ptk064": [(494,505)],
"2005ptk017": [(67,84),(282,289),(633,638),(788,795),(1001,1010),(1052,1061)],
"2005ptk041": [(52,73),(268,284),(469,483)],
"2005ptk117": [(711,715)],
"2007ptk059": [(492,496),(504,533),(689,701),(2399,2404)],
"2007ptk074": [],
"2007ptk095": [(32,39)],
"2012ptk045": [],
"2012ptk052": [],
"2012ptk091": [(428,452),(471,481),(608,632),(730,742),(759,768),(894,921),(935,941)],
"2014ptk030": [(759,766)],
"2014ptk085": [(99,117),(134,146),(1187,1195),(2597,2599)],
"2014ptk141": [(121,125)],
"2015ptk038": [],
"2015ptk042": [(2264,2271),(3431,3437),(3543,3548)],
"2015ptk051": [(416,421)],
"2016ptk005": [],
"2016ptk021": [],
"2016ptk112": [(587,598),(1965,1969)],
"2017ptk047": [(840,846),(1088,1098)],
"2017ptk085": [],
"2017ptk115": [(316,323)],
"2018ptk026": [(84,93),(269,277),(369,374)],
"2018ptk034": [(835,847),(928,939),(1158,1161)],
"2018ptk082": [],
"1999ptk104": [],
"1999ptk126": [(308,325),(449,462)],
"1999ptk130": [(647,660),(712,726),(837,858),(2105,2123),(2312,2322),(3526,3594),(3826,3853)],
"2000ptk065": [],
"2000ptk079": [(140,164),(278,299),(439,447)],
"2000ptk137": [(987,1003)],
"2001ptk083": [(2101,2150),(2420,2430),(2496,2541),(2560,2588),(2848,2859),(2868,2879),(3387,3433),(4349,4359),(5147,5172)],
"2001ptk122": [(422,438),(525,545),(804,828),(1059,1069)],
"2001ptk132": [(290,297)],
"2002ptk131": [(28,44),(55,97)],
"2002ptk184": [(21,45),(97,103)],
"2002ptk196": [],
"2003ptk036": [],
"2003ptk056": [(213,230),(244,260),(284,298),(299,306)],
"2003ptk099": [(772,800)],
"2004ptk026": [(69,80),(583,592),(665,672)],
"2004ptk095": [(102,107),(151,159),(772,788),(966,998)],
"2004ptk105": [(243,305)],
"2005ptk031": [(190,193),(213,216),(333,339),(456,467),(504,513),(521,546),(582,590),(626,646)],
"2005ptk120": [(374,381),(383,394),(488,496)],
"2005ptk124": [(3,37),(100,127),(142,156),(570,577)],
"2006ptk019": [(920,927),(1178,1188)],
"2006ptk032": [(409,428),(555,568)],
"2006ptk140": [(620,629),(1031,1042)],
"2007ptk010": [(10,22),(481,515),(786,799),(801,812),(816,858)],
"2007ptk083": [(530,540),(585,596),(1520,1546),(1553,1568),(1708,1717)],
"2007ptk089": [(538,551),(836,842),(908,918)],
"2008ptk071": [(29,49),(85,93),(130,133),(298,311),(646,658),(1429,1435),(1440,1469),(1548,1558)],
"2008ptk095": [(265,324),(367,388),(392,399),(514,523),(992,996)],
"2008ptk097": [(248,255),(599,608),(892,913)]}

# Correct "almost-narrative" ranges
answers["1999ptk123"]+=[(81,84),(119,125),(131,131),(489,498),(1049,1052),(1205,1207)]
answers["1999ptk129"]+=[(1590,1603),(2807,2811),(3084,3090),(3096,3099),(3255,3264),(3506,3517),(3928,3931),(4308,4315)]
answers["2000ptk008"]+=[(199,202),(252,255),(1388,1396)]
answers["2005ptk041"]+=[(485,488)]
answers["2005ptk117"]+=[(986,1003)]
answers["2014ptk141"]+=[(672,677)]
answers["2015ptk038"]+=[(943,958)]
answers["2015ptk042"]+=[(1369,1375),(1580,1584),(2102,2106),(2851,2855)]
answers["2015ptk051"]+=[(21,31),(553,560)]
answers["2016ptk005"]+=[(262,267),(970,974)]
answers["2016ptk021"]+=[(847,854)]
answers["2016ptk112"]+=[(601,603),(641,643),(659,664)]
answers["2017ptk085"]+=[(272,275)]
answers["2017ptk115"]+=[(301,305),(311,313),(349,351),(547,550),(643,648)]
answers["2018ptk026"]+=[(338,342),(352,358),(394,410)]
answers["2018ptk034"]+=[(359,365),(486,496),(498,501),(526,528),(581,588),(672,677),(887,890),(1023,1025),(1228,1231),(1285,1291)]
answers["2018ptk082"]+=[(546,550),(559,562)]
goodsums={"k":0,"p":0,"r":0}
badsums={"k":0,"p":0,"r":0}
count=0

for code in sorted(answers.keys()):
	for name in glob.glob("????ptk???.txt"):
		if name.split("/")[-1].startswith(code):
			struct=get_narratives(code)
# The next loop only serves to count how many times each key feature
# contributed to "good" (actual narrative) and "bad" fragments
			for k in struct["analysis"].keys():
				rge=(-1,-1)
				good=False
				for pair in struct["narratives"]:
					if k>=pair[0] and k<=pair[1]:
						rge=(pair[0],pair[1])
						break
				if rge==(-1,-1):
					print("!")
				for pair in answers[code]:
					if not (rge[1]<pair[0] or rge[0]>pair[1]):
						good=True
						break
				if "k" in struct["analysis"][k]:
					if good:
						goodsums["k"]+=1
					else:
						badsums["k"]+=1
				if "p" in struct["analysis"][k]:
					if good:
						goodsums["p"]+=1
					else:
						badsums["p"]+=1
				if "r" in struct["analysis"][k]:
					if good:
						goodsums["r"]+=1
					else:
						badsums["r"]+=1
			count+=len(struct["analysis"])
			print(show(name,struct,answers[code]))
			break
print(goodsums)
print(badsums)
print(count)