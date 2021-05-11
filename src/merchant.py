from node import *
import threading

class Merchant(Node):
    def __init__(self):
        Node.__init__(self)
        self.statekeepers = []  # the urls of other merchants
        self.balance = 50
        self.tran_list = {} # {url:[tran1, tran2..], url:[tran1, tran2..]}
    
    def register_statekeeper(self, address):
        # Add statekeepers
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.statekeepers.append(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.statekeepers.append(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

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

# Instantiate the Blockchain
blockchain = Merchant()

@app.route('/register/statekeeper', methods=['POST'])
def new_statekeepers():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_statekeeper(node)
    
    response = {
        'message': 'New statekeeper have been added',
        'total_statekeepers': list(blockchain.statekeepers),
    }
    return jsonify(response), 201

# receive the transaction from contract and send it to all other statekeepers
@app.route('/transaction/broadcast', methods=['POST'])
def transaction_broadcast():
    values = request.get_json()
    transaction = values.get('transaction')
    pending = values.get('pending')
    if transaction is None:
        return "Error: Cannot receive the transaction from contract", 400


    for statekeeper in blockchain.statekeepers:
        # post this transaction to statekeepers
        tuples=(statekeeper, transaction, pending)
        threading.Thread(target=get_consent, args=tuples).start()
        # requests.post("http://"+statekeeper+"/transaction/vote", json={'transaction':transaction, 'pending':pending, 'voter':statekeeper})
    
    response = {
        'message': 'Transaction broadcast finished',
    }
    return jsonify(response), 201

def get_consent(*add):
    i = 0
    statekeeper = ""
    transaction = {}
    pending = []
    for arc in add:
        if i == 0:
            statekeeper = arc
        elif i == 1:
            transaction = arc
        else:
            pending = arc
        i += 1 
    requests.post("http://"+statekeeper+"/transaction/vote", json={'transaction':transaction, 'pending':pending, 'voter':statekeeper})

# receive the transaction from a merchant and vote for it
@app.route('/transaction/vote', methods = ['POST'])
def transaction_vote():
    values = request.get_json()
    transaction = values.get('transaction')
    pending = values.get('pending')
    myurl = values.get('voter')
    if transaction is None:
        return "Error: Cannot receive the transaction from merchant", 400
    if myurl is None:
        return "Error: Cannot receive my url", 400
    # plain = json.dumps(transaction).encode()
    # add the transaction to tran_list
    sender = transaction['sender']
    if blockchain.tran_list.get(sender) is None:
        blockchain.tran_list[sender] = []
    
    # check if there is any hide transactions
    valid = True
    for tran in blockchain.tran_list[sender]:
        valid1 = False
        for pend_tran in pending: 
            if tran['id'] == pend_tran['id']:
                valid1 = True
                break
        valid = valid1
        if (valid == False):
            break

    blockchain.tran_list[sender].append(transaction)
    
    # vote
    if valid :
        print("The transaction request is valid, ", end='')
    else:
        print("The transaction request is not valid, ", end='')
    choice = input("enter your choice (y/N): ")
    if choice == 'y' or choice == 'Y':
        # approve
        requests.post("http://"+Host+":"+contract_node+"/transaction/counting", json={'transaction':transaction, 'statekeeper':myurl, 'result':True})
    else:
        # disapprove
        requests.post("http://"+Host+":"+contract_node+"/transaction/counting", json={'transaction':transaction, 'statekeeper':myurl, 'result':False})
    
    response = {
        'message': 'Transaction vote finished',
        
    }
    return jsonify(response), 201

@app.route('/transaction/delete', methods = ['POST'])
def transaction_delete():
    values = request.get_json()
    dele_tran = values.get('delete')
    if dele_tran is None:
        return "Error: Cannot receive the transaction to delete", 400
    

    sender = dele_tran['sender']
    i = 0
    if sender in blockchain.tran_list.keys():
        for tran in blockchain.tran_list[sender]:
            if tran['id'] == dele_tran['id']:
                del(blockchain.tran_list[sender][i])
                break
            i = i + 1
    response = {
        'message': 'Delete finished',
    }
    return jsonify(response), 201
    
        
            


