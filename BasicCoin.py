# Importing required libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Building a Blockchain
class Blockchain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.create_block(proof=1, previous_hash='0')
        self.nodes=set()
    
    def create_block(self, proof, previous_hash):
        block={'index':len(self.chain)+1,
        'timestamp':str(datetime.datetime.now()),
        'proof':proof,
        'previous_hash':previous_hash,
        'transactions' : self.transactions }
        self.transactions=[]
        self.chain.append(block)
        return block
    def get_previous_block(self):
     return self.chain[-1]
    
   # This function is to check if the proof of work mined is valid 
    def proof_of_work(self, previous_proof):
        new_proof =1
        check_proof=False
        while check_proof is False:
            # Used a non-symmetric arithmetic so that the result of the arithmetic operation is not repititive
            # The idea is to make the operation tough to compute but easy to check 
            # str and encode functions are used to make the value compatible to what the hashlib.sha256() function is expecting
            # The hexdigest() function is for making the value in hexadecimal form
            hash_function = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()

            #The check is for 4 leading zeros in this case as it any hash start with 4 leading zeros is considers a golden nuance
            #Since this is not a realtime blockchain the value is kept easier to compute for any system
            if hash_function[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof
    # Hash Function to get convert the existing blocks into their respective hashes
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    # Check if each block in the blockchain has the correct proof of work
    # Check if Previous Hash of each block is equal to the hash of previous block
    # Thereby making sure we have a valid blockchain
    def is_chain_valid(self, chain):
        previous_block=chain[0]
        block_index=1
        while block_index< len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_function = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_function[:4]!='0000':
                return False
            previous_block = block
            block_index+=1
            return True
    def add_transaction(self,sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_address=urlparse(address)
        self.nodes.add(parsed_address.netloc)
    
    def replace_chain(self):
        network = self.nodes
        longest_chain=None
        max_length=len(self.chain)
        for node in network:
            response=requests.get(f' http://{node}/get_chain')
            if response.status_code==200:
                length=response.json()['length']
                chain=response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain
        if longest_chain:
            self.chain=longest_chain
            return True
        return False
# Mining Blockchain

# Creating a simple webapp using Flask
app=Flask(__name__)
# Creating an address for the node on port 5000 to start with
node_address=str(uuid4()).replace('-','')
# Creating a Blockchain
blockchain = Blockchain()

# Mining a new Block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof=previous_block['proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address,receiver='Udit', amount=10)
    block=blockchain.create_block(proof,previous_hash)
    response={'message':'Houston, Congratulations !! You Have Successfully Mined The Block',
    'index':block['index'],
    'timestamp':block['timestamp'],
    'proof':block['proof'],
    'previous_hash':block['previous_hash'],
    'transactions':block['transactions']}
    
    return jsonify(response),200

# Getting the Entire Blockchain

@app.route('/get_chain',methods=['GET'])
def get_chain():
    response={'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response),200

# Checking if the blockchain is valid

@app.route('/is_valid',methods=['GET'])
def is_valid():
    isValid = blockchain.is_chain_valid(blockchain.chain)
    
    if isValid:
        response={'message':'Houston, All Good. The Blockchain is valid !!'}
    else:
        response={'message':'Houston, we have a problem. The Blockchain is not valid !!'}
    return jsonify(response),200
# Adding a new transaction to the Blockchain
@app.route('/add_transaction',methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys ={'sender', 'receiver', 'amount'}
    if not all ( key in json for key in transaction_keys):
        return 'Houston, some elements of the transaction are missing', 400
    index=blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response={'message':f'Houston, this transaction will be added to the block {index}'}
    return jsonify(response), 201
# Decentralizing the Blockchain

# Connecting new nodes
@app.route('/connect_node',methods=['POST'])
def connect_node():
    json=request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return 'Houston, there are no nodes', 400
    for node in nodes:
        blockchain.add_node(node)
        response={'message':'Houston, all nodes are now connected. The blockchain now contains the following nodes:',
        'total_nodes':list( blockchain.nodes)}
    return jsonify(response), 201
# Replacing the chain with the longest chain if needed
@app.route('/replace_chain',methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    
    if is_chain_replaced:
        response={'message':'Houston, The nodes had different chains so was replaced by the longest one.',
        'new_Chain':blockchain.chain}
    else:
        response={'message':'Houston, All Good. The chain is the longest one !!',
        'actual_chain':blockchain.chain}
    return jsonify(response),200
# Running the app
app.run(host='0.0.0.0', port=5000)