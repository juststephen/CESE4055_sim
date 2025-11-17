from metrics.collector import SimulationConfig

def get_mac_comparison_scenarios() -> list[SimulationConfig]:
    """Compare ALOHA vs CSMA/CA."""
    scenarios = []
    
    for n_nodes in [32, 64]:
        # ALOHA
        scenarios.append(SimulationConfig(
            name=f"mac_aloha_n{n_nodes}",
            n_nodes=n_nodes,
            mac_protocol="aloha",
            routing_protocol="none",
            path_loss_exp=2.5,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
        
        # CSMA/CA
        scenarios.append(SimulationConfig(
            name=f"mac_csma_n{n_nodes}",
            n_nodes=n_nodes,
            mac_protocol="csma_ca",
            routing_protocol="none",
            path_loss_exp=2.5,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
    
    return scenarios

def get_routing_comparison_scenarios() -> list[SimulationConfig]:
    """Compare routing protocols."""
    scenarios = []
    
    for n_nodes in [32, 64]:
        # No routing
        scenarios.append(SimulationConfig(
            name=f"routing_none_n{n_nodes}",
            n_nodes=n_nodes,
            mac_protocol="csma_ca",
            routing_protocol="none",
            path_loss_exp=2.5,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
        
        # Flooding
        scenarios.append(SimulationConfig(
            name=f"routing_flooding_n{n_nodes}",
            n_nodes=n_nodes,
            mac_protocol="csma_ca",
            routing_protocol="flooding",
            path_loss_exp=2.5,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
    
    return scenarios

def get_channel_condition_scenarios() -> list[SimulationConfig]:
    """Test different channel conditions."""
    scenarios = []
    
    for path_loss in [2.0, 2.5, 3.0, 3.5]:
        scenarios.append(SimulationConfig(
            name=f"channel_pathloss{path_loss:.1f}",
            n_nodes=32,
            mac_protocol="csma_ca",
            routing_protocol="flooding",
            path_loss_exp=path_loss,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
    
    for fading in [1.0, 2.0, 3.0]:
        scenarios.append(SimulationConfig(
            name=f"channel_fading{fading:.1f}",
            n_nodes=32,
            mac_protocol="csma_ca",
            routing_protocol="flooding",
            path_loss_exp=2.5,
            fading_std=fading,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=1e5,
            step_size=1e-7,
            duration=1.0
        ))
    
    return scenarios

def get_load_scenarios() -> list[SimulationConfig]:
    """Test different traffic loads."""
    scenarios = []
    
    for data_rate in [1e4, 5e4, 1e5, 2e5, 5e5]:
        scenarios.append(SimulationConfig(
            name=f"load_rate{data_rate:.0e}",
            n_nodes=32,
            mac_protocol="csma_ca",
            routing_protocol="flooding",
            path_loss_exp=2.5,
            fading_std=2.0,
            noise_floor_dbm=-100,
            sinr_threshold_db=20,
            data_rate=data_rate,
            step_size=1e-7,
            duration=1.0
        ))
    
    return scenarios