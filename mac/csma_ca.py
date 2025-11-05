from collections import deque

import numpy as np
from medium.interface import MACInterface, NodeStatus

from .base import MAC

HEADER_BYTES: int = 4
BITRATE: float = 2e6
BUFFER_LEN: int = 5
DIFS: float = 1e-4
CF: float = 4e-5
N: int = 16

class MAC_CSMA_CA(MAC):
    """
    CSMA/CA MAC protocol class.
    """
    def __init__(self, interface: MACInterface) -> None:
        super().__init__(interface)

        self._buffer_out: deque[bytes] = deque(maxlen=BUFFER_LEN)
        self._difs_end: float = self.time + DIFS
        self._cf_end: float = 0
        self._counter: int = np.random.randint(0, N)

    def send(self, address: int, data: bytes) -> None:
        # Flush old messages from buffer to make space for the new message
        while len(self._buffer_out) >= BUFFER_LEN:
            print("Old message ignored")
            self._buffer_out.popleft()
        
        # Add the message with header to the buffer
        self._buffer_out.append(address.to_bytes(HEADER_BYTES, signed=True) + data)

    def receive(self, data: bytes) -> None:
        # Return if data is not received correctly
        if (data == None or len(data) < HEADER_BYTES):
            return

        # Split header from content
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

        # Do nothing if no data to send
        if len(self._buffer_out) == 0:
            return

        # Wait until the channel is free
        if self.interface.status != NodeStatus.IDLE:
            self._difs_end: float = self.time + DIFS
            return

        # Wait for the DIFS period after the channel is free
        if self.time < self._difs_end:
            return
        
        # Wait for 'counter' amount of contention frames
        if self.time < self._cf_end:
            return
        if self._counter > 0:
            self._counter -= 1
            self._cf_end = self.time + CF
            return

        # Transmit the message and reset the counter
        self.interface.antenna_transmit(self._buffer_out.popleft(), bitrate=BITRATE)
        self._counter = np.random.randint(0, N)
