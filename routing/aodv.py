import enum
from collections import deque, defaultdict
from dataclasses import dataclass

from medium.interface import RoutingInterface
from .base import Routing

# --- 1. AODV Packet Types ---
class AodvPacketType(enum.Enum):
    RREQ = 1  # Route Request
    RREP = 2  # Route Reply
    DATA = 3  # Application Data

# --- 2. AODV Packet Header Sizes (in bytes) ---
# Using fixed 4-byte IDs and 2-byte counters.
TYPE_BYTES = 1
ID_BYTES = 4
SEQ_NUM_BYTES = 4
HOP_COUNT_BYTES = 2

# RREQ: [TYPE, RREQ_ID, ORIGIN_ID, ORIGIN_SEQ, TARGET_ID, HOP_COUNT]
RREQ_HEADER_BYTES = TYPE_BYTES + ID_BYTES + ID_BYTES + SEQ_NUM_BYTES + ID_BYTES + HOP_COUNT_BYTES
# RREP: [TYPE, ORIGIN_ID, TARGET_ID, TARGET_SEQ, HOP_COUNT]
RREP_HEADER_BYTES = TYPE_BYTES + ID_BYTES + ID_BYTES + SEQ_NUM_BYTES + HOP_COUNT_BYTES
# DATA: [TYPE, FINAL_DEST_ID]
DATA_HEADER_BYTES = TYPE_BYTES + ID_BYTES


# --- 3. AODV Constants ---
ROUTE_LIFETIME = 5.0       # Time in seconds a route is considered "valid"
RREQ_TIMEOUT = 1.0         # Time to wait before re-sending RREQ
RREQ_ID_LIFETIME = 10.0     # Time to remember a seen RREQ ID
MAX_DATA_BUFFER_SIZE = 20   # Max packets to buffer while waiting for a route
RREQ_RETRY_LIMIT = 5       # Max number of retries before dropping
RREQ_BACKOFF_FACTOR = 2    # Multiplier for timeout (2 = 1s, 2s, 4s, 8s...)

# --- 4. Route Table Entry ---
@dataclass
class RouteTableEntry:
    dest_id: int
    next_hop: int          # The *neighbor* to send to
    hop_count: int
    dest_seq_num: int      # Last known sequence number for the destination
    expiration_time: float # When this route entry becomes invalid

class RoutingAODV(Routing):
    """
    simplified Ad hoc On-demand Distance Vector (AODV) routing protocol.
    """
    
    def __init__(self, interface: RoutingInterface, **kwargs) -> None:
        super().__init__(interface)
        
        # --- AODV State ---
        # This node's own sequence number, incremented for RREPs
        self._my_seq_num: int = 0
        # This node's RREQ ID, incremented for new route discoveries
        self._rreq_id: int = 0
        
        # Stores routes we know: {dest_id: RouteTableEntry}
        self._route_table: dict[int, RouteTableEntry] = {}
        
        # Buffers data for destinations while we find a route
        # {dest_id: deque([(data), (data), ...])}
        self._data_buffer: dict[int, deque] = defaultdict(deque)
        
        # Tracks pending RREQs: {dest_id: (expiration_time, retry_count)}
        self._pending_rreqs: dict[int, tuple[float, int]] = {}
        
        # Cache of seen RREQs to prevent broadcast storms
        # {(originator_id, rreq_id): expiration_time}
        self._seen_rreqs: dict[tuple[int, int], float] = {}
        
        # Get parameters from kwargs if available
        self._route_lifetime = kwargs.get("route_lifetime", ROUTE_LIFETIME)
        self._rreq_timeout_base = kwargs.get("rreq_timeout", RREQ_TIMEOUT) # Renamed
        self._rreq_id_lifetime = kwargs.get("rreq_id_lifetime", RREQ_ID_LIFETIME)
        self._rreq_retry_limit = kwargs.get("rreq_retry_limit", RREQ_RETRY_LIMIT)
        self._rreq_backoff_factor = kwargs.get("rreq_backoff_factor", RREQ_BACKOFF_FACTOR)
        
    def send(self, address: int, data: bytes) -> None:
        """
        Called by the application to send data to a final address.
        """
        self.time = self.interface.time # Get current time
        
        # Look for a valid route in our table
        route = self._get_valid_route(address)
        
        if route:
            # --- 1. Route Found ---
            self._send_data_packet(address, route.next_hop, data)
        
        else:
            # --- 2. No Route Found ---
            # Buffer the data
            if len(self._data_buffer[address]) < MAX_DATA_BUFFER_SIZE:
                self._data_buffer[address].append(data)
            
            # Initiate route discovery, if one isn't already pending
            if address not in self._pending_rreqs:
                self._initiate_rreq(address)
    
    def receive(self, data: bytes, sender_id: int) -> None:
        """
        Called by the MAC layer when it receives ANY packet.
        We must parse the AODV header to know what to do.
        """
        self.time = self.interface.time # Get current time
        
        try:
            packet_type = AodvPacketType(data[0])
            payload = data[TYPE_BYTES:]
        except (IndexError, ValueError):
            return # Malformed packet
            
        # --- 2. Handle Packet based on Type ---
        if packet_type == AodvPacketType.RREQ:
            self._handle_rreq(payload, sender_id)
        elif packet_type == AodvPacketType.RREP:
            self._handle_rrep(payload, sender_id)
        elif packet_type == AodvPacketType.DATA:
            self._handle_data(payload, sender_id)

    def tick(self, time: float) -> None:
        """Heartbeat for managing timeouts."""
        self.time = time
        
        # Proactively remove routes that are no longer valid.
        expired_routes = [
            dest_id for dest_id, route in self._route_table.items()
            if self.time >= route.expiration_time
        ]
        for dest_id in expired_routes:
            # print(f"Node {self.interface.id}: Route to {dest_id} expired.")
            del self._route_table[dest_id]
        
        # --- 1. Check for pending RREQs that timed out ---
        timed_out_rreqs = [
            (dest_id, retry_count) for dest_id, (expiry, retry_count)
            in self._pending_rreqs.items()
            if self.time > expiry
        ]
        for dest_id, retry_count in timed_out_rreqs:
            if retry_count >= self._rreq_retry_limit:
                # --- RREQ Failed Permanently ---
                # Drop all buffered data for this destination
                if dest_id in self._data_buffer:
                    # Optional: Log this failure
                    # print(f"Node {self.interface.id}: RREQ for {dest_id} failed. Dropping data.")
                    del self._data_buffer[dest_id]
                del self._pending_rreqs[dest_id]
            
            else:
                # --- RREQ Timed Out, Retry ---
                # Re-initiate with an incremented retry count
                del self._pending_rreqs[dest_id] # Remove old entry
                self._initiate_rreq(dest_id, retry_count + 1)
            
        # --- 2. Purge very old seen RREQs ---
        old_rreqs = [
            key for key, expiry in self._seen_rreqs.items()
            if self.time > expiry
        ]
        for key in old_rreqs:
            del self._seen_rreqs[key]

    # --- AODV Helper Functions ---

    def _get_valid_route(self, dest_id: int) -> RouteTableEntry | None:
        """Gets a route from the table if it exists and hasn't expired."""
        route = self._route_table.get(dest_id)
        if route and self.time < route.expiration_time:
            # Valid route exists
            return route
        elif route:
            # Route expired, delete it
            del self._route_table[dest_id]
        return None

    def _create_or_update_route(self, dest_id, next_hop, hop_count, dest_seq_num, expiration_time):
        """Intelligently updates the route table based on AODV rules."""
        existing_route = self._get_valid_route(dest_id)
        
        # Rule: A new sequence number is *always* preferred.
        if (not existing_route or
            dest_seq_num > existing_route.dest_seq_num or
            (dest_seq_num == existing_route.dest_seq_num and hop_count < existing_route.hop_count)):
            
            self._route_table[dest_id] = RouteTableEntry(
                dest_id=dest_id,
                next_hop=next_hop,
                hop_count=hop_count,
                dest_seq_num=dest_seq_num,
                expiration_time=expiration_time
            )

    def _initiate_rreq(self, target_id: int, retry_count: int = 0):
        """Broadcasts an RREQ to find a target node."""
        self._rreq_id += 1 # New RREQ_ID
        
        # [TYPE, RREQ_ID, ORIGIN_ID, ORIGIN_SEQ, TARGET_ID, HOP_COUNT]
        header = b''.join([
            bytes([AodvPacketType.RREQ.value]),
            self._rreq_id.to_bytes(ID_BYTES, 'big'),
            self.interface.id.to_bytes(ID_BYTES, 'big', signed=True),
            self._my_seq_num.to_bytes(SEQ_NUM_BYTES, 'big'),
            target_id.to_bytes(ID_BYTES, 'big', signed=True),
            (0).to_bytes(HOP_COUNT_BYTES, 'big') # Hop Count = 0
        ])
        
        # Calculate timeout for this attempt
        current_timeout = self._rreq_timeout_base * (self._rreq_backoff_factor ** retry_count)
        
        # Mark RREQ as pending
        self._pending_rreqs[target_id] = (self.time + current_timeout, retry_count)
        self._seen_rreqs[(self.interface.id, self._rreq_id)] = self.time + self._rreq_id_lifetime
        
        self.interface.MAC_send(-1, header) # Broadcast

    def _handle_rreq(self, payload: bytes, rreq_sender_id: int):
        """Processes a received RREQ packet."""
        try:
            rreq_id = int.from_bytes(payload[0:ID_BYTES], 'big')
            origin_id = int.from_bytes(payload[ID_BYTES:ID_BYTES*2], 'big', signed=True)
            origin_seq = int.from_bytes(payload[ID_BYTES*2:ID_BYTES*2+SEQ_NUM_BYTES], 'big')
            target_id = int.from_bytes(payload[ID_BYTES*2+SEQ_NUM_BYTES:ID_BYTES*3+SEQ_NUM_BYTES], 'big', signed=True)
            hop_count = int.from_bytes(payload[ID_BYTES*3+SEQ_NUM_BYTES:ID_BYTES*3+SEQ_NUM_BYTES+HOP_COUNT_BYTES], 'big')
        except Exception:
            return # Malformed

        # --- 1. Check if we've seen this RREQ ---
        if (origin_id, rreq_id) in self._seen_rreqs:
            return # Duplicate, drop
        self._seen_rreqs[(origin_id, rreq_id)] = self.time + self._rreq_id_lifetime

        # --- 2. Create/Update Reverse Path ---
        # This is CRITICAL. We now know how to get back to the origin.
        self._create_or_update_route(
            dest_id=origin_id,
            next_hop=rreq_sender_id, # This is why we needed the change!
            hop_count=hop_count + 1,
            dest_seq_num=origin_seq,
            expiration_time=self.time + self._route_lifetime
        )

        # --- 3. Check if RREQ is for me ---
        if target_id == self.interface.id:
            # It's for me! Send an RREP.
            self._my_seq_num += 1 # Increment my sequence number
            
            # [TYPE, ORIGIN_ID, TARGET_ID, TARGET_SEQ, HOP_COUNT]
            rrep_packet = b''.join([
                bytes([AodvPacketType.RREP.value]),
                origin_id.to_bytes(ID_BYTES, 'big', signed=True),
                self.interface.id.to_bytes(ID_BYTES, 'big', signed=True),
                self._my_seq_num.to_bytes(SEQ_NUM_BYTES, 'big'),
                (0).to_bytes(HOP_COUNT_BYTES, 'big') # Hops from me to me = 0
            ])
            
            # Send RREP UNICAST back to the origin via the reverse path.
            # We just created the route, so _get_valid_route *should* find it.
            route_to_origin = self._get_valid_route(origin_id)
            if route_to_origin:
                self.interface.MAC_send(route_to_origin.next_hop, rrep_packet)
            
        else:
            # --- 4. Not for me, forward it ---
            # (We skip "intermediate node reply" for simplicity)
            new_hop_count = hop_count + 1
            
            # Re-build RREQ packet with new hop count
            forward_rreq = b''.join([
                bytes([AodvPacketType.RREQ.value]),
                rreq_id.to_bytes(ID_BYTES, 'big'),
                origin_id.to_bytes(ID_BYTES, 'big', signed=True),
                origin_seq.to_bytes(SEQ_NUM_BYTES, 'big'),
                target_id.to_bytes(ID_BYTES, 'big', signed=True),
                new_hop_count.to_bytes(HOP_COUNT_BYTES, 'big')
            ])
            # Re-broadcast RREQ
            self.interface.MAC_send(-1, forward_rreq)

    def _handle_rrep(self, payload: bytes, rrep_sender_id: int):
        """Processes a received RREP packet."""
        try:
            origin_id = int.from_bytes(payload[0:ID_BYTES], 'big', signed=True)
            target_id = int.from_bytes(payload[ID_BYTES:ID_BYTES*2], 'big', signed=True)
            target_seq = int.from_bytes(payload[ID_BYTES*2:ID_BYTES*2+SEQ_NUM_BYTES], 'big')
            hop_count = int.from_bytes(payload[ID_BYTES*2+SEQ_NUM_BYTES:ID_BYTES*2+SEQ_NUM_BYTES+HOP_COUNT_BYTES], 'big')
        except Exception:
            return # Malformed
        
        # --- 1. Create/Update Forward Path ---
        # We now know how to get to the target
        new_hop_count = hop_count + 1
        self._create_or_update_route(
            dest_id=target_id,
            next_hop=rrep_sender_id, # This is why we needed the change!
            hop_count=new_hop_count,
            dest_seq_num=target_seq,
            expiration_time=self.time + self._route_lifetime
        )

        # --- 2. Check if RREP is for me ---
        if origin_id == self.interface.id:
            # This RREP is for me! The route is established.
            # Remove from pending RREQs
            if target_id in self._pending_rreqs:
                del self._pending_rreqs[target_id]
            
            route = self._get_valid_route(target_id)
            if route:
                # We have a valid route, send all buffered data
                while self._data_buffer[target_id]:
                    data = self._data_buffer[target_id].popleft()
                    self._send_data_packet(target_id, route.next_hop, data)
        
        else:
            # --- 3. Not for me, forward it ---
            # Re-build RREP with updated hop count
            forward_rrep = b''.join([
                bytes([AodvPacketType.RREP.value]),
                origin_id.to_bytes(ID_BYTES, 'big', signed=True),
                target_id.to_bytes(ID_BYTES, 'big', signed=True),
                target_seq.to_bytes(SEQ_NUM_BYTES, 'big'),
                new_hop_count.to_bytes(HOP_COUNT_BYTES, 'big')
            ])
            
            # Send RREP UNICAST back to the origin
            route_to_origin = self._get_valid_route(origin_id)
            if route_to_origin:
                self.interface.MAC_send(route_to_origin.next_hop, forward_rrep)

    def _handle_data(self, payload: bytes, data_sender_id: int):
        """Processes a received DATA packet."""
        try:
            # Data Packet: [TYPE, FINAL_DEST_ID, PAYLOAD]
            final_dest_id = int.from_bytes(payload[0:ID_BYTES], 'big', signed=True)
            app_payload = payload[ID_BYTES:]
        except Exception:
            return # Malformed
            
        if final_dest_id == self.interface.id:
            # --- 1. Data is for me ---
            self.interface.receive(app_payload)
        
        else:
            # --- 2. Data is not for me, forward it ---
            route = self._get_valid_route(final_dest_id)
            if route:
                self._send_data_packet(final_dest_id, route.next_hop, app_payload)
            else:
                # No route.
                # A full implementation would buffer and send RREQ.
                # We will just drop it for simplicity.
                pass 
                
    def _send_data_packet(self, final_dest_id: int, next_hop: int, data: bytes):
        """Wraps app data in an AODV DATA header and sends to next hop."""
        
        # Packet: [TYPE, FINAL_DEST_ID, PAYLOAD]
        packet = b''.join([
            bytes([AodvPacketType.DATA.value]),
            final_dest_id.to_bytes(ID_BYTES, 'big', signed=True),
            data
        ])
        
        # Send to the *next hop* (not the final destination)
        self.interface.MAC_send(next_hop, packet)