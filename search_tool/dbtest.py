import pymongo

# A quick test of the MongoDB setup. Should ideally be run after inserting data.

client=pymongo.MongoClient() #authenticate here

dbs=client.list_database_names()
print("Mongo has databases: "+str(dbs))

if "dbname" in dbs:
	db=client.dbname
	colls=db.list_collection_names()
	print("Mongo has collections in dbname: "+str(colls))

	if "ptk" in colls:
		print("A document from the ptk collection:")
		print(db.ptk.find_one())
