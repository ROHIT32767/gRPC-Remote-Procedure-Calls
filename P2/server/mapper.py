import grpc
import sys
import os
from concurrent import futures
from pathlib import Path
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)

import mapper_service_pb2 as mapper_pb2
import mapper_service_pb2_grpc as mapper_pb2_grpc
from mapper_service import MapperServiceServicer

class MapperServer:
    """ gRPC server for handling mapper service requests. """

    def __init__(self, port, mapper_name):
        self.address = "localhost"
        self.port = str(port)  # Ensure port is stored as a string
        self.mapper_name = mapper_name

    def start(self):
        """ Starts the gRPC server and waits for termination. """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        mapper_pb2_grpc.add_MapperServiceServicer_to_server(
            MapperServiceServicer(self.mapper_name), server
        )
        server.add_insecure_port(f"[::]:{self.port}")
        print(f"Mapper server '{self.mapper_name}' running on port {self.port}...")
        server.start()
        server.wait_for_termination()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mapper.py <port> <mapper_name>")
        sys.exit(1)

    port, mapper_name = sys.argv[1], sys.argv[2]
    server = MapperServer(port, mapper_name)
    server.start()
