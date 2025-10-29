# blockchain.py
import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node's address (e.g. 'http://127.0.0.1:5001')
        """
        parsed = urlparse(address)
        if parsed.netloc:
            self.nodes.add(parsed.netloc)
        elif parsed.path:
            # Accepts URLs like '127.0.0.1:5001'
            self.nodes.add(parsed.path)
        else:
            raise ValueError('Invalid node URL')

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid:
        - Check hashes link correctly
        - Check proofs of work
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            last_block_string = json.dumps(last_block, sort_keys=True).encode()
            last_block_hash = hashlib.sha256(last_block_string).hexdigest()
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], block.get('previous_hash')):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus algorithm: replace our chain with the longest valid chain in the network.
        Returns True if our chain was replaced, False if not.
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            try:
                resp = requests.get(f'http://{node}/chain', timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    length = data['length']
                    chain = data['chain']

                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.RequestException:
                # If a node is down or not reachable, skip it
                continue

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block and add it to the chain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Adds a new transaction to the list of transactions.
        Returns the index of the block that will hold this transaction.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Hash a Block (dict) using SHA-256. Must be consistent: sort keys.
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof, last_hash):
        """
        Simple Proof of Work:
         - Find p' such that hash(last_proof, p', last_hash) contains 4 leading zeros
        """
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the proof: hash(last_proof, proof, last_hash) has 4 leading zeros.
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
