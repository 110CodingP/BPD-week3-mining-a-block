import json

f = open("./mempool/00000a2d1a9e29116b539b85b6e893213b1ed95a08b7526a8d59a4b088fc6571.json")
data = json.load(f)
f.close()
# print(data)

for tx in data["vin"]:
    txid = tx["txid"]
    print(txid)
    try:
        f = open(f"./mempool/{txid}")
        new_data = json.load(f)
        f.close()
        print(new_data["txid"])
    except Exception:
        print("File not found")