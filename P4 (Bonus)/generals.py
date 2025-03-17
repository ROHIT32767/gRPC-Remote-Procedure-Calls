import os
import sys
protofiles_path = os.path.join(os.path.dirname(__file__), ".", "client")
sys.path.append(protofiles_path)
from client import GeneralClient
from collections import Counter

class General:
    def __init__(self, id, is_traitor=False, port=50051):
        self.id = id
        self.other_generals = []
        self.orders = []
        self.is_traitor = is_traitor

    def __call__(self, m, order):
        self.orders.append(order)  # Add the commander's initial order
        self.om_algorithm(commander=self, m=m, order=order)

    def _next_order(self, is_traitor, order, i):
        if is_traitor:
            # Flip order for even indices (0, 2, 4, ...)
            if i % 2 == 0:
                return "ATTACK" if order == "RETREAT" else "RETREAT"
        return order  # Loyal generals pass the order as-is

    def om_algorithm(self, commander, m, order):
        print(f"General {self.id} running om_algorithm: commander={commander.id}, m={m}, order={order}")
        if m < 0:
            self.orders.append(order)  # Collect the order
            return
        # For m >= 0, propagate the order to other generals
        for i, l in enumerate(self.other_generals):
            # Skip self and commander
            if l is self or l is commander:
                continue
            print(f"General {self.id} sending order to General {l.id}")
            try:
                target_port = 50051 + l.id
                client = GeneralClient(target_port)
                # Pass the *original commander's ID*, not the current general's ID
                response = client.send_order(
                    commander.id,  # Original commander's ID
                    m - 1,
                    self._next_order(self.is_traitor, order, i)
                )
                l.orders.append(response)
            except Exception as e:
                print(f"General {self.id} failed to send order to General {l.id}: {e}")

    @property
    def decision(self):
        c = Counter(self.orders)
        return c.most_common()