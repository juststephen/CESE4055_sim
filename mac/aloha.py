from medium.interface import MACInterface

from .base import MAC

HEADER_BYTES: int = 4
BITRATE: float = 4e6

class MACAloha(MAC):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, interface: MACInterface) -> None:
        super().__init__(interface)

    def send(self, address: int, data: bytes) -> None:
        self.interface.antenna_transmit(address.to_bytes(HEADER_BYTES, signed=True, byteorder="big") + data, bitrate=BITRATE)       # `byteorder` arg was missing, assigned to default value ('big')

    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header form content
        header: bytes = data[:HEADER_BYTES]
        content: bytes = data[HEADER_BYTES:]

        # Return if data is not intended for this node
        data_id: int = int.from_bytes(header, signed=True, byteorder='big') # `byteorder` arg was missing, assigned to default value ('big')
        if (data_id >= 0 and data_id != self.interface.id):
            return
        
        # Send content to next layer
        self.interface.routing_receive(content)

    def tick(self, time: float) -> None:
        self.time = time
