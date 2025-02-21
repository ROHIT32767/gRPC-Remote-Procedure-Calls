import grpc
import load_balancer_pb2
import load_balancer_pb2_grpc
import time
import threading

def send_request(client_id):
    channel = grpc.insecure_channel('localhost:50051')
    stub = load_balancer_pb2_grpc.LoadBalancerStub(channel)
    response = stub.GetServer(load_balancer_pb2.ClientRequest(client_id=client_id))
    if response.server_address:
        print(f"Client {client_id} assigned to server {response.server_address}")
        # Simulate sending a request to the assigned server
        time.sleep(1)  # Simulate processing time
    else:
        print(f"Client {client_id} could not get a server assignment")

def main():
    clients = [f"Client_{i}" for i in range(10)]  # Simulate 10 clients
    threads = []
    for client in clients:
        thread = threading.Thread(target=send_request, args=(client,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()