from medium.interface import MACInterface
from .base import MAC
from enum import Enum
import numpy as np

class CSMAState(Enum):
    IDLE = 0
    BACKOFF = 1
    RTS_SENT = 2
    WAITING_CTS = 3
    DATA_SENT = 4
    WAITING_ACK = 5

# Frame types
RTS_FRAME = 0x01
CTS_FRAME = 0x02
DATA_FRAME = 0x03
ACK_FRAME = 0x04

HEADER_BYTES: int = 8
BITRATE: float = 4e6
SIFS_DURATION: float = 10e-6  # 10 microseconds
DIFS_DURATION: float = 28e-6  # 28 microseconds
SLOT_TIME: float = 9e-6       # 9 microseconds
CW_MIN: int = 15              # Minimum contention window
CW_MAX: int = 1023            # Maximum contention window

class MACCsmaCaRtsCts(MAC):
    """
    CSMA/CA with RTS/CTS MAC protocol implementation.
    """
    def __init__(self, interface: MACInterface) -> None:
        super().__init__(interface)
        self.state: CSMAState = CSMAState.IDLE
        self.backoff_counter: int = 0
        self.contention_window: int = CW_MIN
        self.pending_packet: tuple[int, bytes] | None = None
        self.expected_ack: bool = False
        self.nav_end: float = 0  # Network Allocation Vector end time
        
    def send(self, address: int, data: bytes) -> None:
        """
        Queue packet for transmission using RTS/CTS handshake.
        """
        if self.state != CSMAState.IDLE:
            # Already processing a packet, should queue or drop
            print(f"Node {self.interface.id}: MAC busy, dropping packet")
            return
            
        self.pending_packet = (address, data)
        self._start_backoff()
    
    def _start_backoff(self) -> None:
        """Start CSMA/CA backoff procedure."""
        if self.interface.status.name != "IDLE" or self.time < self.nav_end:
            # Medium busy or NAV active, wait
            self.state = CSMAState.BACKOFF
            self.backoff_counter = self._random_backoff()
            return
            
        # Medium idle for DIFS, send RTS immediately
        self._send_rts()
    
    def _random_backoff(self) -> int:
        """Generate random backoff value."""
        return np.random.randint(0, self.contention_window)
    
    def _send_rts(self) -> None:
        """Send RTS frame."""
        if not self.pending_packet:
            return
            
        address, data = self.pending_packet
        
        # Calculate total duration: RTS + SIFS + CTS + SIFS + DATA + SIFS + ACK
        data_duration = len(data) * 8 / BITRATE
        total_duration = (3 * SIFS_DURATION + 
                         self._frame_duration(RTS_FRAME) +
                         self._frame_duration(CTS_FRAME) +
                         data_duration +
                         self._frame_duration(ACK_FRAME))
        
        # Build RTS frame: [frame_type, target_addr, duration]
        rts_frame = (RTS_FRAME.to_bytes(1, 'big') +
                    address.to_bytes(4, 'big', signed=True) +
                    int(total_duration * 1e6).to_bytes(3, 'big'))  # duration in microseconds
        
        print(f"Node {self.interface.id}: Sending RTS to {address}")
        self.interface.antenna_transmit(rts_frame, bitrate=BITRATE)
        self.state = CSMAState.WAITING_CTS
        self.expected_ack = (address >= 0)  # Expect ACK only for unicast
        
    def _send_cts(self, sender_addr: int, duration: int) -> None:
        """Send CTS frame in response to RTS."""
        # Build CTS frame: [frame_type, sender_addr, duration]
        cts_frame = (CTS_FRAME.to_bytes(1, 'big') +
                    sender_addr.to_bytes(4, 'big', signed=True) +
                    duration.to_bytes(3, 'big'))
        
        print(f"Node {self.interface.id}: Sending CTS to {sender_addr}")
        self.interface.antenna_transmit(cts_frame, bitrate=BITRATE)
    
    def _send_data(self) -> None:
        """Send actual data packet."""
        if not self.pending_packet:
            return
            
        address, data = self.pending_packet
        
        # Build DATA frame: [frame_type, target_addr, data]
        data_frame = (DATA_FRAME.to_bytes(1, 'big') +
                     address.to_bytes(4, 'big', signed=True) +
                     data)
        
        print(f"Node {self.interface.id}: Sending DATA to {address}")
        self.interface.antenna_transmit(data_frame, bitrate=BITRATE)
        self.state = CSMAState.WAITING_ACK
    
    def _send_ack(self, sender_addr: int) -> None:
        """Send ACK frame."""
        ack_frame = (ACK_FRAME.to_bytes(1, 'big') +
                    sender_addr.to_bytes(4, 'big', signed=True) +
                    b'\x00\x00\x00')  # padding
        
        print(f"Node {self.interface.id}: Sending ACK to {sender_addr}")
        self.interface.antenna_transmit(ack_frame, bitrate=BITRATE)
    
    def _frame_duration(self, frame_type: int) -> float:
        """Calculate transmission duration for control frames."""
        control_frame_size = 8  # bytes for RTS/CTS/ACK
        return control_frame_size * 8 / BITRATE
    
    def receive(self, data: bytes) -> None:
        """
        Process received frames (RTS, CTS, DATA, ACK).
        """
        if len(data) < HEADER_BYTES:
            return
            
        frame_type = data[0]
        source_addr = int.from_bytes(data[1:5], 'big', signed=True)
        
        if frame_type == RTS_FRAME:
            self._handle_rts(source_addr, data)
        elif frame_type == CTS_FRAME:
            self._handle_cts(source_addr, data)
        elif frame_type == DATA_FRAME:
            self._handle_data(source_addr, data[5:])
        elif frame_type == ACK_FRAME:
            self._handle_ack(source_addr)
    
    def _handle_rts(self, sender_addr: int, data: bytes) -> None:
        """Handle received RTS frame."""
        if sender_addr == self.interface.id:
            return  # Ignore our own RTS
            
        duration = int.from_bytes(data[5:8], 'big') / 1e6  # Convert to seconds
        
        # Set NAV to protect the entire transaction
        self.nav_end = self.time + duration
        
        # If this CTS is for us, respond after SIFS
        target_addr = int.from_bytes(data[1:5], 'big', signed=True)
        if target_addr == self.interface.id or target_addr < 0:
            # Schedule CTS transmission after SIFS
            self.interface.medium.schedule(SIFS_DURATION, self._send_cts, 
                                         sender_addr, int(duration * 1e6))
        else:
            print(f"Node {self.interface.id}: Heard RTS, setting NAV for {duration:.6f}s")
    
    def _handle_cts(self, sender_addr: int, data: bytes) -> None:
        """Handle received CTS frame."""
        if self.state != CSMAState.WAITING_CTS:
            return
            
        duration = int.from_bytes(data[5:8], 'big') / 1e6
        
        # Set NAV and schedule DATA transmission after SIFS
        self.nav_end = self.time + duration
        self.interface.medium.schedule(SIFS_DURATION, self._send_data)
        print(f"Node {self.interface.id}: Received CTS, sending DATA after SIFS")
    
    def _handle_data(self, sender_addr: int, data: bytes) -> None:
        """Handle received DATA frame."""
        # Check if this data is for us
        target_addr = int.from_bytes(data[:4], 'big', signed=True)
        actual_data = data[4:]
        
        if target_addr == self.interface.id or target_addr < 0:
            # Send ACK after SIFS and pass data to upper layer
            self.interface.medium.schedule(SIFS_DURATION, self._send_ack, sender_addr)
            self.interface.routing_receive(actual_data)
            print(f"Node {self.interface.id}: Received DATA, sending ACK")
        else:
            print(f"Node {self.interface.id}: Overheard DATA not for us")
    
    def _handle_ack(self, sender_addr: int) -> None:
        """Handle received ACK frame."""
        if self.state == CSMAState.WAITING_ACK:
            print(f"Node {self.interface.id}: Received ACK, transmission successful!")
            self._transmission_success()
        else:
            print(f"Node {self.interface.id}: Received unexpected ACK")
    
    def _transmission_success(self) -> None:
        """Handle successful transmission completion."""
        self.state = CSMAState.IDLE
        self.pending_packet = None
        self.contention_window = CW_MIN  # Reset contention window
        self.expected_ack = False
    
    def _transmission_failed(self) -> None:
        """Handle transmission failure (timeout)."""
        print(f"Node {self.interface.id}: Transmission failed, increasing CW")
        self.contention_window = min(2 * self.contention_window, CW_MAX)
        self.state = CSMAState.IDLE
        # Could retry the packet here
    
    def tick(self, time: float) -> None:
        """Handle timer events for backoff and timeouts."""
        self.time = time
        
        if self.state == CSMAState.BACKOFF:
            if self.interface.status.name == "IDLE" and time >= self.nav_end:
                self.backoff_counter -= 1
                if self.backoff_counter <= 0:
                    self._send_rts()
        
        # Handle timeouts (simplified - in real implementation would use scheduled events)
        if (self.state == CSMAState.WAITING_CTS or 
            self.state == CSMAState.WAITING_ACK) and self.pending_packet:
            address, data = self.pending_packet
            # Simple timeout check (would be better with event scheduling)
            if time - self.time > 0.001:  # 1ms timeout
                self._transmission_failed()