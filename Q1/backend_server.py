import grpc
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading
from concurrent import futures

class BackendServer:
    def __init__(self, address):
        self.address = address
        self.cpu_load = 0.0

    def register_with_load_balancer(self):
        channel = grpc.insecure_channel('localhost:50051')
        stub = load_balancer_pb2_grpc.LoadBalancerStub(channel)
        response = stub.RegisterServer(load_balancer_pb2.ServerRegistration(server_address=self.address))
        if response.success:
            print(f"Server {self.address} registered with Load Balancer")
        else:
            print("Failed to register with Load Balancer")

    def report_load(self):
        channel = grpc.insecure_channel('localhost:50051')
        stub = load_balancer_pb2_grpc.LoadBalancerStub(channel)
        while True:
            stub.ReportLoad(load_balancer_pb2.LoadReport(server_address=self.address, cpu_load=self.cpu_load))
            time.sleep(5)

    def handle_request(self, request, context):
        # Simulate CPU load
        self.cpu_load += 0.1
        time.sleep(1)  # Simulate processing time
        self.cpu_load -= 0.1
        return f"Processed request {request} on server {self.address}"

def serve():
    server_address = 'localhost:50054'  # Change this for multiple servers
    backend_server = BackendServer(server_address)
    backend_server.register_with_load_balancer()

    # Start a thread to report load periodically
    threading.Thread(target=backend_server.report_load, daemon=True).start()

    # Create a gRPC server for handling client requests
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Add your backend server's service implementation here (if needed)
    server.add_insecure_port(server_address)
    server.start()
    print(f"Backend Server running on {server_address}...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()