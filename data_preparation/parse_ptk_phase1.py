import codecs
from re import search, match
from glob import glob

# This script performs the processing of phase 1 parliamentary records (1976-1999).
# It separates the original files into text and metadata;
# stacking them into packs and parsing is the same as in phase 3,
# while page numbers cannot be added at all.
# The final DB-ready outputs are already provided elsewhere;
# this script is only needed to change their construction process.

def is_oppos(party,ds):
	govs=[{"from":"1979-05-26","to":"1982-02-18","parties":["sd","kesk","r","skdl"]},
{"from":"1982-02-19","to":"1982-12-31","parties":["sd","kesk","r","skdl"]},
{"from":"1983-01-01","to":"1983-05-05","parties":["sd","kesk","r","lkp"]},
{"from":"1983-05-06","to":"1987-04-29","parties":["sd","kesk","r","smp"]},
{"from":"1987-04-30","to":"1990-08-28","parties":["sd","kok","r","smp"]},
{"from":"1990-08-29","to":"1991-04-25","parties":["sd","kok","r"]},
{"from":"1991-04-26","to":"1994-06-28","parties":["kesk","kok","r","skl"]},
{"from":"1994-06-29","to":"1995-04-12","parties":["kesk","kok","r"]},
{"from":"1995-04-13","to":"1999-04-14","parties":["sd","kok","vihr","vas","r"]},
{"from":"1999-04-15","to":"2002-05-31","parties":["sd","kok","vihr","vas","r"]},
{"from":"2002-06-01","to":"2003-04-16","parties":["sd","kok","vas","r"]}]
	for gov in govs:
		if ds>=gov["from"] and ds<=gov["to"]:
			return (party in gov["parties"])
	return None
	
def helper(file,line,metadata):
# Writes out metadata-text line pairs for one paragraph at a time.
	file.write("###C:PTK|"+"|".join([k+"="+metadata[k] for k in metadata])+"\n")
	line=line.replace("ed.","edustaja").replace("Ed.","Edustaja")
	file.write(line.replace("\n"," ").replace("  "," ").strip()+"\n")

def split(filename):
# Splits an original phase 1 document (text from PDF) into text and metadata:
# one line of paragraph metadata, followed by one line of paragraph text.
	f=codecs.open(filename,"r",encoding="utf-8-sig")
	lines=f.read(-1).replace(" :",":").split("\r\n")
	f.close()
	out=codecs.open(filename.replace(".txt","_split.txt"),"w",encoding="utf-8")
	attribs={}
	attribs["inro"]=search("^(\d+)\.",lines[0]).group(1)
	year=search("(\d{4})$",lines[0]).group(1)
	day=search(u"(taina|viikkona) (\d{1,2}) p\u00e4iv\u00e4n\u00e4",lines[0]).group(2)
	month=search(u"p\xe4iv\xe4n\xe4 (.+)kuuta",lines[0]).group(1)
	month=str(["tammi","helmi","maalis","huhti","touko",u"kes\xe4",u"hein\xe4","elo","syys","loka","marras","joulu"].index(month)+1)
	date=year+"-"+month.rjust(2,"0")+"-"+day.rjust(2,"0")
	kaika=lines[1].strip().split(" ")[1]
	if "." not in kaika:
		kaika+=".00"
	attribs["date"]=date+" "+kaika.replace("H","13").rjust(5,"0")
	attribs["vp"]=year
	badkeys=["etunimi","sukunimi","asema"]
	j=2
	while j<len(lines):
		if u"P\xe4iv\xe4j\xe4rjestyksess\xe4 oleva" in lines[j] or u"Ulkopuolella p\xe4iv\xe4j\xe4rjestyksen" in lines[j]:
			break
		j+=1
	#idea (for the "ilmoitusasiat" part)
	#jl=2
	#while jl<j:
	#	if "Ilmoitusasia" in lines[jl]:
	#		break
	#	jl+=1
	#attribs["tyyppi"]="ilmasia"
	#append=False
	#paragraph=0
	#for i in range(jl,j):
	#	if "vaalin toimittaminen" in lines[i] or u"j\xe4senluku" in lines[i] or "Ilmoittautuneita edustajia" in lines[i]:
	#		attribs["asia"]=lines[i]
	#		append=False
	#		continue
	#	if append:
	#		if lines[i-1][-1]=="-":
	#			lines[i]=lines[i-1][:-1]+lines[i]
	#		else:
	#			lines[i]=lines[i-1]+" "+lines[i]
	#		append=False
	#		paragraph+=1
	#		attribs["paragraph"]=str(paragraph)
	#		helper(out,lines[i],attribs)
	#		continue
	#	if lines[i][-1] not in ".!\")":
	#		append=True
	sk=False
	if u"Suullisia kysymyksi\xe4" in "".join(lines[0:5]):
		sk=True
	#attribs["sk"]="True"
	paragraph=0
	kesk=False
	append=False
	#del attribs["tyyppi"]
	attribs["lineo1"]=str(j+2)
	pnro=0
	pjnro=0
	for i in range(j+1,len(lines)):
		lines[i]=lines[i].replace("\n","").strip()
		if not lines[i]:
			continue
		if "Puheenvuoron saatuaan lausuu" in lines[i]:
			continue
		if ("eskustelu" in lines[i] and (("julistetaan" in lines[i] and u"p\xe4\xe4ttyneeksi" in lines[i]) or u"p\xe4\xe4ttyy" in lines[i])) or u"Asia on loppuun k\xe4sitelty" in lines[i]:
			#if not sk:
			kesk=False
			attribs["tyyppi"]=u"p\xe4\xe4t\xf6s"
			for key in badkeys:
				if key in attribs:
					del attribs[key]
			#continue
		if match("\d{1,3} \d{6,9}[A-Z]$",lines[i]):
			lines[i]=lines[i-1]
			continue
		if search("^\d{1,2}\)[ \t][^'\"]",lines[i]) and not kesk:
			exp=search("^(\d{1,2})\)[ \t](.+)",lines[i])
			attribs["asia"]=exp.group(2)
			if sk:
				name=search("Ed\.([^:]+)",attribs["asia"]).group(0)
				attribs["asia"]=attribs["asia"].replace(name,"Suullinen kysymys")
			attribs["snoviite"]=exp.group(1)
			attribs["tyyppi"]="johdanto"
			for key in badkeys:
				if key in attribs:
					del attribs[key]
			if not sk:
				kesk=False
			else:
				kesk=True
			append=False
			pjnro=0
			continue
		if "eskustelu:" in lines[i] or "eskustelu jatkuu:" in lines[i]:
			kesk=True
			#continue
		attribs["lineo2"]=str(i+1)
		if ("Ed. " in lines[i][0:5] or "inisteri" in lines[i][0:35]) and ":" in lines[i][0:57] and ("uhemies" in lines[i][0:75] or "alman" in lines[i][0:75]) and kesk: #first letter may be of either case; the second part may not be present
			asema=lines[i][:lines[i].index(":")]
			if "Ed. " in asema:
				attribs["sukunimi"]=asema[4:].replace(" ","")
				attribs["asema"]="Edustaja"
			else:
				idx=asema.find("inisteri")
				attribs["asema"]=asema[0:idx+8]
				attribs["sukunimi"]=asema[idx+8:].replace(" ","")
			if "ekryhma" in attribs and attribs["ekryhma"]:
				attribs["gov"]=is_oppos(attribs["ekryhma"],date)
			if "vastauspuheenvuoro" in attribs["sukunimi"]:
				attribs["sukunimi"]=attribs["sukunimi"].replace("(vastauspuheenvuoro)","")
				attribs["tyyppi"]="vastaus"
			else:
				attribs["tyyppi"]="varsinainen"
			pnro+=1
			pjnro+=1
			attribs["pnro"]=str(pnro)
			attribs["pjnro"]=str(pjnro)
			attribs["ptkviite"]=attribs["inro"]+"/"+attribs["snoviite"]+"/"+attribs["pjnro"]
			lines[i]=lines[i][lines[i].index(":")+2:]
		if append and kesk:
			if lines[i-1]:
				if lines[i-1][-1]=="-":
					lines[i]=lines[i-1][:-1]+lines[i]
				else:
					lines[i]=lines[i-1]+" "+lines[i]
			append=False
			paragraph+=1
			attribs["paragraph"]=str(paragraph)
			helper(out,lines[i],attribs)
			attribs["lineo1"]=str(i+2)
			continue
		if lines[i] and lines[i][-1] not in ".?-!\")":
			append=True
		else:
			paragraph+=1
			attribs["paragraph"]=str(paragraph)
			helper(out,lines[i],attribs)
			attribs["lineo1"]=str(i+2)
	out.close()

os.chdir("./texts") # path to raw text files
for filename in glob("[0-9][0-9][0-9][0-9]ptk[0-9][0-9][0-9].txt"):
	print(filename)
	split(filename)