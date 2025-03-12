import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P1/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from load_balancer_pb2 import ClientRequest, TaskRequest
from load_balancer_pb2_grpc import LoadBalancerStub, ComputeStub

def main(lb_address='localhost:50051'):
    # Connect to Load Balancer
    lb_channel = grpc.insecure_channel(lb_address)
    lb_stub = LoadBalancerStub(lb_channel)

    # Get server address from LB
    server_response = lb_stub.GetServer(ClientRequest())
    print(f"Selected server: {server_response.server_address}")

    # Connect to the selected server
    server_channel = grpc.insecure_channel(server_response.server_address)
    compute_stub = ComputeStub(server_channel)

    # Send a task
    response = compute_stub.ProcessTask(TaskRequest(data="hello"))
    print(f"Result: {response.result}")

if __name__ == '__main__':
    main()