from argparse import ArgumentParser
from collections import Counter


class ByzantineGeneral:
    def __init__(self, general_id, traitor=False):
        self.general_id = general_id
        self.is_traitor = traitor
        self.peers = []
        self.received_orders = []

    def __call__(self, recursion_level, initial_order):
        """Initiates the OM algorithm as the commander."""
        self.om_protocol(leader=self, depth=recursion_level, command=initial_order)

    def _modify_order(self, command, index):
        """Determines the order to pass based on the general's loyalty."""
        if self.is_traitor and index % 2 == 0:
            return "ATTACK" if command == "RETREAT" else "RETREAT"
        return command

    def om_protocol(self, leader, depth, command):
        """Executes the OM algorithm for Byzantine generals."""
        if depth == 0:
            self.received_orders.append(command)
        else:
            for idx, ally in enumerate(self.peers):
                if ally is not self and ally is not leader:
                    ally.om_protocol(leader=self, depth=depth - 1, command=self._modify_order(command, idx))

    @property
    def consensus(self):
        """Returns the most common order received."""
        return Counter(self.received_orders).most_common()


def setup_generals(config_list):
    """Creates and initializes generals based on input configuration."""
    army = [ByzantineGeneral(i, traitor=(spec == "t")) for i, spec in enumerate(config_list)]
    
    # Assign references to all other generals
    for general in army:
        general.peers = army

    return army


def display_results(army):
    """Displays the final decision of each general."""
    for gen in army:
        print(f"General {gen.general_id}: {gen.consensus}")


def main():
    parser = ArgumentParser()
    parser.add_argument("-m", type=int, required=True, help="Recursion depth (M), must be > 0.")
    parser.add_argument("-G", type=str, required=True, help="Comma-separated list of generals ('l,t,l,l...').")
    parser.add_argument("-O", type=str, required=True, choices=["ATTACK", "RETREAT"], help="Initial command from the leader.")

    args = parser.parse_args()
    army_config = args.G.split(',')
    army = setup_generals(army_config)

    # The first general acts as the commander
    army[0](recursion_level=args.m, initial_order=args.O)

    display_results(army)


if __name__ == "__main__":
    main()
