import grpc
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading
import argparse

def send_request(client_id, task_type):
    """Continuously send requests to the load balancer."""
    while True:
        try:
            # Query the Load Balancer for a server
            lb_channel = grpc.insecure_channel('localhost:50051')
            lb_stub = load_balancer_pb2_grpc.LoadBalancerStub(lb_channel)
            server_response = lb_stub.GetServer(load_balancer_pb2.ClientRequest(client_id=client_id))

            if server_response.server_address:
                print(f"Client {client_id} assigned to server {server_response.server_address}")

                # Send the task to the assigned server
                backend_channel = grpc.insecure_channel(server_response.server_address)
                backend_stub = load_balancer_pb2_grpc.BackendStub(backend_channel)
                task_response = backend_stub.ProcessTask(
                    load_balancer_pb2.TaskRequest(task_id=client_id, task_type=task_type)
                )
                print(f"Task response from server {server_response.server_address}: {task_response.result}")
            else:
                print(f"Client {client_id} could not get a server assignment")

            time.sleep(2)  # Wait before sending the next request
        except grpc.RpcError as e:
            print(f"Client {client_id} encountered an error: {e}")
            time.sleep(2)  # Wait before retrying

def main(client_id, task_type):
    clients = [f"{client_id}-{i}" for i in range(5)]
    threads = []
    for client in clients:
        thread = threading.Thread(target=send_request, args=(client, task_type))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_id', type=str, required=True, help='Unique client ID')
    parser.add_argument('--task_type', type=str, required=True, choices=["SIMPLE", "CPU_HEAVY"], help='Type of task to send')
    args = parser.parse_args()
    main(args.client_id, args.task_type)