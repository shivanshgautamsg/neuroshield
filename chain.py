# chain.py
import hashlib, json, time, os

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class SimpleChain:
    def __init__(self, path='chain.json'):
        self.path = path
        if os.path.exists(self.path):
            with open(self.path,'r') as f:
                self.chain = json.load(f)
        else:
            genesis = Block(0, time.time(), {"type":"genesis","note":"NeuroShield genesis"}, "0").__dict__
            # store dict-friendly form (hash included)
            genesis['hash'] = genesis['hash']
            self.chain = [self._block_to_dict(genesis)]
            self._save()

    def _block_to_dict(self, block_obj):
        # block_obj might already be dict
        if isinstance(block_obj, dict):
            return {
                'index': block_obj.get('index'),
                'timestamp': block_obj.get('timestamp'),
                'data': block_obj.get('data'),
                'previous_hash': block_obj.get('previous_hash'),
                'hash': block_obj.get('hash')
            }
        return block_obj.__dict__

    def add_block(self, data):
        last = self.chain[-1]
        new_block = Block(last['index'] + 1, time.time(), data, last['hash'])
        bdict = self._block_to_dict(new_block.__dict__)
        self.chain.append(bdict)
        self._save()
        return bdict

    def verify(self):
        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i-1]
            # recompute hash
            recomputed = hashlib.sha256(json.dumps({
                'index': cur['index'],
                'timestamp': cur['timestamp'],
                'data': cur['data'],
                'previous_hash': cur['previous_hash']
            }, sort_keys=True).encode()).hexdigest()
            if cur['previous_hash'] != prev['hash'] or recomputed != cur['hash']:
                return False, i
        return True, None

    def _save(self):
        with open(self.path,'w') as f:
            json.dump(self.chain, f, indent=2)

if __name__ == '__main__':
    sc = SimpleChain()
    b = sc.add_block({"type":"test","zone":"Test Zone","score":0.5,"note":"initial test"})
    print("Added block:", b)
    ok, idx = sc.verify()
    print("Chain ok?", ok, ("first bad index:"+str(idx)) if not ok else "")
