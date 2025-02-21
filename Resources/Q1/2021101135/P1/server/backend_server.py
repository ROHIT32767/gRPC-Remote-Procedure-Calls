import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P1/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from concurrent import futures
from load_balancer_pb2 import *
from load_balancer_pb2_grpc import LoadBalancerStub
from load_balancer_pb2_grpc import ComputeServicer, add_ComputeServicer_to_server
import time
import random

class ComputeServer(ComputeServicer):
    def ProcessTask(self, request, context):
        # Simulate task processing
        result = request.data.upper()
        time.sleep(random.uniform(0.1, 1.0))  # Simulate variable load
        return TaskResponse(result=result)

def start_server(server_id, lb_address='localhost:50051'):
    # Start the compute server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ComputeServicer_to_server(ComputeServer(), server)
    port = server.add_secure_port('[::]:0', grpc.local_server_credentials())  # Dynamic port
    server.start()
    address = f'localhost:{port}'

    # Register with Load Balancer
    channel = grpc.insecure_channel(lb_address)
    lb_stub = LoadBalancerStub(channel)
    lb_stub.RegisterServer(ServerRegistration(server_id=server_id, address=address))

    # Periodically report load (simulated)
    while True:
        load = random.randint(1, 100)  # Simulate random load
        lb_stub.ReportLoad(LoadUpdate(server_id=server_id, load=load))
        time.sleep(5)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_id', type=str, required=True, help='Unique server ID')
    args = parser.parse_args()
    start_server(args.server_id)