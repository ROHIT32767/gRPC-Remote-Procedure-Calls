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

class BankServer(payment_pb2_grpc.BankServicer):
    def __init__(self, bank_address):
        self.transactions_prepared = set()
        self.data_transaction = {}
        self.bank_address = bank_address 
        self.bank_accounts = self.get_bank_data(bank_address)

    def Prepare(self, request, context):
        print(f"\n[Bank] Prepare received for transaction {request.transaction_id}")
        if ((request.from_account.startswith(self.bank_address + "-")) and (request.from_account not in self.bank_accounts or self.bank_accounts[request.from_account] < request.amount)) or ((request.to_account.startswith(self.bank_address + "-")) and (request.to_account not in self.bank_accounts)):
            return payment_pb2.Vote(vote=False)
        self.transactions_prepared.add(request.transaction_id)
        self.data_transaction[request.transaction_id] = {}
        self.data_transaction[request.transaction_id]["from_account"] = request.from_account  
        self.data_transaction[request.transaction_id]["to_account"] = request.to_account  
        self.data_transaction[request.transaction_id]["amount"] = request.amount  
        return payment_pb2.Vote(vote=True)

    def Commit(self, request, context):
        print(f"\n[Bank] Commit received for transaction {request.transaction_id}")
        if request.transaction_id not in self.transactions_prepared:
            return payment_pb2.Ack(success=False)
        else:
            transaction_id = request.transaction_id
            sender_account, receiver_account, amount = (
                self.data_transaction[transaction_id]["from_account"],
                self.data_transaction[transaction_id]["to_account"],
                self.data_transaction[transaction_id]["amount"],
            )
            if sender_account.startswith(f"{self.bank_address}-"):
                self.bank_accounts[sender_account] -= amount
            if receiver_account.startswith(f"{self.bank_address}-"):
                self.bank_accounts[receiver_account] += amount
            self.transactions_prepared.discard(transaction_id)
            self.data_transaction.pop(transaction_id, None)
            return payment_pb2.Ack(success=True)

    def Abort(self, request, context):
        print(f"\n[Bank] Abort received for transaction {request.transaction_id}")
        if request.transaction_id not in self.transactions_prepared:
            return payment_pb2.Ack(success=True)
        else:
            self.transactions_prepared.remove(request.transaction_id)
            return payment_pb2.Ack(success=True)

    def GetBalance(self, request, context):
        account_number = request.account_number
        print(f"\n[Bank] GetBalance received for account {account_number}")
        if account_number not in self.bank_accounts:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.BankBalanceResponse()
        else:
            print(f"Balance for account {account_number}: {self.bank_accounts[account_number]}")
            return payment_pb2.BankBalanceResponse(balance=self.bank_accounts[account_number])

    def get_bank_data(self, bank_address):
        file_path = f"../utils/{bank_address}_server_accounts.json"
        with open(file_path, "r") as file:
            data = json.load(file)
        return data


def load_credentials(bank_address):
    """ Loads SSL credentials for the given bank. """
    key_path = f"../certificates/{bank_address}_server.key"
    cert_path = f"../certificates/{bank_address}_server.crt"
    ca_cert_path = "../certificates/server_CA.crt"

    with open(key_path, "rb") as key_file, open(cert_path, "rb") as cert_file, open(ca_cert_path, "rb") as ca_file:
        return grpc.ssl_server_credentials([(key_file.read(), cert_file.read())], root_certificates=ca_file.read())

def create_server(bank_address, port):
    """ Initializes and configures the gRPC server for a specific bank. """
    credentials = load_credentials(bank_address)
    server = grpc.server(futures.ThreadPoolExecutor())
    payment_pb2_grpc.add_BankServicer_to_server(BankServer(bank_address), server)
    server.add_secure_port(f"0.0.0.0:{port}", credentials)
    return server

def serve(bank_address, port):
    """ Starts the gRPC bank server and waits for termination. """
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