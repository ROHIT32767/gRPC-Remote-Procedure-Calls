cd P3; python3 -m grpc_tools.protoc -Iprotofiles --python_out=. --grpc_python_out=. protofiles/payment.proto
python3 -m grpc_tools.protoc -Iprotofiles --python_out=. --grpc_python_out=. protofiles/payment.proto

cd P3; cd server; python3 gateway_server.py
cd P3; cd server; python3 bank_server.py --bank bank1 --port 50051
cd P3; cd server; python3 bank_server.py --bank bank2 --port 50052
cd P3; cd client; python3 client.py
```
