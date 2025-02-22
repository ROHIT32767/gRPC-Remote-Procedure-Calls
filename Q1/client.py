import grpc
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading
import argparse

def send_request(client_id):
    """Continuously send requests to the load balancer."""
    while True:
        try:
            channel = grpc.insecure_channel('localhost:50051')
            stub = load_balancer_pb2_grpc.LoadBalancerStub(channel)
            response = stub.GetServer(load_balancer_pb2.ClientRequest(client_id=client_id))
            if response.server_address:
                print(f"Client {client_id} assigned to server {response.server_address}")
                time.sleep(1)  # Simulate processing time
            else:
                print(f"Client {client_id} could not get a server assignment")
        except grpc.RpcError as e:
            print(f"Client {client_id} encountered an error: {e}")
        time.sleep(2)  # Wait before sending the next request

def main(client_id):
    clients = [f"{client_id}-{i}" for i in range(5)]
    threads = []
    for client in clients:
        thread = threading.Thread(target=send_request, args=(client,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_id', type=str, required=True, help='Unique client ID')
    args = parser.parse_args()
    main(args.client_id)