import json
import hashlib

# files = []
# f = open("./mempool/mempool.json","r")
# data = json.load(f)
# f.close()

# for file in data:
#     files.append(file)

# for file in files:
#     f = open(f"./mempool/{file}.json","r")
#     data = json.load(f)
#     f.close()
#     if (data["status"]["confirmed"] is False):
#         print("Not confirmed")

# for tx in data["vin"]:
#     txid = tx["txid"]
#     print(txid)
#     try:
#         f = open(f"./mempool/{txid}")
#         new_data = json.load(f)
#         f.close()
#         print(new_data["txid"])
#     except Exception:
#         print("File not found")