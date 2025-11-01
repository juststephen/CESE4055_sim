import numpy as np
from medium import Medium, Node2D
from mac.csma_ca_rts_cts import MACCsmaCaRtsCts
from routing.none import RoutingNone

def test_rts_cts():
    """Test RTS/CTS implementation with hidden terminal scenario."""
    
    # Create medium
    medium = Medium[Node2D]()
    
    # Create nodes in a line: Node0 -- Node1 -- Node2
    # Node0 and Node2 can't hear each other (hidden terminals)
    nodes = [
        Node2D(0, 0, MACCsmaCaRtsCts, RoutingNone),    # Node 0
        Node2D(50, 0, MACCsmaCaRtsCts, RoutingNone),   # Node 1 (center)
        Node2D(100, 0, MACCsmaCaRtsCts, RoutingNone),  # Node 2
    ]
    
    # Add nodes to medium
    for node in nodes:
        medium.add_node(node)
    
    # Set transmission range so Node0 and Node2 can't hear each other directly
    medium.search_radius = 60  # meters
    medium.path_loss_exp = 3.0  # Higher path loss for quicker signal degradation
    
    print("Starting RTS/CTS test with hidden terminals...")
    print("Node positions: 0(0,0) -- 1(50,0) -- 2(100,0)")
    print("Node0 and Node2 cannot hear each other directly")
    
    # Test 1: Node0 sends to Node1 (should use RTS/CTS)
    print("\n=== Test 1: Node0 → Node1 ===")
    nodes[0].send(1, b"Hello from Node0 to Node1")
    
    # Run simulation for a bit
    for _ in range(100):
        medium.step(0.0001)  # 0.1ms steps
    
    # Test 2: Node2 sends to Node1 while Node0 is transmitting
    print("\n=== Test 2: Node2 → Node1 (potential collision) ===")
    nodes[2].send(1, b"Hello from Node2 to Node1")
    
    # Run simulation more
    for _ in range(200):
        medium.step(0.0001)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_rts_cts()