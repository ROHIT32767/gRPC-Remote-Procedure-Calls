# Command to run protofile
```bash
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. load_balancer.proto
```

# Command to run server
```bash
cd Q1; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 backend_server.py --server_id 50052
```

# Command to run load balancer
```bash
cd Q1; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 load_balancer_server.py
```

# Command to run client
```bash
cd Q1; export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python; python3 client.py --client_id Client_1 --task_type SIMPLE
```

# Command for readjust python implementation
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```

# Command to start etcd
```bash
cd Q1; etcd
```
