import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class MetricsSnapshot:
    """Single point-in-time metrics snapshot."""
    time: float 
    success_rate: float
    avg_delay: float
    avg_speed: float
    messages_sent: int
    messages_received: int
    collision_count: int = 0
    
@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""
    name: str
    n_nodes: int
    mac_protocol: str
    routing_protocol: str
    path_loss_exp: float
    fading_std: float
    noise_floor_dbm: float
    sinr_threshold_db: float
    data_rate: float
    step_size: float
    duration: float
    extra_params: dict[str, Any] = field(default_factory=dict)
    
class MetricsCollector:
    """Collects metrics throughout simulation."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.snapshots: list[MetricsSnapshot] = []
        self.collision_count = 0
        
    def record_snapshot(
        self,
        time: float,
        success_rate: float,
        avg_delay: float,
        avg_speed: float,
        messages_sent: int,
        messages_received: int
    ) -> None:
        """Record a metrics snapshot."""
        snapshot = MetricsSnapshot(
            time=time,
            success_rate=success_rate,
            avg_delay=avg_delay,
            avg_speed=avg_speed,
            messages_sent=messages_sent,
            messages_received=messages_received,
            collision_count=self.collision_count
        )
        self.snapshots.append(snapshot)
        
    def save_timeseries(self, filepath: str | Path) -> None:
        """Save time-series metrics to CSV."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'time', 'success_rate', 'avg_delay', 'avg_speed',
                'messages_sent', 'messages_received', 'collision_count'
            ])
            for snap in self.snapshots:
                writer.writerow([
                    snap.time, snap.success_rate, snap.avg_delay,
                    snap.avg_speed, snap.messages_sent,
                    snap.messages_received, snap.collision_count
                ])
                
    def save_summary(self, filepath: str | Path) -> None:
        """Save configuration and final metrics summary."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        final = self.snapshots[-1] if self.snapshots else None
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Parameter', 'Value'])
            
            # Configuration
            writer.writerow(['config_name', self.config.name])
            writer.writerow(['n_nodes', self.config.n_nodes])
            writer.writerow(['mac_protocol', self.config.mac_protocol])
            writer.writerow(['routing_protocol', self.config.routing_protocol])
            writer.writerow(['path_loss_exp', self.config.path_loss_exp])
            writer.writerow(['fading_std', self.config.fading_std])
            writer.writerow(['noise_floor_dbm', self.config.noise_floor_dbm])
            writer.writerow(['sinr_threshold_db', self.config.sinr_threshold_db])
            writer.writerow(['data_rate', self.config.data_rate])
            writer.writerow(['step_size', self.config.step_size])
            writer.writerow(['duration', self.config.duration])
            
            # Extra parameters
            for key, value in self.config.extra_params.items():
                writer.writerow([f'extra_{key}', value])
            
            # Final metrics
            if final:
                writer.writerow(['final_success_rate', final.success_rate])
                writer.writerow(['final_avg_delay', final.avg_delay])
                writer.writerow(['final_avg_speed', final.avg_speed])
                writer.writerow(['final_messages_sent', final.messages_sent])
                writer.writerow(['final_messages_received', final.messages_received])
                writer.writerow(['final_collision_count', final.collision_count])