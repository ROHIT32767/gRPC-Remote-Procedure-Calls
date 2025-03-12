# Run the protofile
cd P4; cd protofiles; python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. byzantine.proto

# Run servers
```Testcase 1
cd P4; cd server; python3 server.py 0 7 2 False 
cd P4; cd server; python3 server.py 1 7 2 False  
cd P4; cd server; python3 server.py 2 7 2 True   
cd P4; cd server; python3 server.py 3 7 2 False  
cd P4; cd server; python3 server.py 4 7 2 False  
cd P4; cd server; python3 server.py 5 7 2 True   
cd P4; cd server; python3 server.py 6 7 2 False  
```

```Testcase 2
cd P4; cd server; python3 server.py 0 4 1 False
cd P4; cd server; python3 server.py 1 4 1 False
cd P4; cd server; python3 server.py 2 4 1 False
cd P4; cd server; python3 server.py 3 4 1 True
```


# Run clients
```Testcase 1
cd P4; cd client; python3 client.py 7 2
```

```Testcase 2
cd P4; cd client; python3 client.py 4 1
```

