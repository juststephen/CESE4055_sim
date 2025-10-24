from medium.typing import N

from .base import Routing

class RoutingNone(Routing[N]):
    """
    Disabled routing protocol.
    """
    def __init__(self, node: N) -> None:
        super().__init__(node)

    def send(self, address: int, data: bytes) -> None:
        self.node.mac.send(address, data)

    def receive(self, data: bytes) -> None:
        self.node.receive(data)

    def tick(self, time: float) -> None:
        self.time = time
