import sys
import os

PROTO_PATH = os.path.abspath("/home/siva/4_2/DS/A2/2021101135/P2/protofiles")
sys.path.insert(0, PROTO_PATH)

import grpc
from mapreduce_pb2 import *
from mapreduce_pb2_grpc import MasterStub
import hashlib
import time

class MapReduceWorker:
    def __init__(self, master_address='localhost:50052'):
        self.channel = grpc.insecure_channel(master_address)
        self.stub = MasterStub(self.channel)
        self.worker_id = "worker_" + hashlib.md5(str(id(self)).encode()).hexdigest()[:6]

    def run_map_task(self, input_file, task_id, num_reduce):
        # Read input file
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Word Count Example (Modify for other tasks)
        word_counts = {}
        for word in content.split():
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Create intermediate files
        outputs = {}
        for word, count in word_counts.items():
            reduce_id = hash(word) % num_reduce
            filename = f"mr-{task_id}-{reduce_id}.txt"
            outputs.setdefault(filename, []).append(f"{word} {count}\n")
        
        # Write to files
        output_files = []
        for filename, lines in outputs.items():
            with open(filename, 'w') as f:
                f.writelines(lines)
            output_files.append(filename)
        
        return output_files

    def run_reduce_task(self, task_id):
        # Aggregate results from map outputs
        intermediate = []
        for filename in glob.glob(f"mr-*-{task_id}.txt"):
            with open(filename, 'r') as f:
                intermediate.extend(f.readlines())
        
        # Word Count Reduce (Modify for other tasks)
        final_counts = defaultdict(int)
        for line in intermediate:
            word, count = line.strip().split()
            final_counts[word] += int(count)
        
        # Write final output
        output_file = f"out-{task_id}.txt"
        with open(output_file, 'w') as f:
            for word, count in final_counts.items():
                f.write(f"{word} {count}\n")
        
        return [output_file]

    def run(self):
        while True:
            task = self.stub.GetTask(TaskRequest(worker_id=self.worker_id))
            if task.task_type == "wait":
                print("No tasks available. Waiting...")
                time.sleep(5)
                continue
            
            try:
                if task.task_type == "map":
                    outputs = self.run_map_task(task.input_files[0], task.task_id, task.num_reduce)
                elif task.task_type == "reduce":
                    outputs = self.run_reduce_task(task.task_id)
                
                self.stub.SubmitTask(TaskResult(
                    task_type=task.task_type,
                    task_id=task.task_id,
                    output_files=outputs
                ))
            except Exception as e:
                print(f"Task failed: {str(e)}")

if __name__ == '__main__':
    worker = MapReduceWorker()
    worker.run()