import grpc
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading
from concurrent import futures
import etcd3
import argparse

class BackendServer:
    def __init__(self, address):
        self.address = address
        self.cpu_load = 0.0
        self.etcd = etcd3.client()  # Connect to etcd
        self.lease = self.etcd.lease(10)  # Create a lease with a TTL of 10 seconds

    def register_with_etcd(self):
        """Register the server with etcd using a lease."""
        self.etcd.put(f"/servers/{self.address}", self.address, lease=self.lease)
        print(f"Server {self.address} registered with etcd")

    def keep_alive(self):
        """Periodically refresh the lease to keep the server registered."""
        while True:
            try:
                self.lease.refresh()
                time.sleep(5)  # Refresh every 5 seconds
            except Exception as e:
                print(f"Failed to refresh lease: {e}")
                break

    def report_load(self):
        """Periodically report the server's load to the load balancer."""
        channel = grpc.insecure_channel('localhost:50051')
        stub = load_balancer_pb2_grpc.LoadBalancerStub(channel)
        while True:
            stub.ReportLoad(load_balancer_pb2.LoadReport(server_address=self.address, cpu_load=self.cpu_load))
            time.sleep(5)

    def handle_request(self, request, context):
        """Handle client requests and simulate CPU load."""
        self.cpu_load += 0.1
        time.sleep(1)  # Simulate processing time
        self.cpu_load -= 0.1
        return f"Processed request {request} on server {self.address}"

def serve(port_id):
    server_address = 'localhost:' + port_id
    backend_server = BackendServer(server_address)
    backend_server.register_with_etcd()

    # Start a thread to keep the server registered in etcd
    threading.Thread(target=backend_server.keep_alive, daemon=True).start()

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
    parser = argparse.ArgumentParser(description='Backend Server with gRPC')
    parser.add_argument('--server_id', type=str, required=True, help='Unique server ID')
    args = parser.parse_args()
    serve(args.server_id)