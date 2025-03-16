# Command to run protofile
```bash
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. load_balancer.proto
```

# Command to start etcd
```bash
cd P1; etcd
```

# Command to run load balancer
```bash
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python ; python3 load_balancer_server.py -p rr
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python ; python3 load_balancer_server.py -p ll
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python ; python3 load_balancer_server.py -p pf
```

# Command to run server
```bash
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 backend_server.py --server_id 50052
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 backend_server.py --server_id 50053
cd P1; cd server; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 backend_server.py --server_id 50054
```

# Command to run client
```bash
cd P1; cd client; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 client.py --client_id Client_1 --task_type SIMPLE
cd P1; cd client; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 client.py --client_id Client_2 --task_type CPU_HEAVY
```

# Command for readjust python implementation
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```