from xml.etree import cElementTree
from HTMLParser import HTMLParser
from glob import glob
from re import sub,search,compile
import codecs
import datetime
import os

# This script performs the processing of phase 2 parliamentary records (1999-2014).
# It separates the original files into text and metadata;
# stacking them into packs and parsing is the same as in phase 3,
# while page numbers cannot be added at all.
# The final DB-ready outputs are already provided elsewhere;
# this script is only needed to change their construction process.

def helper(file,line,metadata):
# Writes out metadata-text line pairs for one paragraph at a time.
	metadata["paragraph"]=str(metadata["paragraph"])
	file.write("###C:PTK|"+"|".join([k+"="+metadata[k] for k in metadata])+"\n")
	metadata["paragraph"]=int(metadata["paragraph"])
	file.write(line.replace("\n"," ").replace("  "," ").strip()+"\n")

def parse_pvuoro(p,file,attributes):
# Processes a single "speech block" of an MP or another speaker,
# contained inside a "pvuoro" tag.
	attributes.update(p.attrib)
	if "puhnimi" in p.attrib and " " in p.attrib["puhnimi"]:
		attributes["puhnimi"]=p.attrib["puhnimi"].split(" ")[-1]
	elif len(p[0][0])>1:
		attributes["puhnimi"]=p[0][0][1].text.strip()
	if p[0].tag=="edustaja":
		attributes["etunimi"]=p[0][0][0].text.replace("\t"," ").replace("\n"," ").strip().split(" ")[0]
		if "numero" in p[0][0].attrib:
			attributes["numero"]=p[0][0].attrib["numero"]
		else:
			attributes["numero"]=-1
		if p[0][1].text:
			attributes["ekryhma"]=p[0][1].text.strip()
		else:
			attributes["ekryhma"]="NONE"
		attributes["asema"]="Edustaja"
	elif p[0].tag!="te":
		attributes["etunimi"]=p[0][0][1].text.replace("\t"," ").replace("\n"," ").strip()
		if "numero" in p[0][0].attrib:
			attributes["numero"]=p[0][0].attrib["numero"]
		else:
			attributes["numero"]="-1"
		if "Liisa" in p[0][0][0].text:
			attributes["etunimi"]="Liisa"
			attributes["asema"]=p[0][0][0].text.strip().split(" ")[0]
		else:
			attributes["asema"]=p[0][0][0].text.replace("\n"," ").strip()
	for elem in p:
		if elem.text and "te" in elem.tag:
			if "tyyppi" in p.attrib:
				attributes["tyyppi"]=p.attrib["tyyppi"]
			attributes["paragraph"]+=1
			if elem.tag=="te":
				attributes["kieli"]="suomi"
			else:
				attributes["kieli"]="ruotsi"
			helper(file,elem.text,attributes)
		if elem.tag=="pmvali":
			copy=dict(attributes)
			attributes["kieli"]="suomi"
			attributes["tyyppi"]="puhemies"
			for key in ["etunimi","puhnimi","ekryhma","asema"]:
				if key in attributes:
					del attributes[key]
			for te in elem.findall("te"):
				attributes["paragraph"]+=1
				helper(file,te.text,attributes)
			attributes=dict(copy)
		if elem.tag=="vieraili":
			temp=dict(attributes)
			attributes["asia"]=elem[0].text.replace("\n"," ").strip()
			for key in ["etunimi","puhnimi","ityyppi","numero","ekryhma","asema","pjnro","pnro"]:
				if key in attributes:
					del attributes[key]
			attributes["tyyppi"]="puhemies"
			for te in elem.findall("te"):
				attributes["kieli"]="suomi"
				attributes["paragraph"]+=1
				helper(file,te.text,attributes)
			attributes=dict(temp)
	for key in ["etunimi","puhnimi","ityyppi","numero","ekryhma","asema","pjnro","pnro"]:
		if key in attributes:
			del attributes[key]

def split_file(filename):
# Splits an original phase 2 document (XML) into text and metadata:
# one line of paragraph metadata, followed by one line of paragraph text.
	if "Edustajaluettelo" in filename or "Alkusivut" in filename:
		return
	file=open(filename,"r")
	s=file.read(-1)
	file.close()
	h=HTMLParser()
	s="<?xml version=\"1.0\" standalone=\"no\" ?>\n"+s.replace("//FI\" [","//FI\" \"\" [")
	s=s.replace("<?Fm: Validation Off>","")
	s=s.replace("\xb4","&apos;")
	s=s.replace("<snro><snroviit","<snro")
	s=s.replace("<te></te>","")
	s=s.replace("<asiaot></asiaot>","")
	s=s.replace("upjasiat","pjasiat")
	s=s.replace("edpvuoro","pvuoro")
	s=s.replace("vkkokp","ilmasia")
	s=s.replace("<tyhja>","")
	s=s.replace("<katkos>","")
	s=s.replace("<aukko>","")
	s=s.replace("<tyhjanel>","")
	s=s.replace("<viiva>","")
	s=s.replace("<sviiva>","")
	s=s.replace("<ku>","")
	s=s.replace("</ku>","")
	s=s.replace("</aliitev>","</aliite></aliitev>")
	if "<avliite" in s:
		s=sub("(<avliite[^>]*>)","\g<1></avliite>",s)
	if "<askasjat" in s:
		s=sub("(<askasjat[^>]*>)","\g<1></askasjat>",s)
	s=s.replace("</liite>","</aliitenr></liite>")
	s=s.replace("</aanliite>","</liitenro></aanliite>")
	s=sub("(<plnimi[^>]*>)","\g<1></plnimi>",s)
	s=sub("(<osnimi[^>]*>)","\g<1></osnimi>",s)
	s=s.replace("sktrunko","pjkohta")
	s=s.replace("sktpaat","paattam")
	if "talousarvio" in s:
		s=s.replace("<valta","<pjkohta")
		s=s.replace("valta>","pjkohta>")
	s=s.replace("ed.","edustaja")
	s=s.replace("Ed.","Edustaja")
	s=h.unescape(s).encode("utf-8")
	s=s.replace("&sol;","/")
	s=s.replace("&dash;","-")
	s=s.replace("&nbsp;"," ")
	s=s.replace("&lsqb;","[")
	s=s.replace("&rsqb;","]")
	s=s.replace("&ensp;"," ")
	s=s.replace("&","&amp;")
	s=s.replace("\xc2\xa0"," ")
	s=sub(" +"," ",s)
	root=cElementTree.fromstring(s)
	if root.find("ident")[2].text and root.find("ident")[2].text:
		root.attrib["kaika"]=sub("^[^0-9]+","",root.find("ident")[2].text).strip()
		if "(" in root.attrib["kaika"]:
			root.attrib["kaika"]=sub('.+\((.+)\)','\g<1>',root.attrib["kaika"])
		if u"\u2014" in root.attrib["kaika"]:
			root.attrib["kaika"]=root.attrib["kaika"][:-1]
		if "." not in root.attrib["kaika"]:
			root.attrib["kaika"]+=".00"
	temp=[k+"=\""+root.attrib[k]+"\"" for k in root.attrib]
	out=codecs.open(filename.replace(".sgm",".txt").replace("skt","ptk"),"w",encoding="utf-8")
	attributes=dict(root.attrib)
	attributes["tunniste"]=attributes["tunniste"].replace("\t"," ")
	attributes["versio"]=sub("^[^0-9]+","",attributes["versio"])
#Fixing incorrectly specified day attributes
	if attributes["pvm"]=="2.2.2001":
		attributes["pvm"]="Perjantaina 2.2.2001"
	if attributes["pvm"]=="5.2.2002":
		attributes["pvm"]="Tiistaina 5.2.2002"
	if attributes["pvm"]=="26.3.2003":
		attributes["pvm"]="Keskiviikkona 26.3.2003"
	if attributes["pvm"]=="3.2.2004":
		attributes["pvm"]="Tiistaina 3.2.2004"
	if attributes["pvm"]=="2.2.2005":
		attributes["pvm"]="Keskiviikkona 2.2.2005"
	if attributes["pvm"]=="3.2.2006":
		attributes["pvm"]="Perjantaina 3.2.2006"
	if "Maanantai" in attributes["pvm"]:
		attributes["pvm"]="Maanantai"
	else:
		attributes["pvm"]=sub("na.*","",attributes["pvm"].strip())
	attributes["tila"]=attributes["tila"].title().replace("Tarkistetu","Tarkistettu").replace("Tarkistetttu","Tarkistettu")
	attributes["paragraph"]=0
	temporary2=["knro","asia","aktyyppi","akviite","etunimi","numero","ekryhma","asema","kohta","snoviite","kasvaihe"]
	temporary3=["etunimi","puhnimi","ityyppi","numero","ekryhma","asema","pjnro","pnro"]
	if root.tag=="aptk": #avajaiset
		attributes["asia"]=u"Valtiop\u00e4ivien avajaiset"
		attributes["tyyppi"]="johdanto"
		base=root.find("avajais")
		tmp=base.findall("te")
#Exception for the year 2002, when the signature was also placed in ordinary te tags
		if "2002" in attributes["tunniste"] and attributes["inro"]=="209b":
			tmp=tmp[:-3]
		for te in tmp:
			attributes["paragraph"]+=1
			helper(out,te.text,attributes)
		if attributes["ityyppi"]=="avajaisjuhla":
			for term in ["prespuhe","pmpuhe"]:
				pres=base.find(term)
				attributes.update(pres.attrib)
				attributes["tyyppi"]=term
				attributes["asema"]=pres[0][0][0].text.replace("\n"," ").replace("eduskunnan ","").strip().capitalize()
				if pres[0][0][1].text:
					attributes["etunimi"]=pres[0][0][1].text.replace("\t"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0][2].text
				else:
					attributes["etunimi"]=pres[0][0][2].text.replace("\t"," ").replace("\n"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0][2].text.replace("\t"," ").replace("\n"," ").strip().split(" ")[1]
				for t in pres:
					if t.tag=="rte":
						attributes["kieli"]="ruotsi"
					elif t.tag=="te" or t.tag=="pmpterv":
						attributes["kieli"]="suomi"
					else:
						continue
					if not t.text:
						continue
					attributes["paragraph"]+=1
					helper(out,t.text,attributes)
			attributes["tyyppi"]="loppu"
			attributes["paragraph"]+=1
			attributes["kieli"]="suomi"
			helper(out,root.find("paattam")[0].text,attributes)
		else:
			attributes["asia"]=u"Vaalikauden p\u00e4\u00e4tt\u00e4j\u00e4iset"
			for term in ["pmpuhe","prespuhe"]:
				pres=base.find(term)
				attributes.update(pres.attrib)
				attributes["tyyppi"]=term
				attributes["asema"]=pres[0][0][0].text.replace("\n"," ").replace("eduskunnan ","").strip().capitalize()
				if len(pres[0][0])==3: #pres[0][0].find("etunimi") inexplicably returns None, even when that tag is in place - try pres[0][0].find["etunimi"] is None
					attributes["etunimi"]=pres[0][0].find("etunimi").text.replace("\t"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0].find("sukunimi").text
				else:
					attributes["etunimi"]=pres[0][0].find("sukunimi").text.replace("\t"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0].find("sukunimi").text.replace("\t"," ").strip().split(" ")[1]
				for t in pres:
					if t.tag=="rte":
						attributes["kieli"]="ruotsi"
					elif t.tag=="te" or t.tag=="pmpterv":
						attributes["kieli"]="suomi"
					else:
						continue
					attributes["paragraph"]+=1
					helper(out,t.text,attributes)
			attributes["tyyppi"]="loppu"
			base=root.find("epavir")
			for pres in base.findall("pmpuhe"):
				attributes.update(pres.attrib)
				attributes["tyyppi"]="pmpuhe"
				attributes["asema"]=pres[0][0][0].text.replace("\n"," ").replace("eduskunnan ","").strip().capitalize()
				if len(pres[0][0])==3:
					attributes["etunimi"]=pres[0][0].find("etunimi").text.replace("\t"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0].find("sukunimi").text
				else:
					attributes["etunimi"]=pres[0][0].find("sukunimi").text.replace("\t"," ").strip().split(" ")[0]
					attributes["puhnimi"]=pres[0][0].find("sukunimi").text.replace("\t"," ").strip().split(" ")[1]
				for t in pres:
					if t.tag=="rte":
						attributes["kieli"]="ruotsi"
					elif t.tag=="te" or t.tag=="pmpterv":
						attributes["kieli"]="suomi"
					else:
						continue
					attributes["paragraph"]+=1
					helper(out,t.text,attributes)
		out.close()
		return
	if root.tag=="vpjpptk": #valtiopaivien jumalanpalvelus
		attributes["asia"]=u"Valtiop\u00e4ivien jumalanpalvelus"
		for item in root.find("vpjp"):
			if item.tag=="te":
				attributes["tyyppi"]="johdanto"
				attributes["paragraph"]+=1
				helper(out,item.text,attributes)
			else: #saarna
				attributes["tyyppi"]="alkusanat"
				attributes["paragraph"]+=1
				helper(out,item[0].text,attributes)
				attributes["tyyppi"]="saarna"
				for te in item[1:]:
					if te.tag=="te":
						attributes["kieli"]="suomi"
					else:
						attributes["kieli"]="ruotsi"
					attributes["paragraph"]+=1
					helper(out,te.text,attributes)
		if root.find("paattam") is not None:
			attributes["tyyppi"]=u"p\u00e4\u00e4tt\u00e4minen"
			attributes["paragraph"]+=1
			attributes["kieli"]="suomi"
			helper(out,root.find("paattam")[0].text,attributes)
		out.close()
		return
	if attributes["inro"]=="1":
		attributes["asia"]="Puhemiehen ja kahden varapuhemiehen vaalit"
		if root.find("avsanat") is not None:
			for tg in root.find("avsanat"):
				if tg.tag=="te":
					attributes["paragraph"]+=1
					attributes["tyyppi"]="johdanto"
					helper(out,tg.text,attributes)
				if tg.tag=="pmpvuoro":
					for te in tg:
						if te.tag=="te":
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
						if te.tag=="rte":
							attributes["paragraph"]+=1
							attributes["kieli"]="ruotsi"
							helper(out,te.text,attributes)
		anchor=root.find("pjasiat").find("pmvaalit").find("vaalit")
		if anchor is None:
			anchor=root.find("pjasiat").find("pmvaalit")
		for tg in anchor:
			if tg.tag=="pmpvuoro":
				for te in tg:
					if te.tag=="te":
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					if te.tag=="rte":
						attributes["paragraph"]+=1
						attributes["kieli"]="ruotsi"
						helper(out,te.text,attributes)
			if tg.tag=="te":
				attributes["paragraph"]+=1
				attributes["kieli"]="suomi"
				helper(out,tg.text,attributes)
		anchor=root.find("pjasiat").find("pmvaalit").find("vakuutuk")
		if anchor is None:
			anchor=root.find("pjasiat").find("pmvaalit")
		for tg in anchor:
			if tg.tag=="pmpvuoro":
				for te in tg:
					if te.tag=="te":
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					if te.tag=="rte":
						attributes["paragraph"]+=1
						attributes["kieli"]="ruotsi"
						helper(out,te.text,attributes)
			if tg.tag=="te":
				attributes["paragraph"]+=1
				attributes["kieli"]="suomi"
				helper(out,tg.text,attributes)
			if tg.tag=="vakuutus":
				attributes["numero"]=tg[0].attrib["numero"]
				attributes["asema"]=tg[0][0].text.strip().capitalize()
				attributes["etunimi"]=tg[0][1].text.strip()
				attributes["puhnimi"]=tg[0][2].text
				for te in tg[1:]:
					if te.tag=="te":
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					if te.tag=="rte":
						attributes["paragraph"]+=1
						attributes["kieli"]="ruotsi"
						helper(out,te.text,attributes)
			for key in temporary3:
				if key in attributes:
					del attributes[key]
		if root.find("pjasiat").find("pmvaalit").find("pmpuot") is not None:
			temp=[pt[1] for pt in root.find("pjasiat").find("pmvaalit").findall("pmpuot")]
			#anchor=root.find("pjasiat").find("pmvaalit").find("pmpuot")[1]
			attributes.update(temp[0].attrib)
			attributes["numero"]=temp[0][0][0].attrib["numero"]
			attributes["asema"]=temp[0][0][0][0].text.strip().capitalize()
			attributes["etunimi"]=temp[0][0][0][1].text.strip()
			attributes["puhnimi"]=temp[0][0][0][2].text
		else:
			temp=[root.find("pjasiat").find("pmvaalit").findall("pmpvuoro")[-1]]
		for anchor in temp:
			for te in anchor[1:]:
				if te.tag=="te" or te.tag=="pmpterv":
					attributes["paragraph"]+=1
					attributes["kieli"]="suomi"
					helper(out,te.text,attributes)
				if te.tag=="rte":
					attributes["paragraph"]+=1
					attributes["kieli"]="ruotsi"
					helper(out,te.text,attributes)
		for key in temporary3:
			if key in attributes:
				del attributes[key]
		attributes["tyyppi"]="loppu"
		if root.find("lopunilm") is not None:
			ilmasiat=root.find("lopunilm").findall("ilmasia")
		else:
			ilmasiat=root.find("pjasiat").find("pmvaalit").findall("ilmasia")
		for ilmasia in ilmasiat:
			for tg in ilmasia:
				if tg.tag=="pmpvuoro":
					for te in tg:
						if te.tag=="te":
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
						if te.tag=="rte":
							attributes["paragraph"]+=1
							attributes["kieli"]="ruotsi"
							helper(out,te.text,attributes)
				if tg.tag=="askirote":
					for te in tg.find("kirjelma").findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]=tg.find("kirjelma").attrib["kieli"]
						helper(out,te.text,attributes)
				if tg.tag=="te" or tg.tag=="pmpterv":
					attributes["paragraph"]+=1
					attributes["kieli"]="suomi"
					helper(out,tg.text,attributes)
				if tg.tag=="paatokse":
					attributes["tyyppi"]=u"p\u00e4\u00e4t\u00f6s"
					for te in tg.findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)

		if root.find("paattam") is not None:
			attributes["tyyppi"]=u"p\u00e4\u00e4tt\u00e4minen"
			for te in root.find("paattam")[0].findall("te"):
				attributes["kieli"]="suomi"
				attributes["paragraph"]+=1
				helper(out,te.text,attributes)
			attributes["paragraph"]+=1
			if root.find("paattam").find("lopetus") is not None:
				helper(out,root.find("paattam").find("lopetus").text,attributes)
		out.close()
		return
	if root.tag=="skt": #suullinen kyselytunti
		attributes["asia"]=u"Suullisia kysymyksi\u00e4"
		for kys in root.findall("kyskesk"):
			for pvuoro in kys.find("sktkesk").findall("sktpvuor"):
				parse_pvuoro(pvuoro,out,attributes)
			for key in temporary3:
				if key in attributes:
					del attributes[key]
		if root.find("sktilm") is not None:
#exception for file 2003ptk055, when the session was called off
			attributes["tyyppi"]="johdanto"
			for pmp in root.find("sktilm").findall("pmpvuoro"):
				for te in pmp:
					if te.tag=="te":
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					if te.tag=="rte":
						attributes["paragraph"]+=1
						attributes["kieli"]="ruotsi"
						helper(out,te.text,attributes)
			for te in root.find("sktilm").findall("te"):
				attributes["paragraph"]+=1
				attributes["kieli"]="suomi"
				helper(out,te.text,attributes)
			attributes["tyyppi"]=u"p\u00e4\u00e4t\u00f6s"
			if root.find("pmhuom") is not None:
				for te in root.find("pmhuom").findall("te"):
					attributes["paragraph"]+=1
					attributes["kieli"]="suomi"
					helper(out,te.text,attributes)
		#out.close()
		#return
	if root.find("ilmasiat") is not None:
		for ilmasia in root.find("ilmasiat"):
			if ilmasia.tag=="vieraili":
				attributes["tyyppi"]="ilmasia"
				attributes["asia"]=ilmasia[0].text.replace("\n"," ").strip()
				for te in ilmasia.findall("te"):
					attributes["kieli"]="suomi"
					attributes["paragraph"]+=1
					helper(out,te.text,attributes)
				continue
			if ilmasia.tag=="pmmuistos":
				attributes["asia"]=ilmasia[0].text.replace("\n"," ").strip()
				anchor=ilmasia.find("pmpuhe")
				attributes.update(anchor.attrib)
				if anchor.find("pmpjohd") is not None:
					attributes["asema"]=anchor[0][0][0].text.replace("\n"," ").strip().capitalize()
					attributes["etunimi"]=anchor[0][0][1].text.strip()
					attributes["puhnimi"]=anchor[0][0][2].text.strip()
				for te in anchor[1:]:
					if te.tag=="pmpterv" or te.tag=="te":
						attributes["kieli"]="suomi"
						attributes["paragraph"]+=1
						helper(out,te.text,attributes)
					if te.tag=="rte":
						attributes["kieli"]="ruotsi"
						attributes["paragraph"]+=1
						helper(out,te.text,attributes)
				for key in temporary3:
					if key in attributes:
						del attributes[key]
				continue
			if ilmasia.tag!="ilmasia":
				continue
			if ilmasia.find("asiaot") is not None:
				attributes["asia"]=ilmasia.find("asiaot").text.replace("\n"," ").strip()
			for tg in ilmasia:
				if tg.tag=="askirote":
					for te in tg.find("kirjelma").findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]=tg.find("kirjelma").attrib["kieli"]
						helper(out,te.text,attributes)
				if tg.tag=="paatokse":
					attributes["tyyppi"]=u"p\u00e4\u00e4t\u00f6s"
					for te in tg.findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
				if tg.tag=="pmpvuoro":
					attributes["tyyppi"]="ilmasia"
					attributes["kieli"]="suomi"
					for te in tg.findall("te"):
						if te.text:
							s=te.text
							attributes["paragraph"]+=1
							if len(list(te))>0 and te[0].tail:
								s+=te[0].text+te[0].tail
							helper(out,s,attributes)
				if tg.tag=="te":
					if tg.text:
						s=tg.text
						attributes["paragraph"]+=1
						if len(list(tg))>0 and tg[0].tail:
							s+=tg[0].text+tg[0].tail
						helper(out,s,attributes)
				if tg.tag=="edpuhe":
					anchor=tg
					attributes.update(anchor.attrib)
					if "numero" in anchor[0][0].attrib:
						attributes["numero"]=anchor[0][0].attrib["numero"]
					attributes["etunimi"]=anchor[0][0][0].text
					attributes["puhnimi"]=anchor[0][0][1].text
					attributes["ekryhma"]=anchor[0][1].text.strip()
					for te in anchor.findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					for te in anchor.find("valikys").find("kysosa").find("peruste").findall("te"):
						attributes["paragraph"]+=1
						attributes["kieli"]="suomi"
						helper(out,te.text,attributes)
					for te in anchor.find("valikys").find("kysosa").find("kysymys")[0]:
						if te.text:
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
					for key in temporary3:
						if key in attributes:
							del attributes[key]
	for pjasia in root.findall("pjasiat"):
		for pjkohta in [pk for pk in pjasia if pk.tag=="pjkohta" or pk.tag=="ilmasia" or pk.tag=="vieraili"]:
			if pjkohta.tag=="vieraili":
				attributes["asia"]=pjkohta[0].text.replace("\n"," ").strip()
				attributes["tyyppi"]="puhemies"
				for te in pjkohta.findall("te"):
					attributes["kieli"]="suomi"
					attributes["paragraph"]+=1
					helper(out,te.text,attributes)
				continue
			attributes.update(pjkohta[0].attrib)
			if pjkohta[0].find("knro"):
				attributes["knro"]=pjkohta[0].find("knro").text
			if pjkohta[0].find("asia") is not None and pjkohta[0].find("asia").text:
				attributes["asia"]=pjkohta[0].find("asia").text.replace("\n"," ").strip()
			elif pjkohta.find("asiaot") is not None and pjkohta.find("asiaot").text:
				attributes["asia"]=pjkohta.find("asiaot").text.replace("\n"," ").strip()
			if pjkohta[0].find("ak"):
				attributes["aktyyppi"]=pjkohta[0].find("ak")[0].text.replace("\n"," ")
				attributes["akviite"]=pjkohta[0].find("ak")[1].text.replace("\n"," ")
			if len(pjkohta)>1:
				attributes["kieli"]="suomi"
				for tg in pjkohta:
					if tg.tag=="te":
						if tg.text:
							s=tg.text
							if len(list(tg))>0 and tg[0].tail:
								s+=tg[0].text+tg[0].tail
							attributes["kieli"]="suomi"
							attributes["paragraph"]+=1
							helper(out,s,attributes)
					if tg.tag=="rte":
						if tg.text:
							s=tg.text
							if len(list(tg))>0 and tg[0].tail:
								s+=tg[0].text+tg[0].tail
							attributes["kieli"]="ruotsi"
							attributes["paragraph"]+=1
							helper(out,s,attributes)
					if tg.tag=="pmpvuoro":
						attributes["tyyppi"]="johdanto"
						for te in tg:
							if te.tag=="te" and te.text:
								s=te.text
								if len(list(te))>0 and te[0].tail:
									s+=te[0].text+te[0].tail
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,s,attributes)
							if te.tag=="rte" and te.text:
								s=te.text
								if len(list(te))>0 and te[0].tail:
									s+=te[0].text+te[0].tail
								attributes["kieli"]="ruotsi"
								attributes["paragraph"]+=1
								helper(out,s,attributes)
					if tg.tag=="pvuoro":
						parse_pvuoro(tg,out,attributes)
					if tg.tag=="keskust":
						for pvuoro in tg.findall("pvuoro"):
							parse_pvuoro(pvuoro,out,attributes)
						if tg.find("askaskes") is not None:
							for item in tg.find("askaskes"):
								if item.tag=="te":
									attributes["kieli"]="suomi"
									attributes["paragraph"]+=1
									helper(out,item.text,attributes)
								if item.tag=="pmpvuoro":
									for te in item.findall("te"):
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,te.text,attributes)
					if tg.tag=="edpuhe":
						anchor=tg
						attributes.update(anchor.attrib)
						if "numero" in anchor[0][0].attrib:
							attributes["numero"]=anchor[0][0].attrib["numero"]
						attributes["etunimi"]=anchor[0][0][0].text
						attributes["puhnimi"]=anchor[0][0][1].text
						attributes["ekryhma"]=anchor[0][1].text.strip()
						for te in anchor.findall("te"):
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
						for te in anchor.find("valikys").find("kysosa").find("peruste").findall("te"):
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
						for te in anchor.find("valikys").find("kysosa").find("kysymys")[0]:
							if te.text:
								attributes["paragraph"]+=1
								attributes["kieli"]="suomi"
								helper(out,te.text,attributes)
						for key in temporary3:
							if key in attributes:
								del attributes[key]
					if tg.tag=="ponsipaa":
						if tg.find("paatokse") is not None:
							attributes["tyyppi"]=u"p\u00e4\u00e4t\u00f6s"
							for te in tg.find("paatokse").findall("te"):
								if te.text:
									attributes["kieli"]="suomi"
									attributes["paragraph"]+=1
									helper(out,te.text,attributes)
						else:
							for te in tg.findall("te"):
								if te.text:
									attributes["kieli"]="suomi"
									attributes["paragraph"]+=1
									helper(out,te.text,attributes)
					if tg.tag=="paatokse":
						attributes["kieli"]="suomi"
						attributes["tyyppi"]=u"p\u00e4\u00e4t\u00f6s"
						for item in tg:
							if item.tag=="te" and item.text:
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,item.text,attributes)
							if item.tag=="rte" and item.text:
								attributes["kieli"]="ruotsi"
								attributes["paragraph"]+=1
								helper(out,item.text,attributes)
							if item.tag=="pmpvuoro":
								for te in item.findall("te"):
									if te.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,te.text,attributes)
							if item.tag=="pvuoro":
								parse_pvuoro(item,out,attributes)
								for key in temporary3:
									if key in attributes:
										del attributes[key]
							if item.tag=="askaskes":
								for item2 in tg:
									if item2.tag=="te":
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,item2.text,attributes)
									if item2.tag=="pmpvuoro":
										for te in item2.findall("te"):
											attributes["kieli"]="suomi"
											attributes["paragraph"]+=1
											helper(out,te.text,attributes)
							if item.tag=="aanestys":
								for te in item:
									if te.tag=="te" and te.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,te.text,attributes)
									if te.tag=="tulos" or te.tag=="pmpvuoro":
										for tgt in te.findall("te"):
											if tgt.text:
												attributes["kieli"]="suomi"
												attributes["paragraph"]+=1
												helper(out,tgt.text,attributes)
							if item.tag=="ehdtkset":
								for tgt in item:
									if tgt.tag=="te":
										if tgt.text:
											attributes["kieli"]="suomi"
											attributes["paragraph"]+=1
											helper(out,tgt.text,attributes)
										if tgt.tag=="ehdotus":
											if tgt.find("edustaja") is not None:
												anchor=tgt.find("edustaja")
												attributes["numero"]=anchor[0].attrib["numero"]
												attributes["etunimi"]=anchor[0][0].text.replace("\n"," ").strip()
												attributes["puhnimi"]=anchor[0][1].text.replace("\n"," ").strip()
												attributes["ekryhma"]=anchor[1].text.replace("\n"," ").strip()
											for te in tgt.findall("te"):
												attributes["kieli"]="suomi"
												attributes["paragraph"]+=1
												helper(out,te.text,attributes)
										for key in temporary3:
											if key in attributes:
												del attributes[key]
					if tg.tag=="paalk" or tg.tag=="osasto" or tg.tag=="ykperust" or tg.tag=="ylperust":
						for item in tg:
							if item.tag=="te" and item.text:
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,item.text,attributes)
							if item.tag=="rte" and item.text:
								attributes["kieli"]="ruotsi"
								attributes["paragraph"]+=1
								helper(out,item.text,attributes)
							if item.tag=="pmpvuoro":
								for te in item.findall("te"):
									if te.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,te.text,attributes)
							if item.tag=="keskust":
								for pvuoro in item.findall("pvuoro"):
									parse_pvuoro(pvuoro,out,attributes)
							if item.tag=="aanestys":
								for te in item:
									if te.tag=="te" and te.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,te.text,attributes)
									if te.tag=="tulos" or te.tag=="pmpvuoro":
										for tgt in te.findall("te"):
											if tgt.text:
												attributes["kieli"]="suomi"
												attributes["paragraph"]+=1
												helper(out,tgt.text,attributes)
							if item.tag=="paatokse":
								for tgt in item:
									if tgt.tag=="te" and tgt.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,tgt.text,attributes)
									if tgt.tag=="rte" and tgt.text:
										attributes["kieli"]="ruotsi"
										attributes["paragraph"]+=1
										helper(out,tgt.text,attributes)
									if tgt.tag=="pmpvuoro":
										for te in tgt.findall("te"):
											if te.text:
												attributes["kieli"]="suomi"
												attributes["paragraph"]+=1
												helper(out,te.text,attributes)
									if tgt.tag=="pvuoro":
										parse_pvuoro(tgt,out,attributes)
										for key in temporary3:
											if key in attributes:
												del attributes[key]
									if tgt.tag=="aanestys":
										for te in tgt:
											if te.tag=="te" and te.text:
												attributes["kieli"]="suomi"
												attributes["paragraph"]+=1
												helper(out,te.text,attributes)
											if te.tag=="tulos" or te.tag=="pmpvuoro":
												for item2 in te.findall("te"):
													if item2.text:
														attributes["kieli"]="suomi"
														attributes["paragraph"]+=1
														helper(out,item2.text,attributes)
									if tgt.tag=="ehdtkset":
										for item2 in tgt:
											if item2.tag=="te":
												if item2.text:
													attributes["kieli"]="suomi"
													attributes["paragraph"]+=1
													helper(out,item2.text,attributes)
											if item2.tag=="ehdotus":
												if item2.find("edustaja") is not None:
													anchor=item2.find("edustaja")
													attributes["numero"]=anchor[0].attrib["numero"]
													if anchor[0].find("etunimi") is not None:
														attributes["etunimi"]=anchor[0].find("etunimi").text.replace("\n"," ").strip()
													if anchor[0].find("sukunimi") is not None:
														attributes["puhnimi"]=anchor[0].find("sukunimi").text.replace("\n"," ").strip()
													attributes["ekryhma"]=anchor[1].text.replace("\n"," ").strip()
												for te in item2.findall("te"):
													attributes["kieli"]="suomi"
													attributes["paragraph"]+=1
													helper(out,te.text,attributes)
											for key in temporary3:
												if key in attributes:
													del attributes[key]
					if tg.tag=="kyskesk":
						for pvuoro in tg[1].findall("sktpvuor"):
							parse_pvuoro(pvuoro,out,attributes)
							for key in temporary3:
								if key in attributes:
									del attributes[key]
					if tg.tag=="askaskes":
						for item in tg:
							if item.tag=="te":
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,item.text,attributes)
							if item.tag=="pmpvuoro":
								for te in item.findall("te"):
									attributes["kieli"]="suomi"
									attributes["paragraph"]+=1
									helper(out,te.text,attributes)
					if tg.tag=="ilmasia": #in rare cases of elections
						for item in tg:
							if item.tag=="pmpvuoro":
								attributes["tyyppi"]="ilmasia"
								attributes["kieli"]="suomi"
								for te in item.findall("te"):
									if te.text:
										s=te.text
										attributes["paragraph"]+=1
										if len(list(te))>0 and te[0].tail:
											s+=te[0].text+te[0].tail
										helper(out,s,attributes)
							if item.tag=="te":
								if item.text:
									attributes["kieli"]="suomi"
									s=item.text
									attributes["paragraph"]+=1
									if len(list(item))>0 and item[0].tail:
										s+=item[0].text+item[0].tail
									helper(out,s,attributes)
							if item.tag=="rte":
								if item.text:
									attributes["kieli"]="ruotsi"
									s=item.text
									attributes["paragraph"]+=1
									if len(list(item))>0 and item[0].tail:
										s+=item[0].text+item[0].tail
									helper(out,s,attributes)
			for key in temporary3:
				if key in attributes:
					del attributes[key]
		if pjasia.find("pmvaalit") is not None:
			anchor=pjasia.find("pmvaalit")
			if anchor[0].find("asia") is not None and anchor[0].find("asia").text:
				attributes["asia"]=anchor[0].find("asia").text.replace("\n"," ")
			for item in anchor:
				if item.tag=="te":
					if item.text:
						attributes["kieli"]="suomi"
						s=item.text
						attributes["paragraph"]+=1
						if len(list(item))>0 and item[0].tail:
							s+=item[0].text+item[0].tail
						helper(out,s,attributes)
				if item.tag=="rte":
					if item.text:
						attributes["kieli"]="ruotsi"
						s=item.text
						attributes["paragraph"]+=1
						if len(list(item))>0 and item[0].tail:
							s+=item[0].text+item[0].tail
						helper(out,s,attributes)
				if item.tag=="pmpvuoro":
					attributes["tyyppi"]="johdanto"
					attributes["kieli"]="suomi"
					for te in item:
						if te.tag=="te":
							if te.text:
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,te.text,attributes)
						if te.tag=="rte":
							if te.text:
								attributes["kieli"]="ruotsi"
								attributes["paragraph"]+=1
								helper(out,te.text,attributes)
				if item.tag=="prespuhe" or item.tag=="pmpuhe":
					attributes.update(item.attrib)
					attributes["asema"]=item[0][0][0].text.strip()
					attributes["etunimi"]=item[0][0][1].text
					attributes["puhnimi"]=item[0][0][2].text
					for te in item:
						if te.tag=="pmpterv" or te.tag=="te":
							attributes["paragraph"]+=1
							attributes["kieli"]="suomi"
							helper(out,te.text,attributes)
						if te.tag=="rte":
							attributes["paragraph"]+=1
							attributes["kieli"]="ruotsi"
							helper(out,te.text,attributes)
					for key in temporary3:
						if key in attributes:
							del attributes[key]
				if item.tag=="vakuutuk":
					attributes["tyyppi"]="vakuutus"
					for te in item:
						if te.tag=="te":
							if te.text:
								attributes["kieli"]="suomi"
								attributes["paragraph"]+=1
								helper(out,te.text,attributes)
						if te.tag=="rte":
							if te.text:
								attributes["kieli"]="ruotsi"
								attributes["paragraph"]+=1
								helper(out,te.text,attributes)
						if te.tag=="pmpvuoro" or te.tag=="vakuutus":
							for tgt in te:
								if tgt.tag=="te":
									if tgt.text:
										attributes["kieli"]="suomi"
										attributes["paragraph"]+=1
										helper(out,tgt.text,attributes)
								if tgt.tag=="rte":
									if tgt.text:
										attributes["kieli"]="ruotsi"
										attributes["paragraph"]+=1
										helper(out,tgt.text,attributes)
	pmps=root.find("pmpsanat")
	if pmps is not None:
		attributes.update(pmps[1].attrib)
		for tg in pmps[1]:
			if tg.tag=="te":
				attributes["kieli"]="suomi"
				attributes["paragraph"]+=1
				helper(out,tg.text,attributes)
			if tg.tag=="rte":
				attributes["kieli"]="ruotsi"
				attributes["paragraph"]+=1
				helper(out,tg.text,attributes)
	if root.find("paattam") is not None:
		attributes["tyyppi"]=u"p\u00e4\u00e4tt\u00e4minen"
		for te in root.find("paattam")[0].findall("te"):
			attributes["kieli"]="suomi"
			attributes["paragraph"]+=1
			helper(out,te.text,attributes)
		attributes["paragraph"]+=1
		if root.find("paattam").find("lopetus") is not None:
			helper(out,root.find("paattam").find("lopetus").text,attributes)
	out.close()

os.chdir("./texts")
for file in glob("*.sgm"):
	print("Splitting "+file)
	split_file(file)