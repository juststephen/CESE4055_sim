from medium.interface import MACInterface
from medium.typing import N

from .base import MAC

class MACAloha(MAC):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, interface: MACInterface) -> None:
        super().__init__(interface)

    def send(self, address: int, data: bytes) -> None:
        # TODO add address header
        self.interface.antenna_transmit(data, bitrate=4e6)

    def receive(self, data: bytes) -> None:
        # TODO check null data
        # TODO check address header
        self.interface.routing_receive(data)

    def tick(self, time: float) -> None:
        self.time = time
