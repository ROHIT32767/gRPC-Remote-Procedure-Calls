import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P2/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from concurrent import futures
import threading
from mapreduce_pb2 import *
from mapreduce_pb2_grpc import MasterServicer, add_MasterServicer_to_server

class MapReduceMaster(MasterServicer):
    def __init__(self, input_files, num_reduce):
        self.map_tasks = [(f, i) for i, f in enumerate(input_files)]
        self.reduce_tasks = list(range(num_reduce))
        self.completed_map = set()
        self.completed_reduce = set()
        self.lock = threading.Lock()

    def GetTask(self, request, context):
        with self.lock:
            # Assign map tasks first
            if self.map_tasks:
                file_path, task_id = self.map_tasks.pop()
                return TaskAssignment(
                    task_type="map",
                    input_files=[file_path],
                    task_id=task_id,
                    num_reduce=len(self.reduce_tasks)
                )
            
            # Assign reduce tasks after map phase
            if not self.map_tasks and self.reduce_tasks:
                reduce_id = self.reduce_tasks.pop()
                return TaskAssignment(
                    task_type="reduce",
                    task_id=reduce_id,
                    num_reduce=len(self.reduce_tasks)
                )
            
            return TaskAssignment(task_type="wait")

    def SubmitTask(self, request, context):
        with self.lock:
            if request.task_type == "map":
                self.completed_map.add(request.task_id)
            elif request.task_type == "reduce":
                self.completed_reduce.add(request.task_id)
        return TaskAck(success=True)

def start_master(input_dir, num_reduce=3):
    input_files = [f"{input_dir}/file1.txt", f"{input_dir}/file2.txt"]  # Modify this
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    master = MapReduceMaster(input_files, num_reduce)
    add_MasterServicer_to_server(master, server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Master running...")
    server.wait_for_termination()

if __name__ == '__main__':
    start_master("../datasets", num_reduce=3)