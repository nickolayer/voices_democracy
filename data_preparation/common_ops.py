import io
import os

PARSER_PATH="..."

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

def mark_spacing(parsed,split,output):
# For every word in a parsed file, adds SpaceAfter=No
# to the annotation if the word is not separated from the next one.
# This allows the spacing in the sentence text to be reconstructed later.
	file=io.open(parsed,"r",encoding="utf-8")
	sfile=io.open(split,"r",encoding="utf-8")
	out=io.open(output,"w",encoding="utf-8")
	start=0
	for line in file:
		if line.startswith("###C:PAGE"):
			out.write(line)
			continue
		if line.startswith("###C:"):
			sfile.readline()
			sline=sfile.readline()
			start=0
		elif line!="" and line!="\n":
			form=line.split("\t")[1]
			start+=sline[start:].index(form)+len(form)
			if sline[start]==" ":
				start+=1
			elif sline[start]!="\n": #end of paragraph
				line=line.replace("\n","|SpaceAfter=No\n")
		out.write(line)
	file.close()
	sfile.close()
	out.close()

def stack_splits(splits,outpath,maxlines):
# Concatenates individual split files into larger packs.
# The last file that goes over the maxlines limit will be fully included.
	count=1
	outname="pack"+str(count).rjust(2,"0")+"_split.txt"
	outf=io.open(os.path.join(outpath,outname),"w",encoding="utf-8")
	lines=0
	l=len(splits)
	for i in range(0,l):
		inf=io.open(splits[i],"r",encoding="utf-8")
		s=inf.read()
		inf.close()
		lines+=s.count("\n")
		outf.write(s)
		if lines>=maxlines:
			#s=s[:-1]+u"\x0C\n" - could mark the boundary between files
			if i<l-1:
				outf.close()
				count+=1
				outname="pack"+str(count).rjust(2,"0")+"_split.txt"
				outf=io.open(os.path.join(outpath,outname),"w",encoding="utf-8")
			lines=0
	outf.close()

def parse(inf,outf):
# Passes a split file through the dependency parser.
	global PARSER_PATH
	path=os.getcwd()
	if not PARSER_PATH.endswith(os.sep):
		PARSER_PATH+=os.sep
	os.chdir(PARSER_PATH)
	runstr="./split_text_with_comments.sh < \""+inf+"\" | ./parse_conll.sh | python split_clauses.py > \""+outf+"\""
	os.system(runstr)
	os.chdir(path)