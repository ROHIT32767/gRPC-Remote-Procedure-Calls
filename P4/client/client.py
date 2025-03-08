import grpc
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import byzantine_pb2
import byzantine_pb2_grpc
import random
import sys

def run_consensus(n, t):
    # Initialize connections to all nodes
    channels = []
    stubs = []
    for i in range(n):
        channel = grpc.insecure_channel(f'localhost:{50051 + i}')
        stub = byzantine_pb2_grpc.ByzantineServiceStub(channel)
        channels.append(channel)
        stubs.append(stub)

    # Step 1: Commander sends initial order
    commander_id = 0
    initial_order = "Attack" if random.random() > 0.5 else "Retreat"
    print(f"Commander (Node {commander_id}) sends initial order: {initial_order}")

    for i in range(1, n):
        stubs[i].SendOrder(byzantine_pb2.OrderRequest(order=initial_order, sender_id=commander_id))

    # Step 2: Cross-Verification and Forwarding
    for round_num in range(1, t + 1):
        print(f"\nRound {round_num}: Cross-Verification")
        for i in range(n):
            for j in range(n):
                if i != j:
                    stubs[j].ForwardOrder(byzantine_pb2.ForwardRequest(order=initial_order, sender_id=i, round=round_num))

    # Step 3: Query each node for its collected orders
    print("\nFinal Decision: Majority Voting")
    decisions = []
    for i in range(n):
        response = stubs[i].GetOrders(byzantine_pb2.GetOrdersRequest())
        orders = list(response.orders)  # Convert RepeatedScalarContainer to a Python list
        attack_count = orders.count("Attack")
        retreat_count = orders.count("Retreat")
        decision = "Attack" if attack_count > retreat_count else "Retreat"
        decisions.append(decision)
        print(f"Node {i} decides: {decision} (Orders: {orders})")

    # Step 4: Consensus
    final_decision = max(set(decisions), key=decisions.count)
    print(f"\nConsensus Reached: {final_decision}")

if __name__ == "__main__":
    n = int(sys.argv[1])
    t = int(sys.argv[2])
    if n <= 3 * t:
        print("Error: n must be greater than 3t")
    else:
        run_consensus(n, t)