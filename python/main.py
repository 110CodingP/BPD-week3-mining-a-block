"""
Clarifications:
- do we need to check whether ancestors are included and double spends, RBF?
- do we have to maximize the fee?
- are the filenames the txids?
"""

"""
Approach
- select transactions
- construct the coinbase transaction
- create block header
"""

import json
import queue
import time
import hashlib

def main():

    # to calculate compact size
    def cmptSz(data:bytes)->bytes:
        val = len(data) # c'mmon it's compact SIZE for a reason
        if (val<=252):
            return val.to_bytes(1,"little",signed=False)
        elif val>252 and val<=65535:
            return bytes.fromhex("fd") + val.to_bytes(2,"little",signed=False)
        elif val>65535 and val<=4294967295:
            return bytes.fromhex("fe") + val.to_bytes(4,"little",signed=False)
        elif val>4294967295 and val<=18446744073709551615:
            return bytes.fromhex("ff") + val.to_bytes(8,"little",signed=False)
        
    # to find out pushbytes opcode
    def pushbytes(data:bytes)->bytes:
        sz = len(data)
        if (sz<=76):
            return sz.to_bytes(1,byteorder="little",signed=False)
        elif (sz<=255):
            return bytes.fromhex("4c") + sz.to_bytes(1,byteorder="little",signed=False)
        elif (sz<=520):
            return bytes.fromhex("4d") + sz.to_bytes(2,byteorder="little",signed=False)
    
    def hash256(data:bytes)->bytes:
        return hashlib.sha256(hashlib.sha256(data).digest()).digest()
    
    def difficulty_to_bits(difficulty:str)->bytes:
            exp = 0
            for i in range(len(difficulty)):
                if difficulty[i]!='0':
                    break
            if (i%2!=0):
                i-=1
            if (int(difficulty[i:i+2],base=16)>=80):
                i-=2
            exp = (len(difficulty)-(i))//2
            return  bytes.fromhex(difficulty[i+4:i+6]+difficulty[i+2:i+4]+difficulty[i:i+2]) + exp.to_bytes(1,byteorder="little",signed=False)

    # selecting transactions (need to take care of block wt)

    files = []
    f = open("./mempool/mempool.json","r")
    data = json.load(f)
    f.close()

    for file in data:
        files.append(file)
    
    def add():
        pass

    bits = difficulty_to_bits("0000ffff00000000000000000000000000000000000000000000000000000000")
    def find_target(bits):
        bits = bits[::-1]
        bits = bits.hex()
        exp = int(bits[:2],base=16)
        base = int(bits[2:],base=16)<<(8*(exp-3))
        base = base.to_bytes(32,"big",signed=False)
        return base

    target = find_target(bits)

    def find_wtxids(txids):
        wtxids = []
        for txid in txids:
            f = open(f"./mempool/{txid}.json","r")
            data = json.load(f)
            f.close()
            wtxid = hash256(bytes.fromhex(data["hex"]))
            wtxids.append(wtxid)
        return wtxids
    
    def find_root(txids):
        level = [txid[::-1] for txid in txids]

        while (len(level)>=2):
            next_level = []
            for i in range(0,len(level),2):
                if (i+1 == len(level)):
                    next_level.append(hash256(level[i]+level[i]))
                else:
                    next_level.append(hash256(level[i]+level[i+1]))
            level = next_level
    
        return level[0]

    def create_coinbase(witness_root_hash):
        version = bytes.fromhex("01000000")
        marker = bytes.fromhex("00")
        flag = bytes.fromhex("01")

        input_ct = bytes.fromhex("01")
        txid_to_spend = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")
        idx_to_spend = bytes.fromhex("ffffffff")
        block_ht = bytes.fromhex("97040d")
        script_sig = pushbytes(block_ht) + block_ht
        sequence = bytes.fromhex("ffffffff")

        inputs = (
            txid_to_spend + 
            idx_to_spend + 
            cmptSz(script_sig) + 
            script_sig +
            sequence
        )

        witness_reserved_val = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")
        witness = (
            bytes.fromhex("01") + 
            pushbytes(witness_reserved_val) + 
            witness_reserved_val
        )

        output_ct = bytes.fromhex("02")
        output1_amt_sats = (50*(10**8)).to_bytes(8,byteorder="little",signed=True)
        output1_spk = bytes.fromhex("76a914") + bytes.fromhex("3bc28d6d92d9073fb5e3adf481795eaf446bceed") + bytes.fromhex("88ac")
        output2_amt_sats = bytes.fromhex("0000000000000000")

        output2_spk = bytes.fromhex("6a") + bytes.fromhex("24") + bytes.fromhex("aa21a9ed") + hash256(witness_root_hash + witness_reserved_val)

        outputs = (
            output1_amt_sats +
            cmptSz(output1_spk) + 
            output1_spk + 
            output2_amt_sats + 
            cmptSz(output2_spk) + 
            output2_spk
        )

        locktime = bytes.fromhex("00000000")

        coinbase = (
            version + 
            marker + 
            flag + 
            input_ct + 
            inputs + 
            output_ct + 
            outputs + 
            witness + 
            locktime
        )

        coinbase_txid = hash256(
            version +
            input_ct +
            inputs + 
            output_ct + 
            outputs +
            locktime
        )[::-1] # remember to reverse to get the txids
        return [coinbase, coinbase_txid]
    
    # find magic nonce
    def find_nonce(header_without_nonce, target):
        for nonce in range(4294967295+1):
            print(nonce)
            if (hash256(header_without_nonce + nonce.to_bytes(4,"little",signed=False)) <= target ):
                return [True, nonce]
        return [False, nonce]
    
    def create_block(merkle_root, bits, target):
        block_version = bytes.fromhex("00010000")
        previousBlockHash = bytes.fromhex("0000fffe00000000000000000000000000000000000000000000000000000000")[::-1]
    
        # timestamp
        timestamp = int(time.time()).to_bytes(4,byteorder="little",signed=False)

        header_without_nonce = (
            block_version + 
            previousBlockHash + 
            merkle_root +
            timestamp +
            bits
        )
        found, nonce = find_nonce(header_without_nonce,target)
        return [found,header_without_nonce+nonce.to_bytes(4,"little",signed=False)]
    
    # mine
    found = False
    while (found == False):
        txids = []
        # some kind of add transaction function
        wtxids = [bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")]
        wtxids = wtxids + find_wtxids(txids)
        witness_root_hash = find_root(wtxids)


        coinbase, coinbase_txid = create_coinbase(witness_root_hash)


        txids = [coinbase_txid] + txids
        merkle_root = find_root(txids)

        found, block_header = create_block(merkle_root,bits, target)
    
    # output
    f = open("out.txt","w")
    txids = [txid.hex() for txid in txids]
    txids = '\n'.join(txids)
    f.write(f"{block_header.hex()}\n{coinbase.hex()}\n{txids}")
    f.close()

    


if __name__ == "__main__":
    main()

"""
References:
- block header: learnmeabitcoin.com => block header: version + prev_block_hash + merkle-root + time + bits + nonce (remember to reverse)
- mining simulator: learnmeabitcoin.com
- "All the descendants of a conflicting memory pool transaction will be removed at the same time": learnmeabitcoin.com
- steps to construct block : https://learnmeabitcoin.com/technical/mining/candidate-block/#construction
-  if a transaction has ancestors that are currently in the mempool, those ancestors must be included above it in the candidate block. : learnmeabitcoin
- calculating weight of block : https://learnmeabitcoin.com/technical/transaction/size/#:~:text=The%20size%20of%20a%20transaction%20in%20bytes%20mostly%20depends%20on,or%20226%20bytes%20(most%20common)
- blockheader is a fixed size: 320 wu
- version 2 is not required for segwit
- getting the unix epoch time : https://stackoverflow.com/questions/16755394/what-is-the-easiest-way-to-get-current-gmt-time-in-unix-timestamp-format
- target to bits : https://learnmeabitcoin.com/technical/block/bits/#target-to-bits
- minimum block version: https://learnmeabitcoin.com/technical/block/version/#version-numbers
- "The TXIDs should be input in reverse byte order (as they appear on blockchain explorers), but they are converted to natural byte order before the merkle root is calculated.": learmeabitcoin
- finding merkle root : ../test/helper.ts
- bits to target: https://learnmeabitcoin.com/technical/block/bits/#bits-to-target
"""