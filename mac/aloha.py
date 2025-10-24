from medium.typing import N

from .base import MAC

class MACAloha(MAC[N]):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, node: N) -> None:
        super().__init__(node)

    def send(self, address: int, data: bytes) -> None:
        # TODO add address header
        self.node.antenna_transmit(data, bitrate=4e6)

    def receive(self, data: bytes) -> None:
        # TODO check null data
        # TODO check address header
        self.node.routing.receive(data)

    def tick(self, time: float) -> None:
        self.time = time
