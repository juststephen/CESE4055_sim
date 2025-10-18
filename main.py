import numpy as np
from medium import Medium, Node2D

m = Medium[Node2D]()
nodes = [Node2D(*np.random.uniform(-50, 50, size=2)) for _ in range(16)]
for n in nodes:
    m.add_node(n)

nodes[0].transmit('Hello World'.encode())
nodes[1].transmit('https://juststephen.com/'.encode(), frequency=2.401e9)

i: int = 0
while m.has_events_queued:
    m.step(1e-8)
    i += 1
