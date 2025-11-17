import sys
from pathlib import Path

# Ensure parent directory is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiments.runner import ExperimentRunner
from experiments.scenarios import (
    get_mac_comparison_scenarios,
    get_routing_comparison_scenarios,
    get_channel_condition_scenarios,
    get_load_scenarios
)
from experiments.analysis import ResultsAnalyzer

def main():
    runner = ExperimentRunner(output_dir="results")
    
    # Get all scenarios
    all_scenarios = []
    all_scenarios.extend(get_mac_comparison_scenarios())
    all_scenarios.extend(get_routing_comparison_scenarios())
    all_scenarios.extend(get_channel_condition_scenarios())
    all_scenarios.extend(get_load_scenarios())
    
    # Run all experiments
    for config in all_scenarios:
        collector = runner.run_experiment(config, seed=42)
        runner.save_experiment(collector)
    
    # Analyze results
    analyzer = ResultsAnalyzer(results_dir="results")
    analyzer.compare_mac_protocols()
    analyzer.create_summary_table("mac_")
    analyzer.create_summary_table("routing_")
    analyzer.create_summary_table("channel_")
    analyzer.create_summary_table("load_")
    
    print("\nAll experiments completed!")
    print(f"Results saved in: {runner.output_dir}")

if __name__ == "__main__":
    main()