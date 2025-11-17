import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List

class ResultsAnalyzer:
    """Analyze and visualize experiment results."""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        
    def load_experiment(self, name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load timeseries and summary for an experiment."""
        exp_dir = self.results_dir / name
        timeseries = pd.read_csv(exp_dir / "timeseries.csv")
        summary = pd.read_csv(exp_dir / "summary.csv", index_col=0)
        return timeseries, summary
    
    def compare_mac_protocols(self, output_file: str = "mac_comparison.png"):
        """Compare MAC protocols across node counts."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        node_counts = [32, 64]
        
        for n in node_counts:
            aloha_ts, _ = self.load_experiment(f"mac_aloha_n{n}")
            csma_ts, _ = self.load_experiment(f"mac_csma_n{n}")
            
            # Success rate
            axes[0, 0].plot(aloha_ts['time'], aloha_ts['success_rate'], 
                           label=f'ALOHA (n={n})', linestyle='--')
            axes[0, 0].plot(csma_ts['time'], csma_ts['success_rate'],
                           label=f'CSMA/CA (n={n})')
            
            # Delay
            axes[0, 1].plot(aloha_ts['time'], aloha_ts['avg_delay'],
                           label=f'ALOHA (n={n})', linestyle='--')
            axes[0, 1].plot(csma_ts['time'], csma_ts['avg_delay'],
                           label=f'CSMA/CA (n={n})')
            
            # Collisions
            axes[1, 0].plot(aloha_ts['time'], aloha_ts['collision_count'],
                           label=f'ALOHA (n={n})', linestyle='--')
            axes[1, 0].plot(csma_ts['time'], csma_ts['collision_count'],
                           label=f'CSMA/CA (n={n})')
            
            # Messages received
            axes[1, 1].plot(aloha_ts['time'], aloha_ts['messages_received'],
                           label=f'ALOHA (n={n})', linestyle='--')
            axes[1, 1].plot(csma_ts['time'], csma_ts['messages_received'],
                           label=f'CSMA/CA (n={n})')
        
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Success Rate (%)')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Average Delay (s)')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        axes[0, 1].set_yscale('log')
        
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Collision Count')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Messages Received')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / output_file, dpi=300)
        print(f"Saved: {output_file}")
    
    def create_summary_table(self, experiment_prefix: str) -> pd.DataFrame:
        """Create summary table for experiments with common prefix."""
        summaries = []
        
        for exp_dir in sorted(self.results_dir.glob(f"{experiment_prefix}*")):
            if exp_dir.is_dir():
                _, summary = self.load_experiment(exp_dir.name)
                summary['experiment'] = exp_dir.name
                summaries.append(summary)
        
        if summaries:
            df = pd.concat(summaries, axis=1).T
            df.to_csv(self.results_dir / f"{experiment_prefix}_summary.csv")
            return df
        return pd.DataFrame()