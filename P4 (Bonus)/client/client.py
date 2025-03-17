import grpc
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import generals_pb2 as generals_pb2
import generals_pb2_grpc as generals_pb2_grpc

class GeneralClient:
    def __init__(self, port):
        self.channel = grpc.insecure_channel(f'localhost:{port}')
        self.stub = generals_pb2_grpc.GeneralServiceStub(self.channel)

    def send_order(self, commander_id, m, order):
        request = generals_pb2.OrderRequest(commander_id=commander_id, m=m, order=order)
        response = self.stub.SendOrder(request)
        return response.order

if __name__ == "__main__":
    client = GeneralClient(50051)
    response = client.send_order(0, 1, "ATTACK")
    print("Response:", response)