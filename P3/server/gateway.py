import sys
import os
import grpc
from concurrent import futures
import json
import uuid
import os
import sys
import threading
import time
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import argparse
import payment_pb2, payment_pb2_grpc

class GatewayServer(payment_pb2_grpc.PaymentServiceServicer):
    def __init__(self,transaction_timeout=30):
        self.users = self.load_json("../utils/user_details.json")
        self.banks = self.load_json("../utils/bank_details.json")
        self.pending_transactions = {}
        self.processed_transactions = {}  
        self.transaction_timeout = transaction_timeout

    def load_json(self,filepath):        
        with open(filepath, "r") as file:
            return json.load(file)
    def Authenticate(self, request, context):    
        user = self.users.get(request.user_name)
        if not user or user["password"] != request.pass_word:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            return payment_pb2.AuthResponse()
        return payment_pb2.AuthResponse(auth_token=str(uuid.uuid4()))

    def ExecutePayment(self, request, context):
        payment_id = request.payment_id
        if request.payment_id in self.processed_transactions:
            return payment_pb2.PaymentExecutionResponse(is_successful=self.processed_transactions[request.payment_id])

        self.pending_transactions[request.payment_id] = False
        sender_bank, receiver_bank = self.banks[(request.source_account).split("-")[0]], self.banks[(request.destination_account).split("-")[0]]

        # Start a thread to monitor the transaction timeout
        timeout_thread = threading.Thread(target=self._monitor_transaction_timeout, args=(payment_id, sender_bank, receiver_bank))
        timeout_thread.start()

        if not self._prepare_transaction(payment_id, sender_bank, receiver_bank, request):
            self._abort_transaction(payment_id, sender_bank, receiver_bank)
            self.processed_transactions[payment_id] = False
            return payment_pb2.PaymentExecutionResponse(is_successful=False)

        self._commit_transaction(payment_id, sender_bank, receiver_bank)
        self.processed_transactions[payment_id] = True
        return payment_pb2.PaymentExecutionResponse(is_successful=True)
        
    def _prepare_transaction(self, payment_id, sender_bank, receiver_bank, request):
        for bank in [sender_bank, receiver_bank]:
            try:
                if not self._bank_stub(bank).PrepareTransaction(payment_pb2.TransactionPrepareRequest(
                    payment_id=payment_id,
                    source_account=request.source_account,
                    destination_account=request.destination_account,
                    payment_amount=request.payment_amount
                )).is_approved:
                    return False
            except Exception as e:
                print(f"Bank {bank['address']} failed: {e}")
                return False
        return True
    
    def _bank_stub(self, bank):
        creds = grpc.ssl_channel_credentials(root_certificates=open("../certificates/server_CA.crt", "rb").read())
        channel = grpc.secure_channel(bank["address"], creds)
        return payment_pb2_grpc.BankServiceStub(channel)
    
    def _commit_transaction(self, payment_id, sender_bank, receiver_bank):
        for bank in [sender_bank, receiver_bank]:
            self._bank_stub(bank).CommitTransaction(payment_pb2.TransactionCommitRequest(payment_id=payment_id))

    def _abort_transaction(self, payment_id, sender_bank, receiver_bank):
        for bank in [sender_bank, receiver_bank]:
            self._bank_stub(bank).AbortTransaction(payment_pb2.TransactionAbortRequest(payment_id=payment_id))

    def _monitor_transaction_timeout(self, payment_id, sender_bank, receiver_bank):
        start_time = time.time()
        while time.time() - start_time < self.transaction_timeout:
            if payment_id in self.processed_transactions:
                return
            time.sleep(1)  
        if payment_id not in self.processed_transactions:
            print(f"Transaction {payment_id} timed out. Aborting...")
            self._abort_transaction(payment_id, sender_bank, receiver_bank)
            self.processed_transactions[payment_id] = False

    def FetchBalance(self, request, context):
        user = self.users.get(request.user_name)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.BalanceFetchResponse()
        
        accounts = user.get("accounts", [])
        balances = {}
        for account in accounts:
            bank_name = account.split("-")[0]
            bank = self.banks.get(bank_name)
            if bank:
                try:
                    creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/server_CA.crt', 'rb').read())
                    channel = grpc.secure_channel(bank["address"], creds)
                    stub = payment_pb2_grpc.BankServiceStub(channel)
                    response = stub.FetchBankBalance(payment_pb2.BankBalanceFetchRequest(account_number=account))
                    balances[account] = response.account_balance
                except Exception as e:
                    print(f"Error fetching balance for account {account}: {str(e)}")
                    balances[account] = -1 
        return payment_pb2.BalanceFetchResponse(account_balances=balances)
    
    def HealthCheck(self, request, context):
        return payment_pb2.HealthCheckResponse(health_response="Pong")

def create_server(transaction_timeout):
    key_path = "../certificates/gateway_server.key"
    cert_path = "../certificates/gateway_server.crt"

    with open(key_path, "rb") as key_file, open(cert_path, "rb") as cert_file:
        server_credentials = grpc.ssl_server_credentials([(key_file.read(), cert_file.read())])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(GatewayServer(transaction_timeout), server)
    server.add_secure_port("0.0.0.0:50053", server_credentials)
    return server

def serve(transaction_timeout=30):  
    server = create_server(transaction_timeout)
    print("Gateway running...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the Payment Gateway Server.")
    parser.add_argument("--timeout", type=int, default=30, help="Transaction timeout in seconds (default: 30)")
    args = parser.parse_args()
    serve(transaction_timeout=args.timeout)