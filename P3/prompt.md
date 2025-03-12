Write code in python using GRPC to complete the following task: , Give code for all the files required to run the code.

Your task is to build a miniature version of Stripe, which is a payment gateway that interfaces with various
bank servers to manage transactions.

System Components 
•Bank Servers
– Implement a bank server that represents an individual bank.
– Multiple bank servers will be instantiated, each with a unique name.
•Clients
– Implement a client that interacts with the payment gateway.
– Clients must register with the gateway and provide bank account details.
– Multiple clients will be run during testing.
•Payment Gateway
– The central entity that interfaces between clients and bank servers.
– Handles transactions between clients and banks.

Secure Authentication, Authorization, and Logging 

Authentication
A secure and robust payment service requires strict authentication and authorization mechanisms to ensure
only authorized users can access the system and perform transactions. In a Stripe-like service, clients must
authenticate before initiating payments. The system will employ SSL/TLS mutual authentication
for communication security and implement role-based authorization to restrict access to sensitive
operations.
•Clients must authenticate themselves with the Stripe service before making transactions.
•Clients provide their username and password, which are validated against stored credentials (You
can load some users at the server side before hand and these will serve as existing users in the system.
You can also choose to implement an admin which can add users based on details such as their name,
account no, balance etc which is relevant for this problem).
•You can keep a setup file (csv, json, yaml) with dummy data for simulation purposes. The bank
servers would need to read from that file and load the information relevant only to that bank. This
is if you are not implementing an admin who can add users manually. We suggest this method for
simplicity.
•Communication between the client and server is secured using SSL/TLS to prevent eavesdropping.
You can use certificates for this.
•gRPC Configuration: The gateway server will configure SSL/TLS credentials using its own server
certificate and private key. Similarly, the client will verify the server’s certificate using the trusted
Certificate Authority (CA).
•The specific details about how you want to perform authentication(using appropriate certificate
choice, implementation details) is upto you
You can refer to the official documentation of gRPC for authentication

Authorization
Authorization ensures that only authenticated users with the correct permissions can access certain resources.
For example, a client can:
•View their balance.
•Initiate transactions (only within available funds).
•View their transaction history. (Optional)
You are required to implement authorization using gRPC interceptors so that only a client with appropriate
permissions can access their information

Logging
Logging is essential for monitoring the health of the system and troubleshooting potential issues. In
companies, the logs are used for recovery as well but for the scope of this assignment we are just focussing
on capturing logs and will not be utilizing them for any task. gRPC interceptors provide an ideal
mechanism to log every request, response, and error, which is important for both debugging and other
tasks as well.
•Verbose Logging with gRPC Interceptors: To capture detailed logs for each gRPC request, you
need to implement a logging interceptor. This interceptor will log the incoming requests, the server’s
response, the status of the response, and any errors that occur. This logging mechanism will provide
full transparency into the payment flow, helping to track down any issues in real-time.
•Logging Information: The logs should include the following information(you can change as you
feel necessary):
– The transaction amount.
– Client identification information (e.g., client ID, IP address).
– Method name (for e.g., ProcessPayment).
– Any errors or exceptions, including error codes and messages.
•Transaction Integrity and Retry Logging: In case of network failures or timeouts during payment
processing, retries may be attempted. The interceptor will also log when a transaction is retried,
ensuring that the payment gateway correctly handles idempotency

2PC with Timeout
Fairly straightforward. Payments need to be implemented using 2 phase commit transactions. The voters
are going to be the sending and receiving bank servers and the coordinator is the payment gateway. Follow
the algorithm discussed in class or the one linked below.
Note that transactions must be aborted after a certain timeout (keep this a configurable parameter) and
shouldn’t go through on any end if any of the participants ultimately aborts.

Implementation Details
• Use gRPC for communication between components.
• Clearly define gRPC service definitions for all interactions.
• Ensure fault tolerance (e.g. servers should be able to recover from crashes, with the previous state)
and scalability in the system.

Directory Structure
├── certificate
├── client
├── protofiles
└── server