from node import Host, os, contract_node
from uuid import uuid4

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    # 0: customer	1: merchant	2:contract
    parser.add_argument('-i', '--identity', default=0, type=int, help='identity of node')
    args = parser.parse_args()
    port = args.port
    identity = args.identity
    key = str(uuid4())[:8] 

    
    ids = ['customer', 'merchant', 'contract']
    exec("from "+ids[identity]+" import app")

    if identity == 0:
        # default: 50 collateral
        os.system("curl -X POST -H \"Content-Type: application/json\" -d \'{\"nodes\": [\"%s\"], \"collateral\": \"%s\"}\' http://%s/register/customer" % (Host+":"+str(port), str(50), Host+":"+contract_node))
    elif identity == 1:
        os.system("curl -X POST -H \"Content-Type: application/json\" -d \'{\"nodes\": [\"%s\"], \"key\": \"%s\", \"collateral\": \"%s\"}\' http://%s/register/merchant" % (Host+":"+str(port), key, str(50), Host+":"+contract_node))

    app.run(host='0.0.0.0', port=port)

