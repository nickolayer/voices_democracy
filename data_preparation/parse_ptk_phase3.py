import io
import re
import os
from glob import glob

# This script performs the processing of phase 3 parliamentary records (from 2015 and later).
# It separates the original files into text and metadata, runs them through the dependency parser
# and adds page numbers to individual sentences.
# The final DB-ready outputs are already provided elsewhere;
# this script is only needed to change their construction process.

def save(what,attr,where):
# Writes out metadata-text line pairs for one paragraph at a time.
	#if attr["snoviite"]==1: #nimenhuuto
	#	return
	if attr["snoviite"]==2 and attr["asia"]=="Ilmoituksia":
		attr["tyyppi"]="ilmasia"
	if attr["asia"]=="Suullinen kyselytunti" and attr["tyyppi"] not in ["johdanto",u"p\xe4\xe4t\xf6s","puhemies"]:
		attr["tyyppi"]="sktpuheenvuoro"
	if attr["asia"]==u"Seuraava t\xe4ysistunto":
		attr["tyyppi"]=u"p\xe4\xe4tt\xe4minen"
	cp=dict(attr)
	pvuoro_props=["etunimi","sukunimi","ekryhma","asema","gov"]
	if "tyyppi" in cp:
		if cp["tyyppi"]=="puhemies":
			for prop in pvuoro_props:
				if prop in cp:
					del cp[prop]
		if cp["tyyppi"]=="johdanto" or cp["tyyppi"]==u"p\xe4\xe4t\xf6s":
			for prop in pvuoro_props+["pnro","pjnro"]:
				if prop in cp:
					del cp[prop]
			if "ptkviite" in cp:
				temp=cp["ptkviite"].split("/")
				if len(temp)>2:
					cp["ptkviite"]=temp[0]+"/"+temp[1]
	where.write("###C:PTK|"+"|".join([k+"="+str(cp[k]) if isinstance(cp[k],int) else k+"="+cp[k] for k in cp])+"\n")
	where.write(re.sub(" {2,}"," ",what).strip()+"\n")

def split_file(name):
# Splits an original phase 3 document (text from PDF) into text and metadata:
# one line of paragraph metadata, followed by one line of paragraph text.
	attribs={"paragraph":1,"pjnro":0,"snoviite":0}
	inf=io.open(name,"r",encoding="utf-8")
	lines=inf.read(-1).replace("\r\n","\n").split("\n")
	inf.close()
	outf=io.open(name.replace(".txt","_split.txt"),"w",encoding="utf-8")
	text=""
	accum=""
	count=0
	pnro=0
	oldtype=""
	asia_ongoing=False
	skip_one=False
	indented=False
	pvuoro_props=["etunimi","sukunimi","ekryhma","asema","gov"]
	asia_props=["sasia","aktyyppi","akviite","kasvaihe"]+pvuoro_props
	codes=["Hallituksen esitys HE","Lakialoite LA","Kertomus K","Valtioneuvoston selonteko VNS","Keskustelualoite KA","Toimenpidealoite TPA","Talousarvioaloite TAA",u"Vapautuspyynt\xf6 VAP",u"P\xe4\xe4ministerin ilmoitus PI","Valtioneuvoston tiedonanto VNT","Vaali VAA","Kansalaisaloite KAA","Suullinen kysymys SKT",u"V\xe4likysymys VK",u"Lep\xe4\xe4m\xe4\xe4n hyv\xe4ksytty lakiehdotus LJL",u"Valtioneuvoston kirjelm\xe4 VN",u"Eduskuntaty\xf6n j\xe4rjest\xe4minen ETJ","Muu asia M","Puhemiesneuvoston ehdotus PNE"]
	pcodes={u"Ensimm\xe4inen":u"ensimmainen","Toinen":"toinen","Kolmas":"kolmas","Yksi":"yksikasittely","Ainoa":"ainoa","Osittain ainoa, osittain toinen":"toinenainoa"}
	govs=[{"from":"2014-04-04","to":"2014-06-23","parties":["sd","kok","vihr","kd","rkp"]},{"from":"2014-06-24","to":"2014-08-18","parties":["sd","kok","vihr","kd","rkp"]},{"from":"2014-09-18","to":"2015-05-28","parties":["sd","kok","kd","rkp"]},{"from":"2015-05-29","to":"2017-06-12","parties":["kok","kesk","ps"]},{"from":"2017-06-13","to":"2019-06-05","parties":["kok","kesk","si","sin"]},{"from":"2019-06-06","to":"2019-12-09","parties":["sd","kesk","vihr","vas","rkp"]},{"from":"2019-12-10","to":"2021-10-10","parties":["sd","kesk","vihr","vas","rkp"]}]
	for i in range(0,len(lines)):
		if "\x0C" in lines[i]:
			attribs["versio"]=lines[i-1].strip()
			attribs["tila"]=lines[i-2].strip()
			break
	for i in range(0,17):
		if re.search("\d{1,2}\.\d{1,2}.\d{4}",lines[i]) is not None:
			dt=lines[i].split()
			kaika=dt[3][0:5]
			if u"\u2014" in kaika:
				kaika="0"+dt[3][0:4]
			parts=dt[1].split(".")
			if len(parts[0])==1:
				parts[0]="0"+parts[0]
			if len(parts[1])==1:
				parts[1]="0"+parts[1]
			attribs["date"]="-".join(parts[::-1])+" "+kaika
			break
	dt=attribs["date"][0:10]
	attribs["tunniste"]=lines[0][lines[0].index("PTK"):].strip()
	attribs["tunniste"]=attribs["tunniste"].split(" ")[1].split("/")[1]
	attribs["inro"]=int(lines[0][lines[0].index("PTK ")+4:lines[0].index("/")])
	for i in range(0,len(lines)):
		count+=1
		indented=(len(lines[i].lstrip())<len(lines[i]))
		if skip_one:
			skip_one=False
			continue
		if not lines[i] or lines[i]=="\n" or lines[i]=="\f":
			asia_ongoing=False
			continue
		if asia_ongoing:
			if lines[i][0]==" " or lines[i]=="\n":
				asia_ongoing=False
			else:
				if attribs["asia"][-1]=="-":
					attribs["asia"]=attribs["asia"][:-1]+lines[i].strip()
				else:
					attribs["asia"]+=" "+lines[i].strip()
				continue
		coded=False
		for code in codes:
			cname=code.split(" ")[:-1]
			cmark=code.split(" ")[-1]
			if lines[i].lstrip().startswith(code) and "vp" in lines[i] and "vp)" not in lines[i]:
				attribs["aktyyppi"]=" ".join(cname)
				attribs["akviite"]=lines[i][lines[i].index(cmark+" "):lines[i].index("vp")+2]
				coded=True
				break
		for pcode in pcodes:
			if lines[i].lstrip().startswith(pcode+u" k\xe4sittely"):
				attribs["kasvaihe"]=pcodes[pcode]
				coded=True
				break
		if coded:
			continue
		if "Valiokunnan" in lines[i] and "vp" in lines[i]:
			continue
		if u"P\xf6yt\xe4kirja" in lines[i] and "vp" in lines[i]:
			continue
		if u"P\xf6yt\xe4kirjan vakuudeksi" in lines[i]:
			continue
		if lines[i].strip()=="Keskustelu":
			continue
		if "Suullinen kyselytunti" in lines[i] and attribs["asia"]=="Suullinen kyselytunti" and attribs["sasia"].startswith("Suullinen kysymys"):
			attribs["tyyppi"]=u"p\xe4\xe4t\xf6s"
			continue
		if u"Kysymyksen k\xe4sittely p\xe4\xe4ttyi" in lines[i]:
			attribs["tyyppi"]=u"p\xe4\xe4t\xf6s"
		if u"Mietinn\xf6n p\xf6yd\xe4llepano" in lines[i]:
			attribs["kasvaihe"]="mietpoydallepano"
			continue
		if re.match(u" {1,}L\xe4hetekeskustelu[^asnulk]",lines[i]) is not None: #or u"p\xf6yd\xe4llepano" in lines[i]:
			continue
		if u"Keskustelu p\xe4\xe4tt" in lines[i] or u"Yleiskeskustelu p\xe4\xe4tt" in lines[i]:
			attribs["tyyppi"]=u"p\xe4\xe4t\xf6s"
			for key in pvuoro_props:
				if key in attribs:
					del attribs[key]
		if count<15 and re.search("\d{1,2}\.\d{1,2}.\d{4}",lines[i]) is not None:
			continue
		if count<60 and count>50 and lines[i].count(" ")>90:
			continue
		lines[i]=lines[i].strip()
		if lines[i].isdigit():
			continue
		if "snoviite" in attribs and re.match(str(attribs["snoviite"])+"\.\d{1,2}\. [A-Z]",lines[i]) is not None and (not indented):
			if text.strip():
				save(text,attribs,outf)
				attribs["paragraph"]+=1
				text=""
			attribs["sasia"]=lines[i][lines[i].index(" ")+1:].strip()
			if attribs["sasia"].startswith("Suullinen kysymys") and "Suullinen kysymys SKT" not in lines[i+1]:
			# wraps to next line
				if lines[i].endswith("-"):
					attribs["sasia"]=attribs["sasia"][:-1]+lines[i+1].strip()
				else:
					attribs["sasia"]+=" "+lines[i+1].strip()
				skip_one=True
			continue
		if re.match(str(attribs["snoviite"]+1)+" {0,1}\. (?!asia)",lines[i]) is not None and ("kannattamana" not in lines[i]) and ("lakiehdotuksen" not in lines[i]) and (". lakiehdotus" not in lines[i]) and lines[i].split(" ")[-1].strip() not in ["ps","kok","vihr","vas","r","kesk","kd","sd"] and (not indented): #(("asia" not in attribs) or ("vaali" not in attribs["asia"])):
			if text.strip():
				save(text,attribs,outf)
				attribs["paragraph"]+=1
				text=""
			attribs["asia"]=lines[i][lines[i].index(" ")+1:].strip()
			for key in asia_props:
				if key in attribs:
					del attribs[key]
			asia_ongoing=True
			attribs["pjnro"]=0
			attribs["tyyppi"]="johdanto"
			attribs["snoviite"]=int(lines[i][:lines[i].index(".")])
			continue
		if lines[i].strip()==u"L\xe4hetekeskustelu" and attribs["tyyppi"]=="johdanto":
			attribs["kasvaihe"]="lahetekeskustelu"
			continue
		if re.search(u"(Ensimm\xe4inen varapuhemies|Toinen varapuhemies|Puhemies) [A-Z][\w-]+ [A-Z][\w-]+:",lines[i],re.UNICODE) is not None:
			if attribs["tyyppi"]!="johdanto":
				attribs["tyyppi"]="puhemies"
			lines[i]=lines[i][lines[i].index(": ")+2:]
		if "asia" not in attribs:
			continue
		if "Jaakko Jonkka :" in lines[i]: # for 2016ptk083
			lines[i]=lines[i].replace("Jaakko Jonkka :","Valtioneuvoston oikeuskansleri Jaakko Jonkka:")
		if "14.01 Jaakko Jonkka (esittelypuheenvuoro):" in lines[i]: # for 2016ptk083
			lines[i]=lines[i].replace("14.01 Jaakko Jonkka (esittelypuheenvuoro):", "14.01 Valtioneuvoston oikeuskansleri Jaakko Jonkka (esittelypuheenvuoro):")
		if len(lines[i])>=6 and re.match("\d{1,2}\.\d\d ",lines[i]) is not None and lines[i].endswith("-") and ":" not in lines[i] and ("ministeri" in lines[i]):
#very long titles, such as Ulkomaankauppa- ja kehitysministeri Lenita Toivakka (esittelypuheenvuoro), don't fit on one line
#and the colon wraps onto the next one; this attempts to "undo" the wrap, moving the whole intro back to the original line
			temp=lines[i+1].lstrip()
			spaces=len(lines[i+1])-len(temp)
			lines[i]=lines[i][:-1]+temp[:temp.index(":")+1]+" "
			lines[i+1]=lines[i+1][0:spaces]+temp[temp.index(":")+2:]
		if (len(lines[i])>=6 and re.match("\d{1,2}\.\d\d ",lines[i]) is not None and ":" in lines[i]) or accum: #new speech block
			if text:
#If the previous paragraph was not terminated, save it now
				if "pjnro" in attribs and attribs["pjnro"]>0:
					attribs["ptkviite"]=str(attribs["inro"])+"/"+str(attribs["snoviite"])+"/"+str(attribs["pjnro"])
				else:
					attribs["ptkviite"]=str(attribs["inro"])+"/"+str(attribs["snoviite"])
				temp={}
				if attribs["tyyppi"]=="puhemies":
					for k in pvuoro_props:
						if k in attribs:
							temp[k]=attribs[k]
							del attribs[k]
					temp["tyyppi"]=oldtype
				save(text,attribs,outf)
				if attribs["tyyppi"]=="puhemies":
					attribs.update(temp)
				attribs["paragraph"]+=1
				text=""
			lines[i]=" ".join(lines[i].split())
			if ":" not in lines[i]:
				accum=lines[i]
				continue
			if accum:
				lines[i]=accum[:-1]+lines[i]
			parts=lines[i][0:lines[i].index(":")].split(" ")
			sbb=0
			if "(vastauspuheenvuoro)" in lines[i]:
				attribs["tyyppi"]="vastaus"
				sbb=1
			elif "(esittelypuheenvuoro)" in lines[i]:
				attribs["tyyppi"]="esittely"
				sbb=1
			else:
				attribs["tyyppi"]="varsinainen"
			oldtype=attribs["tyyppi"]
			if "ministeri" not in lines[i] or lines[i].index("ministeri")>lines[i].index(":"): #MP
			#alternatively: if parts[1][0].isupper() and parts[2][0].isupper()
				attribs["etunimi"]=parts[1]
				attribs["sukunimi"]=parts[2]
				if len(parts)>3:
					attribs["ekryhma"]=parts[3]
					attribs["asema"]="edustaja"
				else:
					attribs["asema"]="muu"
			else:
				if parts[-1-sbb] in ["kesk","kok","sd","vihr","ps","r","vas","skl","erl","rem","alk","kd","lib"]:
					attribs["ekryhma"]=parts[-1-sbb]
					sbb+=1
				elif "ekryhma" in attribs:
					del attribs["ekryhma"]
				attribs["sukunimi"]=parts[-1-sbb]
				attribs["etunimi"]=parts[-2-sbb]
				attribs["asema"]=" ".join(parts[1:-2-sbb])
			if "Timo V. Korhonen" in lines[i]:
				attribs["sukunimi"]="Korhonen"
				attribs["etunimi"]="Timo V."
				attribs["ekryhma"]="kesk"
				attribs["asema"]="edustaja"
			if "Suldaan Said Ahmed" in lines[i]:
				attribs["sukunimi"]="Said Ahmed"
				attribs["etunimi"]="Suldaan"
				attribs["ekryhma"]="vas"
				attribs["asema"]="edustaja"
			if (re.search("\d\.\d{2} Eduskunnan oikeusasiamies",lines[i]) is not None) or (re.search("\d\.\d{2} Valtioneuvoston oikeuskansleri",lines[i]) is not None):
				attribs["asema"]=parts[1]+" "+parts[2]
				attribs["sukunimi"]=parts[4]
				attribs["etunimi"]=parts[3]
				if "ekryhma" in attribs:
					del attribs["ekryhma"]
			if attribs["sukunimi"]=="Hiekkataipale" and attribs["etunimi"]=="Risto": # for 2017ptk070
				attribs["asema"]="Apulaisoikeuskansleri"
				if "ekryhma" in attribs:
					del attribs["ekryhma"]
			if "asema" in attribs:
				if attribs["asema"]=="edustaja":
					for gv in govs:
						if dt>=gv["from"] and dt<=gv["to"]:
							attribs["gov"]=(attribs["ekryhma"] in gv["parties"])
							break
				elif "gov" in attribs:
					del attribs["gov"] # or try placing it when a speech block is flushed, if that's observable
			if accum:
				accum=""
			text=""
			lines[i]=lines[i][lines[i].index(":")+2:]
			attribs["pjnro"]+=1
			pnro+=1
			attribs["pnro"]=pnro
		text+=lines[i]
		if text.endswith("-"):
			text=text[:-1]
		elif text.endswith(("?","!",":",".",")","]",'"',u"\u201d")):
		#if the next line exists, has text but is not indented, the paragraph continues without saving
			if i<len(lines)-1 and lines[i+1] and lines[i+1][0]!=" ":
				text+=" "
				continue
			if "pjnro" in attribs and attribs["pjnro"]>0:
				attribs["ptkviite"]=str(attribs["inro"])+"/"+str(attribs["snoviite"])+"/"+str(attribs["pjnro"])
			else:
				attribs["ptkviite"]=str(attribs["inro"])+"/"+str(attribs["snoviite"])
			temp={}
			if attribs["tyyppi"]=="puhemies":
				for k in pvuoro_props:
					if k in attribs:
						temp[k]=attribs[k]
						del attribs[k]
				temp["tyyppi"]=oldtype
			save(text,attribs,outf)
			if attribs["tyyppi"]=="puhemies":
				attribs.update(temp)
			attribs["paragraph"]+=1
			text=""
		else:
			text+=" "
	outf.close()

def group_texts(textpath,packpath,maxlines):
# Concatenates individual split files into larger packs.
# The last file that goes over the maxlines limit will be fully included.
	count=1
	outf=io.open(packpath+os.sep+"pack"+str(count).rjust(2,"0")+"_split.txt","w",encoding="utf-8")
	lines=0
	for name in sorted(glob(textpath+os.sep+"*_split.txt")):
		inf=io.open(name,"r",encoding="utf-8")
		for line in inf:
			outf.write(line)
			lines+=1
		inf.close()
		if lines>=maxlines:
			outf.close()
			count+=1
			outf=io.open(packpath+os.sep+"pack"+str(count).rjust(2,"0")+"_split.txt","w",encoding="utf-8")
			lines=0
	outf.close()

def test_file(filename):
# Complains if a split file or pack doesn't have metadata in odd-numbered lines,
# or has them in even-numbered lines.
	file=io.open(filename,"r",encoding="utf-8")
	count=0
	for line in file:
		count+=1
		if ("###C:" not in line and count%2==1) or ("###C:" in line and count%2==0):
			print("Error in line "+str(count)+", file "+filename)
			print(line)
			break
	file.close()
	
def mark_pages(filename,raw_path):
# Adds page numbers to every sentence of a parsed file.
# They are drawn from the original text files, where page breaks are form feed characters.
# The parsed file may contain multiple documents, which should have their originals stored under raw_path.
# For example, document PTK 138/2020 vp (which has vp=2020 and inro=138) requires the original file 2020ptk138.txt.
	docid="1900ptk000"
	old_docid=docid
	page=1
	pos=0
	written_page=1
	buffer=[]
	copy=""
	parstart=-1
	sentstart=-1
	parflag=False
	source=io.open(filename,"r",encoding="utf-8")
	dest=io.open(filename.replace("_parsed","_final"),"w",encoding="utf-8")
	for line in source:
		if line.startswith("###C:"):
			attribs=line.replace("\n","").split("|")
			attribs={pair.split("=")[0]:pair.split("=")[1] for pair in attribs [1:]}
			docid=str(attribs["vp"])+"ptk"+str(attribs["inro"]).rjust(3,"0")
			if docid!=old_docid:
				print(docid)
				raw=io.open(raw_path+docid+".txt","r",encoding="utf-8")
				s=raw.read()
				raw.close()
				lines=[x.strip(" ") for x in s.split("\r\n")]
				for i in range(0,len(lines)-1):
					if not lines[i]:
						continue
					if lines[i][-1]=="-":
# if a line ends in a hyphen, the remainder of the word must be found on the next line, deleted from there and glued to the beginning
						next=i+1
						if not lines[i+1]: # page break
# in case of a page break, the next line continues only after the page's footer, so a few lines before that must be skipped
							for j in range(i+1,i+20):
# furthermore, the first page's footer contains the document's version and status, not the page number like all subsequent ones
								if lines[j] and (not lines[j].isdigit()) and (re.search(u"P\xf6yt\xe4kirja PTK \d{1,3}/\d{1,4} vp",lines[j]) is None) and (re.match("\d\.\d{1,2}",lines[j].strip()) is None) and (lines[j].strip() not in ["Valmis","Tarkistettu",u"Hyv\xe4ksytty"]):
									next=j
									break
						if " " in lines[next]:
							idx=lines[next].index(" ")
							lines[i]=lines[i][:-1]+lines[next][:idx]
							lines[next]=lines[next][idx+1:]
						else:
							lines[i]=lines[i][:-1]+lines[next]
							lines[next]=""
					i+=1
				s=" ".join(lines)
				if buffer:
					while parstart>pages[page]:
						page+=1
					copy=copy.replace("\n","|page="+str(page)+"\n")
					dest.write(copy)
					for b in buffer:
						dest.write(b)
				pages=[0]+[m.start(0) for m in re.finditer("\x0C",s)]
				pages.append(99999999)
				old_docid=docid
				page=1
				pos=0
				written_page=1
				buffer=[]
				copy=""
				parstart=-1
				sentstart=-1
				parflag=False
			if parflag:
				copy=copy.replace("\n","|page="+str(page)+"\n")
				dest.write(copy)
				dest.write("\n")
			if buffer:
				while parstart>pages[page]:
					page+=1
				copy=copy.replace("\n","|page="+str(page)+"\n")
				dest.write(copy)
				for b in buffer:
					dest.write(b)
				buffer=[]
				parstart=-1
				sentstart=-1
			copy=line
			parflag=True
			continue
		if line=="" or line=="\n": #end of sentence
			temppage=page
			while sentstart>pages[temppage]:
				temppage+=1
			if temppage>written_page:
				written_page=temppage
				i=len(buffer)-1
				while buffer[i]!="\n":
					i-=1
				buffer.insert(i+1,"###C:PAGE|page="+str(temppage)+"\n")
			buffer.append(line)
			sentstart=-1
			continue
		parflag=False
		word=line.split("\t")[1]
		print((word,pos))
		pos+=s[pos:].index(word)+len(word)
		if parstart==-1:
			parstart=pos-len(word)
			written_page=page
			while parstart>pages[written_page]:
				written_page+=1
		if sentstart==-1:
			sentstart=pos-len(word)
		buffer.append(line)
	source.close()
	while parstart>pages[page]:
		page+=1
	copy=copy.replace("\n","|page="+str(page)+"\n")
	dest.write(copy)
	for b in buffer:
		dest.write(b)
	dest.close()
	
# Main routine:
# Download the original PDFs, for example, https://www.parliament.fi/FI/vaski/Poytakirja/Documents/PTK_138+2020.pdf
# (138 is the document number, 2020 is the year)
# Rename these files to 2020ptk138.pdf, for example:
# rename 's/PTK_(\d{1})\+2020.pdf/2020ptk00$1.pdf/' *.pdf
# rename 's/PTK_(\d{2})\+2020.pdf/2020ptk0$1.pdf/' *.pdf
# rename 's/PTK_(\d{3})\+2020.pdf/2020ptk$1.pdf/' *.pdf
# Convert all PDFs into text:
# pdftotext -layout 2020ptk138.pdf

# Separate text from metadata
os.chdir("./texts") # path to raw text files, e.g. 2020ptk138.txt
for file in glob("./*.txt"):
	if "split" not in file:
		print("Splitting "+file)
		split_file(file)

# Stack split files into larger packs
group_texts(".","../packs",25000)

# Test the structure of packs
for file in sorted(glob("../packs/pack??_split.txt")):
	test_file(file)

# Parse the packs
os.chdir("Finnish-dep-parser")
for file in glob("../packs/pack??_split.txt"):
	runstr="./split_text_with_comments.sh < \""+file+"\" | ./parse_conll.sh | python split_clauses.py > \""+file.replace("split","parsed")+"\""
	print("Parsing "+file)
	os.system(runstr)

# Add page numbers
for file in sorted(glob("../packs/pack??_parsed.txt")):
	mark_pages(file,"/txt/")

# Files pack??_final.txt are now suitable for DB insertion