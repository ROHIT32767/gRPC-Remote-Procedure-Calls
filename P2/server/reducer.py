import grpc
import sys
import os
from concurrent import futures
from pathlib import Path

protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)

import reducer_service_pb2 as reducer_pb2
import reducer_service_pb2_grpc as reducer_pb2_grpc
from reducer_service import ReducerServiceServicer

class ReducerServer:
    """ gRPC server for handling reducer service requests. """

    def __init__(self, port, reducer_name):
        self.address = "localhost"
        self.port = str(port)  # Ensure port is stored as a string
        self.reducer_name = reducer_name

    def start(self):
        """ Starts the gRPC server and waits for termination. """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        reducer_pb2_grpc.add_ReducerServiceServicer_to_server(
            ReducerServiceServicer(self.reducer_name), server
        )
        server.add_insecure_port(f"[::]:{self.port}")
        print(f"Reducer server '{self.reducer_name}' running on port {self.port}...")
        server.start()
        server.wait_for_termination()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reducer.py <port> <reducer_name>")
        sys.exit(1)

    port, reducer_name = sys.argv[1], sys.argv[2]
    server = ReducerServer(port, reducer_name)
    server.start()
