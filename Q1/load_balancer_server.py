import grpc
from concurrent import futures
import load_balancer_pb2
import load_balancer_pb2_grpc
import threading
import time

class LoadBalancerServicer(load_balancer_pb2_grpc.LoadBalancerServicer):
    def __init__(self, load_balancing_policy="Round Robin"):  # Default policy is Round Robin
        self.servers = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_balancing_policy = load_balancing_policy  # Initialize the load balancing policy

    def GetServer(self, request, context):
        with self.lock:
            if not self.servers:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details('No servers available')
                return load_balancer_pb2.ServerResponse()

            # Implement different load balancing policies
            if self.load_balancing_policy == "Pick First":
                server = self.servers[0]
            elif self.load_balancing_policy == "Round Robin":
                server = self.servers[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.servers)
            elif self.load_balancing_policy == "Least Load":
                server = min(self.servers, key=lambda s: s['load'])

            return load_balancer_pb2.ServerResponse(server_address=server['address'])

    def RegisterServer(self, request, context):
        with self.lock:
            self.servers.append({'address': request.server_address, 'load': 0.0})
            return load_balancer_pb2.RegistrationResponse(success=True)

    def ReportLoad(self, request, context):
        with self.lock:
            for server in self.servers:
                if server['address'] == request.server_address:
                    server['load'] = request.cpu_load
                    break
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