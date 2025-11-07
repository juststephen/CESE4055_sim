from medium.interface import MACInterface

from .base import MAC

HEADER_BYTES: int = 4

class MACAloha(MAC):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, interface: MACInterface, *, bitrate: float = 2e6) -> None:
        """
        Initialise MAC protocol class.

        Parameters
        ----------
        interface: MACInterface
            Accessible for the MAC layer.
        bitrate: float, default: 2e6
            The bitrate for sending raw data using this protocol.
        """
        super().__init__(interface)

        self._bitrate = bitrate

    def send(self, address: int, data: bytes) -> None:
        self.interface.antenna_transmit(address.to_bytes(HEADER_BYTES, signed=True) + data, bitrate=self._bitrate)

    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header form content
        header: bytes = data[:HEADER_BYTES]
        content: bytes = data[HEADER_BYTES:]

        # Return if data is not intended for this node
        data_id: int = int.from_bytes(header, signed=True)
        if (data_id >= 0 and data_id != self.interface.id):
            return
        
        # Send content to next layer
        self.interface.routing_receive(content)

    def tick(self, time: float) -> None:
        self.time = time
