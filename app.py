from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
from uuid import uuid4
from blockchain import Blockchain
import json
import os

app = Flask(__name__)
CORS(app)

node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

# ===============================
# 🌍 FRONTEND ROUTES
# ===============================
@app.route('/')
def index():
    chain_data = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return render_template('index.html', chain=chain_data)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    recipient = request.form['recipient']
    amount = request.form['amount']

    tx = {
        'sender': sender,
        'recipient': recipient,
        'amount': int(amount)
    }
    blockchain.new_transaction(sender, recipient, int(amount))
    return redirect(url_for('index'))

@app.route('/mine', methods=['POST'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    last_hash = blockchain.hash(last_block)
    proof = blockchain.proof_of_work(last_proof, last_hash)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    block = blockchain.new_block(proof, previous_hash=last_hash)
    return redirect(url_for('index'))

@app.route('/resolve', methods=['POST'])
def resolve():
    blockchain.resolve_conflicts()
    return redirect(url_for('index'))


# ===============================
# ⚙️ BACKEND API ROUTES
# ===============================
@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction_api():
    values = request.get_json(force=True)
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    return jsonify({'message': f'Transaction will be added to Block {index}'}), 201

@app.route('/mine_block', methods=['GET'])
def mine_block():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    last_hash = blockchain.hash(last_block)
    proof = blockchain.proof_of_work(last_proof, last_hash)
    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)
    block = blockchain.new_block(proof, previous_hash=last_hash)
    return jsonify(block), 200


# ===============================
# 🚀 MAIN ENTRY POINT
# ===============================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Railway sets PORT automatically
    app.run(host='0.0.0.0', port=port)
