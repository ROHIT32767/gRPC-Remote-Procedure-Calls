import grpc
from concurrent import futures
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import generals_pb2 as generals_pb2
import generals_pb2_grpc as generals_pb2_grpc

class GeneralServicer(generals_pb2_grpc.GeneralServiceServicer):
    def __init__(self, general):
        self.general = general

    def SendOrder(self, request, context):
        try:
            commander_id = request.commander_id
            m = request.m
            order = request.order

            print(f"General {self.general.id} received order: commander_id={commander_id}, m={m}, order={order}")

            # Validate commander_id exists in the other_generals list
            if commander_id < 0 or commander_id >= len(self.general.other_generals):
                raise ValueError(f"Invalid commander_id: {commander_id}")

            commander = self.general.other_generals[commander_id]
            self.general.om_algorithm(commander=commander, m=m, order=order)
            return generals_pb2.OrderResponse(order=order)
        except Exception as e:
            print(f"Error in General {self.general.id}: {e}")
            raise e

def serve(general, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    generals_pb2_grpc.add_GeneralServiceServicer_to_server(GeneralServicer(general), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"General {general.id} started on port {port}")
    return server  # Return the server instance