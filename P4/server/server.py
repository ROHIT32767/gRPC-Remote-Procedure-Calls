import grpc
from concurrent import futures
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import byzantine_pb2
import byzantine_pb2_grpc
import random

class ByzantineServer(byzantine_pb2_grpc.ByzantineServiceServicer):
    def __init__(self, node_id, n, t, is_traitor=False):
        self.node_id = node_id
        self.n = n
        self.t = t
        self.is_traitor = is_traitor
        self.orders = []

    def SendOrder(self, request, context):
        order = request.order
        sender_id = request.sender_id
        print(f"Node {self.node_id} received order '{order}' from Node {sender_id}")
        if self.is_traitor:
            order = "Retreat" if order == "Attack" else "Attack"  # Traitor changes the order
        self.orders.append(order)
        return byzantine_pb2.OrderResponse(success=True)

    def ForwardOrder(self, request, context):
        order = request.order
        sender_id = request.sender_id
        round_num = request.round
        print(f"Node {self.node_id} received forwarded order '{order}' from Node {sender_id} in round {round_num}")
        if self.is_traitor:
            order = "Retreat" if order == "Attack" else "Attack"  # Traitor changes the order
        self.orders.append(order)
        return byzantine_pb2.ForwardResponse(success=True)

    def GetOrders(self, request, context):
        return byzantine_pb2.GetOrdersResponse(orders=self.orders)  # Return collected orders

def serve(node_id, n, t, is_traitor=False):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    byzantine_pb2_grpc.add_ByzantineServiceServicer_to_server(ByzantineServer(node_id, n, t, is_traitor), server)
    server.add_insecure_port(f'[::]:{50051 + node_id}')
    print(f"Node {node_id} started on port {50051 + node_id}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    import sys
    node_id = int(sys.argv[1])
    n = int(sys.argv[2])
    t = int(sys.argv[3])
    is_traitor = sys.argv[4].lower() == "true"
    serve(node_id, n, t, is_traitor)