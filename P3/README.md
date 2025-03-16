# Command to run the protofile
cd P3; python3 -m grpc_tools.protoc -Iprotofiles --python_out=. --grpc_python_out=. protofiles/payment.proto

# Command to run the gateway server
cd P3; cd server; python3 gateway.py

# Command to run the bank server
cd P3; cd server; python3 bank.py --bank bank1 --port 50051
cd P3; cd server; python3 bank.py --bank bank2 --port 50052

# Command to run the client
cd P3; cd client; python3 client.py --port 50053

# Example commands for client.py
payment bank1-1234 bank2-5678 100
payment bank1-1234 bank2-6789 100

# Gateway certificate
openssl req -newkey rsa:4096 -nodes -keyout certificates/payment_gateway_server.key -out certificates/payment_gateway_server.csr -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost"

# For CA certificate
openssl x509 -req -in certificates/payment_gateway_server.csr -CA certificates/server_CA.crt -CAkey certificates/server_CA.key -CAcreateserial -out certificates/payment_gateway_server.crt -extfile <(printf "subjectAltName=DNS:localhost")

# For Bank certificate
openssl req -newkey rsa:4096 -nodes -keyout certificates/bank_server_1.key -out certificates/bank_server_1.csr -subj "/CN=bank_server_1" -addext "subjectAltName=DNS:localhost"
openssl x509 -req -in certificates/bank_server_1.csr -CA certificates/server_CA.crt -CAkey certificates/server_CA.key -CAcreateserial -out certificates/bank_server_1.crt -extfile <(printf "subjectAltName=DNS:localhost")
