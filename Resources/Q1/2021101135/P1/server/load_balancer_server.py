import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P1/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from concurrent import futures
import time
from load_balancer_pb2 import *
from load_balancer_pb2_grpc import LoadBalancerServicer, add_LoadBalancerServicer_to_server


class LoadBalancer(LoadBalancerServicer):
    def __init__(self, policy='round_robin'):
        self.servers = {}  # Format: {server_id: {"address": "ip:port", "load": 0}}
        self.policy = policy
        self.rr_index = 0

    def RegisterServer(self, request, context):
        self.servers[request.server_id] = {
            "address": request.address,
            "load": 0
        }
        print(f"Server {request.server_id} registered at {request.address}")
        return RegistrationResponse(success=True)

    def ReportLoad(self, request, context):
        if request.server_id in self.servers:
            self.servers[request.server_id]["load"] = request.load
            print(f"Server {request.server_id} load updated to {request.load}")
        return RegistrationResponse(success=True)

    def GetServer(self, request, context):
        if not self.servers:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return ServerResponse()

        if self.policy == 'pick_first':
            selected = list(self.servers.values())[0]
        elif self.policy == 'round_robin':
            server_list = list(self.servers.values())
            selected = server_list[self.rr_index % len(server_list)]
            self.rr_index += 1
        elif self.policy == 'least_load':
            selected = min(self.servers.values(), key=lambda x: x["load"])
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ServerResponse()

        return ServerResponse(server_address=selected["address"])

def serve(policy='round_robin'):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LoadBalancerServicer_to_server(LoadBalancer(policy), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print(f"Load Balancer running with policy: {policy}")
    server.wait_for_termination()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--policy', type=str, default='round_robin', help='Load balancing policy')
    args = parser.parse_args()
    serve(args.policy)