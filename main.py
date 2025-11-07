from typing import Any
import numpy as np
from PySide6.QtWidgets import QApplication
import sys

from mac import MACAloha, MAC_CSMA_CA
from medium import Medium, Node2D
from ui import MainWindow
from routing import RoutingNone, RoutingFlooding

np.random.seed(0)

# Demonstration configurations

# # Config: Aloha with full coverage (no routing)
# COORD_MAX: float = 1e3
# THREAD_PARAM: dict[str, Any] = {
#     "step_size": 1e-7,
#     "data_rate": 1e6
# }
# MAC_TYPE = MACAloha
# MAC_PARAM: dict[str, Any] = {
#     "bitrate": 2e7,
# }
# ROUTING_TYPE = RoutingNone

# Config: CSMA/CA with low coverage, flooding as routing protocol
COORD_MAX: float = 1e5
THREAD_PARAM: dict[str, Any] = {
    "step_size": 1e-5,
    "data_rate": 1e4
}
MAC_TYPE = MAC_CSMA_CA
MAC_PARAM: dict[str, Any] = {
    "bitrate": 2e6,
    "buf_len": 5,
    "difs": 1e-4,
    "n": 16,
    "cf": 4e-5
}
ROUTING_TYPE = RoutingFlooding

m = Medium[Node2D]()
nodes = []
for _ in range(1048):
    x, y = np.random.uniform(-COORD_MAX, COORD_MAX, size=2)
    n = Node2D(x, y, MAC_TYPE, ROUTING_TYPE, mac_param=MAC_PARAM)
    m.add_node(n)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(m, thread_param=THREAD_PARAM)
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())
