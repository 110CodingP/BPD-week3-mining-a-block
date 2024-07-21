"""
Clarifications:
- do we need to check whether ancestors are included and double spends, RBF?
- do we have to maximize the fee?
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
    
    # selecting transactions
    
    # creating the coinbase txn
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
    # if only coinbase txn is present
    witness_root_hash = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")
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

    # construct the block
    block_version = bytes.fromhex("00010000")
    previousBlockHash = bytes.fromhex("0000fffe00000000000000000000000000000000000000000000000000000000")[::-1]
    merkle_root = coinbase_txid[::-1]
    
    # timestamp
    timestamp = int(time.time()).to_bytes(4,byteorder="little",signed=False)

    # bits
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
    
    # print(difficulty_to_bits("0000ffff00000000000000000000000000000000000000000000000000000000").hex())
    bits = difficulty_to_bits("0000ffff00000000000000000000000000000000000000000000000000000000")

    header_without_nonce = (
        block_version + 
        previousBlockHash + 
        merkle_root +
        timestamp +
        bits
    )
    
    nonce = bytes.fromhex("00000000")

    # nonce
    # found = False
    # correct below code
    # exp = int((bits.hex())[:2],base=16)
    # target = int((bits.hex())[2:],base=16)<<exp
    # for random_num in range(4294967295+1):
    #     nonce = random_num.to_bytes(4,byteorder="little",signed=False)
    #     hash_val = hash256(header_without_nonce + nonce)
    #     if (int(hash_val.hex(),base=16)<exp = int((bits.hex())[:2],base=16)
    # target = int((bits.hex())[2:],base=16)<<exptarget):
    #         found = True
    #         header_hash = hash_val
    #         break
    
    f = open("out.txt","w")
    f.write(f"{(header_without_nonce+nonce).hex()}\n{coinbase.hex()}\n{coinbase_txid.hex()}")
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
"""