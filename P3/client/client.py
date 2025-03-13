import grpc
import uuid
import logging
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc
import argparse

class Client:
    def __init__(self,port):
        self.channel = grpc.secure_channel(
            "localhost:" + str(port),
            grpc.ssl_channel_credentials(
                root_certificates=open('../certificates/ca.crt', 'rb').read()
            ),
            options=[('grpc.ssl_target_name_override', 'localhost')]
        )
        self.stub = payment_pb2_grpc.PaymentGatewayStub(self.channel)
        self.token = None

    def login(self, username, password):
        try:
            response = self.stub.Login(payment_pb2.LoginRequest(username=username, password=password))
            if response.token:
                self.token = response.token
                logger.info(f"Login successful for user: {username}")
                return True
            else:
                logger.error(f"Login failed for user: {username}")
                return False
        except grpc.RpcError as e:
            logger.error(f"Login error: {e.details()}")
            return False

    def send_payment(self, from_acc, to_acc, amount):
        txn_id = str(uuid.uuid4())
        try:
            response = self.stub.ProcessPayment(payment_pb2.PaymentRequest(
                transaction_id=txn_id,
                from_account=from_acc,
                to_account=to_acc,
                amount=amount
            ))
            if response.success:
                logger.info(f"Payment successful: {txn_id}, From: {from_acc}, To: {to_acc}, Amount: {amount}")
            else:
                logger.error(f"Payment failed: {txn_id}, From: {from_acc}, To: {to_acc}, Amount: {amount}")
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Payment error: {e.details()}")
            return False

    def get_balance(self, username):
        try:
            # Call the GetBalance method on the gateway server
            response = self.stub.GetBalance(payment_pb2.GatewayBalanceRequest(username=username))
            if response.accounts:
                logger.info(f"Balances for user {username}:")
                for account, balance in response.accounts.items():
                    logger.info(f"Account: {account}, Balance: {balance}")
            else:
                logger.error(f"No accounts found for user: {username}")
        except grpc.RpcError as e:
            logger.error(f"Error fetching balance: {e.details()}")

def run_tests(port=50053):
    client = Client(port)
    client_user_name = ""
    while True:
        command = input("Enter command: ")
        if command == "login":
            if client_user_name:
                logger.error("User already logged in")
                continue
            username = input("Enter username: ")
            password = input("Enter password: ")
            client.login(username, password)
            client_user_name = username
        elif command == "payment":
            from_acc = input("Enter from account: ")
            to_acc = input("Enter to account: ")
            amount = float(input("Enter amount: "))
            client.send_payment(from_acc, to_acc, amount)
        elif command == "balance":
            client.get_balance(client_user_name)
        elif command == "logout":
            client.token = None
            logger.info("Logged out")
            client_user_name = ""
        elif command == "exit":
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Payment Client')
    parser.add_argument('--port', type=int, required=True, help='Port number to connect to')
    args = parser.parse_args()
    log_file_name = f"client_{args.port}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_name),  
            logging.StreamHandler()  
        ]
    )
    logger = logging.getLogger(__name__)
    run_tests(port=args.port)