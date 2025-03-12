python3 -m grpc_tools.protoc -Iprotofiles --python_out=. --grpc_python_out=. protofiles/payment.proto

cd server; python3 bank_server.py --bank bank1 --port 50051
cd server; python3 bank_server.py --bank bank2 --port 50052
cd server; python3 gateway_server.py
