import sys
import os
import grpc
from concurrent import futures
import json
import uuid
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

class GatewayServer(payment_pb2_grpc.PaymentGatewayServicer):
    def __init__(self):
        self.users = self.load_json("../utils/user_details.json")
        self.banks = self.load_json("../utils/bank_details.json")
        self.pending_transactions = {}
        self.processed_transactions = {}  

    def load_json(self,filepath):        
        with open(filepath, "r") as file:
            return json.load(file)
    def Login(self, request, context):    
        user = self.users.get(request.username)
        if not user or user["password"] != request.password:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            return payment_pb2.LoginResponse()
        return payment_pb2.LoginResponse(token=str(uuid.uuid4()))

    def ProcessPayment(self, request, context):
        trxn_id = request.transaction_id
        if request.transaction_id in self.processed_transactions:
            return payment_pb2.PaymentResponse(success=self.processed_transactions[request.transaction_id])

        self.pending_transactions[request.transaction_id] = False
        sender_bank, receiver_bank = self.banks[(request.from_account).split("-")[0]], self.banks[(request.to_account).split("-")[0]]

        if not self._prepare_transaction(trxn_id, sender_bank, receiver_bank, request):
            self._abort_transaction(trxn_id, sender_bank, receiver_bank)
            self.processed_transactions[trxn_id] = False
            return payment_pb2.PaymentResponse(success=False)

        self._commit_transaction(trxn_id, sender_bank, receiver_bank)
        self.processed_transactions[trxn_id] = True
        return payment_pb2.PaymentResponse(success=True)
        
    def _prepare_transaction(self, trxn_id, sender_bank, receiver_bank, request):
        """ Handles the prepare phase of 2PC. """
        for bank in [sender_bank, receiver_bank]:
            try:
                if not self._bank_stub(bank).Prepare(payment_pb2.PrepareRequest(
                    transaction_id=trxn_id,
                    from_account=request.from_account,
                    to_account=request.to_account,
                    amount=request.amount
                )).vote:
                    return False
            except Exception as e:
                print(f"Bank {bank['address']} failed: {e}")
                return False
        return True
    
    def _bank_stub(self, bank):
        """ Creates a secure gRPC stub for a bank. """
        creds = grpc.ssl_channel_credentials(root_certificates=open("../certificates/server_CA.crt", "rb").read())
        channel = grpc.secure_channel(bank["address"], creds)
        return payment_pb2_grpc.BankStub(channel)
    
    def _commit_transaction(self, trxn_id, sender_bank, receiver_bank):
        """ Commits a transaction after a successful prepare phase. """
        for bank in [sender_bank, receiver_bank]:
            self._bank_stub(bank).Commit(payment_pb2.CommitRequest(transaction_id=trxn_id))

    def _abort_transaction(self, trxn_id, sender_bank, receiver_bank):
        """ Aborts a transaction if prepare phase fails. """
        for bank in [sender_bank, receiver_bank]:
            self._bank_stub(bank).Abort(payment_pb2.AbortRequest(transaction_id=trxn_id))

    def GetBalance(self, request, context):
        user = self.users.get(request.username)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.GatewayBalanceResponse()
        
        accounts = user.get("accounts", [])
        balances = {}
        for account in accounts:
            bank_name = account.split("-")[0]
            bank = self.banks.get(bank_name)
            if bank:
                try:
                    creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/server_CA.crt', 'rb').read())
                    channel = grpc.secure_channel(bank["address"], creds)
                    stub = payment_pb2_grpc.BankStub(channel)
                    response = stub.GetBalance(payment_pb2.BankBalanceRequest(account_number=account))
                    balances[account] = response.balance
                except Exception as e:
                    print(f"Error fetching balance for account {account}: {str(e)}")
                    balances[account] = -1 
        return payment_pb2.GatewayBalanceResponse(accounts=balances)
    
    def Ping(self, request, context):
        return payment_pb2.PingResponse(message="Pong")

def create_server():
    """ Initializes and configures the gRPC server with secure credentials. """
    key_path = "../certificates/gateway_server.key"
    cert_path = "../certificates/gateway_server.crt"

    with open(key_path, "rb") as key_file, open(cert_path, "rb") as cert_file:
        server_credentials = grpc.ssl_server_credentials([(key_file.read(), cert_file.read())])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentGatewayServicer_to_server(GatewayServer(), server)
    server.add_secure_port("0.0.0.0:50053", server_credentials)
    return server

def serve():
    """ Starts the gRPC server and waits for termination. """
    server = create_server()
    print("Gateway running...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
