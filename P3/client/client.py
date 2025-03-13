import grpc
import uuid
import logging
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

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
            response = self.stub.GetBalance(payment_pb2.BalanceRequest(username=username))
            if response.accounts:
                logger.info(f"Balances for user {username}:")
                for account, balance in response.accounts.items():
                    logger.info(f"Account: {account}, Balance: {balance}")
            else:
                logger.error(f"No accounts found for user: {username}")
        except grpc.RpcError as e:
            logger.error(f"Error fetching balance: {e.details()}")

# Test cases
def run_tests():
    client = Client()

    # Test 1: Valid login
    logger.info("Running Test 1: Valid login")
    if client.login("alice", "password123"):
        logger.info("Test 1 passed: Login successful")
    else:
        logger.error("Test 1 failed: Login unsuccessful")

    # Test 2: Invalid login
    logger.info("Running Test 2: Invalid login")
    if not client.login("alice", "wrongpassword"):
        logger.info("Test 2 passed: Invalid login handled correctly")
    else:
        logger.error("Test 2 failed: Invalid login not handled correctly")

    # Test 3: Get Balance
    logger.info("Running Test 3: Get Balance")
    client.get_balance("alice")


    # Test 4: Valid payment
    logger.info("Running Test 4: Valid payment")
    if client.send_payment("bank1-1234", "bank2-5678", 100.0):
        logger.info("Test 4 passed: Payment successful")
    else:
        logger.error("Test 4 failed: Payment unsuccessful")

    # Test 5: Get Balance after payment
    logger.info("Running Test 5: Get Balance after payment")
    client.get_balance("alice")

    # Test 6: Insufficient funds
    logger.info("Running Test 6: Insufficient funds")
    if not client.send_payment("bank1-1234", "bank2-5678", 10000.0):  # Assuming insufficient balance
        logger.info("Test 6 passed: Insufficient funds handled correctly")
    else:
        logger.error("Test 6 failed: Insufficient funds not handled correctly")

    # Test 5: Invalid account
    logger.info("Running Test 7: Invalid account")
    if not client.send_payment("bank1-9999", "bank2-5678", 100.0):  # Assuming invalid account
        logger.info("Test 7 passed: Invalid account handled correctly")
    else:
        logger.error("Test 7 failed: Invalid account not handled correctly")

if __name__ == '__main__':
    run_tests()