import grpc
import uuid
import logging
import os
import sys
import argparse
import threading
import time

protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

class ClientServer:
    def __init__(self, port):
        self.port = port
        self.auth_token = None
        self.pending_payments = []
        self.offline = False  
        self.lock = threading.Lock()  
        self.channel = None
        self.stub = None
        self._reconnect()
        self.connectivity_thread = threading.Thread(target=self._check_connectivity, daemon=True)
        self.connectivity_thread.start()
        self.retry_thread = threading.Thread(target=self._retry_pending_payments, daemon=True)
        self.retry_thread.start()

    def _reconnect(self):
        if self.channel:
            self.channel.close()  
        self.channel = grpc.secure_channel(
            f"localhost:{self.port}",
            grpc.ssl_channel_credentials(
                root_certificates=open('../certificates/server_CA.crt', 'rb').read()
            ),
            options=[('grpc.ssl_target_name_override', 'localhost')]
        )
        self.stub = payment_pb2_grpc.PaymentServiceStub(self.channel)

    def user_login(self, user_name, pass_word):
        try:
            response = self.stub.Authenticate(payment_pb2.AuthRequest(user_name=user_name, pass_word=pass_word))
            if not response.auth_token:
                logger.error(f"Authentication failed for user: {user_name}")
                return False
            else:
                self.auth_token = response.auth_token
                self.logged_user = user_name
                logger.info(f"Authentication successful for user: {user_name}")
                return True
        except grpc.RpcError as e:
            logger.error(f"Authentication error: {e.details()}")
            return False

    def _send_payment_impl(self, source_account, destination_account, payment_amount, payment_id):
        try:
            response = self.stub.ExecutePayment(payment_pb2.PaymentExecutionRequest(
                payment_id=payment_id,
                source_account=source_account,
                destination_account=destination_account,
                payment_amount=payment_amount
            ))
            if response.is_successful:
                logger.info(f"Payment successful: {payment_id}, From: {source_account}, To: {destination_account}, Amount: {payment_amount}")
            else:
                logger.error(f"Payment failed: {payment_id}, From: {source_account}, To: {destination_account}, Amount: {payment_amount}")
            return response.is_successful
        except grpc.RpcError as e:
            logger.error(f"Payment error: {e.details()}")
            return False

    def send_payment(self, source_account, destination_account, payment_amount):
        if not self.logged_user:
            logger.error("No user logged in. Please log in first.")
            return False

        if (not self.offline) and not self._validate_source_account(source_account):
            logger.error(f"Payment failed: Account {source_account} is not owned by the logged-in user.")
            return False
        
        payment_id = str(uuid.uuid4())  
        if self.offline:
            with self.lock:
                self.pending_payments.append((source_account, destination_account, payment_amount, payment_id))
            logger.info(f"Payment queued (offline): From: {source_account}, To: {destination_account}, Amount: {payment_amount}, Payment ID: {payment_id}")
            return False
        else:
            return self._send_payment_impl(source_account, destination_account, payment_amount, payment_id)

    def get_balance(self, user_name):
        if not self.logged_user:
            logger.error("No user logged in. Please log in first.")
            return
        if user_name != self.logged_user:
            logger.error(f"Permission denied. You can only view your own balances.")
            return
        try:
            response = self.stub.FetchBalance(payment_pb2.BalanceFetchRequest(user_name=user_name))
            if response.account_balances:
                logger.info(f"Balances for user {user_name}:")
                for account, balance in response.account_balances.items():
                    logger.info(f"Account: {account}, Balance: {balance}")
            else:
                logger.error(f"No accounts found for user: {user_name}")
        except grpc.RpcError as e:
            logger.error(f"Error fetching balance: {e.details()}")

    def _validate_source_account(self, source_account):
        try:
            response = self.stub.FetchBalance(payment_pb2.BalanceFetchRequest(user_name=self.logged_user))
            if source_account in response.account_balances:
                return True
            else:
                return False
        except grpc.RpcError as e:
            logger.error(f"Error validating source_account: {e.details()}")
            return False

    def _check_connectivity(self):
        while True:
            try:
                response = self.stub.HealthCheck(payment_pb2.HealthCheckRequest(health_message="Ping"))
                if self.offline:
                    logger.info("Reconnected to the gateway server.")
                self.offline = False
            except grpc.RpcError as e:
                if not self.offline:
                    logger.warning("Offline: Unable to connect to the gateway server.")
                self.offline = True
                self._reconnect()
            time.sleep(5)  

    def _retry_pending_payments(self):
        while True:
            if not self.offline and self.pending_payments:
                with self.lock:
                    payments_to_retry = self.pending_payments.copy()
                    self.pending_payments.clear()

                for payment in payments_to_retry:
                    source_account, destination_account, payment_amount, payment_id = payment
                    logger.info(f"Retrying payment: From: {source_account}, To: {destination_account}, Amount: {payment_amount}, Payment ID: {payment_id}")
                    self._send_payment_impl(source_account, destination_account, payment_amount, payment_id)
            time.sleep(5)

    def logout(self):
        self.auth_token = None
        self.logged_user = None

def run_tests(port=50053):
    client = ClientServer(port)
    client_user_name = ""
    while True:
        command = input("Enter command: ")
        if command == "login":
            if client_user_name:
                logger.error("User already logged in")
                continue
            user_name = input("Enter user name: ")
            pass_word = input("Enter password: ")
            client.user_login(user_name, pass_word)
            client_user_name = user_name
        elif command == "payment":
            source_account = input("Enter source account: ")
            destination_account = input("Enter destination account: ")
            payment_amount = float(input("Enter payment amount: "))
            client.send_payment(source_account, destination_account, payment_amount)
        elif command == "balance":
            client.get_balance(client_user_name)
        elif command == "logout":
            client.logout()
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