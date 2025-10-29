from flask import Flask, render_template, request, redirect, url_for
import requests
import json

app = Flask(__name__)

NODE_URL = "http://127.0.0.1:5000"  # Change to your node URL

@app.route('/')
def index():
    try:
        chain = requests.get(f"{NODE_URL}/chain").json()
        nodes = requests.get(f"{NODE_URL}/nodes/list").json() if "nodes/list" in locals() else {"nodes": []}
        pending = requests.get(f"{NODE_URL}/transactions/pending").json() if "transactions/pending" in locals() else {"transactions": []}
        return render_template('index.html', chain=chain, nodes=nodes, pending=pending)
    except Exception as e:
        return f"Error fetching blockchain data: {e}"

@app.route('/mine', methods=['POST'])
def mine():
    requests.get(f"{NODE_URL}/mine")
    return redirect(url_for('index'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    recipient = request.form['recipient']
    amount = request.form['amount']
    tx = {'sender': sender, 'recipient': recipient, 'amount': int(amount)}
    headers = {'Content-Type': 'application/json'}
    requests.post(f"{NODE_URL}/transactions/new", data=json.dumps(tx), headers=headers)
    return redirect(url_for('index'))

@app.route('/resolve', methods=['POST'])
def resolve():
    requests.get(f"{NODE_URL}/nodes/resolve")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(port=8000, debug=True)
