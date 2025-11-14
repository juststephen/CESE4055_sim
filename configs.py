from mac import MACAloha, MAC_CSMA_CA, MAC_MACA_PR
from routing import RoutingNone, RoutingFlooding, RoutingAODV


EXPERIMENTS = {
    'aloha_test': {
        "COORD_MAX": 500,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e2},
        "MAC_TYPE": MACAloha,
        "MAC_PARAM": {"bitrate": 2e6},
        "ROUTING_TYPE": RoutingNone,
        "ROUTING_PARAM": {}
    },
    'csma_noroute': {
        "COORD_MAX": 500,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e4},
        "MAC_TYPE": MAC_CSMA_CA,
        "MAC_PARAM": {"bitrate": 2e6,"buf_len": 20,"difs": 3e-3,"n": 16,"cf": 1e-3},
        "ROUTING_TYPE": RoutingNone,
        "ROUTING_PARAM": {}
    },
    'csma_flooding': {
        "COORD_MAX": 20000,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e3},
        "MAC_TYPE": MAC_CSMA_CA,
        "MAC_PARAM": {"bitrate": 2e6,"buf_len": 20,"difs": 3e-3,"n": 16,"cf": 1e-3},
        "ROUTING_TYPE": RoutingFlooding,
        "ROUTING_PARAM": {}
    },
    'csma_aodv': {
        "COORD_MAX": 500,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e2}, #48.1%
        "MAC_TYPE": MAC_CSMA_CA,
        "MAC_PARAM": {"bitrate": 2e6,"buf_len": 20,"difs": 3e-3,"n": 16,"cf": 1e-3},
        "ROUTING_TYPE": RoutingAODV,
        "ROUTING_PARAM": {"route_lifetime": 5.0, "rreq_timeout": 1.0, "rreq_retry_limit": 5}
    },
    'maca_noroute': {
        "COORD_MAX": 500,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e3},
        "MAC_TYPE": MAC_MACA_PR,
        "MAC_PARAM": {"bitrate": 2e6, "buf_len": 5, "n_slots": 20, "t_slot": 1e-3, "t_cts_timeout": 5e-4, "cw_base": 4},
        "ROUTING_TYPE": RoutingNone,
        "ROUTING_PARAM": {}
    },
    'maca_flooding': {
        "COORD_MAX": 20000,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e4},
        "MAC_TYPE": MAC_MACA_PR,
        "MAC_PARAM": {"bitrate": 2e6, "buf_len": 5, "n_slots": 20, "t_slot": 1e-3, "t_cts_timeout": 5e-4, "cw_base": 4},
        "ROUTING_TYPE": RoutingFlooding,
        "ROUTING_PARAM": {}
    },
    'maca_aodv': {
        "COORD_MAX": 20000,
        "THREAD_PARAM": {"step_size": 1e-5, "data_rate": 1e4},
        "MAC_TYPE": MAC_MACA_PR,
        "MAC_PARAM": {"bitrate": 2e6, "buf_len": 5, "n_slots": 20, "t_slot": 1e-3, "t_cts_timeout": 5e-4, "cw_base": 4},
        "ROUTING_TYPE": RoutingAODV,
        "ROUTING_PARAM": {"route_lifetime": 5.0, "rreq_timeout": 1.0, "rreq_retry_limit": 5}
    }
}