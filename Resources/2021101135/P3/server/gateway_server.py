import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P3/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from concurrent import futures
from payment_pb2 import *
from payment_pb2_grpc import *
import json
import uuid
import time
from threading import Lock

class GatewayServer(PaymentGatewayServicer):
    def __init__(self):
        # Load users and banks from utils files
        with open('../utils/users.json') as f:
            self.users = json.load(f) 
        with open('../utils/banks.json') as f:
            self.banks = json.load(f) 
        self.pending_txns = {}  # Track pending transactions for idempotency
        self.txn_details = {} 
        self.txn_lock = Lock()  # Thread-safe access


    def Login(self, request, context):
        user = self.users.get(request.username)
        if user and user["password"] == request.password:
            return LoginResponse(token=str(uuid.uuid4()))
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        return LoginResponse()

    def ProcessPayment(self, request, context):
         # Idempotency check with lock
        with self.txn_lock:
            if request.transaction_id in self.pending_txns:
                return PaymentResponse(success=self.pending_txns[request.transaction_id])
            
            # Mark as "in progress" to block duplicates
            self.pending_txns[request.transaction_id] = False
        
        self.txn_details[request.transaction_id] = (
        request.from_account, 
        request.to_account, 
        request.amount
    )
        
        # Start 2PC
        sender_bank = self._get_bank(request.from_account)
        receiver_bank = self._get_bank(request.to_account)
        
        # Phase 1: Prepare
        prepare_ok = True
        for bank in [sender_bank, receiver_bank]:
            try:
                creds = grpc.ssl_channel_credentials(
                root_certificates=open('../../certificates/server_CA.crt', 'rb').read() )
                channel = grpc.secure_channel(bank["address"], creds)
                stub = BankStub(channel)
                response = stub.Prepare(PrepareRequest(
                    transaction_id=request.transaction_id,
                    from_account=request.from_account,
                    to_account=request.to_account,
                    amount=request.amount
                ))
                print(f"Bank {bank['address']} voted: {response.vote}")
                if not response.vote:
                    prepare_ok = False

            except:
                print(f"Bank {bank['address']} failed: {str(e)}")
                prepare_ok = False
        
        # Phase 2: Commit/Abort
        if prepare_ok:
            for bank in [sender_bank, receiver_bank]:
                creds = grpc.ssl_channel_credentials(
                root_certificates=open('../../certificates/server_CA.crt', 'rb').read() )
                channel = grpc.secure_channel(bank["address"], creds)
                stub = BankStub(channel)  
                stub.Commit(CommitRequest(transaction_id=request.transaction_id))
            with self.txn_lock:
                self.pending_txns[request.transaction_id] = True
            return PaymentResponse(success=True)
        else:
            for bank in [sender_bank, receiver_bank]:
                creds = grpc.ssl_channel_credentials(
                root_certificates=open('../../certificates/server_CA.crt', 'rb').read() )
                channel = grpc.secure_channel(bank["address"], creds)
                stub = BankStub(channel)
                stub.Abort(AbortRequest(transaction_id=request.transaction_id))
            with self.txn_lock:
                self.pending_txns[request.transaction_id] = False
            return PaymentResponse(success=False)

    def _get_bank(self, account_number):
        bank_name = account_number.split("-")[0]  # account format: "bank1-1234"
        return self.banks[bank_name]

def serve():
    # Load SSL credentials
    server_credentials = grpc.ssl_server_credentials(
        [(open('../../certificates/gateway_server.key', 'rb').read(), open('../../certificates/gateway_server.crt', 'rb').read())]
    )
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_PaymentGatewayServicer_to_server(GatewayServer(), server)
    server.add_secure_port('0.0.0.0:50053', server_credentials)
    server.start()
    print("Gateway running...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()