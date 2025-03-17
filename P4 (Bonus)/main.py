from argparse import ArgumentParser
from collections import Counter
import threading
import time
from generals import General
import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), ".", "server")
sys.path.append(protofiles_path)
from server import serve
import grpc

def init_generals(generals_spec):
    generals = []
    for i, spec in enumerate(generals_spec):
        general = General(i, port=50051 + i)
        if spec == "l":
            pass
        elif spec == "t":
            general.is_traitor = True
        else:
            print("Error, bad input in generals list: {}".format(generals_spec))
            exit(1)
        generals.append(general)
    # Share the same list of generals across all instances
    for general in generals:
        general.other_generals = generals
    return generals

def print_decisions(generals):
    for i, general in enumerate(generals):
        print(f"General {i}: {general.decision}")

def main():
    parser = ArgumentParser()
    parser.add_argument("-m", type=int, dest="recursion",
                        help="The level of recursion in the algorithm, where M > 0.")
    parser.add_argument("-G", type=str, dest="generals",
                        help="A string of generals (ie 'l,t,l,l,l'...), where l is loyal and t is a traitor.")
    parser.add_argument("-O", type=str, dest="order",
                        help="The order the commander gives to the other generals (O ∈ {ATTACK,RETREAT})")
    args = parser.parse_args()

    generals_spec = [x.strip() for x in args.generals.split(',')]
    generals = init_generals(generals_spec=generals_spec)

    # List to store server instances
    servers = []

    # Start gRPC servers for each general
    for i, general in enumerate(generals):
        port = 50051 + i
        server = serve(general, port)  # Start the server and store the instance
        servers.append(server)

    # Wait for servers to initialize
    time.sleep(5)

    # Start the algorithm
    generals[0](m=args.recursion, order=args.order)

    # Print decisions
    print_decisions(generals)

    # Shutdown all servers
    for server in servers:
        server.stop(0)  # Gracefully stop the server
    print("All servers stopped. Exiting program.")

if __name__ == "__main__":
    main()