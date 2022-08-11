from audioop import add
from re import U
from time import time
import json
import hashlib
from urllib import response
from uuid import uuid4
from flask import Flask, jsonify, request
from numpy import block
import requests
from urllib.parse import urlparse

class Blockchain:
    
    def __init__(self):
        self.nuove_transazioni = []
        self.catena = []
        self.nodi = set()

        with open('blockchain.txt','r', encoding='utf-8-sig') as file:
            result = json.loads(file.read())
            for block in result:
                self.catena.append(block)

        with open('nodi.txt','r' , encoding='utf-8-sig') as file:
                result = json.loads(file.read())
                print(result)
                for node in result:
                    self.nodi.add(node)

        self.algoritmo_per_consenso()

    @property
    def _ultimo_blocco(self):
        return self.catena[-1]
 
    @staticmethod
    def _hash(blocco):
        """
        
        Crea un hash a 256bit di un blocco

        :param blocco: blocco da cui generare l'hash
        
        """

        block_string = json.dumps(blocco,sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


    def registrazione_nuovo_nodo(self,address):
        """     
        Aggiunge un nuovo nodo alla lista di nodi

        :param address: indirizzo nodo ad es. 'http://10.0.0.2:8080'
 
        """

        parsed_url = urlparse(address)

        if parsed_url.netloc:
            self.nodi.add(parsed_url.netloc)
        elif parsed_url.path: 
            self.nodi.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

        with open('nodi.txt','w' , encoding='utf-8-sig') as file:
            file.write(json.dumps(list(self.nodi)))



    def validazione_catena(self, blockchain_da_validare):

        """
            Determina se una blockchain è valida   

            :param blockchain_da_validare: la blockchain da validare
            :return True se Valido, False Altrimenti

        """
        
        ultimo_blocco = blockchain_da_validare[0]
        indice_corrente = 1

        while indice_corrente < len(blockchain_da_validare):
            
            blocco = blockchain_da_validare[indice_corrente]
             
            print(f'{ultimo_blocco}')
            print(f'{blocco}')
            print("\n------------\n")

            hash_ultimo_blocco = self._hash(ultimo_blocco)

            if blocco['hash_precedente'] != hash_ultimo_blocco:

                return False

            if not self.validazione_prova(ultimo_blocco['proof'],blocco['proof'],hash_ultimo_blocco):
                return False


            ultimo_blocco = blocco
            indice_corrente += 1 

        return True

    
    def algoritmo_per_consenso(self):
        """
        
        Risoluzione conflitti tramite verifica tra catene diverse
        Viene Sostituita la catena corrente con quella più lunga
        :return True per la blockchain sostituita, False se resta valida la blockchain attuale

        """

        vicini = self.nodi
        nuova_blockchain = None
        max_len = len(self.catena)

        temp_nodi = self.nodi.copy()

        # verifico la blockchain dei "vicini"


        for node in vicini:

            # check if node is alive
            url = f'http://{node}/chain'
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    lunghezza = response.json()['length']
                    catena = response.json()['chain']

                    if lunghezza > max_len and self.validazione_catena(catena):
                        max_len = lunghezza
                        nuova_blockchain = catena
    
            
                if nuova_blockchain:
                    self.catena = nuova_blockchain   

                    with open('blockchain.txt','w' , encoding='utf-8-sig') as file:
                        file.write(json.dumps(self.catena))

                    return True

            except:        
                temp_nodi.remove(node)
                continue


        if len(temp_nodi) < len(self.nodi):
            self.nodi = temp_nodi

            with open('nodi.txt','w' , encoding='utf-8-sig') as file:
                if len(self.nodi) > 0:
                     file.write(json.dumps(self.nodi))
                else:
                    file.write(json.dumps([]))
            
        return False

    def nuovo_blocco(self,proof,hash_precedente):
        """
        Crea un nuovo blocco nella blockchain

        :param proof: la "prova" fornita dall'algoritmo Proof of Work
        :param hash_precedente 
        :return un nuovo blocco        
        
        """

        block = {
            'index' : len(self.catena) + 1,
            'timestamp' : time() ,
            'transazioni': self.nuove_transazioni,
            'proof': proof,
            'hash_precedente': hash_precedente or self._hash(self.catena[-1])
        }

        self.nuove_transazioni = []
        
        self.catena.append(block)

        with open('blockchain.txt','w' , encoding='utf-8-sig') as file:
            file.write(json.dumps(self.catena))

        return block


    def nuova_transazione(self,id,canale,dati,timestamp):

        """
        Crea una nuova transazione che sarà inserita nel prossimo blocco minato

        :param id: identificatore di chi ha generato il messaggio
        :param canale: bluetooth/zigbee/wifi/ethernet
        :param dati: messaggio
        :param timestamp: data e ora dell'operazione
        :return indice del blocco che conterrà la transazione
        
        """

        self.nuove_transazioni.append({
            'id': id,
            'canale':canale,
            'dati' : dati,
            'timestamp' : timestamp
        })
        
        return self.ultimo_blocco['index'] + 1




    def proof_of_work(self,ultimo_blocco):
        """
        Algoritmo di PoW

        Trova un numero n tale che hash(p+n) finisca con 4 zeri
        dove n è la nuova prova e p la prova del blocco precedente

        :param ultimo_blocco: blocco precedente
        :return <int>
        """

        ultima_prova = ultimo_blocco['proof']
        ultimo_hash = self._hash(ultimo_blocco)

        prova = 0

        while self.validazione_prova(ultima_prova,prova,ultimo_hash) is False:
            prova += 1

        return prova



    @staticmethod
    def validazione_prova(ultima_prova,prova,ultimo_hash):

        """
        
        Valida la prova verificando che l'hash dell'ultima prova insieme a quella della 
        prova attuale e dell hash del blocco precedente termini con 6 zeri

        :param ultima_prova <int>
        :param prova <int> prova corrente
        :prarm ultimo_hash <str> hash del blocco precedente
        :return <bool> risultato della validazione
        
        """

        supposizione = f'{ultima_prova}-{prova}-{ultimo_hash}'.encode()
        hash_della_supposizione = hashlib.sha256(supposizione).hexdigest()
        return hash_della_supposizione[:4] == '0000'


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-','')

blockchain = Blockchain()

@app.route('/mine',methods=['GET'])
def mine():
    
    #Ottengo la prova dall'algoritmo PoW
    ultimo_blocco = blockchain.ultimo_blocco
    prova = blockchain.proof_of_work(ultimo_blocco)

    #Creo un nuovo blocco con la prova e l'hash del blocco precedente

    blockchain.nuova_transazione(
        id=node_identifier,
        canale='',
        dati='',
        timestamp=time()
    )

    hash_precedente = blockchain.hash(ultimo_blocco)
    blocco = blockchain.nuovo_blocco(prova,hash_precedente)
    
    response = {
        'message': 'Nuovo blocco minato',
        'index': blocco['index'],
        'transazioni': blocco['transazioni'],
        'proof': blocco['proof'],
        'hash_precedente': blocco['hash_precedente']
    }

    return jsonify(response), 200


@app.route('/transaction/new',methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['id','canale','dati','timestamp']
    if not all(k in values for k in required):
        msg = 'Missing values'
        missing = list (set(required) - set(values))

        for m in missing:
            msg += m
            if m != missing[-1]:
                msg += ', '
        return msg, 400 

    index = blockchain.nuova_transazione(**values)

    response = {'message': f'Transazione aggiunta alla catena con indice {index}'}
    return jsonify(response), 201


@app.route('/chain',methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.catena,
        'length': len(blockchain.catena)
    }
    return jsonify(response), 200


@app.route('/nodes/register',methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodo = values.get('node')
    if nodo is None:
        return "Error: Please supply a valid list of nodes", 400

    blockchain.registrazione_nuovo_nodo(nodo)

    nodi = list(blockchain.nodi)
    nodi_txt = ''
    for nodo in blockchain.nodi:
        nodi_txt += nodo
        if nodo != nodi[-1]:
            nodi_txt += ', '


    response = {
        'message': 'Nodo aggiunto',
        'nodi': nodi_txt
    }

    return jsonify(response), 201


@app.route('/nodes/resolve',methods=['GET'])
def consensus():
    replaced = blockchain.algoritmo_per_consenso()

    if replaced:
        response = {
            'message': 'La catena è stata sostituita',
            'chain': blockchain.catena
        }

    else:
        response = {
            'message': 'La catena è stata mantenuta',
            'chain': blockchain.catena
        }
    
    
    return jsonify(response), 200



if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='porta di ascolto')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0',port=port)
    