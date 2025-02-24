import threading
import time
from Q1.client.client import get_server_address, send_request

def client_thread(client_id):
    while True:
        server_address = get_server_address()
        if server_address:
            send_request(server_address)
        time.sleep(1)

if __name__ == '__main__':
    threads = []
    for i in range(10):  # Number of clients
        thread = threading.Thread(target=client_thread, args=(f"client{i}",))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()