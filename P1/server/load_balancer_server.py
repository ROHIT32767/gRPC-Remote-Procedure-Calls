import grpc
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
from concurrent import futures
import load_balancer_pb2
import load_balancer_pb2_grpc
import threading
import etcd3
import time

class LoadBalancerServicer(load_balancer_pb2_grpc.LoadBalancerServicer):
    def __init__(self, load_balancing_policy="Round Robin"):
        self.servers = {}  
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_balancing_policy = load_balancing_policy
        self.etcd = etcd3.client()  
        threading.Thread(target=self.watch_servers, daemon=True).start()

    def watch_servers(self):
        """Watch for changes in etcd to maintain an updated list of servers."""
        print("Watching etcd for server updates...")
        while True:
            try:
                with self.lock:
                    servers = self.etcd.get_prefix('/servers/')
                    self.servers = {
                        key.decode('utf-8').split('/')[-1]: 0.0
                        for key, _ in servers
                    }
                print(f"Available servers: {list(self.servers.keys())}")
                time.sleep(5)  
            except Exception as e:
                print(f"Failed to fetch server list: {e}")
                break

    def GetServer(self, request, context):
        with self.lock:
            if not self.servers:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details('No servers available')
                return load_balancer_pb2.ServerResponse()

            if self.load_balancing_policy == "Pick First":
                server = list(self.servers.keys())[0]
            elif self.load_balancing_policy == "Round Robin":
                if self.current_index >= len(self.servers):
                    self.current_index = 0
                if self.current_index < 0:
                    self.current_index = len(self.servers) - 1
                while list(self.servers.keys())[self.current_index] not in self.servers:
                    self.current_index = (self.current_index + 1) % len(self.servers)
                server = list(self.servers.keys())[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.servers)
            elif self.load_balancing_policy == "Least Load":
                server = min(self.servers.keys(), key=lambda k: self.servers[k])

            print(f"Client {request.client_id} assigned to server {server}")
            return load_balancer_pb2.ServerResponse(server_address=server)

    def ReportLoad(self, request, context):
        with self.lock:
            if request.server_address in self.servers:
                self.servers[request.server_address] = request.cpu_load
                print(f"Server {request.server_address} reported load: {request.cpu_load}")
            return load_balancer_pb2.LoadReportResponse(success=True)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    load_balancer_pb2_grpc.add_LoadBalancerServicer_to_server(LoadBalancerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Load Balancer Server running on port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()