import grpc
import uuid
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

class Client:
    def __init__(self):
        self.channel = grpc.secure_channel(
            'localhost:50053',
            grpc.ssl_channel_credentials(
                root_certificates=open('../certificates/ca.crt', 'rb').read()
            ),
            options=[('grpc.ssl_target_name_override', 'localhost')]
        )
        self.stub = payment_pb2_grpc.PaymentGatewayStub(self.channel)
        self.token = None

    def login(self, username, password):
        response = self.stub.Login(payment_pb2.LoginRequest(username=username, password=password))
        self.token = response.token

    def send_payment(self, from_acc, to_acc, amount):
        txn_id = str(uuid.uuid4())
        response = self.stub.ProcessPayment(payment_pb2.PaymentRequest(
            transaction_id=txn_id,
            from_account=from_acc,
            to_account=to_acc,
            amount=amount
        ))
        return response.success

if __name__ == '__main__':
    client = Client()
    client.login("alice", "password123")
    success = client.send_payment("bank1-1234", "bank2-5678", 100.0)
    print("Success:", success)