import sys
import os
from concurrent import futures
import grpc
import json
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

class BankServer(payment_pb2_grpc.BankServicer):
    def __init__(self, bank_name):
        self.bank_name = bank_name
        self.accounts = self._load_accounts(bank_name)
        self.prepared_txns = set()
        self.txn_data = {}

    def Prepare(self, request, context):
        print(f"\n[Bank] Prepare received for txn {request.transaction_id}")
        if request.from_account.startswith(self.bank_name + "-"):
            if request.from_account not in self.accounts or self.accounts[request.from_account] < request.amount:
                return payment_pb2.Vote(vote=False)
        if request.to_account.startswith(self.bank_name + "-"):
            if request.to_account not in self.accounts:
                return payment_pb2.Vote(vote=False)
        self.prepared_txns.add(request.transaction_id)
        self.txn_data[request.transaction_id] = {
            "from_account": request.from_account,
            "to_account": request.to_account,
            "amount": request.amount
        }
        return payment_pb2.Vote(vote=True)

    def Commit(self, request, context):
        print(f"\n[Bank] Commit received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            txn_details = self.txn_data[request.transaction_id]
            sender_account = txn_details["from_account"]
            receiver_account = txn_details["to_account"]
            amount = txn_details["amount"]
            if sender_account.startswith(self.bank_name + "-"):
                self.accounts[sender_account] -= amount
            if receiver_account.startswith(self.bank_name + "-"):
                self.accounts[receiver_account] += amount
            self.prepared_txns.remove(request.transaction_id)
            del self.txn_data[request.transaction_id]
            return payment_pb2.Ack(success=True)
        return payment_pb2.Ack(success=False)

    def Abort(self, request, context):
        print(f"\n[Bank] Abort received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            self.prepared_txns.remove(request.transaction_id)
        return payment_pb2.Ack(success=True)

    def _load_accounts(self, bank_name):
        with open(f'../config/{bank_name}_accounts.json') as f:
            return json.load(f)

def serve(bank_name, port):
    credentials = grpc.ssl_server_credentials(
        [(open(f'../certificates/{bank_name}.key', 'rb').read(), 
         open(f'../certificates/{bank_name}.crt', 'rb').read())],
        root_certificates=open('../certificates/ca.crt', 'rb').read()
    )
    server = grpc.server(futures.ThreadPoolExecutor())
    payment_pb2_grpc.add_BankServicer_to_server(BankServer(bank_name), server)
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