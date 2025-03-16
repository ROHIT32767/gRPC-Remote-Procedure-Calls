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
import argparse

class BankServer(payment_pb2_grpc.BankServiceServicer):
    def __init__(self, bank_address):
        self.prepared_transactions = set()
        self.transaction_data = {}
        self.bank_address = bank_address 
        self.bank_accounts = self.get_bank_data(bank_address)

    def PrepareTransaction(self, request, context):
        print(f"\n[Bank] PrepareTransaction received for transaction {request.payment_id}")
        if ((request.source_account.startswith(self.bank_address + "-")) and (request.source_account not in self.bank_accounts or self.bank_accounts[request.source_account] < request.payment_amount)) or ((request.destination_account.startswith(self.bank_address + "-")) and (request.destination_account not in self.bank_accounts)):
            return payment_pb2.TransactionVote(is_approved=False)
        self.prepared_transactions.add(request.payment_id)
        self.transaction_data[request.payment_id] = {}
        self.transaction_data[request.payment_id]["source_account"] = request.source_account  
        self.transaction_data[request.payment_id]["destination_account"] = request.destination_account  
        self.transaction_data[request.payment_id]["payment_amount"] = request.payment_amount  
        return payment_pb2.TransactionVote(is_approved=True)

    def CommitTransaction(self, request, context):
        print(f"\n[Bank] CommitTransaction received for transaction {request.payment_id}")
        if request.payment_id not in self.prepared_transactions:
            return payment_pb2.TransactionAck(is_successful=False)
        else:
            payment_id = request.payment_id
            sender_account, receiver_account, amount = (
                self.transaction_data[payment_id]["source_account"],
                self.transaction_data[payment_id]["destination_account"],
                self.transaction_data[payment_id]["payment_amount"],
            )
            if sender_account.startswith(f"{self.bank_address}-"):
                self.bank_accounts[sender_account] -= amount
            if receiver_account.startswith(f"{self.bank_address}-"):
                self.bank_accounts[receiver_account] += amount
            self.prepared_transactions.discard(payment_id)
            self.transaction_data.pop(payment_id, None)
            return payment_pb2.TransactionAck(is_successful=True)

    def AbortTransaction(self, request, context):
        print(f"\n[Bank] AbortTransaction received for transaction {request.payment_id}")
        if request.payment_id not in self.prepared_transactions:
            return payment_pb2.TransactionAck(is_successful=True)
        else:
            self.prepared_transactions.remove(request.payment_id)
            return payment_pb2.TransactionAck(is_successful=True)

    def FetchBankBalance(self, request, context):
        account_number = request.account_number
        print(f"\n[Bank] FetchBankBalance received for account {account_number}")
        if account_number not in self.bank_accounts:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.BankBalanceFetchResponse()
        else:
            print(f"Balance for account {account_number}: {self.bank_accounts[account_number]}")
            return payment_pb2.BankBalanceFetchResponse(account_balance=self.bank_accounts[account_number])

    def get_bank_data(self, bank_address):
        file_path = f"../utils/{bank_address}_server_accounts.json"
        with open(file_path, "r") as file:
            data = json.load(file)
        return data

def load_credentials(bank_address):
    key_path = f"../certificates/{bank_address}_server.key"
    cert_path = f"../certificates/{bank_address}_server.crt"
    ca_cert_path = "../certificates/server_CA.crt"

    with open(key_path, "rb") as key_file, open(cert_path, "rb") as cert_file, open(ca_cert_path, "rb") as ca_file:
        return grpc.ssl_server_credentials([(key_file.read(), cert_file.read())], root_certificates=ca_file.read())

def create_server(bank_address, port):
    credentials = load_credentials(bank_address)
    server = grpc.server(futures.ThreadPoolExecutor())
    payment_pb2_grpc.add_BankServiceServicer_to_server(BankServer(bank_address), server)
    server.add_secure_port(f"0.0.0.0:{port}", credentials)
    return server

def serve(bank_address, port):
    server = create_server(bank_address, port)
    print(f"{bank_address} Bank running on port {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a secure gRPC Bank Server.")
    parser.add_argument("--bank", type=str, required=True, help="Bank identifier (e.g., bank1, bank2).")
    parser.add_argument("--port", type=int, required=True, help="Port number for the bank server.")
    args = parser.parse_args()
    serve(args.bank, args.port)