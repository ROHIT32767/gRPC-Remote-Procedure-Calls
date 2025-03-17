# Usage

## Parameters
The simulation is run using the `main.py` script with the following parameters:

| Parameter | Description |
|-----------|-------------|
| `-m` | The recursion depth of the OM algorithm. Must be a positive integer. |
| `-G` | A comma-separated list of generals, where `l` denotes a loyal general and `t` denotes a traitor. The first general is the commander. |
| `-O` | The order given by the commander. Must be either `ATTACK` or `RETREAT`. |

## Example
To run the simulation with the following configuration:

- **Recursion depth (`-m`)**: `3`
- **Generals (`-G`)**: `l,l,l,t,t,l,l,t,l` (9 generals, with Generals 3, 4, and 7 as traitors)
- **Order (`-O`)**: `ATTACK`

Run the following command:

```bash
python3 main.py -m 3 -G "l,l,l,t,t,l,l,t,l" -O ATTACK
```

## Output
The program will output the decisions of each general in the following format:

```
General 0: [('ATTACK', 5)]
General 1: [('ATTACK', 6)]
General 2: [('ATTACK', 5)]
General 3: [('ATTACK', 4), ('RETREAT', 1)]
General 4: [('ATTACK', 3), ('RETREAT', 2)]
General 5: [('ATTACK', 6)]
General 6: [('ATTACK', 6)]
General 7: [('ATTACK', 4), ('RETREAT', 1)]
General 8: [('ATTACK', 6)]
```

Each line shows the final decision of a general, represented as a list of tuples. Each tuple contains:

1. The order (e.g., `ATTACK` or `RETREAT`).
2. The number of times the order was received.
