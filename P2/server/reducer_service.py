from concurrent import futures
import grpc
import sys
import os
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import  reducer_service_pb2 as reducer_pb2
import reducer_service_pb2_grpc as reducer_pb2_grpc
from pathlib import Path
import os
import sys

class ReducerServiceServicer(reducer_pb2_grpc.ReducerServiceServicer):
    def __init__(self, reducer_name):
        self.reducer_name = reducer_name
        self.shuffled_and_sorted_data = {}
        self.path = ""
    
    def file_write(self, path, content):
        with open(path, "a+") as file:
            file.write(content + "\n")
    
    def word_count_function(self, key, values):
        self.file_write(self.path + "/" + self.reducer_name , key + " " + str(len(values)))
        return self.path + "/" + self.reducer_name
    
    def inverted_index_function(self, key, values):
        self.file_write(os.path.join(self.path, self.reducer_name), f"{key} {", ".join(map(str, set(values)))}")
        return os.path.join(self.path, self.reducer_name)
    
    def reduce(self, request, context):
        self.path = request.output_location
        Path(self.path).mkdir(parents=True, exist_ok=True)
        partition_files_path = request.partition_files_path
        query = request.query
        self.shuffled_and_sorted_data = {}
        for file_path in partition_files_path:
            with open(file_path, "r") as file:
                for line in file:
                    key, value = line.split()
                    value = int(value)
                    self.shuffled_and_sorted_data.setdefault(key, []).append(value)
        reduce_function = (
            self.word_count_function if query == 1 else self.inverted_index_function
        )
        for key, value in self.shuffled_and_sorted_data.items():
            final_output_path = reduce_function(key, value)
        return reducer_pb2.ReduceResponse(
            status=reducer_pb2.ReduceResponse.Status.SUCCESS,
            output_file_path=final_output_path
        )