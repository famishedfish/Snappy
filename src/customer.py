from node import *

class Customer(Node):
    def __init__(self):
        Node.__init__(self)
        self.balance = 100
        self.pending_transaction = []

# Instantiate the Blockchain
blockchain = Customer()

@app.route('/balance', methods=['GET'])
def get_balance():
    response = {
        'balance': blockchain.balance,
    }
    return jsonify(response), 200
    
@app.route('/balance/update', methods=['POST'])
def update_balance():
    values = request.get_json()
    balan = values.get('balance')
    if balan is None: 
        return "Error: Please supply a valid balance", 400
    else:
        blockchain.balance = balan
    response = {
        'balance': blockchain.balance,
    }
    return jsonify(response), 200

@app.route('/transaction/create', methods=['POST'])
def new_transaction():
    transaction = request.get_json()    # a dict
    
    choice = input("Launch an attack (y/N): ")
    if choice == 'y' or choice == 'Y':
        r = requests.post("http://"+Host+":"+contract_node+"/transaction/check", json={'transaction':transaction, 'pending':[]})
    else:
        r = requests.post("http://"+Host+":"+contract_node+"/transaction/check", json={'transaction':transaction, 'pending':blockchain.pending_transaction})
    print(r.text)
    
    response = {
        'balance': blockchain.balance,
    }
    return jsonify(response), 200

@app.route('/transaction/pass', methods=['POST'])
def add_transaction():
    transaction = request.get_json()    # a dict

    blockchain.pending_transaction.append(transaction.get('transaction'))
    print("\033[1;33;44;4mTransaction with %s, amount %d} success.\033[0m" % (blockchain.pending_transaction[-1]['recipient'], blockchain.pending_transaction[-1]['amount']))
    
    response = {
        'balance': blockchain.balance,
    }
    return jsonify(response), 200