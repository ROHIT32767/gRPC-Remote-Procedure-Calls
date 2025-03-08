# Run the protofile
cd P4; cd protofiles; python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. byzantine.proto

# Run servers
cd P4; cd server; python3 server.py 0 7 2 False 
cd P4; cd server; python3 server.py 1 7 2 False  
cd P4; cd server; python3 server.py 2 7 2 True   
cd P4; cd server; python3 server.py 3 7 2 False  
cd P4; cd server; python3 server.py 4 7 2 False  
cd P4; cd server; python3 server.py 5 7 2 True   
cd P4; cd server; python3 server.py 6 7 2 False  

# Run clients
cd P4; cd client; python3 client.py 7 2

