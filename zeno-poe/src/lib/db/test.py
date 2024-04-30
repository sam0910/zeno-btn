"""
# del db[b"2"]

# for key in db:
     print(key)

# print(b"2" in db)

# Print after b2
for word in db.values(b"2"):
    print("word", word)
# db.flush()
"""
MYDB = "/data/ota.db"
from db.connect import DB

# import samos as s
# s.rm(MYDB)

# with DB(MYDB) as db:
#     db.set(1, "one")
#     db.set(2, "one2")
#     db.set(3, "one3")
#     db.set("wifi", "ssid:wertt,passwd:1010103")
#     db.set("aifi", "ssid:wertt,passwd:1010103")
#     db.set(4, "one4")
#     db.set(5, "one5")
#     db.set(6, "one6")
#     db.set(7, "one7")

#     for key in db.db:
#         print("key", key)

#     print("b2_exist", db.exist(2))
#     db.delete(2)
#     print("b2_exist", db.exist(2))
#     db.delete(2)

#     a = db.get("wifi")
#     print(a)

#     # for word in db.values(bytes("777888002", "utf-8")):
#     #     print("word", word)

# print("Done")


from db.connect import DB

db = DB("/data/ota.db")

with db:
    print(db.get(3))
    print(db.get(4))

usys.exit()

db = DB("/data/ota.db")
db.connect()
db.list()


for word in db.db.values(b"wifi"):
    print(word)

a = db.get(4)
print(a)
print(db.connected)

db.close()
print(db.connected)
