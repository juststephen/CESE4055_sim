from medium.interface import MACInterface

from .base import MAC

# Define header parts
DEST_ID_BYTES: int = 4
SENDER_ID_BYTES: int = 4 # Assuming 4-byte IDs
HEADER_BYTES: int = DEST_ID_BYTES + SENDER_ID_BYTES

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
        dest_b = address.to_bytes(DEST_ID_BYTES, signed=True)
        sender_b = self.interface.id.to_bytes(SENDER_ID_BYTES, signed=True)
        self.interface.antenna_transmit(dest_b + sender_b + data, bitrate=self._bitrate)
    
    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header form content
        dest_id_b: bytes = data[:DEST_ID_BYTES]
        sender_id_b: bytes = data[DEST_ID_BYTES:HEADER_BYTES]
        content: bytes = data[HEADER_BYTES:]
        
        # Parse header
        dest_id: int = int.from_bytes(dest_id_b, signed=True)
        sender_id: int = int.from_bytes(sender_id_b, signed=True)

        # Return if data is not intended for this node
        if (dest_id >= 0 and dest_id != self.interface.id):
            return
        
        # Send content AND sender_id to next layer
        self.interface.routing_receive(content, sender_id)

    def tick(self, time: float) -> None:
        self.time = time
