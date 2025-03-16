import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), "..", "protofiles")
sys.path.append(protofiles_path)
import mapper_service_pb2 as mapper_pb2
import mapper_service_pb2_grpc as mapper_pb2_grpc
import reducer_service_pb2 as reducer_pb2
import reducer_service_pb2_grpc as reducer_pb2_grpc
from concurrent import futures
import logging
import grpc
import time
import subprocess
import shutil
from pathlib import Path
from multiprocessing.pool import ThreadPool
import argparse

map_intermediate_location = []

class MasterServer:
    def __init__(self, query, n_mappers, n_reducers):
        self.query = query
        self.input_location = os.path.abspath("../dataset")
        self.output_location = os.path.abspath("../outputs")
        self.n_mappers = n_mappers
        self.n_reducers = n_reducers
        self.mappers = self.get_ports(n_mappers, 8080)
        self.reducers = self.get_ports(n_reducers, 8810)

    def get_ports(self, count, base_port):
        """Assigns consecutive ports to workers starting from base_port."""
        return {f"worker_{i + 1}": base_port + i for i in range(count)}

    def split_input(self):
        files = os.listdir(self.input_location)
        print("Input files:", files)
        n_input_files = len(files)
        mapper_to_files_mapping = {}
        chunk_size = max(1, n_input_files // self.n_mappers) 
        idle_mappers = 0
        file_index = 0
        for mapper_id in range(1, self.n_mappers + 1):
            assigned_files = files[file_index:file_index + chunk_size]
            file_ids = list(range(file_index, file_index + len(assigned_files)))
            file_index += len(assigned_files)

            if assigned_files:
                mapper_to_files_mapping[mapper_id] = [assigned_files, file_ids]
            else:
                idle_mappers += 1
                mapper_name = f"worker_{mapper_id}"
                self.mappers.pop(mapper_name, None)  
        mapper_id = 1
        while file_index < n_input_files:
            mapper_to_files_mapping.setdefault(mapper_id, [[], []])
            mapper_to_files_mapping[mapper_id][0].append(files[file_index])
            mapper_to_files_mapping[mapper_id][1].append(file_index)
            file_index += 1
            mapper_id = (mapper_id % self.n_mappers) + 1 

        self.n_mappers -= idle_mappers 
        print("Mapper to files mapping:", mapper_to_files_mapping)
        return mapper_to_files_mapping


    def create_mappers(self):
        mappers_process = []
        for mapper_name, port in self.mappers.items():
            mapper = subprocess.Popen(['python3', os.path.join(os.path.dirname(__file__), "..", "server", "mapper.py"), str(port), mapper_name])
            print(f"Mapper instance '{mapper_name}' started successfully on port {port} with process ID {mapper.pid}")
            mappers_process.append(mapper)
            time.sleep(1)
        return mappers_process

    def create_reducers(self):
        reducers_process = []
        for reducer_name, port in self.reducers.items():
            reducer = subprocess.Popen(['python3', os.path.join(os.path.dirname(__file__), "..", "server", "reducer.py"), str(port), reducer_name])
            print(f"Reducer instance '{reducer_name}' started successfully on port {port} with process ID {reducer.pid}")
            reducers_process.append(reducer)
            time.sleep(1)
        return reducers_process

    def terminate_mappers(self, mappers_process):
        print("Initiating mapper termination...")
        for mapper in mappers_process:
            mapper.terminate()

    def terminate_reducers(self, reducers_process):
        print("Initiating reducer termination...")
        for reducer in reducers_process:
            reducer.terminate()

    def map_function(self, mapper_to_files_mapping, item):
        mapper_index = list(self.mappers.keys()).index(item[0]) + 1
        port = item[1]
        
        with grpc.insecure_channel(f'localhost:{port}', options=[('grpc.enable_http_proxy', 0)]) as channel:
            stub = mapper_pb2_grpc.MapperServiceStub(channel)
            request = mapper_pb2.MapRequest(
                query=self.query,
                input_location=self.input_location,
                input_split_files=mapper_to_files_mapping[mapper_index][0],
                input_split_file_id=mapper_to_files_mapping[mapper_index][1],
                n_reducers=self.n_reducers
            )
            
            response = stub.map(request)
            if response.status == mapper_pb2.MapResponse.Status.SUCCESS:
                print("Status: SUCCESS")
                print(f"Intermediate data stored at: {response.intermediate_file_location}")
                map_intermediate_location.append(response.intermediate_file_location)
            else:
                print("Status: FAILURE")


    def reduce_function(self, intermediate_file_locations, item):
        reducer_index = list(self.reducers.keys()).index(item[0]) + 1
        port = item[1]
        partition_paths = [
            os.path.join(path, f"P{reducer_index - 1}") 
            for path in intermediate_file_locations 
            if os.path.exists(os.path.join(path, f"P{reducer_index - 1}"))
        ]

        if not partition_paths:
            print(f"No partition files found for reducer {reducer_index}. Skipping.")
            return

        with grpc.insecure_channel(f'localhost:{port}', options=[('grpc.enable_http_proxy', 0)]) as channel:
            stub = reducer_pb2_grpc.ReducerServiceStub(channel)
            request = reducer_pb2.ReduceRequest(
                query=self.query,
                partition_files_path=partition_paths,
                output_location=self.output_location
            )

            response = stub.reduce(request)

            if response.status == reducer_pb2.ReduceResponse.Status.SUCCESS:
                print("Status: SUCCESS OPERATION")
                print(f"Output data stored at: {response.output_file_path}")
            else:
                print("Status: FAILURE OPERATION")

    def map(self, mapper_to_files_mapping):
        with ThreadPool() as pool:
            pool.starmap(self.map_function, [(mapper_to_files_mapping, item) for item in self.mappers.items()])

    def reduce(self, intermediate_file_locations):
        with ThreadPool() as pool:
            pool.starmap(self.reduce_function, [(intermediate_file_locations, item) for item in self.reducers.items()])
    
    def aggregate_reducer_outputs(self):
        final_output_path = os.path.join(self.output_location, "final_output.txt")
        with open(final_output_path, "w") as final_output_file:
            for reducer_name in self.reducers.keys():
                reducer_output_path = os.path.join(self.output_location, reducer_name)
                if os.path.exists(reducer_output_path):
                    with open(reducer_output_path, "r") as reducer_output_file:
                        final_output_file.write(reducer_output_file.read())
        print(f"Aggregated final output written to {final_output_path}")


if __name__ == '__main__':
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Distributed MapReduce Master")
    parser.add_argument("--query", type=int, required=True, help="Query to perform: 1 (WordCount), 2 (InvertedIndex)")
    parser.add_argument("--mappers", type=int, required=True, help="Number of mappers")
    parser.add_argument("--reducers", type=int, required=True, help="Number of reducers")
    args = parser.parse_args()

    if Path("../folders").exists():
        shutil.rmtree("../folders")
    if Path("../outputs").exists():
        shutil.rmtree("../outputs")

    master = MasterServer(args.query, args.mappers, args.reducers)
    mappers_process = master.create_mappers()
    mapper_to_files_mapping = master.split_input()
    master.map(mapper_to_files_mapping)
    time.sleep(20)
    master.terminate_mappers(mappers_process)
    reducers_process = master.create_reducers()
    master.reduce(map_intermediate_location)
    time.sleep(20)
    master.terminate_reducers(reducers_process)
    master.aggregate_reducer_outputs()