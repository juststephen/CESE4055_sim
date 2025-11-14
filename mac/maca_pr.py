import enum
from collections import deque
import numpy as np
from medium.interface import MACInterface, NodeStatus
from .base import MAC

# --- Packet Types ---
class MacaPacketType(enum.Enum):
    RTS = 1  # Request to Send
    CTS = 2  # Clear to Send
    DATA = 3 # Data packet (with PR)

# --- Node States ---
class NodeState(enum.Enum):
    IDLE = 1      # Doing nothing
    BACKOFF = 2   # Waiting after a failed handshake
    WAIT_CTS = 3  # Sent RTS, waiting for CTS
    SEND_DATA = 4 # Received CTS, clear to send data
    BACKOFF_BROADCAST = 5

# --- Slot States ---
class SlotState(enum.Enum):
    IDLE = 1      # This slot is free
    RESERVED = 2  # We (or a 1-hop neighbor) are using this slot

# --- Packet Header Sizes (in bytes) ---
TYPE_BYTES = 1
ADDR_BYTES = 4  # Assuming 4-byte node IDs
SLOT_BYTES = 2  # For the slot index in the PR

# RTS Packet: [TYPE, SENDER_ID, DEST_ID]
RTS_HEADER_BYTES = TYPE_BYTES + ADDR_BYTES + ADDR_BYTES
# CTS Packet: [TYPE, SENDER_ID, DEST_ID]
CTS_HEADER_BYTES = TYPE_BYTES + ADDR_BYTES + ADDR_BYTES
# DATA Packet: [TYPE, SENDER_ID, DEST_ID, RESERVED_SLOT_INDEX]
DATA_HEADER_BYTES = TYPE_BYTES + ADDR_BYTES + ADDR_BYTES + SLOT_BYTES


class MAC_MACA_PR(MAC):
    """
    Implementation of MACA with Piggy-Backed Reservation (MACA/PR).
    """

    def __init__(self, interface: MACInterface, **kwargs) -> None:
        super().__init__(interface)
        
        # --- 1. Get Parameters ---
        self._bitrate: float = kwargs.get("bitrate", 2e6)
        
        # TDMA "PR" parameters
        self._n_slots: int = kwargs.get("n_slots", 20)      #  20 slots per frame
        self._t_slot: float = kwargs.get("t_slot", 1e-3)    #  1ms per slot
        self._frame_duration = self._n_slots * self._t_slot # Total frame duration
        
        # MACA timers
        # Time to wait for a CTS after sending RTS
        self._t_cts_timeout: float = kwargs.get("t_cts_timeout", 5e-4) 
        # Base contention window for backoff
        self._cw_base: int = kwargs.get("cw_base", 4)
        
        # --- 2. Node State ---
        self._buffer_out = deque(maxlen=kwargs.get("buf_len", 5))
        self._state = NodeState.IDLE
        self._state_timer: float = 0.0 # Timer for states like WAIT_CTS
        self._contention_window: int = self._cw_base
        
        # This is the "PR" schedule
        self._schedule: list[SlotState] = [SlotState.IDLE] * self._n_slots
        
        # Store pending packet info during handshake
        self._pending_addr: int = -1
        self._pending_data: bytes = b""
        
        # Track frame number to know when to clear the schedule
        self._current_frame: int = 0

    def send(self, address: int, data: bytes) -> None:
        
        if len(self._buffer_out) == self._buffer_out.maxlen:
            self._buffer_out.popleft() # Drop oldest packet if buffer is full
        self._buffer_out.append((address, data))

    def receive(self, data: bytes) -> None:
        
        if data is None:
            return # Ignore collisions/noise

        self.time = self.interface.time # Get current time
        
        try:
            # --- 1. Parse Packet Header ---
            packet_type = MacaPacketType(data[0])
            sender_id = int.from_bytes(data[TYPE_BYTES : TYPE_BYTES+ADDR_BYTES], 'big', signed=True)
            dest_id = int.from_bytes(data[TYPE_BYTES+ADDR_BYTES : TYPE_BYTES+ADDR_BYTES*2], 'big', signed=True)
        except Exception:
            return # Malformed packet

        # --- 2. Handle Packet based on Type ---
        
        # Get current TDMA slot for checking reservations
        current_slot = int((self.time % self._frame_duration) / self._t_slot)
        
        if packet_type == MacaPacketType.RTS:
            if (dest_id == self.interface.id and 
                self._state == NodeState.IDLE and
                self.interface.status == NodeStatus.IDLE and
                self._schedule[current_slot] == SlotState.IDLE):
                
                # Send CTS back to the sender
                cts_packet = self._create_cts_packet(sender_id)
                self.interface.antenna_transmit(cts_packet, bitrate=self._bitrate)
        elif packet_type == MacaPacketType.CTS:
            if (dest_id == self.interface.id and
                sender_id == self._pending_addr and
                self._state == NodeState.WAIT_CTS):
                
                # We won contention! Move to SEND_DATA state
                self._state = NodeState.SEND_DATA
                self._state_timer = self.time # Trigger immediate send in next tick
                self._contention_window = self._cw_base # Reset backoff
            
        elif packet_type == MacaPacketType.DATA:
            # Eavesdrop on all DATA packets to get the "PR" reservation
            
            # Parse the PR header
            try:
                slot_index = int.from_bytes(data[DATA_HEADER_BYTES-SLOT_BYTES : DATA_HEADER_BYTES], 'big')
            except Exception:
                return # Malformed PR header

            # Update our schedule.
            # This is how we avoid the 2-hop hidden terminal problem in the *future*
            if slot_index < self._n_slots:
                self._schedule[slot_index] = SlotState.RESERVED

            # If this data is for me, pass it up
            if dest_id == self.interface.id or dest_id == -1:
                payload = data[DATA_HEADER_BYTES:]
                # sender_id was parsed at the top!
                self.interface.routing_receive(payload, sender_id)

    def tick(self, time: float) -> None:
        """The 'heartbeat' of the protocol."""
        self.time = time
        
        # --- 0. Check for Frame Rollover ---
        # Calculate the current frame number
        frame_num = int(self.time // self._frame_duration)
        if frame_num > self._current_frame:
            # We have entered a new frame. Clear the reservation schedule.
            self._schedule = [SlotState.IDLE] * self._n_slots
            self._current_frame = frame_num
        
        # --- 1. Get current TDMA slot ---
        # This is for the "PR" part
        current_slot = int((self.time % self._frame_duration) / self._t_slot)
        
        # --- 2. Handle Timeouts ---
        if self._state == NodeState.WAIT_CTS and self.time > self._state_timer:
            # We sent an RTS, but got no CTS. Handshake failed!
            # Go to exponential backoff
            self._state = NodeState.BACKOFF
            self._contention_window *= 2 # Double backoff window
            backoff_slots = np.random.randint(0, self._contention_window)
            self._state_timer = self.time + backoff_slots * self._t_slot # Wait
            
        elif self._state == NodeState.BACKOFF and self.time > self._state_timer:
            # Backoff is over, return to IDLE
            self._state = NodeState.IDLE
        
        elif self._state == NodeState.BACKOFF_BROADCAST and self.time > self._state_timer:
            # Backoff timer expired. Check if channel is *still* idle.
            if self.interface.status == NodeStatus.IDLE:
                # Yes, send the broadcast
                data_packet = self._create_data_packet(
                    self._pending_addr, # This is -1
                    0, # No slot reservation
                    self._pending_data
                )
                self.interface.antenna_transmit(data_packet, bitrate=self._bitrate)
                
                # Clean up and return to IDLE
                self._pending_addr = -1
                self._pending_data = b""
                self._state = NodeState.IDLE
            else:
                # Channel became busy while we waited.
                # Wait one more slot time and try again.
                self._state_timer = self.time + self._t_slot
            
        # --- 3. Main State Machine ---
        
        if self._state == NodeState.IDLE:
            # Can we try to send something?
            if (len(self._buffer_out) > 0 and 
                self.interface.status == NodeStatus.IDLE and
                self._schedule[current_slot] == SlotState.IDLE):
                
                # Yes! Pop packet from buffer and start RTS/CTS handshake
                self._pending_addr, self._pending_data = self._buffer_out.popleft()
                
                # --- CHECK FOR BROADCAST ---
                if self._pending_addr == -1:
                    # It's a BROADCAST. Don't send. Go to BACKOFF.
                    self._state = NodeState.BACKOFF_BROADCAST
                    # Pick a random backoff in a small window
                    backoff_slots = np.random.randint(0, self._cw_base)
                    self._state_timer = self.time + backoff_slots * self._t_slot
                
                else:
                    # It's a UNICAST.
                    # Do the normal RTS/CTS handshake.
                    rts_packet = self._create_rts_packet(self._pending_addr)
                    self.interface.antenna_transmit(rts_packet, bitrate=self._bitrate)
                    
                    self._state = NodeState.WAIT_CTS
                    self._state_timer = self.time + self._t_cts_timeout

        elif self._state == NodeState.SEND_DATA:
            # We got a CTS! Send our DATA packet.
            
            # --- "PR" Logic: Find a future slot to reserve ---
            future_slot_index = (current_slot + 1) % self._n_slots
            for i in range(self._n_slots):
                idx = (current_slot + 1 + i) % self._n_slots
                if self._schedule[idx] == SlotState.IDLE:
                    future_slot_index = idx
                    break
            # We've picked 'future_slot_index'. Reserve it.
            self._schedule[future_slot_index] = SlotState.RESERVED
            
            # Create DATA packet with the PR
            data_packet = self._create_data_packet(
                self._pending_addr, 
                future_slot_index, 
                self._pending_data
            )
            self.interface.antenna_transmit(data_packet, bitrate=self._bitrate)
            
            # Clean up and return to IDLE
            self._pending_addr = -1
            self._pending_data = b""
            self._state = NodeState.IDLE
            

    
    def _create_rts_packet(self, dest_id: int) -> bytes:
        type_b = bytes([MacaPacketType.RTS.value])
        sender_b = self.interface.id.to_bytes(ADDR_BYTES, 'big', signed=True)
        dest_b = dest_id.to_bytes(ADDR_BYTES, 'big', signed=True)
        return type_b + sender_b + dest_b

    def _create_cts_packet(self, dest_id: int) -> bytes:
        type_b = bytes([MacaPacketType.CTS.value])
        sender_b = self.interface.id.to_bytes(ADDR_BYTES, 'big', signed=True)
        dest_b = dest_id.to_bytes(ADDR_BYTES, 'big', signed=True)
        return type_b + sender_b + dest_b

    def _create_data_packet(self, dest_id: int, slot_index: int, data: bytes) -> bytes:
        type_b = bytes([MacaPacketType.DATA.value])
        sender_b = self.interface.id.to_bytes(ADDR_BYTES, 'big', signed=True)
        dest_b = dest_id.to_bytes(ADDR_BYTES, 'big', signed=True)
        slot_b = slot_index.to_bytes(SLOT_BYTES, 'big')
        
        header = type_b + sender_b + dest_b + slot_b
        return header + data