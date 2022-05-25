#See http://modpython.org/live/mod_python-3.3.1/doc-html/pyapi-mprequest.html
import re
import json
import codecs
import datetime
from threading import Thread
from bson.json_util import dumps
from timeit import default_timer
from time import sleep
from constants import ptk_newf
import pymongo

# The search engine that passes the user's query to the DB
# and returns sentences matching it.

MAX_RESULTS=1000
patterns=[]
all_lemmas=1

def logger(log,var):
  log.write(str(var)+"\n")
  log.flush()

def statistics(coll,log):
  global patterns
  cursor=coll["collection"].find(coll["query"]).batch_size(MAX_RESULTS).limit(50000)
  docs=[]
  for doc in cursor:
    docs.append(doc)
  years={u"[ei merkint\xe4\xe4]":0}
  words={}
  field="date"
  target=patterns[0]
  tree={target:[]}
  count=0
  logger(log,len(docs))
  for doc in docs:
    if field not in doc["metadata"]:
      years[u"[ei merkint\xe4\xe4]"]+=1
    elif doc["metadata"][field].year in years:
      years[doc["metadata"][field].year]+=1
    else:
      years[doc["metadata"][field].year]=1
    wcount=0
    for word in doc["words"]:
      if word["cpos"]=="PUNCT":
        wcount+=1
        continue
      if word["lemma"] in words:
        words[word["lemma"]]+=1
      else:
        words[word["lemma"]]=1
      if re.search(re.compile(target),word["lemma"]) is not None:
        tree[target].append((count,wcount))
      wcount+=1
    count+=1
  if years[u"[ei merkint\xe4\xe4]"]==0:
    del years[u"[ei merkint\xe4\xe4]"]
  pairs=[]
  for loc in tree[target]:
    pair=[]
    for i in range(loc[1]+1,len(docs[loc[0]]["words"])):
      if docs[loc[0]]["words"][i]["cpos"]=="PUNCT":
        continue
      pair.append(docs[loc[0]]["words"][i]["lemma"])
      if len(pair)==2:
        break
    if len(pair)==1:
      pair.append("[ei sanaa]")
      #pair=["[no word]",pair[0]]
    if len(pair)==0:
      pair=["[ei sanaa]","[ei sanaa]"]
    pairs.append(pair)
  top={}
  for p in [x[0] for x in pairs]:
    if p in top:
      top[p]+=1
    else:
      top[p]=1
  p=[]
  for k in top:
    p.append((k,top[k]))
  p.sort(key=lambda k: k[1])
  top=[]
  for pair in reversed(p[-11:]):
    top.append({"Word":pair[0],"Count":pair[1]})
  tops=[top]
  cnt=1
  logger(log,top)
  for word in reversed(p[-11:]):
    logger(log,word)
    if word[0]=="[ei sanaa]":
      continue
    results={}
    for pt in pairs:
      if pt[0]==word[0]:
        if pt[1] in results:
          results[pt[1]]+=1
        else:
          results[pt[1]]=1
    logger(log,results)
    tres=[]
    for k in results:
      tres.append((k,results[k]))
    tres.sort(key=lambda k: k[1])
    tops.append([])
    for pr in reversed(tres[-11:]):
      tops[cnt].append({"Word":pr[0],"Count":pr[1]})
    cnt+=1
  return {"stats":{"years":years,"lemmas":words,"total":len(docs),"patterns":patterns,"tree":tops}}

def process(target,log):
  global patterns
  global all_lemmas
#Scans the entire query object, replacing all {"lemma":"..."} strings with regex objects.
  if isinstance(target,(int,long,float,basestring)):
    return
  logger(log,target)
  try:
    for key in target:
      if key=="form":
        all_lemmas*=0
      if key=="lemma" or key=="text" or key=="rlemma":
        patterns.append(target[key])
        all_lemmas*=2
        #logger(log,target[key])
        if key=="lemma" and target[key][0]!="^":
          all_lemmas*=0
        target[key]=re.compile(target[key],re.UNICODE)
        continue
      if isinstance(target[key],dict):
        process(target[key],log)
      if isinstance(target[key],list):
        for each in target[key]:
          process(each,log)
  except Exception as e:
    logger(log,str(e))

class newThread(Thread):

  def __init__(self,colls,name):
    Thread.__init__(self)
    self.colls=colls
    self.n=name
    self.file=None

  def run(self):
    global all_lemmas
    file=codecs.open("./users/cache_"+self.n+".txt","a",encoding="utf-8")
    cnt=MAX_RESULTS
    self.file=codecs.open("./logt.txt","w",encoding="utf-8")
    for coll in self.colls:
      if not coll["active"]:
        continue
      temp=[]
      if not coll["cursor"]:
        logger(self.file,"new cursor")
        if all_lemmas>1:
          coll["cursor"]=coll["collection"].find(coll["query"],{"_id":1})
          logger(self.file,"thread used")
        else:
          coll["cursor"]=coll["collection"].find(coll["query"],{"_id":1}).batch_size(MAX_RESULTS)
      for doc in coll["cursor"]:
        cnt+=1
        temp.append(str(doc["_id"]))
        if cnt%MAX_RESULTS==0:
          file.write("|"+coll["name"]+"|"+";".join(temp)+"\n")
          file.flush()
          temp=[]
        if cnt>=50000:
          file.write(str(cnt))
          file.close()
          return
      if temp:
        file.write("|"+coll["name"]+"|"+";".join(temp))
      logger(self.file,cnt)
    if cnt%MAX_RESULTS!=0:
      file.write("\n")
    self.file.close()
    file.write(str(cnt))
    file.close()

def index(req,reqs):
  global patterns
  global all_lemmas
  all_lemmas=1
  patterns=[]
  ob=json.loads(reqs)
  hasc=pymongo.has_c()
  req.get_basic_auth_pw()
  req.headers_out["Pragma"]="no-cache"
  req.headers_out["Cache-Control"]="no-cache"
  name=req.user
  out=codecs.open("./log.txt","a",encoding="utf-8")
  logger(out,ob)
  true_count=0
  quick={}
  if "batch" in ob:
    try:
      times=[default_timer()]
      cache=codecs.open("./users/cache_"+name+".txt","r",encoding="utf-8")
      count=0
      found=False
      for line in cache:
        if count==ob["batch"]-1:
          found=True
          break
        count+=1
      logger(out,count)
      if count<ob["batch"] and not found:
        cache.close()
        sleep(3)
        return json.dumps({"count":-1},separators=(',',':'))
      parts=line.replace("\n","").split("|")
      i=1
      sum=0
      while i<len(parts)-1:
        quick[parts[i]]=[int(p) for p in parts[i+1].split(";")]
        sum+=len(quick[parts[i]])
        i+=2
      true_count=-1
      for line in cache:
        if "|" not in line:
          true_count=int(line)
          break
      cache.close()
      logger(out,true_count)
      logger(out,quick)
      if true_count==-1:
          true_count=-(ob["batch"]-1)*MAX_RESULTS-sum
      times.append(default_timer())
    except Exception as e:
      logger(out,str(e))
  client=pymongo.MongoClient() #authenticate here
  strs=[]
  db=client.vode_db
  radius=0
  return_stats=False
  if "extend" in ob:
    trans={"minute":db.ptk}
    if ob["type"] not in trans:
      return dumps({"text":""})
    doc=trans[ob["type"]].find_one({"_id":int(ob["_id"])+int(ob["offset"])})
    if doc:
      return dumps({"text":doc["text"]})
    else:
      return dumps({"text":""})
  if "radius" in ob:
    radius=ob["radius"]
    del ob["radius"]
  if "stats" in ob:
    return_stats=True
    del ob["stats"]
  times=[default_timer()]
  process(ob,out)
  if "metadata.date" in ob:
    if "$lte" in ob["metadata.date"]:
      ob["metadata.date"]["$lte"]=datetime.datetime.strptime(ob["metadata.date"]["$lte"],"%Y-%m-%dT%H:%M:%S.%fZ")
    if "$gte" in ob["metadata.date"]:
      ob["metadata.date"]["$gte"]=datetime.datetime.strptime(ob["metadata.date"]["$gte"],"%Y-%m-%dT%H:%M:%S.%fZ")
  caching=False
  cursors=[]
  query={}
  for key in ob:
    if key!="dataset" and key!="range":
      query[key]=ob[key]
  if "dataset" not in ob:
    ob["dataset"]={}
    for key in quick:
      ob["dataset"][key]={}
  for elem in sorted(ob["dataset"].iterkeys(),key=([name+str(i) for i in range(1,11)]+["minute"]).index):
    partial=dict(query)
    for key in ob["dataset"][elem]:
      partial[key]=ob["dataset"][elem][key]
    if elem=="minute":
      cursors.append({"collection":db.ptk,"cursor":None,"name":"minute","min_result":-1,"max_result":0,"active":True,"query":partial})
    if name in elem:
      if "metadata.date" in partial:
        del partial["metadata.date"]
      cursors.append({"collection":db[elem],"cursor":None,"name":elem,"min_result":-1,"max_result":0,"active":True,"query":partial})
  if return_stats:
    return json.dumps(statistics(cursors[0],out))
  if quick:
    tempcount=0
    for coll in cursors:
      if coll["name"] in quick:
        coll["query"]={"_id":{"$in":quick[coll["name"]]}}
        coll["min_result"]=tempcount
        coll["max_result"]=tempcount+len(quick[coll["name"]])-1
        tempcount+=len(quick[coll["name"]])
      else:
        coll["max_result"]=-1
  logger(out,cursors)
  times.append(default_timer())
  if "batch" not in ob and "range" not in ob: # cache
    count=0
    cur=None
    ids=[]
    for coll in cursors:
      #try:
      logger(out,all_lemmas)
      if all_lemmas>1 and (name not in coll["name"]):
        cur=coll["collection"].find(coll["query"],{"_id":1,"words":1}) 
        #logger(out,"used")
      else:
        cur=coll["collection"].find(coll["query"],{"_id":1}).batch_size(MAX_RESULTS)
      #except Exception as e:
      # logger(out,str(e))
      coll["min_result"]=count
      cur_count=0
      for doc in cur:
        count+=1
        cur_count+=1
        ids.append(doc["_id"])
        if count>=MAX_RESULTS:
          break
      if cur_count==0:
        coll["max_result"]=-1
      else:
        coll["max_result"]=coll["min_result"]+cur_count-1
      if count>=MAX_RESULTS:
        coll["cursor"]=cur
        break
      coll["active"]=False
    file=None
    if count>0:
      file=codecs.open("./users/cache_"+name+".txt","w",encoding="utf-8")
      for coll in cursors:
        file.write("|"+coll["name"]+"|"+";".join([str(ids[i]) for i in range(coll["min_result"],coll["max_result"]+1)]))
        if coll["max_result"]==MAX_RESULTS-1:
          break
      file.write("\n")
    else:
      return json.dumps({"count":0,"data":[],"times":[]},separators=(',',':'))
    if count>0 and count<MAX_RESULTS:
      true_count=count
      file.write(str(count))
    else:
#Doesn't cover the rare case when count==MAX_RESULTS and no more results are available -
#there's no hasNext method for the cursor to check this
      true_count=-count
    if file:
      file.close()
    ob={"_id":{"$in":ids}}
    caching=True # done caching
  if "batch" in ob:
    del ob["batch"]
  times.append(default_timer())
  rng=-1
  if "range" in ob:
    rng=ob["range"]
    del ob["range"]
  final=[]
  dsets=[]
  count=0
  for coll in cursors:
    if coll["max_result"]==-1:
      continue
    if rng>-1:
      ob=coll["query"]
      cur_count=0
      patterns=[]
      strs=[]
      seqs=[]
      tds=[]
      coll["min_result"]=count
      if "$or" in ob:
        patterns=[w for w in ob["$or"] if "$all" in w["words"]]
      elif "words" in ob and "$all" in ob["words"]:
        patterns.append(ob)
      for p in patterns:
        all=p["words"]["$all"]
        words=list(all)
        w2=[]
        for x in words:
          if "lemma" in x["$elemMatch"]:
            w2.append(x["$elemMatch"]["lemma"])
          elif "rlemma" in x["$elemMatch"]:
            w2.append(x["$elemMatch"]["rlemma"])
          elif "form" in x["$elemMatch"]:
            w2.append(x["$elemMatch"]["form"])
        logger(out,str(words))
        logger(out,str(p))
        ob["words"]=all[0]
        if "$or" in ob:
          del ob["$or"]
        pseqs=[]
        #td={}
        if count>=10000:
          break
        for root in coll["collection"].find(ob,{"_id":1,"words.$":1}).sort("_id",1):
          try:
            if count>=10000:
              break
            #found=[]
            id_min=root["_id"]
            id_max=id_min
            #td[root["_id"]]=[root["words"][0]["form"]]
            for word in words[1:]:
              ids=[i for i in range(id_min-rng,id_max+rng+1) if i<id_min or i>id_max]
              subquery={"_id":{"$in":ids},"words":word}
              #subquery={"$and":[{"_id":{"$in":ids}},{"words":word}]}
              #for prev in found:
              #  subquery["$and"].append({"$not":{"_id":prev[0],"words.id":prev[1]}})
              logger(out,ids)
              subdocs=[doc for doc in coll["collection"].find(subquery,{"_id":1,"words.$":1})]
              if subdocs:
                for doc in subdocs:
                  logger(out,str((doc["_id"],id_min,id_max)))
                  if doc["_id"]<id_min:
                    id_min=doc["_id"]
                  if doc["_id"]>id_max:
                    id_max=doc["_id"]
              else:
                id_min=-1
                id_max=-1
                break
            if id_min<0:
              continue
          except Exception as e:
            logger(out,"B1"+str(e))
          if len(pseqs)==0:
            pseqs.append((id_min,id_max))
            count+=1
          elif pseqs[-1][0]//10000!=id_min//10000:
            pseqs.append((id_min,id_max))
            count+=1
          else:
            if id_min>pseqs[-1][1]+1:
              pseqs.append((id_min,id_max))
              count+=1
            else:
              pseqs[-1]=(pseqs[-1][0],id_max)
        if pseqs:
          seqs.append(sorted(pseqs,key=lambda p: p[0]))
        #tds.append(dict(td))
      if not seqs:
        coll["min_result"]=-1
        coll["max_result"]=-1
        continue
      #tdc=0
      for pseq in seqs:
        ids=[]
        for pair in pseq:
          ids+=range(pair[0]-radius,pair[1]+radius+1)
        src=sorted([doc for doc in coll["collection"].find({"_id":{"$in":ids}}) if doc is not None], key=lambda d: d["_id"])
        true_ids=[doc["_id"] for doc in src]
        positions=[]
        i=0
        cur=0
        start=0
        end=0
        while i<len(true_ids):
          if true_ids[i]>pseq[cur][1]+radius:
            end=i-1
            positions.append((start,end))
            start=i
            cur+=1
            if cur>=len(pseq):
              break
            while true_ids[start]>=pseq[cur][0]-radius:
              start-=1
            start+=1
          i+=1
        positions.append((start,len(true_ids)-1))
        for i in range(0,len(positions)):
          txt=""
          ftxt=[]
          for j in range(positions[i][0],positions[i][1]+1):
            txt=src[j]["text"]
            for word in w2:
              matched=[]
              for tgt in src[j]["words"]:
                if re.match(word,tgt["lemma"]) is not None and tgt["form"] not in matched: # it might have rlemma instead
                  rg=re.compile(u"\\b("+tgt["form"]+u")\\b",re.UNICODE)
                  txt=re.sub(rg,"|\g<1>|",txt)
                  matched.append(tgt["form"])
            ftxt.append(txt)
          ftxt=["(...) "*(true_ids[positions[i][0]]-(pseq[i][0]-radius))]+ftxt+[" (...)"*(pseq[i][1]+radius-true_ids[positions[i][1]])]
          result=src[positions[i][0]]
          result["text"]=" ".join(ftxt)
          result["sentence"]=true_ids[positions[i][0]]%10000
          result["_id"]=(result["_id"]//10000)*10000+result["sentence"]
          if radius>0 or positions[i][0]!=positions[i][1]:
            result["endsentence"]=true_ids[positions[i][1]]%10000
          result["maxorder"]=ptk_newf[result["_id"]//10000]
          strs.append(result)
          cur_count+=1
        #tdc+=1
      strs.sort(key=lambda d:d["_id"])
      if cur_count==0:
        coll["max_result"]=-1
        coll["min_result"]=-1
      else:
        coll["max_result"]=coll["min_result"]+cur_count-1
      true_count+=len(strs)
    else:
      strs=[]
      if quick:
        curs=coll["collection"].find(coll["query"]).limit(MAX_RESULTS)
      else:
        curs=coll["collection"].find({"_id":{"$in":ids[coll["min_result"]:coll["max_result"]+1]}}).hint("_id_").limit(MAX_RESULTS)
      #doctype=coll["name"]
      #if name in coll["name"]:
      #  doctype=doc["type"]
      for doc in curs:
        try:
          if radius>0:
            doc["text"]="| "+doc["text"]+" |"
            before=[i for i in range(doc["_id"]-1,doc["_id"]-radius-1,-1)]
            for id in before:
              dt=coll["collection"].find_one({"_id":id},{"text":1})
              if dt is None:
                doc["text"]="(...) "+doc["text"]
              else:
                doc["text"]=dt["text"]+" "+doc["text"]
            after=[i for i in range(doc["_id"]+1,doc["_id"]+radius+1)]
            for id in after:
              dt=coll["collection"].find_one({"_id":id},{"text":1})
              if dt is None:
                doc["text"]+=" (...)"
              else:
                doc["text"]+=" "+dt["text"]
          doc["maxorder"]=ptk_newf[doc["_id"]//10000]
          strs.append(doc)
        except Exception as e:
          logger(out,str(e)+"t1")
      #if coll["name"]=="minute":
      #  strs.sort(key=lambda item: item["_id"])
      #elif name in coll["name"]:
         #strs.sort(key=lambda item: item["_id"]) # this will need better handling
    if coll["min_result"]>=0:
      if name in coll["name"]:
        offset=0
        tlist=[]
        for cname in ["minute"]:
          subset=[]
          try:
            subset=[strs[i] for i in range(0,len(strs)) if strs[i]["type"]==cname]
          except Exception as e:
            logger(out,str(e))
          if len(subset)>0:
            dsets.append({"name":cname+"_"+coll["name"],"min":coll["min_result"]+offset,"max":coll["min_result"]+offset+len(subset)-1})
            offset+=len(subset)
            tlist+=list(subset)
        final+=tlist
      else:
        dsets.append({"name":coll["name"],"min":coll["min_result"],"max":coll["max_result"]})
        final+=strs
  out.close()
  if caching and true_count==-MAX_RESULTS:
    thread=newThread(cursors,name)
    thread.start()
  req.headers_out["Content-Type"]="application/json"
  #final=csv(final)
  times.append(default_timer())
  #result=dumps(final)
  times.append(default_timer())
  times={"started":times[0],"begincaching":times[1],"done_caching":times[2],"finished":times[3],"json_dumps":times[4],"diffs":[times[1]-times[0],times[2]-times[1],times[3]-times[2],times[4]-times[3]]}
  return dumps({"count":int(true_count),"data":final,"datasets":dsets,"time":times},separators=(',', ':'))
