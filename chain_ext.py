# chain_ext.py
import json
import time
import hashlib
from pathlib import Path

class ChainExt:
    def __init__(self, path="chain.json"):
        self.path = Path(path)
        if not self.path.exists():
            self._init_chain()

    def _init_chain(self):
        genesis = {
            "index": 0,
            "timestamp": time.time(),
            "data": {"type": "genesis"},
            "previous_hash": "0"*64
        }
        genesis["hash"] = self._hash_block(genesis)
        self._write([genesis])

    def _write(self, chain):
        with open(self.path, "w") as f:
            json.dump(chain, f, indent=2)

    def _read(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def _hash_block(self, block):
        block_s = json.dumps({k:block[k] for k in block if k!="hash"}, sort_keys=True).encode()
        return hashlib.sha256(block_s).hexdigest()

    def add_block(self, data):
        chain = self._read()
        prev = chain[-1]
        block = {
            "index": prev["index"]+1,
            "timestamp": time.time(),
            "data": data,
            "previous_hash": prev["hash"],
        }
        block["hash"] = self._hash_block(block)
        chain.append(block)
        self._write(chain)
        return block

    def verify(self):
        chain = self._read()
        for i in range(1,len(chain)):
            if chain[i]["previous_hash"] != chain[i-1]["hash"]:
                return False, i
            if self._hash_block(chain[i]) != chain[i]["hash"]:
                return False, i
        return True, None
