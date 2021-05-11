from node import *
import threading

class Contract(Node):
    def __init__(self):
        Node.__init__(self)
        self.customers = {} # {url: collateral, url:[key, collateral], ...}
        self.merchants = {} # {url: [key, collateral], url:[key, collateral], ...}
        self.current_transactions = [] # {'transaction':{}, 'state':(0:wait), 'approve':(int), 'disapprove':(int), 'voter':[url1, url2, ...]}
        self.sequence = 0

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_customer(self, address, collateral):
        # :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            parsed_url = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            parsed_url = parsed_url.path
        else:
            raise ValueError('Invalid URL')

        # Add a customer
        self.customers[parsed_url] = int(collateral)
    
    def register_merchant(self, address, key, collateral):
        # Get new url
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            parsed_url = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            parsed_url = parsed_url.path
        else:
            raise ValueError('Invalid URL')

        # Add a merchant
        self.merchants[parsed_url] = ["", 0]
        self.merchants[parsed_url][0] = key  
        self.merchants[parsed_url][1] = int(collateral)
        
        
    def config_merchants(self):
        for merchant in self.merchants.keys():
            update_balance(merchant, get_balance(merchant) - self.merchants[merchant][1])
            merchants_url = ""  # all other merchants
            for url in self.merchants.keys():
                if url == merchant:
                    continue
                merchants_url += "\"http://" + url + "\", "
            merchants_url = merchants_url[:-2]
            os.system("curl -X POST -H \"Content-Type: application/json\" -d \'{\"nodes\": [%s]}\' http://%s/register/statekeeper" % (merchants_url, merchant))    

    def config_customers(self):
        for customer in self.customers.keys():
            update_balance(customer, get_balance(customer) - self.customers[customer])


    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
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

# Instantiate the Blockchain
blockchain = Contract()

def get_balance(url):   # url: http://xx.xx.xx.xx:xx
    #os.system("curl \"http://%s/balance\"" % url)
    balance = json.loads(requests.get("http://"+url+"/balance").text)['balance']
    return balance

def update_balance(url, balance):   # url: http://xx.xx.xx.xx:xx
    requests.post("http://"+url+"/balance/update", json={'balance':balance})

@app.route('/register/customer', methods=['POST'])
def new_customer():
    values = request.get_json()
    nodes = values.get('nodes')
    collateral = values.get('collateral')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    if collateral is None:
        return "Error: Please supply a valid collateral", 400

    blockchain.register_customer(nodes[0], collateral)

    response = {
        'message': 'New customer have been added',
        'total_customers': list(blockchain.customers),
    }
    return jsonify(response), 201

@app.route('/register/merchant', methods=['POST'])
def new_merchant():
    values = request.get_json()
    node = values.get('nodes')
    key = values.get('key')
    collateral = values.get('collateral')
    if node is None:
        return "Error: Please supply a valid list of nodes", 400
    if key is None:
        return "Error: Please supply a valid key", 400

    blockchain.register_merchant(node[0], key, collateral)

    response = {
        'message': 'New customer have been added',
        'total_merchants': list(blockchain.merchants),
    }
    return jsonify(response), 201
    

@app.route('/register/config', methods=['GET'])
def register_config():
    blockchain.config_merchants()
    blockchain.config_customers()
    response = {
        'message': 'Config done',
    }
    return jsonify(response), 200


@app.route('/transaction/check', methods=['POST'])
def transaction_check():
    values = request.get_json()
    new_transaction = values.get('transaction') # no http
    pending_list = values.get('pending')    
    if new_transaction is None:
        return "Error: Please supply a valid new_transaction", 400
    sender = new_transaction['sender']
    recipient = new_transaction['recipient']
    amount = new_transaction['amount']

    # check if the sender and recipient exist
    if blockchain.customers.get(sender) is None:
        return "Error: the sender does not exist", 400
    elif blockchain.merchants.get(recipient) is None:
        return "Error: the recipient does not exist", 400
    
    # check if the collateral is enough
    total_amount = amount
    for transaction in pending_list:
        total_amount = total_amount + transaction['amount']
    if blockchain.customers[sender] < total_amount:
        return "Error: collateral of the sender is not enough", 400
    
    # Add id to it
    new_transaction['id'] = blockchain.sequence
    
    # Initialize current_transactions[n]
    total = -1 * (len(blockchain.merchants) - 1)
    blockchain.current_transactions.append({'transaction':new_transaction, 'total':total, 'voter':[]})
    blockchain.sequence += 1
    
    # send this transaction to the merchant(recipient)
    requests.post("http://"+recipient+"/transaction/broadcast", json={'transaction':new_transaction, 'pending':pending_list})

    response = {
        'message': 'check done',
    }
    return jsonify(response), 201

@app.route('/transaction/counting', methods=['POST'])
def transation_counting():
    values = request.get_json()
    current_tran = values.get('transaction')
    voter = values.get('myurl')
    result = values.get('result')
    i = 0
    for transation in blockchain.current_transactions:
        if transation['transaction']['id']== current_tran['id']:
            blockchain.current_transactions[i]['total'] += 1
            if result:
                blockchain.current_transactions[i]['voter'].append(voter)
            if blockchain.current_transactions[i]['total'] == 0:
                # all merchants finished voting
                if len(blockchain.current_transactions[i]['voter']) >= len(blockchain.merchants)//2:
                    # get consensus
                    print("\033[1;33;44;4mTransaction %d voting passed\033[0m" % current_tran['id'])
                    tuples=(current_tran, 5)
                    threading.Thread(target=send_pass, args=tuples).start()
                else:
                    # failed
                    print("\033[1;33;44;4mTransaction %d voting failed\033[0m" % current_tran['id'])
                    blockchain.current_transactions.remove(transation)
                    for merchant in blockchain.merchants.keys():
                        tuples=(merchant, current_tran)
                        threading.Thread(target=send_fail, args=tuples).start()
            break
        i += 1

    response = {
        'message': 'Consent verified',
        'total_merchants': list(blockchain.merchants),
    }
    return jsonify(response), 201

def send_pass(*add):
    current_tran = {}
    i = 0
    for arc in add:
        if i == 0:
            current_tran = arc
        i += 1
    requests.post("http://"+current_tran['sender']+"/transaction/pass", json={'transaction':current_tran})

def send_fail(*add):
    merchant = ""
    current_tran = {}
    i = 0
    for arc in add:
        if i == 0:
            merchant = arc
        else:
            current_tran = arc
        i += 1
    requests.post("http://"+merchant+"/transaction/delete", json={'delete':current_tran})
    