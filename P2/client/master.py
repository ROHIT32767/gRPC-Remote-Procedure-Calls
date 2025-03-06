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

class Master:
    def __init__(self, query, n_mappers, n_reducers):
        self.query = query
        self.input_location = os.path.join(os.path.dirname(__file__), "..", "dataset")  # Resolve input path
        self.output_location = os.path.join(os.path.dirname(__file__), "..", "outputs")  # Resolve output path
        self.n_mappers = n_mappers
        self.n_reducers = n_reducers
        self.mappers = self._assign_ports(n_mappers, 8080)
        self.reducers = self._assign_ports(n_reducers, 8810)

    def _assign_ports(self, count, start_port):
        return {f"worker_{i + 1}": start_port + i for i in range(count)}

    def input_split(self):
        files = os.listdir(self.input_location)
        print("input files: ", files)
        n_input_files = len(files)
        mapper_to_files_mapping = {}

        if self.query == 3:
            chunk_size = 2
        elif self.n_mappers > n_input_files:
            chunk_size = 1
        else:
            chunk_size = n_input_files // self.n_mappers

        mapper_i = 1
        file_i = 0

        idle_mapper_num = 0
        # First assigning chunk size number of files to each mapper
        while mapper_i <= self.n_mappers:
            end = file_i + chunk_size
            file_list = []
            file_id_list = []
            while file_i < end and file_i < n_input_files:
                file_list.append(files[file_i])
                file_id_list.append(file_i)
                file_i = file_i + 1
            if len(file_list) != 0:
                mapper_to_files_mapping[mapper_i] = [file_list, file_id_list]
            else:
                idle_mapper_num += 1
                mapper_name = f"worker_{mapper_i}"  # Use the correct key format
                if mapper_name in self.mappers:  # Check if the mapper exists before deleting
                    del self.mappers[mapper_name]
            mapper_i = mapper_i + 1

        self.n_mappers -= idle_mapper_num
        # Assigning remaining files (1 to each mapper)
        mapper_i = 1
        while file_i < n_input_files:
            if mapper_i not in mapper_to_files_mapping:
                mapper_to_files_mapping[mapper_i] = [[], []]  # Initialize if not present
            mapper_to_files_mapping[mapper_i][0].append(files[file_i])
            mapper_to_files_mapping[mapper_i][1].append(file_i)
            file_i = file_i + 1
            mapper_i = mapper_i + 1

        print("Mapper to files mapping:", mapper_to_files_mapping)
        return mapper_to_files_mapping

    def spawn_mappers(self):
        mappers_process = []
        for mapper_name, port in self.mappers.items():
            mapper_script_path = os.path.join(os.path.dirname(__file__), "..", "server", "mapper_service.py")
            mapper = subprocess.Popen(['python3', mapper_script_path, str(port), mapper_name])
            print(f"Mapper {mapper_name} started on port {port} with PID {mapper.pid}")
            mappers_process.append(mapper)
            time.sleep(1)
        return mappers_process

    def spawn_reducers(self):
        reducers_process = []
        for reducer_name, port in self.reducers.items():
            reducer_script_path = os.path.join(os.path.dirname(__file__), "..", "server", "reducer_service.py")
            reducer = subprocess.Popen(['python3', reducer_script_path, str(port), reducer_name])
            print(f"Reducer {reducer_name} started on port {port} with PID {reducer.pid}")
            reducers_process.append(reducer)
            time.sleep(1)
        return reducers_process

    def terminate_mappers(self, mappers_process):
        print("Terminating mappers...")
        for mapper in mappers_process:
            mapper.terminate()

    def terminate_reducers(self, reducers_process):
        print("Terminating reducers...")
        for reducer in reducers_process:
            reducer.terminate()

    def mapFunction(self, mapper_to_files_mapping, item):
        num = list(self.mappers.items()).index(item) + 1
        port = item[1]
        with grpc.insecure_channel(f'localhost:{port}', options=(('grpc.enable_http_proxy', 0),)) as channel:
            stub = mapper_pb2_grpc.MapperServiceStub(channel)
            response = stub.map(mapper_pb2.MapRequest(
                query=self.query,
                input_location=self.input_location,
                input_split_files=mapper_to_files_mapping[num][0],
                input_split_file_id=mapper_to_files_mapping[num][1],
                n_reducers=self.n_reducers
            ))
            if response.status == mapper_pb2.MapResponse.Status.SUCCESS:
                print("Status: SUCCESS")
                print("Location of Intermediate data:", response.intermediate_file_location)
                map_intermediate_location.append(response.intermediate_file_location)
            else:
                print("Status: FAILURE")

    def reduceFunction(self, intermediate_file_locations, item):
        num = list(self.reducers.items()).index(item) + 1
        port = item[1]
        partition_paths = [path + f"/P{num-1}" for path in intermediate_file_locations if os.path.exists(path + f"/P{num-1}")]
        if not partition_paths:
            print(f"No partition files found for reducer {num}. Skipping.")
            return

        with grpc.insecure_channel(f'localhost:{port}', options=(('grpc.enable_http_proxy', 0),)) as channel:
            stub = reducer_pb2_grpc.ReducerServiceStub(channel)
            response = stub.reduce(reducer_pb2.ReduceRequest(
                query=self.query,
                partition_files_path=partition_paths,
                output_location=self.output_location
            ))
            if response.status == reducer_pb2.ReduceResponse.Status.SUCCESS:
                print("Status: SUCCESS")
                print("Location of Output data:", response.output_file_path)
            else:
                print("Status: FAILURE")

    def map(self, mapper_to_files_mapping):
        with ThreadPool() as pool:
            pool.starmap(self.mapFunction, [(mapper_to_files_mapping, item) for item in self.mappers.items()])

    def reduce(self, intermediate_file_locations):
        with ThreadPool() as pool:
            pool.starmap(self.reduceFunction, [(intermediate_file_locations, item) for item in self.reducers.items()])
    
    def aggregate_reducer_outputs(self):
        final_output_path = os.path.join(self.output_location, "final_output.txt")
        with open(final_output_path, "w") as final_output_file:
            for reducer_name in self.reducers.keys():
                reducer_output_path = os.path.join(self.output_location, reducer_name)
                if os.path.exists(reducer_output_path):
                    with open(reducer_output_path, "r") as reducer_output_file:
                        final_output_file.write(reducer_output_file.read())
                    # os.remove(reducer_output_path)  # Optionally, remove the individual reducer output file after aggregation
        print(f"Aggregated final output written to {final_output_path}")


if __name__ == '__main__':
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Distributed MapReduce Master")
    parser.add_argument("--query", type=int, required=True, help="Query to perform: 1 (WordCount), 2 (InvertedIndex)")
    parser.add_argument("--mappers", type=int, required=True, help="Number of mappers")
    parser.add_argument("--reducers", type=int, required=True, help="Number of reducers")
    args = parser.parse_args()

    if Path("folders").exists():
        shutil.rmtree("folders")
    if Path("outputs").exists():
        shutil.rmtree("outputs")

    master = Master(args.query, args.mappers, args.reducers)
    mappers_process = master.spawn_mappers()
    mapper_to_files_mapping = master.input_split()
    master.map(mapper_to_files_mapping)
    time.sleep(20)
    master.terminate_mappers(mappers_process)
    reducers_process = master.spawn_reducers()
    master.reduce(map_intermediate_location)
    time.sleep(20)
    master.terminate_reducers(reducers_process)
    master.aggregate_reducer_outputs()  # Call the new method to aggregate reducer outputs