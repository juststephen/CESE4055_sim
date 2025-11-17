from medium.interface import RoutingInterface

from .base import Routing

class RoutingNone(Routing):
    """
    Disabled routing protocol.
    """
    def __init__(self, node: RoutingInterface) -> None:
        super().__init__(node)

    def send(self, address: int, data: bytes) -> None:
        # Ignore routing and just send the message
        self.interface.MAC_send(address, data)

    def receive(self, data: bytes, sender_id: int) -> None:
        # No routing data to intercept, ignore sender_id
        self.interface.receive(data)

    def tick(self, time: float) -> None:
        self.time = time
