Write code in python to extend the given code to implement the following functionalites:

Functionality - 1 : Idempotent Payments 
When you’re designing some systems, changes are inherently idempotent e.g. updating user information
repeatedly yields the same result (think of any PUT request). In other cases however, this might not be
true – consider adding courses in registration. If you do it twice, there will either be an error or you will
end up with two versions of the course... unless you set up idempotent additions.
That is what you have to do here, and it will be a much more critical feature than for a course registration
system. You have to make sure that if the same transaction gets retried (perhaps the earlier one failed to
return in the specified timeout and the server resent the transaction), the application of these changes is
idempotent. So if the transaction is of Rs. 100, the system shouldn’t accidentally deduct Rs. 200 from the
sender’s account.
There are various ways of doing this. The simplest would be to compare timestamps – if equal, consider
them the same payment. And this is not allowed in this assignment, because while the system you are
building is small, there’s no reason to lock that in and not make it scaleable.

See the stripe blog for one way of ensuring payments that occur exactly once. 
To summarize, the requirements are:
•Ensure payments are idempotent—retrying a transaction should not cause multiple deductions.
•Simple timestamp-based deduplication is not allowed.
•Implement a scalable approach (refer to the blog)

```Stripe blog
Making liberal use of idempotency
The easiest way to address inconsistencies in distributed state caused by failures is to implement server endpoints so that they’re idempotent, which means that they can be called any number of times while guaranteeing that side effects only occur once.

When a client sees any kind of error, it can ensure the convergence of its own state with the server’s by retrying, and can continue to retry until it verifiably succeeds. This fully addresses the problem of an ambiguous failure because the client knows that it can safely handle any failure using one simple technique.

As an example, consider the API call for a hypothetical DNS provider that enables us to add subdomains via an HTTP request:

curl https://example.com/domains/stripe.com/records/s3.stripe.com \
   -X PUT \
   -d type=CNAME \
   -d value="stripe.s3.amazonaws.com" \
   -d ttl=3600
All the information needed to create a record is included in the call, and it’s perfectly safe for a client to invoke it any number of times. If the server receives a call that it realizes is a duplicate because the domain already exists, it simply ignores the request and responds with a successful status code.

According to HTTP semantics, the PUT and DELETE verbs are idempotent, and the PUT verb in particular signifies that a target resource should be created or replaced entirely with the contents of a request’s payload (in modern RESTful parlance, a modification would be represented by a PATCH).

Guaranteeing “exactly once” semantics
While the inherently idempotent HTTP semantics around PUT and DELETE are a good fit for many API calls, what if we have an operation that needs to be invoked exactly once and no more? An example might be if we were designing an API endpoint to charge a customer money; accidentally calling it twice would lead to the customer being double-charged, which is very bad.

This is where idempotency keys come into play. When performing a request, a client generates a unique ID to identify just that operation and sends it up to the server along with the normal payload. The server receives the ID and correlates it with the state of the request on its end. If the client notices a failure, it retries the request with the same ID, and from there it’s up to the server to figure out what to do with it.

If we consider our sample network failure cases from above:

On retrying a connection failure, on the second request the server will see the ID for the first time, and process it normally.
On a failure midway through an operation, the server picks up the work and carries it through. The exact behavior is heavily dependent on implementation, but if the previous operation was successfully rolled back by way of an ACID database, it’ll be safe to retry it wholesale. Otherwise, state is recovered and the call is continued.
On a response failure (i.e. the operation executed successfully, but the client couldn’t get the result), the server simply replies with a cached result of the successful operation.
The Stripe API implements idempotency keys on mutating endpoints (i.e. anything under POST in our case) by allowing clients to pass a unique value in with the special Idempotency-Key header, which allows a client to guarantee the safety of distributed operations:

curl https://api.stripe.com/v1/charges \
   -u sk_test_BQokikJOvBiI2HlWgH4olfQ2: \
   -H "Idempotency-Key: AGJ6FJMkGQIpHUTX" \
   -d amount=2000 \
   -d currency=usd \
   -d description="Charge for Brandur" \
   -d customer=cus_A8Z5MHwQS7jUmZ
If the above Stripe request fails due to a network connection error, you can safely retry it with the same idempotency key, and the customer is charged only once
```

Functionality - 2 : Offline Payments 
Say the client initiates a payment, but the payment gateway is down (or you’re offline) and you’re unable to send the request i.e. it fails.
To handle such situations, the client must maintain a queue of payments when it’s offline and (re)send the pending ones when the connection comes back up. (Tip: Does the idempotent assumption simplify anything for you in this feature?)
Requirements
•Clients must queue payments when they are offline.
•Pending payments should be automatically resent once connectivity is restored (You may choose to
keep a periodic check, but the period in that case must be appropriately chosen).
•Only handle cases where the client is offline, not the payment gateway.
•Notify clients about the success/failure of processed payments – offline or otherwise.


bank_server.py
```python
import sys
import os
from concurrent import futures
import grpc
import json
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import payment_pb2, payment_pb2_grpc

class BankServer(payment_pb2_grpc.BankServicer):
    def __init__(self, bank_name):
        self.bank_name = bank_name
        self.accounts = self._load_accounts(bank_name)
        self.prepared_txns = set()
        self.txn_data = {}

    def Prepare(self, request, context):
        print(f"\n[Bank] Prepare received for txn {request.transaction_id}")
        if request.from_account.startswith(self.bank_name + "-"):
            if request.from_account not in self.accounts or self.accounts[request.from_account] < request.amount:
                return payment_pb2.Vote(vote=False)
        if request.to_account.startswith(self.bank_name + "-"):
            if request.to_account not in self.accounts:
                return payment_pb2.Vote(vote=False)
        self.prepared_txns.add(request.transaction_id)
        self.txn_data[request.transaction_id] = {
            "from_account": request.from_account,
            "to_account": request.to_account,
            "amount": request.amount
        }
        return payment_pb2.Vote(vote=True)

    def Commit(self, request, context):
        print(f"\n[Bank] Commit received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            txn_details = self.txn_data[request.transaction_id]
            sender_account = txn_details["from_account"]
            receiver_account = txn_details["to_account"]
            amount = txn_details["amount"]
            if sender_account.startswith(self.bank_name + "-"):
                self.accounts[sender_account] -= amount
            if receiver_account.startswith(self.bank_name + "-"):
                self.accounts[receiver_account] += amount
            self.prepared_txns.remove(request.transaction_id)
            del self.txn_data[request.transaction_id]
            return payment_pb2.Ack(success=True)
        return payment_pb2.Ack(success=False)

    def Abort(self, request, context):
        print(f"\n[Bank] Abort received for txn {request.transaction_id}")
        if request.transaction_id in self.prepared_txns:
            self.prepared_txns.remove(request.transaction_id)
        return payment_pb2.Ack(success=True)

    def GetBalance(self, request, context):
        account_number = request.account_number
        print(f"\n[Bank] GetBalance received for account {account_number}")
        if account_number in self.accounts:
            print(f"Balance for account {account_number}: {self.accounts[account_number]}")
            return payment_pb2.BankBalanceResponse(balance=self.accounts[account_number])
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_pb2.BankBalanceResponse()

    def _load_accounts(self, bank_name):
        with open(f'../config/{bank_name}_accounts.json') as f:
            return json.load(f)

def serve(bank_name, port):
    credentials = grpc.ssl_server_credentials(
        [(open(f'../certificates/{bank_name}.key', 'rb').read(), 
         open(f'../certificates/{bank_name}.crt', 'rb').read())],
        root_certificates=open('../certificates/ca.crt', 'rb').read()
    )
    server = grpc.server(futures.ThreadPoolExecutor())
    payment_pb2_grpc.add_BankServicer_to_server(BankServer(bank_name), server)
    server.add_secure_port(f'0.0.0.0:{port}', credentials)
    server.start()
    print(f"{bank_name} Bank running...")
    server.wait_for_termination()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bank', type=str, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    serve(args.bank, args.port)
```

gateway_server.py
```python
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
            return payment_pb2.GatewayBalanceResponse()
        
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
                    # Use BankBalanceRequest
                    response = stub.GetBalance(payment_pb2.BankBalanceRequest(account_number=account))
                    balances[account] = response.balance
                except Exception as e:
                    print(f"Error fetching balance for account {account}: {str(e)}")
                    balances[account] = -1  # Indicate error
        return payment_pb2.GatewayBalanceResponse(accounts=balances)

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
```

client.py
```python
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
```

payment.proto
```proto
syntax = "proto3";

service PaymentGateway {
  rpc Login(LoginRequest) returns (LoginResponse);     // Authentication
  rpc ProcessPayment(PaymentRequest) returns (PaymentResponse); // 2PC payment
  rpc GetBalance(GatewayBalanceRequest) returns (GatewayBalanceResponse); // For user balance
}

service Bank {
  rpc Prepare(PrepareRequest) returns (Vote);         // 2PC Phase 1
  rpc Commit(CommitRequest) returns (Ack);            // 2PC Phase 2
  rpc Abort(AbortRequest) returns (Ack);
  rpc GetBalance(BankBalanceRequest) returns (BankBalanceResponse); // For account balance
}

// ---------- Messages ----------
message LoginRequest {
  string username = 1;
  string password = 2;
}

message LoginResponse {
  string token = 1;
}

message PaymentRequest {
  string transaction_id = 1;
  string from_account = 2;
  string to_account = 3;
  double amount = 4;
}

message PaymentResponse {
  bool success = 1;
}

message PrepareRequest {
  string transaction_id = 1;
  string from_account = 2;
  string to_account = 3;
  double amount = 4;
}

message Vote {
  bool vote = 1;
}

message CommitRequest {
  string transaction_id = 1;
}

message AbortRequest {
  string transaction_id = 1;
}

message Ack {
  bool success = 1;
}

// Separate messages for PaymentGateway and Bank
message GatewayBalanceRequest {
  string username = 1; // Username to fetch balances for
}

message GatewayBalanceResponse {
  map<string, double> accounts = 1; // Map of account numbers to balances
}

message BankBalanceRequest {
  string account_number = 1; // Account number to fetch balance for
}

message BankBalanceResponse {
  double balance = 1; // Balance of the account
}
```
