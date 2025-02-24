import grpc
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading
from concurrent import futures
import etcd3
import psutil
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

    def report_load_to_lb(self):
        """Periodically report the server's load to the Load Balancer via gRPC."""
        lb_channel = grpc.insecure_channel('localhost:50051')
        lb_stub = load_balancer_pb2_grpc.LoadBalancerStub(lb_channel)
        while True:
            try:
                self.cpu_load = self.get_cpu_usage()
                lb_stub.ReportLoad(load_balancer_pb2.LoadReport(server_address=self.address, cpu_load=self.cpu_load))
                print(f"Reported load for server {self.address}: {self.cpu_load}")
                time.sleep(5)
            except Exception as e:
                print(f"Failed to report load to LB: {e}")
                break

    def get_cpu_usage(self):
        """Measure the CPU usage of the current process."""
        return psutil.cpu_percent(interval=1)  # Measure CPU usage over 1 second

    def handle_simple_task(self, request):
        """Handle a simple task."""
        return f"Processed simple task {request} on server {self.address}"

    def handle_cpu_heavy_task(self, request):
        """Handle a CPU-heavy task."""
        n = 10000000  # Adjust this value to control the task's intensity
        total = 0
        for i in range(n):
            total += i
        return f"Processed CPU-heavy task {request} on server {self.address}. Sum: {total}"

class BackendServicer(load_balancer_pb2_grpc.BackendServicer):
    def __init__(self, backend_server):
        self.backend_server = backend_server

    def ProcessTask(self, request, context):
        """Process a task based on the task type."""
        if request.task_type == "SIMPLE":
            result = self.backend_server.handle_simple_task(request.task_id)
        elif request.task_type == "CPU_HEAVY":
            result = self.backend_server.handle_cpu_heavy_task(request.task_id)
        else:
            result = f"Unknown task type: {request.task_type}"
        return load_balancer_pb2.TaskResponse(result=result)

def serve(port_id):
    server_address = 'localhost:' + port_id
    backend_server = BackendServer(server_address)
    backend_server.register_with_etcd()

    # Start a thread to keep the server registered in etcd
    threading.Thread(target=backend_server.keep_alive, daemon=True).start()

    # Start a thread to report load periodically to LB
    threading.Thread(target=backend_server.report_load_to_lb, daemon=True).start()

    # Create a gRPC server for handling client requests
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    load_balancer_pb2_grpc.add_BackendServicer_to_server(BackendServicer(backend_server), server)
    server.add_insecure_port(server_address)
    server.start()
    print(f"Backend Server running on {server_address}...")
    server.wait_for_termination()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backend Server with gRPC')
    parser.add_argument('--server_id', type=str, required=True, help='Unique server ID (port number)')
    args = parser.parse_args()
    serve(args.server_id)