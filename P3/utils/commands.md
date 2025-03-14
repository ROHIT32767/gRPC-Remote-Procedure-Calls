# Command to run the protofile
cd P3; python3 -m grpc_tools.protoc -Iprotofiles --python_out=. --grpc_python_out=. protofiles/payment.proto

# Command to run the gateway server
cd P3; cd server; python3 gateway_server.py

# Command to run the bank server
cd P3; cd server; python3 bank_server.py --bank bank1 --port 50051
cd P3; cd server; python3 bank_server.py --bank bank2 --port 50052

# Command to run the client
cd P3; cd client; python3 client.py --port 50053

# Example commands for client.py
payment bank1-1234 bank2-5678 100