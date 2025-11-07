from medium.interface import RoutingInterface

from .base import Routing

ID_BYTES: int = 3
INDEX_BYTES: int = 2
HEADER_BYTES: int = 2 * ID_BYTES + INDEX_BYTES
INDEX_TIMEOUT: float = 1.0

class RoutingFlooding(Routing):
    """
    Flooding routing protocol.
    """
    def __init__(self, node: RoutingInterface) -> None:
        super().__init__(node)

        self._index: int = 0
        self._received: dict[bytes, float] = dict()

    def send(self, address: int, data: bytes) -> None:
        # Convert header info to binary
        target: bytes = address.to_bytes(ID_BYTES, signed=True)
        sender: bytes = self.interface.id.to_bytes(ID_BYTES, signed=True)
        index: bytes = self._index.to_bytes(INDEX_BYTES, signed=False)

        # Increment index
        self._index += 1
        if self._index >= 1 >> (8 * INDEX_BYTES):
              self._index = 0
        
        # Broadcast header + data
        header: bytes = target + sender + index
        self.interface.MAC_send(-1, header + data)

    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header from content
        header: bytes = data[:HEADER_BYTES]
        content: bytes = data[HEADER_BYTES:]
    
        # If this message is already received, ignore
        previous = self._received.get(header)
        if previous and self.time - previous < INDEX_TIMEOUT:
            return
        self._received[header] = self.time

        # Forward the message if data is not intended for this node
        target: int = int.from_bytes(header[:ID_BYTES], signed=True)
        if (target >= 0 and target != self.interface.id):
            self.interface.MAC_send(-1, data)
            return

        # Send content to next layer
        self.interface.receive(content)

    def tick(self, time: float) -> None:
        self.time = time
