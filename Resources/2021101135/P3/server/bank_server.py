import sys
import os
from concurrent import futures

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P3/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from payment_pb2 import *
from payment_pb2_grpc import *
import json

class BankServer(BankServicer):
    def __init__(self, bank_name):
        self.bank_name = bank_name
        self.accounts = self._load_accounts(bank_name)
        self.prepared_txns = set()
        self.txn_data = {}

    def Prepare(self, request, context):
        print(f"\n[Bank] Prepare received for txn {request.transaction_id}")
        print(f"From: {request.from_account}, To: {request.to_account}, Amount: {request.amount}")

        # Check sender account (only if sender belongs to this bank)
        if request.from_account.startswith(self.bank_name + "-"):
            if request.from_account not in self.accounts:
                print(f"Sender account {request.from_account} not found")
                return Vote(vote=False)
            if self.accounts[request.from_account] < request.amount:
                print(f"Insufficient balance in {request.from_account}")
                return Vote(vote=False)

        # Check receiver account (only if receiver belongs to this bank)
        if request.to_account.startswith(self.bank_name + "-"):
            if request.to_account not in self.accounts:
                print(f"Receiver account {request.to_account} not found")
                return Vote(vote=False)

        self.prepared_txns.add(request.transaction_id)
        self.txn_data[request.transaction_id] = {
            "from_account": request.from_account,
            "to_account": request.to_account,
            "amount": request.amount
        }
        return Vote(vote=True)

    def Commit(self, request, context):
        print(f"\n[Bank] Commit received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            try:
                # Get transaction details from stored data
                txn_details = self.txn_data[request.transaction_id]
                sender_account = txn_details["from_account"]
                receiver_account = txn_details["to_account"]
                amount = txn_details["amount"]
                
                print(f"Deducting {amount} from {sender_account}")
                
                # Deduct from sender account (if belongs to this bank)
                if sender_account.startswith(self.bank_name + "-"):
                    self.accounts[sender_account] -= amount
                    print(f"New balance for {sender_account}: {self.accounts[sender_account]}")
                
                # Add to receiver account (if belongs to this bank)
                if receiver_account.startswith(self.bank_name + "-"):
                    self.accounts[receiver_account] += amount
                    print(f"New balance for {receiver_account}: {self.accounts[receiver_account]}")
                
                # Cleanup
                self.prepared_txns.remove(request.transaction_id)
                del self.txn_data[request.transaction_id]
                
                return Ack(success=True)
                
            except KeyError as e:
                print(f"Transaction data not found: {str(e)}")
                return Ack(success=False)
        
        print("Transaction not in prepared state")
        return Ack(success=False)

    def Abort(self, request, context):
        print(f"\n[Bank] Abort received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            self.prepared_txns.remove(request.transaction_id)
        return Ack(success=True)


    def _load_accounts(self, bank_name):
        with open(f'../utils/{bank_name}_accounts.json') as f:
            return json.load(f)

def serve(bank_name, port):
    credentials = grpc.ssl_server_credentials(
        [(open(f'../../certificates/{bank_name}.key', 'rb').read(), 
          open(f'../../certificates/{bank_name}.crt', 'rb').read())],
        root_certificates=open('../../certificates/ca.crt', 'rb').read()
    )
    server = grpc.server(futures.ThreadPoolExecutor())
    add_BankServicer_to_server(BankServer(bank_name), server)
    server.add_secure_port(f'0.0.0.0:{port}', credentials)
    server.start()
    print(f"{bank_name} Bank running...")
    server.wait_for_termination()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bank', type=str, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    serve(args.bank, args.port)