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
        with open('../config/users.json') as f:
            self.users = json.load(f)
        with open('../config/banks.json') as f:
            self.banks = json.load(f)
        self.pending_txns = {}

    def Login(self, request, context):
        user = self.users.get(request.username)
        if user and user["password"] == request.password:
            return payment_pb2.LoginResponse(token=str(uuid.uuid4()))
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        return payment_pb2.LoginResponse()

    def ProcessPayment(self, request, context):
        if request.transaction_id in self.pending_txns:
            return payment_pb2.PaymentResponse(success=self.pending_txns[request.transaction_id])
        self.pending_txns[request.transaction_id] = False
        sender_bank = self._get_bank(request.from_account)
        receiver_bank = self._get_bank(request.to_account)
        prepare_ok = True
        for bank in [sender_bank, receiver_bank]:
            try:
                creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/ca.crt', 'rb').read())
                channel = grpc.secure_channel(bank["address"], creds)
                stub = payment_pb2_grpc.BankStub(channel)
                response = stub.Prepare(payment_pb2.PrepareRequest(
                    transaction_id=request.transaction_id,
                    from_account=request.from_account,
                    to_account=request.to_account,
                    amount=request.amount
                ))
                if not response.vote:
                    prepare_ok = False
            except Exception as e:
                print(f"Bank {bank['address']} failed: {str(e)}")
                prepare_ok = False
        if prepare_ok:
            for bank in [sender_bank, receiver_bank]:
                creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/ca.crt', 'rb').read())
                channel = grpc.secure_channel(bank["address"], creds)
                stub = payment_pb2_grpc.BankStub(channel)
                stub.Commit(payment_pb2.CommitRequest(transaction_id=request.transaction_id))
            self.pending_txns[request.transaction_id] = True
            return payment_pb2.PaymentResponse(success=True)
        else:
            for bank in [sender_bank, receiver_bank]:
                creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/ca.crt', 'rb').read())
                channel = grpc.secure_channel(bank["address"], creds)
                stub = payment_pb2_grpc.BankStub(channel)
                stub.Abort(payment_pb2.AbortRequest(transaction_id=request.transaction_id))
            self.pending_txns[request.transaction_id] = False
            return payment_pb2.PaymentResponse(success=False)

    def GetBalance(self, request, context):
        user = self.users.get(request.username)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.BalanceResponse()
        
        accounts = user.get("accounts", [])
        balances = {}
        for account in accounts:
            bank_name = account.split("-")[0]
            bank = self.banks.get(bank_name)
            if bank:
                try:
                    creds = grpc.ssl_channel_credentials(root_certificates=open('../certificates/ca.crt', 'rb').read())
                    channel = grpc.secure_channel(bank["address"], creds)
                    stub = payment_pb2_grpc.BankStub(channel)
                    # Call the GetBalance method on the bank server
                    response = stub.GetBalance(payment_pb2.BalanceRequest(account_number=account))
                    balances[account] = response.balance
                except Exception as e:
                    print(f"Error fetching balance for account {account}: {str(e)}")
                    balances[account] = -1  # Indicate error
        return payment_pb2.BalanceResponse(accounts=balances)

    def _get_bank(self, account_number):
        bank_name = account_number.split("-")[0]
        return self.banks[bank_name]

def serve():
    server_credentials = grpc.ssl_server_credentials(
        [(open('../certificates/gateway.key', 'rb').read(), open('../certificates/gateway.crt', 'rb').read())]
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentGatewayServicer_to_server(GatewayServer(), server)
    server.add_secure_port('0.0.0.0:50053', server_credentials)
    server.start()
    print("Gateway running...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()