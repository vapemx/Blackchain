from flask import Flask, jsonify, request
from urllib.parse import urlparse
from random import randint
from uuid import uuid4
import argparse
import requests
import datetime
import hashlib
import json


# Crear la blockchain
class Blockchain:
    def __init__(self):
        #Cadena que contiene los bloques
        self.chain = []
        self.transactions = []
        self.accounts = [{'pub_key': 'MASTER', 'balance': 100000000}] # Cantidad de pinkcoins en circulación
        #Bloque Genesis
        self.create_block(proof=1, previous_hash='0')
        #Nodos
        self.nodes = set()
        

    def create_wallet(self, entropy):
        # Algoritmo de aleatoriedad basado en la entropia dada
        seed = 0
        for caracter in entropy:
            seed += ord(caracter)

        private_key = hashlib.sha256(str(seed*randint(1, seed*seed)).encode()).hexdigest()
        pub_key = hashlib.sha256(str(private_key).encode()).hexdigest()

        account = {'pub_key': pub_key,
                   'balance': 1}
        self.accounts.append(account)
        return pub_key, private_key


    # Añadir nodos a la red
    def add_node(self, address):
        parsed_url = urlparse(address) # Address de flask
        self.nodes.add(parsed_url.netloc)


    # Prueba de consenso Reemplazar la cadena por la más larga
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)

        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
            
            if longest_chain:
                self.chain = longest_chain
                return True

            return False


    # Crear un nuevo bloque
    def create_block(self, proof, previous_hash):
        # Realizar las transacciones
        for transaction in self.transactions:
            for account in self.accounts:
                if transaction['sender'] == 'MASTER':
                    account['balance'] -= transaction['amount']                
                if hashlib.sha256(str(transaction['sender']).encode()).hexdigest() in account['pub_key']:
                    account['balance'] -= transaction['amount']
                if transaction['receiver'] in account['pub_key']:
                    account['balance'] += transaction['amount']

        # Crear el bloque
        block = {'index': len(self.chain)+1,
                'timestamp': str(datetime.datetime.now()),
                'proof': proof,
                'previous_hash': previous_hash,
                'transactions': self.transactions,
                'accounts': self.accounts.copy()}
        
        self.transactions = []        
        self.chain.append(block)
        
        return block


    # Añadir una transacción al mempool
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        
        previous_block = self.get_previous_block()
        
        return previous_block['index'] + 1
    

    # Obtener el último bloque de la cadena
    def get_previous_block(self):
        return self.chain[-1]
    

    # Problema a minar 
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
            
        return new_proof
        

    # Obtener el hash de un bloque
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        
        return hashlib.sha256(encoded_block).hexdigest()


    # Comprobar la validez de la cadena
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof ** 2).encode()).hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
        
        return True
        

# Argumentos de entrada para el puerto
parser = argparse.ArgumentParser(description='Puerto de ejecución de la blockchain')
    
parser.add_argument('--port', '-p', dest='port', type=int, help='Puerto de ejecución de la blockchain.')
args = parser.parse_args()
port = args.port

# Ejecución de la blockchain
app = Flask(__name__)

# Crear una dirección para el nodo
node_address = str(uuid4()).replace('-', '')

blockchain = Blockchain()

# Minar nuevo bloque
@app.route('/mine_block', methods=['GET'])

def mine_block():
    # Se busca una cartera a recompensar por la minería
    json = request.get_json()
    if json is None or json.get('receiver') is None:
        return 'Faltan elementos en la transacción', 400

    # Proof of work
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)

    # Recompensa por minar
    if blockchain.get_previous_block()['index'] == 0:
        receiver = 'MASTER'
    else:
        receiver = json.get('receiver')    
    blockchain.add_transaction(sender='MASTER', receiver=receiver, amount=1)

    # Crear el bloque
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Felicidades, has minado un bloque!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions'],
                'accounts': block['accounts']}
    
    return jsonify(response), 200 
     

# Obtener la cadena de bloques completa
@app.route('/get_chain', methods=['GET'])

def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    
    return jsonify(response), 200


# Comprobación de la cadena
@app.route('/is_valid', methods=['GET'])

def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    
    if is_valid:
        response = {'message': 'La cadena es valida'}
    else:
        response = {'message': 'La cadena no es valida'}
    
    return jsonify(response), 200


# Añadir una nueva transacción al bloque
@app.route('/add_transaction', methods=['POST'])

def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Faltan elementos en la transacción', 400

    if json['sender'] == 'MASTER':
        response = {'message': 'No se puede enviar fondos desde la cuenta MASTER'}
        return jsonify(response), 400

    # Sólo se pueden realizar transacciones aprobadas por una llave privada
    # Por lo que, con ese input, se genera una llave pública y se realiza la transacción
    sender_priv_key = json['sender']
    sender_pub_key = hashlib.sha256(str(sender_priv_key).encode()).hexdigest()

    for account in blockchain.accounts:
        if sender_pub_key not in account['pub_key']:
            response = {'message': 'La cuenta emisora no existe'}
            break
        
        elif sender_pub_key == json['receiver']:
            response = {'message': 'No se puede enviar fondos a la misma cuenta'}
            break
        
        elif json['receiver'] not in account['pub_key']:
            response = {'message': 'La cuenta receptora no existe'}
            break

        elif json['amount'] <= 0:
            response = {'message': 'La cantidad debe ser mayor a 0'}
            break

        elif json['amount'] > account['balance']:
            response = {'message': 'Fondos insuficientes'}
            break

        else:
            index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
            response = {'message': f'La transacción será añadida al bloque {index}'}
    
    return jsonify(response), 201


# Conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])

def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No hay nodos', 401
    
    for node in nodes:
        blockchain.add_node(node)
    
    response = {'message': 'Todos los nodos estan conectados. La blockchain contiene los siguientes nodos:',
                'total_nodes': list(blockchain.nodes)}

    return jsonify(response), 201


# Reemplazar la cadena por la más larga, en caso de no tener la mas larga
@app.route('/replace_chain', methods=['GET'])

def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'La cadena ha sido reemplazada por la más larga',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'La cadena es la más larga',
                    'actual_chain': blockchain.chain}
    
    return jsonify(response), 200


# Crear wallet
@app.route('/create_wallet', methods=['POST'])

def create_wallet():
    json = request.get_json()
    # Entropia de aleatoriedad
    entropy = json.get('entropy')
    if entropy is None or entropy == '':
        return 'No hay entropía', 401
    
    pub_key, private_key = blockchain.create_wallet(entropy)
    response = {'Llave publica': pub_key,
                'Llave privada': private_key}

    # Guardar llaves en archivos separados
    public_key_data = {
    'public_key': pub_key
    }
    with open(f'public_key_{port}.json', 'w') as public_key_file:
        json.dump(public_key_data, public_key_file)

    private_key_data = {
        'private_key': private_key
    }
    with open(f'private_key_{port}.json', 'w') as private_key_file:
        json.dump(private_key_data, private_key_file)

    return jsonify(response), 201


# Correr APP
app.run(host='0.0.0.0', port=port)