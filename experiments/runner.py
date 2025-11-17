import numpy as np
from pathlib import Path
from typing import Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mac import MACAloha, MAC_CSMA_CA
from medium import Medium, Node2D, Messages
from routing import RoutingNone, RoutingFlooding
from metrics import MetricsCollector, SimulationConfig

class ExperimentRunner:
    """Runs automated simulation experiments."""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_experiment(
        self,
        config: SimulationConfig,
        *,
        snapshot_interval: float = 1e-3,
        seed: int | None = None
    ) -> MetricsCollector:
        """Run a single experiment with given configuration."""
        
        if seed is not None:
            np.random.seed(seed)
            
        # Reset static counters
        from medium.node import Node
        Node._next_id = 0
        Messages._messages.clear()
        Messages._broadcasts.clear()
        Messages._sent_count = 0
        Messages._received_count = 0
        Messages._total_delay = 0
        Messages._total_speed = 0
        
        # Create medium
        medium = Medium[Node2D]()
        medium.path_loss_exp = config.path_loss_exp
        medium.fading_std = config.fading_std
        medium.noise_floor_dbm = config.noise_floor_dbm
        medium.sinr_threshold_db = config.sinr_threshold_db
        
        # Select protocols
        mac_class = {
            'aloha': MACAloha,
            'csma_ca': MAC_CSMA_CA
        }[config.mac_protocol.lower()]
        
        routing_class = {
            'none': RoutingNone,
            'flooding': RoutingFlooding
        }[config.routing_protocol.lower()]
        
        # Create nodes in a grid or random positions
        grid_size = int(np.ceil(np.sqrt(config.n_nodes)))
        spacing = 1000  # meters
        
        for i in range(config.n_nodes):
            x = (i % grid_size) * spacing
            y = (i // grid_size) * spacing
            # Add some randomness
            x += np.random.uniform(-spacing/4, spacing/4)
            y += np.random.uniform(-spacing/4, spacing/4)
            
            node = Node2D(
                x, y,
                mac_class,
                routing_class,
                mac_param=config.extra_params.get('mac_param', {}),
                routing_param=config.extra_params.get('routing_param', {})
            )
            medium.add_node(node)
        
        # Create metrics collector
        collector = MetricsCollector(config)
        
        # Run simulation
        current_time = 0.0
        next_snapshot = snapshot_interval
        next_message = 0.0
        msg_interval = 33 / config.data_rate  # Average message length / data rate
        
        print(f"Running: {config.name}")
        
        while current_time < config.duration:
            # Step simulation
            medium.step(config.step_size)
            current_time = medium.time
            
            # Generate traffic
            if current_time >= next_message:
                i = np.random.randint(0, len(medium.nodes))
                j = i
                while j == i:
                    j = np.random.randint(0, len(medium.nodes))
                
                node = medium.nodes[i]
                other = medium.nodes[j]
                dist = np.sqrt((other.x - node.x)**2 + (other.y - node.y)**2)
                
                msg = f"Sender:{i}, Code:{int(10*np.random.rand())}, Dist:{dist:.2e}"
                node.send(j, msg.encode())
                
                next_message = current_time + np.random.exponential(msg_interval)
            
            # Record snapshot
            if current_time >= next_snapshot:
                collector.collision_count = medium.collision_count
                collector.record_snapshot(
                    current_time,
                    Messages.get_success_rate(),
                    Messages.get_avg_delay(),
                    Messages.get_avg_speed(),
                    Messages._sent_count,
                    Messages._received_count
                )
                next_snapshot += snapshot_interval
        
        print(f"Completed: {config.name}")
        print(f"  Success rate: {Messages.get_success_rate():.1f}%")
        print(f"  Avg delay: {Messages.get_avg_delay():.2e}s")
        print(f"  Collisions: {medium.collision_count}")
        
        return collector
    
    def save_experiment(self, collector: MetricsCollector) -> None:
        """Save experiment results."""
        exp_dir = self.output_dir / collector.config.name
        exp_dir.mkdir(parents=True, exist_ok=True)
        
        collector.save_timeseries(exp_dir / "timeseries.csv")
        collector.save_summary(exp_dir / "summary.csv")