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

class Client:
    def __init__(self, port):
        self.port = port
        self.token = None
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
        """
        Recreate the gRPC channel and stub.
        """
        if self.channel:
            self.channel.close()  
        self.channel = grpc.secure_channel(
            f"localhost:{self.port}",
            grpc.ssl_channel_credentials(
                root_certificates=open('../certificates/ca.crt', 'rb').read()
            ),
            options=[('grpc.ssl_target_name_override', 'localhost')]
        )
        self.stub = payment_pb2_grpc.PaymentGatewayStub(self.channel)

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

    def _send_payment_impl(self, from_acc, to_acc, amount):
        """
        Internal implementation to send a payment.
        """
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

    def send_payment(self, from_acc, to_acc, amount):
        """
        Send a payment. If offline, queue the payment for later retry.
        """
        if self.offline:
            with self.lock:
                self.pending_payments.append((from_acc, to_acc, amount))
            logger.info(f"Payment queued (offline): From: {from_acc}, To: {to_acc}, Amount: {amount}")
            return False
        else:
            return self._send_payment_impl(from_acc, to_acc, amount)

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

    def _check_connectivity(self):
        """
        Periodically check connectivity to the gateway server using the Ping method.
        """
        while True:
            try:
                response = self.stub.Ping(payment_pb2.PingRequest(message="Ping"))
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
        """
        Periodically retry pending payments when the server is back online.
        """
        while True:
            if not self.offline and self.pending_payments:
                with self.lock:
                    payments_to_retry = self.pending_payments.copy()
                    self.pending_payments.clear()

                for payment in payments_to_retry:
                    logger.info(f"Retrying payment: From: {payment[0]}, To: {payment[1]}, Amount: {payment[2]}")
                    self._send_payment_impl(*payment)
            time.sleep(5)  # Check every 5 seconds


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