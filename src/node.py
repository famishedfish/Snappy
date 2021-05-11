import hashlib
import json
import os
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request



class Node:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()	# store urls

contract_node = "8000"
Host = "10.211.55.3"
My_port = ""

# Instantiate the Node
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

@app.route('/exit', methods=['GET'])
def exits():
    exit(1)
    


