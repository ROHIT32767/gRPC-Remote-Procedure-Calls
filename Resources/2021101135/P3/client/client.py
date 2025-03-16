import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P3/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from payment_pb2 import *
from payment_pb2_grpc import PaymentGatewayStub
import uuid
import time

class Client:
    def __init__(self):
        self.channel = grpc.secure_channel(
            'localhost:50053',
            grpc.ssl_channel_credentials(
                root_certificates=open('../../certificates/server_CA.crt', 'rb').read()
            ),
            options=[('grpc.ssl_target_name_override', 'localhost')]
        )

        self.stub = PaymentGatewayStub(self.channel)
        self.token = None

    def login(self, username, password):
        response = self.stub.Login(LoginRequest(username=username, password=password))
        self.token = response.token

    def send_payment(self, from_acc, to_acc, amount):
        max_retries = 3
        for attempt in range(max_retries):
            txn_id = str(uuid.uuid4())  
            try:
                response = self.stub.ProcessPayment(PaymentRequest(
                    transaction_id=txn_id, 
                    from_account=from_acc,
                    to_account=to_acc,
                    amount=amount
                ))
                return response.success
            except grpc.RpcError as e:
                print(f"Payment failed. Retrying... ({attempt+1}/{max_retries})")
                time.sleep(2)
        print("Payment failed after retries. Saving to offline queue...")
        return False

if __name__ == '__main__':
    client = Client()
    client.login("alice", "password123")
    success = client.send_payment("bank1-1234", "bank2-5678", 100.0)
    print("Success:", success)