import numpy as np
from medium import Node2D, Medium2D

m = Medium2D()
nodes = [Node2D(*np.random.uniform(-50, 50, size=2)) for _ in range(16)]
for n in nodes:
    m.add_node(n)

nodes[0].transmit('Hello World'.encode())

i: int = 0
while m.has_events_queued:
    print(f'Time step {i}')
    m.step(1e-8)
    i += 1
