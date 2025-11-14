from collections import deque

import numpy as np
from medium.interface import MACInterface, NodeStatus

from .base import MAC

# Define header parts
DEST_ID_BYTES: int = 4
SENDER_ID_BYTES: int = 4 # Assuming 4-byte IDs
HEADER_BYTES: int = DEST_ID_BYTES + SENDER_ID_BYTES

class MAC_CSMA_CA(MAC):
    """
    CSMA/CA MAC protocol class.
    """
    def __init__(
        self,
        interface: MACInterface,
        *,
        bitrate: float = 2e6,
        buf_len: int = 5,
        difs: float = 1e-4,
        n: int = 16,
        cf: float = 4e-5
    ) -> None:
        """
        Initialise MAC protocol class.

        Parameters
        ----------
        interface: MACInterface
            Accessible for the MAC layer.
        bitrate: float, default: 2e6
            The bitrate for sending raw data using this protocol.
        buf_len: int, default: 5
            The size of the buffer that holds messages until the channel is free.
        difs: float, default: 1e-4
            The time to wait after the channel is free.
        n: int, default: 16
            The maximum slots to wait.
        cf: float, default: 4e-5
            The duration of a slot.
        """
        super().__init__(interface)
        
        # Parameters
        self._bitrate: float = bitrate
        self._buf_len: int = buf_len
        self._difs: float = difs
        self._n: int = n
        self._cf: float = cf

        # State
        self._buffer_out: deque[bytes] = deque(maxlen=buf_len)
        self._difs_end: float = self.time + difs
        self._cf_end: float = 0
        self._counter: int = np.random.randint(0, n)

    def send(self, address: int, data: bytes) -> None:
        # Flush old messages from buffer to make space for the new message
        while len(self._buffer_out) >= self._buf_len:
            print("Old message ignored")
            self._buffer_out.popleft()
        
        # Add the message with header to the buffer
        dest_b = address.to_bytes(DEST_ID_BYTES, signed=True)
        sender_b = self.interface.id.to_bytes(SENDER_ID_BYTES, signed=True)
        self._buffer_out.append(dest_b + sender_b + data)
        
    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header from content
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

        # Do nothing if no data to send
        if len(self._buffer_out) == 0:
            return

        # Wait until the channel is free
        if self.interface.status != NodeStatus.IDLE:
            self._difs_end: float = self.time + self._difs
            return

        # Wait for the DIFS period after the channel is free
        if self.time < self._difs_end:
            return
        
        # Wait for 'counter' amount of contention frames
        if self.time < self._cf_end:
            return
        if self._counter > 0:
            self._counter -= 1
            self._cf_end = self.time + self._cf
            return

        # Transmit the message and reset the counter
        self.interface.antenna_transmit(self._buffer_out.popleft(), bitrate=self._bitrate)
        self._counter = np.random.randint(0, self._n)
