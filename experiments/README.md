# Experiments

This folder contains automated testing infrastructure for running systematic network simulation experiments and analyzing results.

## Overview

The experiments framework enables reproducible testing of different MAC protocols, routing protocols, channel conditions, and traffic loads. Results are automatically collected, saved as CSV files, and visualized through comparative plots.

## Structure
```
experiments/
├── __init__.py          # Package initialization
├── runner.py            # Core experiment execution engine
├── scenarios.py         # Predefined test scenario configurations
├── analysis.py          # Results analysis and visualization
└── run_all.py          # Main script to run all experiments
```

## Files

### `runner.py`
Contains the `ExperimentRunner` class that:
- Manages experiment execution
- Resets simulation state between runs
- Creates node topologies (grid with randomization)
- Generates traffic according to specified data rates
- Records metrics at regular intervals
- Saves results to CSV files

### `scenarios.py`
Defines four categories of test scenarios:
- **MAC Comparison**: ALOHA vs CSMA/CA across different node counts
- **Routing Comparison**: Direct routing vs Flooding
- **Channel Conditions**: Varying path loss exponent and fading
- **Load Testing**: Different traffic data rates

Each scenario is configured with:
- Network size (number of nodes)
- Protocol selection (MAC + Routing)
- Physical layer parameters
- Traffic characteristics
- Simulation duration

### `analysis.py`
Contains the `ResultsAnalyzer` class for:
- Loading experiment timeseries and summary data
- Generating comparative plots
- Creating summary tables across experiment groups
- Exporting publication-ready figures

### `run_all.py`
Main execution script that:
1. Instantiates the experiment runner
2. Loads all scenario configurations
3. Runs each experiment sequentially
4. Saves individual results
5. Generates comparative analyses and plots

## Usage

### Run All Experiments

From the project root directory:
```bash
python -m experiments.run_all
```

This will:
- Run all 24 predefined scenarios (takes 1-2 hours with default settings)
- Save results to `results/` directory
- Generate summary CSVs and comparison plots

### Run Individual Scenario Groups

Modify `run_all.py` to run specific scenario groups:
```python
from experiments.runner import ExperimentRunner
from experiments.scenarios import get_mac_comparison_scenarios

runner = ExperimentRunner(output_dir="results")

# Run only MAC comparison experiments
for config in get_mac_comparison_scenarios():
    collector = runner.run_experiment(config, seed=42)
    runner.save_experiment(collector)
```

### Create Custom Scenarios

Add custom scenarios in `scenarios.py`:
```python
from metrics import SimulationConfig

def get_custom_scenarios() -> list[SimulationConfig]:
    scenarios = []
    scenarios.append(SimulationConfig(
        name="custom_test",
        n_nodes=50,
        mac_protocol="csma_ca",
        routing_protocol="flooding",
        path_loss_exp=2.5,
        fading_std=2.0,
        noise_floor_dbm=-100,
        sinr_threshold_db=20,
        data_rate=1e5,
        step_size=1e-7,
        duration=0.5  # Shorter for quick testing
    ))
    return scenarios
```

## Output Structure

Results are organized as:
```
results/
├── mac_aloha_n32/
│   ├── timeseries.csv       # Time-series metrics
│   └── summary.csv          # Configuration and final metrics
├── mac_csma_n32/
│   ├── timeseries.csv
│   └── summary.csv
├── ...
├── mac_comparison.png       # Comparative visualization
├── mac__summary.csv         # Aggregated MAC experiment results
├── routing__summary.csv     # Aggregated routing results
├── channel__summary.csv     # Aggregated channel results
└── load__summary.csv        # Aggregated load test results
```

### Timeseries CSV Format

| time | success_rate | avg_delay | avg_speed | messages_sent | messages_received | collision_count |
|------|--------------|-----------|-----------|---------------|-------------------|-----------------|
| 0.001 | 45.2 | 0.0012 | 425301.2 | 100 | 45 | 1523 |
| 0.002 | 46.8 | 0.0013 | 431245.7 | 203 | 95 | 3102 |
| ... | ... | ... | ... | ... | ... | ... |

### Summary CSV Format

Contains configuration parameters and final metrics for each experiment.

## Performance Optimization

To speed up experiments for testing:

1. **Reduce node counts** in `scenarios.py`:
```python
   for n_nodes in [16, 32]:  # Instead of [32, 64]
```

2. **Shorten simulation duration**:
```python
   duration=0.1  # Instead of 1.0
```

3. **Increase step size** (less accurate):
```python
   step_size=1e-6  # Instead of 1e-7
```

4. **Test single scenario**:
```python
   scenarios = get_mac_comparison_scenarios()[:1]
```

## Metrics Collected

- **Success Rate**: Percentage of messages successfully delivered end-to-end
- **Average Delay**: Mean time from transmission to reception
- **Average Speed**: Mean effective propagation speed (distance/delay)
- **Messages Sent**: Total messages originated
- **Messages Received**: Total messages successfully delivered
- **Collision Count**: Number of transmission collisions detected

## Dependencies

- `numpy`: Random number generation and array operations
- `pandas`: Data loading and manipulation
- `matplotlib`: Result visualization
- `pathlib`: File system operations

## Notes

- Random seed (42) ensures reproducibility across runs
- Static counters are reset between experiments to prevent cross-contamination
- Node positions use grid layout with randomization for realistic topology
- Traffic generation follows Poisson process (exponential inter-arrival times)