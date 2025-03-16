from concurrent import futures
import grpc
import sys
import os
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import mapper_service_pb2 as mapper_pb2
import mapper_service_pb2_grpc as mapper_pb2_grpc
from pathlib import Path
import os
import sys

class MapperServiceServicer(mapper_pb2_grpc.MapperServiceServicer):
    def __init__(self, mapper_name):
        self.mapper_name = mapper_name
        self.path = os.path.join(os.path.dirname(__file__), "..", "folders", "ID_" + mapper_name)
        self.intermediate_data = {}
        self.n_reducers = 0
        self.query = 0
        Path(self.path).mkdir(parents=True, exist_ok=True)
    
    def file_read(self, path):
        with open(path, "r") as file:
            file_content = file.read().splitlines()
        return file_content
    
    def file_write(self, path, content):
        with open(path, "a+") as file:
            file.write(content + "\n")
    
    def word_count_function(self, key, value):
        for word in value.split():
            self.file_write(os.path.join(self.path, f"P{str(len(word) % self.n_reducers)}"), f"{word.lower()} 1")
                
    def inverted_index_function(self, key, value):
        for line in value:
            for word in line.split():
                self.file_write(os.path.join(self.path, f"P{str(len(word) % self.n_reducers)}"), f"{word.lower()} {key}")

    def map(self, request, context):
        self.n_reducers = request.n_reducers
        self.query = request.query
        for idx, file_name in enumerate(request.input_split_files):
            file_content = self.file_read(os.path.join(request.input_location, file_name))
            if request.query == 1:
                for line in file_content:
                    self.word_count_function(line, file_content[line])
            elif request.query == 2:
                self.inverted_index_function(request.input_split_file_id[idx], file_content)

        return mapper_pb2.MapResponse(
            intermediate_file_location=self.path, 
            status=mapper_pb2.MapResponse.Status.SUCCESS
        )
